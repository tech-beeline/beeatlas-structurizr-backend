"""
Утилиты для проверок CNT.01–CNT.03 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.container.check_container`` для
оценок CNT.01 (контейнеры), CNT.02 (containerViews), CNT.03 (технология у связей
между контейнерами). Без импортов structurizr_utils; без Techradar / GIT / SEC.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def _same_system_id(left: Any, right: Any) -> bool:
    """Сравнение идентификаторов системы (int/str из JSON)."""
    return str(left) == str(right)


def analyze_cnt_workspace(
    data: Dict[str, Any],
    cmdb: str,
) -> Tuple[bool, bool, bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Анализ контейнерной модели для системы с кодом ``cmdb``.

    Returns:
        (cnt01_ok, cnt02_ok, cnt03_ok, rows_cnt01, rows_cnt02, rows_cnt03)
        Словари в ``rows_*`` — поля для Pydantic Detail моделей.
        Для CNT.01 в ``rows_cnt01`` дополнительно поля ``technology`` и ``tags`` контейнера.
        Поле ``date`` во всех ``rows_*`` — ``properties.modified`` найденной softwareSystem (или ``""``).
        Для CNT.03 в ``rows_cnt03`` дополнительно ``source_name`` и ``target_name``
        (приёмник: имя контейнера по ``destinationId``, иначе имя softwareSystem, иначе сам id).
    """
    cmdb_l = cmdb.lower().strip()
    systems: List[Dict[str, Any]] = data.get("model", {}).get("softwareSystems", [])

    all_container_names: Dict[str, str] = {}
    all_software_system_names: Dict[str, str] = {}
    for s in systems:
        sid_k = str(s.get("id", ""))
        if sid_k:
            all_software_system_names[sid_k] = str(s.get("name", ""))
        for c in s.get("containers", []) or []:
            cid_k = str(c.get("id", ""))
            if cid_k:
                all_container_names[cid_k] = str(c.get("name", ""))

    system_id: Any = -1
    system_modified: str = ""
    entries_cnt01: List[Dict[str, Any]] = []
    relationships: Dict[str, Dict[str, Any]] = {}
    violations_cnt03: List[Dict[str, str]] = []

    for s in systems:
        if str(s.get("properties", {}).get("cmdb", "")).lower().strip() != cmdb_l:
            continue
        system_id = s.get("id", 0)
        props = s.get("properties") or {}
        raw_modified = props.get("modified")
        system_modified = str(raw_modified) if raw_modified is not None else ""
        logger.info("CNT: найдена система id=%s для cmdb=%s", system_id, cmdb)

        for c in s.get("containers", []) or []:
            cid = c.get("id", "")
            container_name = c.get("name", f"Container {len(entries_cnt01) + 1}")
            tech_raw = c.get("technology", "")
            technology = str(tech_raw) if tech_raw is not None else ""
            raw_tags = c.get("tags", [])
            if isinstance(raw_tags, list):
                tags = [str(t) for t in raw_tags]
            else:
                tags = []
            entries_cnt01.append(
                {
                    "container_id": str(cid),
                    "container_name": str(container_name),
                    "technology": technology,
                    "tags": tags,
                }
            )

            for r in c.get("relationships", []) or []:
                rid = r.get("id")
                if rid is None:
                    continue
                rel = dict(r)
                rel["source_name"] = container_name
                relationships[str(rid)] = rel

        break

    for rid, rel in relationships.items():
        tech = rel.get("technology", "")
        if tech == "":
            source = str(rel.get("source_name", ""))
            desc = str(rel.get("description", "Описание связи отсутствует"))
            dest_raw = rel.get("destinationId")
            dest_id = str(dest_raw) if dest_raw is not None else ""
            target_name = (
                all_container_names.get(dest_id, "")
                or all_software_system_names.get(dest_id, "")
                or dest_id
            )
            violations_cnt03.append(
                {
                    "relationship_id": str(rid),
                    "source_name": source,
                    "target_name": target_name,
                    "description": desc,
                }
            )
            logger.warning("CNT.03: связь без технологии id=%s %s", rid, desc)

    cnt01_ok = len(entries_cnt01) > 0

    container_views = data.get("views", {}).get("containerViews") or []
    entries_cnt02: List[Dict[str, str]] = []
    for v in container_views:
        if _same_system_id(v.get("softwareSystemId", 0), system_id):
            vk = str(v.get("key", v.get("id", f"view_{len(entries_cnt02) + 1}")))
            title = str(v.get("title", f"Container View {len(entries_cnt02) + 1}"))
            entries_cnt02.append({"view_key": vk, "title": title})
            logger.debug("CNT.02: containerView key=%s system=%s", vk, system_id)

    cnt02_ok = len(entries_cnt02) > 0
    cnt03_ok = len(violations_cnt03) == 0

    rows_cnt01: List[Dict[str, Any]] = []
    if cnt01_ok:
        for e in entries_cnt01:
            rows_cnt01.append(
                {
                    "code": e["container_id"],
                    "name": e["container_name"],
                    "date": system_modified,
                    "status": "OK",
                    "check": True,
                    "technology": e.get("technology", ""),
                    "tags": list(e.get("tags", [])),
                }
            )
    else:
        rows_cnt01.append(
            {
                "code": "CNT.01",
                "name": "Система не содержит контейнеров или не найдена по cmdb",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
                "technology": "",
                "tags": [],
            }
        )

    rows_cnt02: List[Dict[str, Any]] = []
    if cnt02_ok:
        for e in entries_cnt02:
            rows_cnt02.append(
                {
                    "code": e["view_key"],
                    "name": e["title"],
                    "date": system_modified,
                    "status": "OK",
                    "check": True,
                }
            )
    else:
        rows_cnt02.append(
            {
                "code": "CNT.02",
                "name": "Не найдено контейнерной диаграммы для данной системы",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        )

    rows_cnt03: List[Dict[str, Any]] = []
    if cnt03_ok:
        rows_cnt03.append(
            {
                "code": "CNT.03",
                "name": "Все связи между контейнерами имеют технологию",
                "date": system_modified,
                "status": "OK",
                "check": True,
                "source_name": "",
                "target_name": "",
            }
        )
    else:
        for v in violations_cnt03:
            rows_cnt03.append(
                {
                    "code": v["relationship_id"],
                    "name": f"{v['source_name']} → {v['target_name']}: {v['description']}",
                    "date": system_modified,
                    "status": "FAIL",
                    "check": False,
                    "source_name": v["source_name"],
                    "target_name": v["target_name"],
                }
            )

    return cnt01_ok, cnt02_ok, cnt03_ok, rows_cnt01, rows_cnt02, rows_cnt03
