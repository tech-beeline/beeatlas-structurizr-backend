"""
Утилиты для проверок DEP.01–DEP.03 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.deployment`` без импортов structurizr_utils.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src_fitness_functions.beeatlas_api import get_beeatlas_api

logger = logging.getLogger(__name__)

InfraLookup = Callable[[str], List[str]]


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


def _cmdb_in_parents(cmdb_l: str, parents: List[str]) -> bool:
    return cmdb_l in [str(p).lower().strip() for p in parents]


def _type_contains_k8s(node_type: Any) -> bool:
    return "k8s" in str(node_type or "").lower()


def _append_dep03_children(
    deployment_node: Dict[str, Any],
    queue: List[Dict[str, Any]],
    *,
    under_k8s: bool,
) -> None:
    """Потомки узла с ``properties.type``, содержащим ``k8s``, не участвуют в сверке."""
    children_under_k8s = under_k8s or _type_contains_k8s((deployment_node.get("properties") or {}).get("type"))
    for child in deployment_node.get("children") or []:
        child_copy = dict(child)
        child_copy["under_k8s_parent"] = children_under_k8s
        queue.append(child_copy)


def _collect_dep03_rows(
    data: Dict[str, Any],
    cmdb: str,
    system_modified: str,
    infra_lookup: InfraLookup,
    *,
    products_api_configured: bool,
) -> Tuple[bool, List[Dict[str, Any]]]:
    if not products_api_configured:
        return True, [
            {
                "code": "DEP.03",
                "name": "Проверка пропущена: не задан URL_PRODUCTS",
                "date": system_modified,
                "status": "SKIP",
                "check": True,
            }
        ]

    cmdb_l = _norm_cmdb(cmdb)
    queue: List[Dict[str, Any]] = []
    found_rows: List[Dict[str, Any]] = []
    not_found_rows: List[Dict[str, Any]] = []

    for deployment_node in (data.get("model") or {}).get("deploymentNodes") or []:
        environment = str(deployment_node.get("environment", "") or "").strip()
        if not environment:
            continue
        parents = infra_lookup(environment)
        if not parents:
            logger.info("DEP.03: deployment environment не найден в CMDB: %s", environment)
            continue
        for child in deployment_node.get("children") or []:
            queue.append(child)

    while queue:
        deployment_node = queue.pop(0)
        if deployment_node.get("under_k8s_parent"):
            _append_dep03_children(deployment_node, queue, under_k8s=True)
            continue

        props = deployment_node.get("properties") or {}
        deployment_node_type = props.get("type")
        is_k8s_type = _type_contains_k8s(deployment_node_type)
        is_has_instances = len(deployment_node.get("containerInstances") or []) > 0
        environment = str(deployment_node.get("environment", "") or "").strip()
        name = str(deployment_node.get("name", "") or "").strip()

        if is_has_instances and name:
            parents = infra_lookup(name)
            label = f"Стенд {environment}, узел {name} (VM)"
            row = {
                "code": f"vm-{environment}-{name}",
                "name": label,
                "date": system_modified,
            }
            if _cmdb_in_parents(cmdb_l, parents):
                found_rows.append({**row, "status": "OK", "check": True})
            else:
                not_found_rows.append({**row, "status": "FAIL", "check": False})
        elif is_k8s_type and name:
            parents = infra_lookup(name)
            label = f"Стенд {environment}, namespace {name} (k8s)"
            row = {
                "code": f"k8s-{environment}-{name}",
                "name": label,
                "date": system_modified,
            }
            if _cmdb_in_parents(cmdb_l, parents):
                found_rows.append({**row, "status": "OK", "check": True})
            else:
                not_found_rows.append({**row, "status": "FAIL", "check": False})

        _append_dep03_children(deployment_node, queue, under_k8s=False)

    if not found_rows and not not_found_rows:
        return False, [
            {
                "code": "DEP.03",
                "name": "Нет узлов развёртывания для сверки с CMDB",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        ]

    dep03_ok = len(not_found_rows) == 0
    return dep03_ok, found_rows + not_found_rows


def analyze_dep_workspace(
    data: Dict[str, Any],
    cmdb: str,
    *,
    infra_lookup: Optional[InfraLookup] = None,
) -> Tuple[bool, bool, bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Анализ развёртывания для системы ``cmdb``.

    Returns:
        (dep01_ok, dep02_ok, dep03_ok, rows_dep01, rows_dep02, rows_dep03)
    """
    system_modified = _system_modified(data, cmdb)
    model = data.get("model") or {}
    views = data.get("views") or {}

    rows_dep01: List[Dict[str, Any]] = []
    seen_environments: Set[str] = set()
    for deployment_node in model.get("deploymentNodes") or []:
        environment = str(deployment_node.get("environment", "") or "").strip()
        if not environment or environment in seen_environments:
            continue
        seen_environments.add(environment)
        rows_dep01.append(
            {
                "code": environment,
                "name": environment,
                "date": system_modified,
                "status": "OK",
                "check": True,
            }
        )
    dep01_ok = len(rows_dep01) > 0
    if not dep01_ok:
        rows_dep01 = [
            {
                "code": "DEP.01",
                "name": "У приложения нет ни одного deployment environment",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        ]

    deployment_views = views.get("deploymentViews") or []
    rows_dep02: List[Dict[str, Any]] = []
    for view in deployment_views:
        view_key = str(view.get("key", "") or "").strip()
        view_title = str(view.get("title", "") or "").strip() or f"Deployment Diagram {view_key}"
        if not view_key:
            continue
        rows_dep02.append(
            {
                "code": view_key,
                "name": view_title,
                "date": system_modified,
                "status": "OK",
                "check": True,
            }
        )
    dep02_ok = len(rows_dep02) > 0
    if not dep02_ok:
        rows_dep02 = [
            {
                "code": "DEP.02",
                "name": "У приложения нет ни одной deployment диаграммы",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        ]

    api = get_beeatlas_api()
    lookup = infra_lookup or api.fetch_product_infra_parents
    products_configured = bool((os.getenv("URL_PRODUCTS") or "").strip() or api.products_base_url)
    dep03_ok, rows_dep03 = _collect_dep03_rows(
        data,
        cmdb,
        system_modified,
        lookup,
        products_api_configured=products_configured,
    )

    return dep01_ok, dep02_ok, dep03_ok, rows_dep01, rows_dep02, rows_dep03
