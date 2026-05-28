"""
Утилиты для проверок SQ.01–SQ.02 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.sequences`` без импортов structurizr_utils.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src_fitness_functions.beeatlas_api import get_beeatlas_api

logger = logging.getLogger(__name__)


def _norm_cmdb(cmdb: str) -> str:
    return str(cmdb or "").lower().strip()


def _system_modified(data: Dict[str, Any], cmdb: str) -> str:
    cmdb_l = _norm_cmdb(cmdb)
    for s in (data.get("model") or {}).get("softwareSystems") or []:
        if str((s.get("properties") or {}).get("cmdb", "")).lower().strip() != cmdb_l:
            continue
        raw = (s.get("properties") or {}).get("modified")
        return str(raw) if raw is not None else ""
    return ""


def build_product_capabilities(containers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """TC из Products API по контейнерам (как ``get_product_capabilities``)."""
    result: Dict[str, List[str]] = {}
    for cnt in containers:
        cnt_name = str(cnt.get("code", "-"))
        for interface in cnt.get("interfaces") or []:
            if not isinstance(interface, dict):
                continue
            interface_code = str(interface.get("code", ""))
            tc = interface.get("techCapability")
            if isinstance(tc, dict) and tc.get("code"):
                code = str(tc["code"])
                msg = f"Реализуется в контейнере {cnt_name}, интерфейсе {interface_code}"
                result.setdefault(code, []).append(msg)
            for operation in interface.get("operations") or []:
                if not isinstance(operation, dict):
                    continue
                op_tc = operation.get("techCapability")
                if isinstance(op_tc, dict) and op_tc.get("code"):
                    code = str(op_tc["code"])
                    name = str(operation.get("name", ""))
                    msg = f"Реализуется в контейнере {cnt_name}, api {name}"
                    result.setdefault(code, []).append(msg)
    return result


def _capability_hint_text(hints: List[str]) -> str:
    return "; ".join(hints)


def _full_tc_code(cmdb: str, tc_code: str) -> str:
    """Полный код TC с префиксом CMDB системы (``productCode``)."""
    pc = str(cmdb or "").strip()
    tc = str(tc_code or "").strip()
    if not tc:
        return pc
    if not pc:
        return tc
    prefix = f"{pc}."
    if tc.lower() == pc.lower() or tc.lower().startswith(prefix.lower()):
        return tc
    return f"{prefix}{tc}"


def _dynamic_view_name(view: Dict[str, Any]) -> str:
    title = str(view.get("title", "") or "").strip()
    if title:
        return title
    description = str(view.get("description", "") or "").strip()
    if description:
        return description
    return str(view.get("key", "") or "").strip()


def _build_element_names(data: Dict[str, Any]) -> Dict[str, str]:
    names: Dict[str, str] = {}
    model = data.get("model") or {}
    for person in model.get("people") or []:
        if isinstance(person, dict) and person.get("id") is not None:
            names[str(person["id"])] = str(person.get("name", "Person"))
    for system in model.get("softwareSystems") or []:
        if not isinstance(system, dict) or system.get("id") is None:
            continue
        sid = str(system["id"])
        names[sid] = str(system.get("name", "System"))
        for container in system.get("containers") or []:
            if not isinstance(container, dict) or container.get("id") is None:
                continue
            cid = str(container["id"])
            names[cid] = str(container.get("name", "Container"))
            for component in container.get("components") or []:
                if isinstance(component, dict) and component.get("id") is not None:
                    names[str(component["id"])] = str(component.get("name", "Component"))
    return names


def _build_relationships_index(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    model = data.get("model") or {}
    for person in model.get("people") or []:
        for rel in person.get("relationships") or []:
            if isinstance(rel, dict) and rel.get("id") is not None:
                index[str(rel["id"])] = rel
    for system in model.get("softwareSystems") or []:
        if not isinstance(system, dict):
            continue
        for rel in system.get("relationships") or []:
            if isinstance(rel, dict) and rel.get("id") is not None:
                index[str(rel["id"])] = rel
        for container in system.get("containers") or []:
            if not isinstance(container, dict):
                continue
            for rel in container.get("relationships") or []:
                if isinstance(rel, dict) and rel.get("id") is not None:
                    index[str(rel["id"])] = rel
            for component in container.get("components") or []:
                if not isinstance(component, dict):
                    continue
                for rel in component.get("relationships") or []:
                    if isinstance(rel, dict) and rel.get("id") is not None:
                        index[str(rel["id"])] = rel
    return index


def _plantuml_alias(name: str, element_id: str, used: Dict[str, int]) -> str:
    ascii_part = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())
    if re.search(r"[a-zA-Z0-9]", ascii_part):
        base = ascii_part[:48]
    else:
        base = f"elem_{element_id}"
    if not base[0].isalpha():
        base = f"e_{base}"
    alias = base[:48]
    if alias in used:
        used[alias] += 1
        alias = f"{alias}_{used[alias]}"
    else:
        used[alias] = 0
    return alias


def _escape_plantuml_label(text: str) -> str:
    return str(text or "").replace("\n", " ").replace('"', "'").strip()


def dynamic_view_to_plantuml(
    view: Dict[str, Any],
    *,
    element_names: Dict[str, str],
    relationships_index: Dict[str, Dict[str, Any]],
) -> str:
    """Сценарий dynamic-диаграммы в формате PlantUML sequence."""
    view_name = _dynamic_view_name(view)
    lines: List[str] = ["@startuml", f"title {_escape_plantuml_label(view_name)}"]

    id_to_alias: Dict[str, str] = {}
    used_aliases: Dict[str, int] = {}

    def ensure_participant(element_id: str) -> str:
        eid = str(element_id)
        if eid in id_to_alias:
            return id_to_alias[eid]
        display = _escape_plantuml_label(element_names.get(eid, f"Element {eid}"))
        alias = _plantuml_alias(display, eid, used_aliases)
        id_to_alias[eid] = alias
        lines.append(f'participant "{display}" as {alias}')
        return alias

    for element in view.get("elements") or []:
        if isinstance(element, dict) and element.get("id") is not None:
            ensure_participant(str(element["id"]))

    view_relationships = [
        r for r in (view.get("relationships") or []) if isinstance(r, dict)
    ]
    view_relationships.sort(key=lambda r: int(str(r.get("order", 0) or "0")))

    for view_rel in view_relationships:
        rel_id = str(view_rel.get("id", "") or "")
        model_rel = relationships_index.get(rel_id, {})
        source_id = str(model_rel.get("sourceId", "") or "")
        dest_id = str(model_rel.get("destinationId", "") or "")
        if not source_id or not dest_id:
            continue
        src_alias = ensure_participant(source_id)
        dst_alias = ensure_participant(dest_id)
        description = _escape_plantuml_label(
            view_rel.get("description") or model_rel.get("description", "")
        )
        technology = _escape_plantuml_label(str(model_rel.get("technology", "") or ""))
        label = description
        if technology:
            label = f"{description} [{technology}]" if description else f"[{technology}]"
        if not label:
            label = rel_id
        arrow = "-->>" if view_rel.get("response") else "->>"
        lines.append(f"{src_alias} {arrow} {dst_alias}: {label}")

    lines.append("@enduml")
    return "\n".join(lines)


def _sq01_summary_row(
    *,
    code: str,
    name: str,
    system_modified: str,
    status: str,
    check: bool,
) -> Dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "date": system_modified,
        "status": status,
        "check": check,
    }


def validate_format_with_http_request(text: str) -> bool:
    pattern = r"[\s\S]*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) .*$"
    return bool(re.match(pattern, str(text or "")))


def is_rest(technology: str) -> bool:
    return bool(re.search(r"HTTP|HTTPS|REST", str(technology or ""), re.IGNORECASE))


def _collect_relationship_technologies(data: Dict[str, Any]) -> Dict[str, str]:
    relationships: Dict[str, str] = {}
    for system in (data.get("model") or {}).get("softwareSystems") or []:
        for rel in system.get("relationships") or []:
            if isinstance(rel, dict) and rel.get("id") is not None:
                relationships[str(rel["id"])] = str(rel.get("technology", "") or "")
        for container in system.get("containers") or []:
            for rel in container.get("relationships") or []:
                if isinstance(rel, dict) and rel.get("id") is not None:
                    relationships[str(rel["id"])] = str(rel.get("technology", "") or "")
    return relationships


def analyze_sq01_workspace(
    data: Dict[str, Any],
    cmdb: str,
    *,
    caps_list: Optional[Dict[str, List[str]]] = None,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    SQ.01: для каждой TC из Products API есть ``dynamicView`` с ключом, совпадающим с кодом TC.
    """
    system_modified = _system_modified(data, cmdb)
    api = get_beeatlas_api()
    products_configured = bool((os.getenv("URL_PRODUCTS") or "").strip() or api.products_base_url)

    if not products_configured:
        return True, [
            _sq01_summary_row(
                code="SQ.01",
                name="Проверка пропущена: не задан URL_PRODUCTS",
                system_modified=system_modified,
                status="SKIP",
                check=True,
            )
        ]

    if caps_list is None:
        caps_list = build_product_capabilities(api.fetch_product_containers(cmdb))

    if not caps_list:
        return False, [
            _sq01_summary_row(
                code="SQ.01",
                name="Нет определенных capability",
                system_modified=system_modified,
                status="FAIL",
                check=False,
            )
        ]

    capabilities: Dict[str, str] = {item: item for item in caps_list}
    capabilities_short: Dict[str, str] = {
        item.split(".")[-1]: item if "." in item else item for item in caps_list
    }
    element_names = _build_element_names(data)
    relationships_index = _build_relationships_index(data)

    ok_rows: List[Dict[str, Any]] = []
    fail_rows: List[Dict[str, Any]] = []

    for view in (data.get("views") or {}).get("dynamicViews") or []:
        key = str(view.get("key", "") or "").strip()
        if not key:
            continue
        founded_cap = capabilities.get(key) or capabilities_short.get(key, "")
        if not founded_cap:
            continue

        ok_rows.append(
            {
                "code": _full_tc_code(cmdb, founded_cap),
                "name": _dynamic_view_name(view),
                "date": system_modified,
                "status": "OK",
                "check": True,
                "plantUML": dynamic_view_to_plantuml(
                    view,
                    element_names=element_names,
                    relationships_index=relationships_index,
                ),
            }
        )
        capabilities.pop(key, None)
        capabilities.pop(founded_cap, None)
        capabilities_short.pop(key, None)
        capabilities_short.pop(founded_cap, None)

    for cap_code in capabilities.values():
        fail_rows.append(
            {
                "code": _full_tc_code(cmdb, cap_code),
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        )

    sq01_ok = len(fail_rows) == 0 and len(ok_rows) > 0
    if not ok_rows and not fail_rows:
        sq01_ok = False
    return sq01_ok, ok_rows + fail_rows


def analyze_sq02_workspace(
    data: Dict[str, Any],
    cmdb: str,
    *,
    caps_list: Optional[Dict[str, List[str]]] = None,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    SQ.02: на sequence-диаграммах TC REST-связи содержат HTTP-метод в ``description``.
    """
    system_modified = _system_modified(data, cmdb)
    api = get_beeatlas_api()
    products_configured = bool((os.getenv("URL_PRODUCTS") or "").strip() or api.products_base_url)

    if not products_configured:
        return True, [
            {
                "code": "SQ.02",
                "name": "Проверка пропущена: не задан URL_PRODUCTS",
                "date": system_modified,
                "status": "SKIP",
                "check": True,
            }
        ]

    if caps_list is None:
        caps_list = build_product_capabilities(api.fetch_product_containers(cmdb))

    if not caps_list:
        return True, [
            {
                "code": "SQ.02",
                "name": "Нет реализованных TC для проверки HTTP-запросов",
                "date": system_modified,
                "status": "OK",
                "check": True,
            }
        ]

    capabilities: Dict[str, str] = {item: item for item in caps_list}
    capabilities_short: Dict[str, str] = {
        item.split(".")[-1]: item if "." in item else item for item in caps_list
    }
    relationships = _collect_relationship_technologies(data)

    ok_rows: List[Dict[str, Any]] = []
    fail_rows: List[Dict[str, Any]] = []

    for view in (data.get("views") or {}).get("dynamicViews") or []:
        key = str(view.get("key", "") or "").strip()
        if not key:
            continue
        founded_cap = capabilities.get(key) or capabilities_short.get(key, "")
        if not founded_cap:
            continue

        tc_code = _full_tc_code(cmdb, founded_cap)
        for rel in view.get("relationships") or []:
            if not isinstance(rel, dict):
                continue
            rel_id = str(rel.get("id", "") or "")
            description = str(rel.get("description", "") or "")
            tech = relationships.get(rel_id, "")
            if not is_rest(tech):
                continue
            rel_label = rel_id or f"{key}-rel"
            label = f"{rel_label}: {description} ({tech})".strip()
            row = {
                "code": tc_code,
                "name": label,
                "date": system_modified,
            }
            if validate_format_with_http_request(description):
                ok_rows.append({**row, "status": "OK", "check": True})
            else:
                fail_rows.append({**row, "status": "FAIL", "check": False})

    sq02_ok = len(fail_rows) == 0
    if not ok_rows and not fail_rows:
        return True, [
            {
                "code": "SQ.02",
                "name": "Нет REST-вызовов на sequence-диаграммах TC",
                "date": system_modified,
                "status": "OK",
                "check": True,
            }
        ]
    return sq02_ok, ok_rows + fail_rows
