"""
HTTP-доступ к внешним сервисам для fitness functions (FDM / BeeAtlas-контур)
через единый API Gateway с HMAC авторизацией.

Централизует вызовы, которые ранее выполнялись через ``requests`` напрямую
к индивидуальным сервисам:

- **Document Service** — JSON workspace по ``docId``;
- **Capability API** — ``GET .../tech-capabilities/product/{id}``;
- **Products API** — ``GET .../product/infra``, ``GET .../product/{cmdb}/container``;
- **TechRadar** — ``GET /tech``, ``GET /tech/product-tech``;
- **Произвольные HTTPS URL** — загрузка текста OpenAPI-спецификаций для API.01–API.03.

Конфигурация (env-переменные):
- ``GATEWAY_URL`` — базовый URL API Gateway
- ``API_KEY`` — ключ для HMAC авторизации
- ``API_SECRET`` — секрет для HMAC авторизации
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import HTTPException

from src_fitness_functions.config import settings
from src_fitness_functions.sdk.auth import HMACAuth
from src_fitness_functions.sdk.http_client import HTTPClient
from src_fitness_functions.sdk.exceptions import (
    GatewayException,
    NotFoundError,
)

logger = logging.getLogger(__name__)

_INFRASTRUCTURE_SECTORS = ("Управление данными", "Платформа и инфраструктура")

_default_api: Optional["BeeAtlasAPI"] = None


class BeeAtlasAPI:
    """HTTP-вызовы к Document Service, Capability, Products, TechRadar
    через единый API Gateway с HMAC-SHA256 авторизацией."""

    def __init__(
        self,
        *,
        gateway_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: int = 60,
        verify_ssl: bool = False,
    ) -> None:
        gw_url = (
            gateway_url
            or settings.gateway_url
            or os.getenv("GATEWAY_URL", "")
        )
        key = (
            api_key
            or settings.api_key
            or os.getenv("API_KEY", "")
        )
        secret = (
            api_secret
            or settings.api_secret
            or os.getenv("API_SECRET", "")
        )

        if not gw_url:
            raise ValueError(
                "GATEWAY_URL не задан. Укажите переменную окружения GATEWAY_URL "
                "или передайте gateway_url в конструктор."
            )

        self._http = HTTPClient(
            base_url=gw_url,
            auth=HMACAuth(key, secret) if key and secret else None,
            timeout=timeout,
            retries=3,
            verify_ssl=verify_ssl,
        )

        # Отдельная сессия для загрузки произвольных URL (OpenAPI-спеки и т.д.)
        # — без HMAC авторизации, без привязки к gateway.
        self._raw_session = requests.Session()

    # ------------------------------------------------------------------
    # Document Service
    # ------------------------------------------------------------------

    def get_workspace_document(
        self,
        document_id: int,
        *,
        user_id: Optional[str] = None,
        user_roles: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ``GET /api-gateway/document/v1/documents/{id}`` — workspace JSON.

        Тот же контракт, что у ``structurizr_utils.models.model_documents.get_document``.
        """
        path = f"/api-gateway/document/v1/documents/{document_id}"
        headers: Dict[str, str] = {}
        if user_id:
            headers["user-id"] = str(user_id)
        if user_roles:
            headers["user-roles"] = user_roles

        try:
            result = self._http.get(path, headers=headers)
            if isinstance(result, dict):
                return result
            # Если вернулась строка — попробуем распарсить
            import json
            return json.loads(result)
        except GatewayException as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # ------------------------------------------------------------------
    # Capability API
    # ------------------------------------------------------------------

    def fetch_capability_responsibility(
        self, product_id: int, *, timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        GET ``/api-gateway/capability/v1/tech-capabilities/product/{id}``
        — список ``responsibility``.

        При ошибке сети или HTTP возвращает пустой список.
        """
        if product_id <= 0:
            return []

        path = f"/api-gateway/capability/v1/tech-capabilities/product/{product_id}"
        try:
            body = self._http.get(path)
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

    # ------------------------------------------------------------------
    # Products API
    # ------------------------------------------------------------------

    def fetch_product_infra_parents(
        self, name: str, *, timeout: int = 30
    ) -> List[str]:
        """
        GET ``/api-gateway/product/v1/product/infra?name=...``
        — ``parentSystems``.

        При ошибке возвращает пустой список.
        """
        if not (name or "").strip():
            return []

        path = "/product/api/v1/product/infra"
        try:
            body = self._http.get(path, params={"name": name.strip()})
        except NotFoundError:
            return []
        except Exception as e:
            logger.warning(
                "Products API infra lookup error for name=%s: %s", name, e
            )
            return []

        parents = body.get("parentSystems") if isinstance(body, dict) else []
        if not isinstance(parents, list):
            return []
        return [str(p).strip() for p in parents if str(p).strip()]

    def fetch_product_containers(
        self, cmdb: str, *, timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        GET ``/api-gateway/product/v1/product/{cmdb}/container``
        — контейнеры продукта.

        При ошибке возвращает пустой список.
        """
        cmdb_s = str(cmdb or "").strip()
        if not cmdb_s:
            return []

        path = f"/api-gateway/product/v1/product/{cmdb_s}/container"
        try:
            body = self._http.get(path)
        except NotFoundError:
            return []
        except Exception as e:
            logger.warning(
                "Products API containers fetch error cmdb=%s: %s", cmdb_s, e
            )
            return []

        if isinstance(body, list):
            return [c for c in body if isinstance(c, dict)]
        return []

    # ------------------------------------------------------------------
    # TechRadar
    # ------------------------------------------------------------------

    def fetch_all_tech(self, *, timeout: int = 60) -> List[Dict[str, Any]]:
        """GET ``/api-gateway/techradar/v1/tech`` — все технологии TechRadar."""
        path = "/api-gateway/techradar/v1/tech"
        try:
            body = self._http.get(path)
        except Exception as e:
            logger.warning("TechRadar /tech error: %s", e)
            return []

        return (
            [t for t in body if isinstance(t, dict)]
            if isinstance(body, list)
            else []
        )

    def fetch_product_tech(self, *, timeout: int = 60) -> List[Dict[str, Any]]:
        """GET ``/api-gateway/techradar/v1/tech/product-tech`` — технологии продуктов."""
        path = "/api-gateway/techradar/v1/tech/product-tech"
        try:
            body = self._http.get(path)
        except Exception as e:
            logger.warning("TechRadar product-tech error: %s", e)
            return []

        return (
            [p for p in body if isinstance(p, dict)]
            if isinstance(body, list)
            else []
        )

    def fetch_techradar_infrastructure_labels(
        self, *, timeout: int = 60
    ) -> List[str]:
        """
        Метки технологий из секторов инфраструктуры TechRadar.
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

    # ------------------------------------------------------------------
    # Произвольные HTTP URL (OpenAPI-спеки и т.п.)
    # ------------------------------------------------------------------

    def download_http_text(
        self,
        url: str,
        *,
        timeout: int = 5,
        headers: Optional[Dict[str, str]] = None,
        verify: bool = False,
    ) -> str:
        """
        GET по ``http``/``https``; при ошибке или не-200 — пустая строка.

        Используется для загрузки OpenAPI-спецификаций по произвольным URL.
        Не проходит через API Gateway и не использует HMAC авторизацию.
        """
        try:
            hdrs = headers if headers is not None else {}
            response = self._raw_session.get(
                url, headers=hdrs, verify=verify, timeout=timeout
            )
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
    Workspace JSON для роутеров ``ff_*`` — Document Service через
    ``get_beeatlas_api().get_workspace_document`` и TTL-кеш
    ``document_cache`` (read-through).
    """
    from src_fitness_functions.api import document_cache

    return document_cache.get_cached_workspace(document_id)