"""
Утилиты для проверок CX.01–CX.03 по JSON workspace Structurizr (по **модели**, не по View).

- CX.01 — взаимодействие пользователя с системой: существует Person со связью
  (в любом направлении) к целевой SoftwareSystem или её контейнерам.
- CX.02 — технологии UI: среди контейнеров целевой системы, связанных с Person,
  есть контейнер, в ``technology`` которого встречается label из фиксированного
  списка UI-технологий (``_FRONTEND_LABELS``, источник — export_technology xlsx).
- CX.03 — TC (component ``type=capability``) в контейнерах, связанных с Person;
  связка TC с шагами Customer Journey — заглушка (TO-DO, не влияет на ``check``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src_fitness_functions.sdk.technology_utils import check_tr

logger = logging.getLogger(__name__)

# Источник: export_technology_20260828_072921.xlsx (колонка label; сектора «Языки»
# и «Фреймворки и инструменты»). UI-технологии (включая мобильные UI-языки).
# Статус технологии в TechRadar здесь не учитывается — важно лишь, что технология UI.
_FRONTEND_LABELS: Set[str] = {
    # Языки/разметка (сектор «Языки»)
    "HTML", "CSS", "JavaScript", "TypeScript", "jQuery",
    # Фреймворки и инструменты (сектор «Фреймворки и инструменты»)
    "React", "React Native", "Angular", "Vue", "Next.js", "GatsbyJS",
    "Remix", "Eleventy", "Webpack", "Node.js", "Jest", "devexpress",
    # Мобильные UI-языки (сектор «Языки»)
    "Swift", "Objective-C", "Kotlin",
}

# Словарь для ``check_tr``: порядок по убыванию длины label, чтобы более специфичный
# label («React Native») матчился раньше короткого («React»).
_FRONTEND_TR: Dict[str, str] = {
    label: "adopt" for label in sorted(_FRONTEND_LABELS, key=len, reverse=True)
}


@dataclass
class CxWorkspaceContext:
    """Общий контекст разбора модели для проверок CX.01–CX.03."""

    cmdb: str
    system_modified: str = ""
    system_found: bool = False
    ui_persons: List[Dict[str, str]] = field(default_factory=list)          # [{id, name}]
    person_related_containers: List[Dict[str, Any]] = field(default_factory=list)  # [{id, name, technology, has_frontend}]
    tc_rows: List[Dict[str, str]] = field(default_factory=list)             # [{code, name, container_name}]


def _norm_cmdb(cmdb: Any) -> str:
    return str(cmdb or "").lower().strip()


def _system_modified(data: Dict[str, Any], cmdb: str) -> str:
    """``properties.modified`` целевой системы (пустая строка, если не задан)."""
    cmdb_l = _norm_cmdb(cmdb)
    for s in (data.get("model") or {}).get("softwareSystems") or []:
        if _norm_cmdb((s.get("properties") or {}).get("cmdb", "")) != cmdb_l:
            continue
        raw = (s.get("properties") or {}).get("modified")
        return str(raw) if raw is not None else ""
    return ""


def _full_tc_code(cmdb: str, code: str) -> str:
    """Полное имя TC в виде ``CMDB.код`` (без повторного префикса)."""
    cm = str(cmdb or "").strip()
    cd = str(code or "").strip()
    if not cd:
        return ""
    if not cm:
        return cd
    if "." in cd and cd.lower().startswith(cm.lower() + "."):
        return cd
    return f"{cm}.{cd}"


def _detail_row(
    code: str,
    name: str,
    system_modified: str,
    *,
    ok: bool,
    **extra: Any,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "code": code,
        "name": name,
        "date": system_modified,
        "status": "OK" if ok else "FAIL",
        "check": ok,
    }
    row.update(extra)
    return row


def _find_target_system(data: Dict[str, Any], cmdb: str) -> Optional[Dict[str, Any]]:
    """Первая software system с ``properties.cmdb == cmdb`` (без учёта регистра)."""
    cmdb_l = _norm_cmdb(cmdb)
    for system in (data.get("model") or {}).get("softwareSystems") or []:
        if not isinstance(system, dict):
            continue
        if _norm_cmdb((system.get("properties") or {}).get("cmdb", "")) == cmdb_l:
            return system
    return None


def _collect_ui_persons(
    data: Dict[str, Any], system: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Person'ы со связью к целевой системе или её контейнерам — в любом направлении:
    person→system/container, system→person, container→person.
    """
    sys_id = str(system.get("id", ""))
    container_ids: Set[str] = {
        str(c.get("id", "")) for c in system.get("containers") or []
        if isinstance(c, dict) and c.get("id")
    }
    target_ids = {sys_id} | container_ids
    ui_persons: List[Dict[str, str]] = []
    for person in (data.get("model") or {}).get("people") or []:
        if not isinstance(person, dict):
            continue
        pid = str(person.get("id", ""))
        if not pid:
            continue
        is_ui = False
        # person -> system/container
        for rel in person.get("relationships") or []:
            if isinstance(rel, dict) and str(rel.get("destinationId", "")) in target_ids:
                is_ui = True
                break
        # system -> person
        if not is_ui:
            for rel in system.get("relationships") or []:
                if isinstance(rel, dict) and str(rel.get("destinationId", "")) == pid:
                    is_ui = True
                    break
        # container -> person
        if not is_ui:
            for c in system.get("containers") or []:
                if not isinstance(c, dict):
                    continue
                for rel in c.get("relationships") or []:
                    if isinstance(rel, dict) and str(rel.get("destinationId", "")) == pid:
                        is_ui = True
                        break
                if is_ui:
                    break
        if is_ui:
            ui_persons.append({"id": pid, "name": str(person.get("name", "") or "")})
    return ui_persons


