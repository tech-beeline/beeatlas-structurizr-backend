"""
Утилиты для проверок CTX.01–CTX.03 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.context.check_context`` для оценок
CTX.01 (systemContextViews), CTX.02 (подписи связей), CTX.03 (технология связей).
Без импортов structurizr_utils.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def _same_system_id(left: Any, right: Any) -> bool:
    """Сравнение идентификаторов системы (int/str из JSON)."""
    return str(left) == str(right)


def analyze_ctx_workspace(
    data: Dict[str, Any],
    cmdb: str,
) -> Tuple[bool, bool, bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Анализ контекстных диаграмм для системы с кодом ``cmdb`` (``productCode``).

    Returns:
        (ctx01_ok, ctx02_ok, ctx03_ok, rows_ctx01, rows_ctx02, rows_ctx03)
        Словари в ``rows_*`` — поля для Pydantic Detail моделей (``code``, ``name``, ``date``, ``status``, ``check``).
        Поле ``date`` — ``properties.modified`` целевой softwareSystem (или ``""``).
        Для CTX.03 дополнительно ``target_name`` (приёмник) и ``technology`` (значение из связи).
    """
    cmdb_l = cmdb.lower().strip()
    model = data.get("model") or {}
    views = data.get("views") or {}
    systems: List[Dict[str, Any]] = model.get("softwareSystems") or []

    system_name_by_id: Dict[str, str] = {}
    for s in systems:
        sid = str(s.get("id", ""))
        if sid:
            system_name_by_id[sid] = str(s.get("name", "")).strip()

    system_id: Any = None
    system_modified: str = ""
    target_system: Dict[str, Any] | None = None

    for s in systems:
        if str((s.get("properties") or {}).get("cmdb", "")).lower().strip() != cmdb_l:
            continue
        target_system = s
        system_id = s.get("id")
        raw_modified = (s.get("properties") or {}).get("modified")
        system_modified = str(raw_modified) if raw_modified is not None else ""
        logger.info("CTX: найдена система id=%s для cmdb=%s", system_id, cmdb)
        break

    context_views: List[Dict[str, Any]] = []
    if system_id is not None:
        for v in views.get("systemContextViews") or []:
            if _same_system_id(v.get("softwareSystemId"), system_id):
                context_views.append(v)
                logger.debug(
                    "CTX: systemContextView key=%s system=%s",
                    v.get("key"),
                    system_id,
                )

    entries_ctx01: List[Dict[str, str]] = []
    for v in context_views:
        vk = str(v.get("key", v.get("id", f"view_{len(entries_ctx01) + 1}")))
        title = str(v.get("title", "Context Diagram"))
        entries_ctx01.append({"view_key": vk, "title": title})

    relationship_rows: List[Dict[str, Any]] = []

    if target_system is not None and context_views:
        for rel in target_system.get("relationships") or []:
            rid_raw = rel.get("id")
            if rid_raw is None:
                continue
            rid = str(rid_raw)
            description = str(rel.get("description", "") or "").strip()
            technology = str(rel.get("technology", "") or "").strip()
            dest_raw = rel.get("destinationId")
            dest_id = str(dest_raw) if dest_raw is not None else ""
            target_name = system_name_by_id.get(dest_id, "") or dest_id
            relationship_rows.append(
                {
                    "relationship_id": rid,
                    "target_name": target_name,
                    "description": description,
                    "technology": technology,
                    "has_description": bool(description),
                    "has_technology": bool(technology),
                }
            )

    ctx01_ok = len(entries_ctx01) > 0
    # Как в check_context: без systemContextView связи не анализируются — CTX.02/03 не падают.
    if not ctx01_ok:
        ctx02_ok = True
        ctx03_ok = True
    else:
        ctx02_ok = all(r["has_description"] for r in relationship_rows)
        ctx03_ok = all(r["has_technology"] for r in relationship_rows)

    rows_ctx01: List[Dict[str, Any]] = []
    if ctx01_ok:
        for e in entries_ctx01:
            rows_ctx01.append(
                {
                    "code": e["view_key"],
                    "name": e["title"],
                    "date": system_modified,
                    "status": "OK",
                    "check": True,
                }
            )
    else:
        rows_ctx01.append(
            {
                "code": "CTX.01",
                "name": "Не найдена контекстная диаграмма для данной системы",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        )

    rows_ctx02: List[Dict[str, Any]] = []
    if not ctx01_ok:
        rows_ctx02.append(
            {
                "code": "CTX.02",
                "name": "Контекстная диаграмма отсутствует — проверка подписей связей не требовалась",
                "date": system_modified,
                "status": "OK",
                "check": True,
            }
        )
    elif relationship_rows:
        for r in relationship_rows:
            if not r["has_description"]:
                continue
            tn = r["target_name"]
            suffix = f" → {tn}" if tn else ""
            rows_ctx02.append(
                {
                    "code": r["relationship_id"],
                    "name": f"{r['description']}{suffix}",
                    "date": system_modified,
                    "status": "OK",
                    "check": True,
                }
            )
        for r in relationship_rows:
            if r["has_description"]:
                continue
            tn = r["target_name"]
            suffix = f" → {tn}" if tn else ""
            rows_ctx02.append(
                {
                    "code": r["relationship_id"],
                    "name": f"Связь без названия{suffix}",
                    "date": system_modified,
                    "status": "FAIL",
                    "check": False,
                }
            )
    else:
        rows_ctx02.append(
            {
                "code": "CTX.02",
                "name": "На контекстной диаграмме нет связей для проверки",
                "date": system_modified,
                "status": "OK",
                "check": True,
            }
        )

    rows_ctx03: List[Dict[str, Any]] = []
    if not ctx01_ok:
        rows_ctx03.append(
            {
                "code": "CTX.03",
                "name": "Контекстная диаграмма отсутствует — проверка технологий связей не требовалась",
                "date": system_modified,
                "status": "OK",
                "check": True,
                "target_name": "",
                "technology": "",
            }
        )
    elif relationship_rows:
        for r in relationship_rows:
            if not r["has_technology"]:
                continue
            tn = r["target_name"]
            tech = r["technology"]
            desc = r["description"] or "—"
            suffix = f" → {tn}" if tn else ""
            rows_ctx03.append(
                {
                    "code": r["relationship_id"],
                    "name": f"{desc}{suffix}: {tech}",
                    "date": system_modified,
                    "status": "OK",
                    "check": True,
                    "target_name": tn,
                    "technology": tech,
                }
            )
        for r in relationship_rows:
            if r["has_technology"]:
                continue
            tn = r["target_name"]
            desc = r["description"] or "Описание связи отсутствует"
            suffix = f" → {tn}" if tn else ""
            rows_ctx03.append(
                {
                    "code": r["relationship_id"],
                    "name": f"Связь без технологии{suffix}: {desc}",
                    "date": system_modified,
                    "status": "FAIL",
                    "check": False,
                    "target_name": tn,
                    "technology": "",
                }
            )
    else:
        rows_ctx03.append(
            {
                "code": "CTX.03",
                "name": "На контекстной диаграмме нет связей для проверки",
                "date": system_modified,
                "status": "OK",
                "check": True,
                "target_name": "",
                "technology": "",
            }
        )

    if target_system is None:
        not_found = "Система не найдена по cmdb (productCode)"
        for rows in (rows_ctx01, rows_ctx02, rows_ctx03):
            rows.clear()
            rows.append(
                {
                    "code": "CTX.01",
                    "name": not_found,
                    "date": "",
                    "status": "FAIL",
                    "check": False,
                }
            )
        rows_ctx02[0]["code"] = "CTX.02"
        rows_ctx03[0]["code"] = "CTX.03"
        rows_ctx03[0]["target_name"] = ""
        rows_ctx03[0]["technology"] = ""
        return False, False, False, rows_ctx01, rows_ctx02, rows_ctx03

    return ctx01_ok, ctx02_ok, ctx03_ok, rows_ctx01, rows_ctx02, rows_ctx03
