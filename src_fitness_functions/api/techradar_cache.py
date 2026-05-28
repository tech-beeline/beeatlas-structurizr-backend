"""
Кеш справочника TechRadar (read-through, TTL).

Источник данных — HTTP через :class:`src_fitness_functions.beeatlas_api.BeeAtlasAPI`
(``fetch_all_tech``, ``fetch_product_tech``). При каждом обращении удаляются записи с истёкшим TTL.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Tuple

from src_fitness_functions.beeatlas_api import get_beeatlas_api

logger = logging.getLogger(__name__)

TTL_SECONDS = 15 * 60
_INFRASTRUCTURE_SECTORS = ("Управление данными", "Платформа и инфраструктура")

_lock = threading.Lock()
# monotonic_ts_at_store -> (all_tech, product_tech)
_cache: Dict[str, Tuple[float, Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]] = {}
_CATALOG_KEY = "catalog"


def _purge_expired(now: float) -> None:
    expired = [key for key, (ts, _) in _cache.items() if now - ts > TTL_SECONDS]
    for key in expired:
        del _cache[key]
        logger.debug("techradar_cache: expired evicted key=%s", key)


def get_cached_techradar_catalog() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Read-through: все технологии и product-tech из кеша или подгрузить с TechRadar.

    Пустые ответы API кешируются (повторные вызовы не бьют в сеть до истечения TTL).
    """
    now = time.monotonic()
    with _lock:
        _purge_expired(now)
        hit = _cache.get(_CATALOG_KEY)
        if hit is not None:
            ts, payload = hit
            if now - ts <= TTL_SECONDS:
                techs, product_tech = payload
                logger.debug(
                    "techradar_cache: hit age_s=%.1f techs=%s product_tech=%s",
                    now - ts,
                    len(techs),
                    len(product_tech),
                )
                return techs, product_tech
            del _cache[_CATALOG_KEY]

        api = get_beeatlas_api()
        techs = api.fetch_all_tech()
        product_tech = api.fetch_product_tech()
        _cache[_CATALOG_KEY] = (time.monotonic(), (techs, product_tech))
        logger.debug(
            "techradar_cache: miss loaded techs=%s product_tech=%s",
            len(techs),
            len(product_tech),
        )
        return techs, product_tech


def get_cached_infrastructure_labels() -> List[str]:
    """Метки технологий инфраструктурных секторов (из кешированного ``/api/v1/tech``)."""
    labels: List[str] = []
    for item in get_cached_techradar_catalog()[0]:
        if not isinstance(item, dict):
            continue
        sector = item.get("sector") or {}
        sector_name = sector.get("name") if isinstance(sector, dict) else ""
        if sector_name not in _INFRASTRUCTURE_SECTORS:
            continue
        label = str(item.get("label", "") or "").lower().strip()
        if label:
            labels.append(label)
    return labels