def _container_has_frontend_tech(technology: str) -> bool:
    """Токенизация ``technology`` и совпадение с label из ``_FRONTEND_LABELS`` (как ``check_tr``)."""
    tr = check_tr(_FRONTEND_TR, technology)
    return len(tr.radar) > 0


def _person_related_containers(
    data: Dict[str, Any],
    system: Dict[str, Any],
    ui_person_ids: Set[str],
) -> List[Dict[str, Any]]:
    """Контейнеры целевой системы, связанные с UI-Person (container→person или person→container)."""
    person_rels: Dict[str, Set[str]] = {}
    for person in (data.get("model") or {}).get("people") or []:
        if not isinstance(person, dict):
            continue
        pid = str(person.get("id", ""))
        if pid not in ui_person_ids:
            continue
        person_rels[pid] = {
            str(r.get("destinationId", ""))
            for r in person.get("relationships") or []
            if isinstance(r, dict)
        }

    rows: List[Dict[str, Any]] = []
    for c in system.get("containers") or []:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id", ""))
        if not cid:
            continue
        related = False
        # container -> person
        for rel in c.get("relationships") or []:
            if isinstance(rel, dict) and str(rel.get("destinationId", "")) in ui_person_ids:
                related = True
                break
        # person -> container
        if not related:
            for destinations in person_rels.values():
                if cid in destinations:
                    related = True
                    break
        if related:
            technology = str(c.get("technology", "") or "")
            rows.append({
                "id": cid,
                "name": str(c.get("name", "") or ""),
                "technology": technology,
                "has_frontend": _container_has_frontend_tech(technology),
            })
    return rows


def _collect_tcs(
    data: Dict[str, Any],
    cmdb: str,
    person_related_container_ids: Set[str],
) -> List[Dict[str, str]]:
    """TC (component ``type=capability``) в person-related контейнерах целевой системы."""
    if not person_related_container_ids:
        return []
    # Ленивый импорт: ``capability_utils`` тянет ``psycopg2``, который нужен только CX.03.
    from src_fitness_functions.sdk.capability_utils import parse_capability_workspace

    analysis = parse_capability_workspace(data, cmdb)
    rows: List[Dict[str, str]] = []
    seen: Set[str] = set()
    for tc in list(analysis.full_capabilities) + list(analysis.incomplete_capabilities):
        if str(tc.container_id) not in person_related_container_ids:
            continue
        code = _full_tc_code(cmdb, tc.code)
        if code in seen:
            continue
        seen.add(code)
        rows.append({
            "code": code,
            "name": tc.name,
            "container_name": tc.container_name,
        })
    return rows


