"""
Кеш workspace-документов по docId (read-through, TTL).

Источник данных — HTTP ``GET`` Document Service через
:class:`src_fitness_functions.beeatlas_api.BeeAtlasAPI`.
При каждом обращении удаляются записи с истёкшим TTL.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Tuple

from src_fitness_functions.beeatlas_api import get_beeatlas_api

logger = logging.getLogger(__name__)

TTL_SECONDS = 15 * 60

_lock = threading.Lock()
# doc_id -> (monotonic_ts_at_store, payload)
_cache: Dict[int, Tuple[float, Dict[str, Any]]] = {}


def _purge_expired(now: float) -> None:
    """Удалить из кеша записи старше TTL (вызывается под lock)."""
    expired = [doc_id for doc_id, (ts, _) in _cache.items() if now - ts > TTL_SECONDS]
    for doc_id in expired:
        del _cache[doc_id]
        logger.debug("document_cache: expired evicted doc_id=%s", doc_id)


def get_cached_workspace(document_id: int) -> Dict[str, Any]:
    """
    Read-through: вернуть JSON workspace для docId из кеша или подгрузить и положить в кеш.

    Успешные ответы кешируются на TTL_SECONDS. Ошибки загрузки документа не кешируются.
    """
    now = time.monotonic()
    with _lock:
        _purge_expired(now)
        hit = _cache.get(document_id)
        if hit is not None:
            ts, payload = hit
            age = now - ts
            if age <= TTL_SECONDS:
                logger.debug(
                    "document_cache: hit doc_id=%s age_s=%.1f",
                    document_id,
                    age,
                )
                return payload
            del _cache[document_id]

        data = get_beeatlas_api().get_workspace_document(document_id)
        _cache[document_id] = (time.monotonic(), data)
        logger.debug("document_cache: miss loaded doc_id=%s", document_id)
        return data
