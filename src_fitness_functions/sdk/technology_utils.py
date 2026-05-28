"""
Утилиты для проверок TECH.01–TECH.06 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.technology.check_technology``
без импортов structurizr_utils.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src_fitness_functions.api.techradar_cache import get_cached_techradar_catalog
from src_fitness_functions.beeatlas_api import get_beeatlas_api

logger = logging.getLogger(__name__)

_STANDARD_PROTOCOLS = {
    "rest": "adopt",
    "http": "adopt",
    "https": "adopt",
    "tcp": "adopt",
    "amqp": "adopt",
    "soap": "adopt",
    "udp": "adopt",
}
_TECH06_EXCEPTIONS = {
    "HTML",
    "CSS",
    "SSH 2.0",
    "Docker",
    "Alpine Linux",
    "HCL",
    "Groovy",
    "Jinja",
    "Prometheus",
}
@dataclass
class TechCheckResult:
    holded: List[str] = field(default_factory=list)
    missed: List[str] = field(default_factory=list)
    all_tokens: List[str] = field(default_factory=list)
    radar: List[str] = field(default_factory=list)


@dataclass
class TechWorkspaceContext:
    cmdb: str
    system_modified: str = ""
    skip: bool = False
    skip_message: str = ""
    system_found: bool = False
    tech_status: Dict[str, str] = field(default_factory=dict)
    tech_status_protocols: Dict[str, str] = field(default_factory=dict)
    found_technology: Set[str] = field(default_factory=set)
    holded_technology: Set[str] = field(default_factory=set)
    unknown_technology: Set[str] = field(default_factory=set)
    containers_wo_technology: Set[str] = field(default_factory=set)
    tech_container_map: Dict[str, str] = field(default_factory=dict)
    holded_tech_details: List[str] = field(default_factory=list)
    tech04_fail_rows: List[str] = field(default_factory=list)
    tech05_fail_rows: List[str] = field(default_factory=list)
    monitoring_missing: Set[str] = field(default_factory=set)


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


def _detail_row(
    code: str,
    name: str,
    system_modified: str,
    *,
    ok: bool,
) -> Dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "date": system_modified,
        "status": "OK" if ok else "FAIL",
        "check": ok,
    }


def _skip_row(code: str, message: str, system_modified: str) -> Dict[str, Any]:
    return {
        "code": code,
        "name": message,
        "date": system_modified,
        "status": "SKIP",
        "check": True,
    }


def check_tr(technologies: Dict[str, str], value: str) -> TechCheckResult:
    """Проверка строки технологий/протоколов по словарю TechRadar (как ``check_tr``)."""
    result = TechCheckResult()
    for tech in re.split(r"[,\t;]+", str(value or "").lower()):
        token = tech.strip()
        result.all_tokens.append(token)
        found_label: Optional[str] = None
        for radar_label in technologies:
            if token.find(radar_label.lower()) >= 0:
                found_label = radar_label
                if technologies[radar_label] == "hold":
                    result.holded.append(token)
                break
        if found_label is None:
            if token and not token.isnumeric():
                result.missed.append(token)
        elif token and not token.isnumeric():
            result.radar.append(token)
    return result


def _ring_name(tech_item: Dict[str, Any]) -> str:
    ring = tech_item.get("ring") or {}
    if isinstance(ring, dict):
        return str(ring.get("name") or "adopt").lower().strip()
    return "adopt"


def _sector_id(tech_item: Dict[str, Any]) -> Optional[int]:
    sector = tech_item.get("sector") or {}
    if isinstance(sector, dict) and sector.get("id") is not None:
        try:
            return int(sector["id"])
        except (TypeError, ValueError):
            return None
    return None


def _build_tech_status_maps(techs: List[Dict[str, Any]]) -> Tuple[Dict[str, str], Dict[str, str]]:
    tech_status: Dict[str, str] = {}
    tech_status_protocols: Dict[str, str] = {}
    for tech in techs:
        label = str(tech.get("label", "") or "").lower().strip()
        if not label:
            continue
        ring = _ring_name(tech)
        tech_status[label] = ring
        if _sector_id(tech) == 3:
            tech_status_protocols[label] = ring
    tech_status_protocols.update(_STANDARD_PROTOCOLS)
    return tech_status, tech_status_protocols


def build_tech_workspace_context(data: Dict[str, Any], cmdb: str) -> TechWorkspaceContext:
    """Разбор workspace и TechRadar для TECH.01–TECH.06."""
    ctx = TechWorkspaceContext(cmdb=cmdb, system_modified=_system_modified(data, cmdb))
    api = get_beeatlas_api()
    if not (os.getenv("URL_TECHRADAR") or "").strip() and not api.techradar_base_url:
        ctx.skip = True
        ctx.skip_message = "Проверка пропущена: не задан URL_TECHRADAR"
        return ctx

    techs, product_tech = get_cached_techradar_catalog()
    if not techs:
        ctx.skip = True
        ctx.skip_message = "Проверка пропущена: TechRadar недоступен или пустой ответ"
        return ctx

    ctx.tech_status, ctx.tech_status_protocols = _build_tech_status_maps(techs)
    cmdb_l = _norm_cmdb(cmdb)

    for system in (data.get("model") or {}).get("softwareSystems") or []:
        if str((system.get("properties") or {}).get("cmdb", "")).lower().strip() != cmdb_l:
            continue
        ctx.system_found = True

        for relationship in system.get("relationships") or []:
            if not isinstance(relationship, dict):
                continue
            rel_name = str(relationship.get("description", "") or "")
            rel_tech = str(relationship.get("technology", "") or "")
            tr = check_tr(ctx.tech_status_protocols, rel_tech)
            for token in tr.missed:
                ctx.tech05_fail_rows.append(f"{rel_name} - {token}")

        for container in system.get("containers") or []:
            if not isinstance(container, dict):
                continue
            from_landscape = str((container.get("properties") or {}).get("source", "")) == "landscape"
            container_name = str(container.get("name", "") or "")
            if not from_landscape:
                technology = str(container.get("technology", "") or "").lower().strip()
                if not technology:
                    ctx.containers_wo_technology.add(container_name)
                else:
                    tr = check_tr(ctx.tech_status, technology)
                    for token in tr.all_tokens:
                        ctx.found_technology.add(token)
                    for token in tr.holded:
                        ctx.holded_technology.add(token)
                        ctx.holded_tech_details.append(f"{token} (Container: {container_name})")
                    for token in tr.missed:
                        ctx.unknown_technology.add(token)
                    for token in tr.radar:
                        prev = ctx.tech_container_map.get(token, "")
                        ctx.tech_container_map[token] = f"{prev}{container_name}, "

            for relationship in container.get("relationships") or []:
                if not isinstance(relationship, dict):
                    continue
                rel_name = str(relationship.get("description", "") or "")
                rel_tech = str(relationship.get("technology", "") or "")
                rel_id = str(relationship.get("id", "") or "")
                tr = check_tr(ctx.tech_status_protocols, rel_tech)
                for token in tr.holded:
                    ctx.tech04_fail_rows.append(f"{rel_id} {rel_name} ({token})")
                for token in tr.missed:
                    ctx.tech05_fail_rows.append(rel_name)

    for product in product_tech:
        alias = str(product.get("alias", "") or "").lower().strip()
        if alias != cmdb_l:
            continue
        for tech in product.get("tech") or []:
            if not isinstance(tech, dict):
                continue
            label = str(tech.get("label", "") or "")
            if not label or label in _TECH06_EXCEPTIONS:
                continue
            tech_label_l = label.lower()
            found = tech_label_l in ctx.found_technology or any(
                tech_label_l in t for t in ctx.found_technology
            )
            if not found:
                ctx.monitoring_missing.add(label)

    return ctx


def analyze_tech01_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    ctx = build_tech_workspace_context(data, cmdb)
    if ctx.skip:
        return True, [_skip_row("TECH.01", ctx.skip_message, ctx.system_modified)]
    if not ctx.system_found:
        return False, [
            _detail_row("TECH.01", "Система не найдена по productCode", ctx.system_modified, ok=False)
        ]

    ok_rows: List[Dict[str, Any]] = []
    fail_rows: List[Dict[str, Any]] = []
    seen_ok: Set[str] = set()
    for token in sorted(ctx.found_technology):
        if token in ctx.unknown_technology or token in seen_ok:
            continue
        seen_ok.add(token)
        ring = ctx.tech_status.get(token, "-")
        for label, status in ctx.tech_status.items():
            if token.find(label) >= 0:
                ring = status
                break
        ok_rows.append(_detail_row(token, ring, ctx.system_modified, ok=True))

    for token in sorted(ctx.unknown_technology):
        fail_rows.append(_detail_row(token, "-", ctx.system_modified, ok=False))

    tech01_ok = len(ctx.unknown_technology) == 0 and (len(ok_rows) > 0 or len(fail_rows) == 0)
    if not ok_rows and not fail_rows:
        tech01_ok = True
        ok_rows.append(
            _detail_row("TECH.01", "Нет технологий у контейнеров (не landscape)", ctx.system_modified, ok=True)
        )
    return tech01_ok, ok_rows + fail_rows


def analyze_tech02_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    ctx = build_tech_workspace_context(data, cmdb)
    if ctx.skip:
        return True, [_skip_row("TECH.02", ctx.skip_message, ctx.system_modified)]
    if not ctx.system_found:
        return False, [
            _detail_row("TECH.02", "Система не найдена по productCode", ctx.system_modified, ok=False)
        ]

    if not ctx.holded_technology:
        return True, [
            _detail_row("TECH.02", "Нет технологий в статусе HOLD", ctx.system_modified, ok=True)
        ]

    fail_rows = [
        _detail_row(f"hold-{i + 1}", detail, ctx.system_modified, ok=False)
        for i, detail in enumerate(ctx.holded_tech_details)
    ]
    if not fail_rows:
        fail_rows = [
            _detail_row(tech, f"{tech} (HOLD)", ctx.system_modified, ok=False)
            for tech in sorted(ctx.holded_technology)
        ]
    return False, fail_rows


def analyze_tech03_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    ctx = build_tech_workspace_context(data, cmdb)
    if ctx.skip:
        return True, [_skip_row("TECH.03", ctx.skip_message, ctx.system_modified)]
    if not ctx.system_found:
        return False, [
            _detail_row("TECH.03", "Система не найдена по productCode", ctx.system_modified, ok=False)
        ]

    ok_rows: List[Dict[str, Any]] = []
    for tech, containers in sorted(ctx.tech_container_map.items()):
        ok_rows.append(_detail_row(tech, containers.rstrip(", "), ctx.system_modified, ok=True))

    fail_rows = [
        _detail_row(container, "Нет technology", ctx.system_modified, ok=False)
        for container in sorted(ctx.containers_wo_technology)
    ]

    tech03_ok = len(ctx.containers_wo_technology) == 0
    if tech03_ok and not ok_rows and not fail_rows:
        ok_rows.append(_detail_row("TECH.03", "Нет контейнеров для проверки", ctx.system_modified, ok=True))
    return tech03_ok, ok_rows + fail_rows


def analyze_tech04_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    ctx = build_tech_workspace_context(data, cmdb)
    if ctx.skip:
        return True, [_skip_row("TECH.04", ctx.skip_message, ctx.system_modified)]
    if not ctx.system_found:
        return False, [
            _detail_row("TECH.04", "Система не найдена по productCode", ctx.system_modified, ok=False)
        ]

    if not ctx.tech04_fail_rows:
        return True, [
            _detail_row("TECH.04", "Нет протоколов в статусе HOLD", ctx.system_modified, ok=True)
        ]

    fail_rows = [
        _detail_row(f"rel-{i + 1}", row, ctx.system_modified, ok=False)
        for i, row in enumerate(ctx.tech04_fail_rows)
    ]
    return False, fail_rows


def analyze_tech05_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    ctx = build_tech_workspace_context(data, cmdb)
    if ctx.skip:
        return True, [_skip_row("TECH.05", ctx.skip_message, ctx.system_modified)]
    if not ctx.system_found:
        return False, [
            _detail_row("TECH.05", "Система не найдена по productCode", ctx.system_modified, ok=False)
        ]

    if not ctx.tech05_fail_rows:
        return True, [
            _detail_row("TECH.05", "Все протоколы из TechRadar", ctx.system_modified, ok=True)
        ]

    fail_rows = [
        _detail_row(f"protocol-{i + 1}", row, ctx.system_modified, ok=False)
        for i, row in enumerate(ctx.tech05_fail_rows)
    ]
    return False, fail_rows


def analyze_tech06_workspace(data: Dict[str, Any], cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    ctx = build_tech_workspace_context(data, cmdb)
    if ctx.skip:
        return True, [_skip_row("TECH.06", ctx.skip_message, ctx.system_modified)]
    if not ctx.system_found:
        return False, [
            _detail_row("TECH.06", "Система не найдена по productCode", ctx.system_modified, ok=False)
        ]

    if not ctx.monitoring_missing:
        return True, [
            _detail_row(
                "TECH.06",
                "Нет расхождений архитектуры и мониторинга",
                ctx.system_modified,
                ok=True,
            )
        ]

    fail_rows = [
        _detail_row(label, f"{label} (Monitoring)", ctx.system_modified, ok=False)
        for label in sorted(ctx.monitoring_missing)
    ]
    return False, fail_rows