def _match_cj_steps(
    tc_codes: List[str],
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    ЗАГЛУШКА (TO-DO): связка TC ↔ шаги Customer Journey ещё не реализована.

    Возвращает пустой список — проверка CX.03 не падает из-за заглушки.
    Реализация будет добавлена отдельной задачей (в модели CJ пока нет).
    """
    return []


def build_cx_context(data: Dict[str, Any], cmdb: str) -> CxWorkspaceContext:
    """Разбор модели для проверок CX.01–CX.03 (без TechRadar и без views)."""
    ctx = CxWorkspaceContext(cmdb=cmdb, system_modified=_system_modified(data, cmdb))
    system = _find_target_system(data, cmdb)
    if system is None:
        return ctx
    ctx.system_found = True
    ctx.ui_persons = _collect_ui_persons(data, system)
    ui_person_ids = {p["id"] for p in ctx.ui_persons}
    ctx.person_related_containers = _person_related_containers(data, system, ui_person_ids)
    prc_ids = {c["id"] for c in ctx.person_related_containers}
    ctx.tc_rows = _collect_tcs(data, cmdb, prc_ids)
    return ctx


def analyze_cx01_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """CX.01 — взаимодействие пользователя с системой: есть UI-Person."""
    ctx = build_cx_context(data, cmdb)
    if not ctx.system_found:
        return False, [
            _detail_row("CX.01", "Система не найдена по productCode (cmdb)", ctx.system_modified, ok=False)
        ]
    if not ctx.ui_persons:
        return False, [
            _detail_row(
                "CX.01",
                "Нет персон со связью с системой или её контейнерами",
                ctx.system_modified,
                ok=False,
            )
        ]
    rows = [_detail_row(p["id"], p["name"], ctx.system_modified, ok=True) for p in ctx.ui_persons]
    return True, rows


def analyze_cx02_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """CX.02 — технологии UI: person-related контейнер с label из списка UI-технологий."""
    ctx = build_cx_context(data, cmdb)
    if not ctx.system_found:
        return False, [
            _detail_row("CX.02", "Система не найдена по productCode (cmdb)", ctx.system_modified, ok=False)
        ]
    if not ctx.person_related_containers:
        return True, [
            _detail_row(
                "CX.02",
                "Нет контейнеров, связанных с Person — проверка не требовалась",
                ctx.system_modified,
                ok=True,
            )
        ]
    ok_rows = [
        _detail_row(
            c["id"], c["name"], ctx.system_modified, ok=True, technology=c["technology"]
        )
        for c in ctx.person_related_containers
        if c["has_frontend"]
    ]
    if not ok_rows:
        return False, [
            _detail_row(
                "CX.02",
                "Нет контейнера, связанного с Person, с технологиями UI",
                ctx.system_modified,
                ok=False,
            )
        ]
    return True, ok_rows


def analyze_cx03_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """CX.03 — TC в person-related контейнерах со связкой к шагам CJ (связка — заглушка)."""
    ctx = build_cx_context(data, cmdb)
    if not ctx.system_found:
        return False, [
            _detail_row("CX.03", "Система не найдена по productCode (cmdb)", ctx.system_modified, ok=False)
        ]
    if not ctx.person_related_containers:
        return True, [
            _detail_row(
                "CX.03",
                "Нет контейнеров, связанных с Person — проверка не требовалась",
                ctx.system_modified,
                ok=True,
            )
        ]
    if not ctx.tc_rows:
        return False, [
            _detail_row(
                "CX.03",
                "Нет TC (component type=capability) в контейнерах, связанных с Person",
                ctx.system_modified,
                ok=False,
            )
        ]
    _match_cj_steps([t["code"] for t in ctx.tc_rows], data)  # TODO-заглушка
    rows = [
        _detail_row(
            t["code"],
            f"{t['name']} ({t['container_name']}). "
            "Заглушка (TBD): связка TC с шагами Customer Journey не реализована",
            ctx.system_modified,
            ok=True,
        )
        for t in ctx.tc_rows
    ]
    return True, rows
