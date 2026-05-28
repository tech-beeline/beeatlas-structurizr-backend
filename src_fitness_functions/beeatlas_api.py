"""
HTTP-доступ к внешним сервисам для fitness functions (FDM / BeeAtlas-контур).

Централизует вызовы, которые ранее выполнялись через ``requests`` в
``structurizr_utils.models.model_documents``, ``sdk.capability_utils`` и
``sdk.api_utils.ApiSpecLoader``:

- **Document Service** — JSON workspace по ``docId`` (роутеры ``ff_*`` вызывают ``get_workspace_json_cached``, внутри — TTL ``document_cache`` и ``BeeAtlasAPI.get_workspace_document``);
- **Capability API** — ``GET .../tech-capabilities/product/{id}`` (ветка landscape / CPB.01);
- **Products API** — ``GET .../product/infra`` (DEP.03), ``GET .../product/{cmdb}/container`` (SQ.01);
- **TechRadar** — ``GET /api/v1/tech``, ``GET /api/v1/tech/product-tech`` (низкоуровневые вызовы; для FF — read-through кеш в [`techradar_cache`](src_fitness_functions/api/techradar_cache.py));
- **Произвольные HTTPS URL** — загрузка текста OpenAPI-спецификаций для API.01–API.03.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import HTTPException
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

_DEFAULT_DOCUMENTS_BASE = (
    "https://document-service-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru"
)
_DEFAULT_CAPABILITY_BASE = (
    "https://capability-backend-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru"
)
_DEFAULT_TECHRADAR_BASE = (
    "https://techradar-backend-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru"
)
_INFRASTRUCTURE_SECTORS = ("Управление данными", "Платформа и инфраструктура")

_default_api: Optional["BeeAtlasAPI"] = None


class BeeAtlasAPI:
    """Синхронные HTTP-вызовы к Document Service, Capability backend и внешним URL."""

    def __init__(
        self,
        *,
        documents_base_url: Optional[str] = None,
        capability_base_url: Optional[str] = None,
        products_base_url: Optional[str] = None,
        techradar_base_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.documents_base_url = (
            documents_base_url or os.getenv("URL_DOCUMENTS") or _DEFAULT_DOCUMENTS_BASE
        ).rstrip("/")
        self.capability_base_url = (
            capability_base_url or os.getenv("CAPABILITY_API_URL") or _DEFAULT_CAPABILITY_BASE
        ).rstrip("/")
        self.products_base_url = (products_base_url or os.getenv("URL_PRODUCTS") or "").rstrip("/")
        self.techradar_base_url = (
            techradar_base_url or os.getenv("URL_TECHRADAR") or _DEFAULT_TECHRADAR_BASE
        ).rstrip("/")
        self._session = session or requests.Session()

    def get_workspace_document(
        self,
        document_id: int,
        *,
        user_id: Optional[str] = None,
        user_roles: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ``GET {URL_DOCUMENTS}/api/v1/documents/{id}`` — тот же контракт, что у
        ``structurizr_utils.models.model_documents.get_document``.
        """
        url = f"{self.documents_base_url}/api/v1/documents/{document_id}"
        headers: Dict[str, str] = {}
        if user_id:
            headers["user-id"] = str(user_id)
        if user_roles:
            headers["user-roles"] = user_roles
        response = self._session.get(url, headers=headers, verify=False, timeout=60)
        if response.status_code == 200:
            return json.loads(response.content)
        raise HTTPException(status_code=response.status_code, detail=response.text)

    def fetch_capability_responsibility(self, product_id: int, *, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        GET ``/api/v1/tech-capabilities/product/{id}`` — список ``responsibility`` (как ``load_capabilities``).

        При ошибке сети или HTTP возвращает пустой список.
        """
        if product_id <= 0:
            return []
        url = urljoin(self.capability_base_url + "/", f"api/v1/tech-capabilities/product/{product_id}")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            r = self._session.get(url, headers=headers, verify=False, timeout=timeout)
            r.raise_for_status()
            body = r.json()
        except Exception as e:
            logger.warning("Capability API responsibility fetch failed: %s", e)
            return []
        resp = body if isinstance(body, dict) else {}
        rows = resp.get("responsibility")
        if not isinstance(rows, list):
            return []
        out: List[Dict[str, Any]] = []
        for item in rows:
            if isinstance(item, dict) and item.get("code"):
                out.append(item)
        return out

    def fetch_product_infra_parents(self, name: str, *, timeout: int = 30) -> List[str]:
        """
        GET ``/api/v1/product/infra?name=...`` — ``parentSystems`` (как ``get_product_infra``).

        При ошибке или не заданном ``URL_PRODUCTS`` возвращает пустой список.
        """
        if not self.products_base_url or not (name or "").strip():
            return []
        url = f"{self.products_base_url}/api/v1/product/infra"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            r = self._session.get(
                url,
                params={"name": name.strip()},
                headers=headers,
                verify=False,
                timeout=timeout,
            )
            if r.status_code not in (200, 204):
                logger.warning(
                    "Products API infra lookup failed: %s %s for name=%s",
                    r.status_code,
                    r.reason,
                    name,
                )
                return []
            body = r.json() if r.content else {}
            parents = body.get("parentSystems") if isinstance(body, dict) else []
            if not isinstance(parents, list):
                return []
            return [str(p).strip() for p in parents if str(p).strip()]
        except Exception as e:
            logger.warning("Products API infra lookup error for name=%s: %s", name, e)
            return []

    def fetch_product_containers(self, cmdb: str, *, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        GET ``/api/v1/product/{cmdb}/container`` — контейнеры продукта (как ``get_product_containers``).

        При ошибке или не заданном ``URL_PRODUCTS`` возвращает пустой список.
        """
        cmdb_s = str(cmdb or "").strip()
        if not self.products_base_url or not cmdb_s:
            return []
        url = f"{self.products_base_url}/api/v1/product/{cmdb_s}/container"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            r = self._session.get(url, headers=headers, verify=False, timeout=timeout)
            if r.status_code not in (200, 204):
                logger.warning(
                    "Products API containers fetch failed: %s %s cmdb=%s",
                    r.status_code,
                    r.reason,
                    cmdb_s,
                )
                return []
            body = r.json() if r.content else []
            if isinstance(body, list):
                return [c for c in body if isinstance(c, dict)]
            return []
        except Exception as e:
            logger.warning("Products API containers fetch error cmdb=%s: %s", cmdb_s, e)
            return []

    def fetch_all_tech(self, *, timeout: int = 60) -> List[Dict[str, Any]]:
        """GET ``/api/v1/tech`` — все технологии TechRadar (как ``get_all_tech``)."""
        if not self.techradar_base_url:
            return []
        url = f"{self.techradar_base_url}/api/v1/tech"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            r = self._session.get(url, headers=headers, verify=False, timeout=timeout)
            if r.status_code not in (200, 204):
                logger.warning("TechRadar /tech failed: %s %s", r.status_code, r.reason)
                return []
            body = r.json() if r.content else []
            return [t for t in body if isinstance(t, dict)] if isinstance(body, list) else []
        except Exception as e:
            logger.warning("TechRadar /tech error: %s", e)
            return []

    def fetch_product_tech(self, *, timeout: int = 60) -> List[Dict[str, Any]]:
        """GET ``/api/v1/tech/product-tech`` — технологии продуктов (как ``get_product_tech``)."""
        if not self.techradar_base_url:
            return []
        url = f"{self.techradar_base_url}/api/v1/tech/product-tech"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            r = self._session.get(url, headers=headers, verify=False, timeout=timeout)
            if r.status_code not in (200, 204):
                logger.warning("TechRadar product-tech failed: %s %s", r.status_code, r.reason)
                return []
            body = r.json() if r.content else []
            return [p for p in body if isinstance(p, dict)] if isinstance(body, list) else []
        except Exception as e:
            logger.warning("TechRadar product-tech error: %s", e)
            return []

    def fetch_techradar_infrastructure_labels(self, *, timeout: int = 60) -> List[str]:
        """
        Метки технологий из секторов инфраструктуры TechRadar (как в ``check_container`` / GIT.01).
        """
        labels: List[str] = []
        for item in self.fetch_all_tech(timeout=timeout):
            sector = item.get("sector") or {}
            sector_name = sector.get("name") if isinstance(sector, dict) else ""
            if sector_name not in _INFRASTRUCTURE_SECTORS:
                continue
            label = str(item.get("label", "") or "").lower().strip()
            if label:
                labels.append(label)
        return labels

    def download_http_text(
        self,
        url: str,
        *,
        timeout: int = 5,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = False,
    ) -> str:
        """
        GET по ``http``/``https``; при ошибке или не-200 — пустая строка (как в ``ApiSpecLoader``).
        """
        try:
            hdrs = headers if headers is not None else {}
            response = self._session.get(url, headers=hdrs, verify=verify, timeout=timeout)
            if response.status_code == 200:
                return response.text
            logger.warning(
                "Ошибка загрузки по HTTP: %s %s",
                response.status_code,
                response.reason,
            )
        except Exception as e:
            logger.error("Ошибка при загрузке по HTTP: %s", e)
        return ""


def get_beeatlas_api() -> BeeAtlasAPI:
    """Общий экземпляр клиента для роутеров ``ff_*`` и SDK."""
    global _default_api
    if _default_api is None:
        _default_api = BeeAtlasAPI()
    return _default_api


def get_workspace_json_cached(document_id: int) -> Dict[str, Any]:
    """
    Workspace JSON для роутеров ``ff_*`` — Document Service через ``get_beeatlas_api().get_workspace_document``
    и TTL-кеш ``document_cache`` (read-through).
    """
    from src_fitness_functions.api import document_cache

    return document_cache.get_cached_workspace(document_id)
