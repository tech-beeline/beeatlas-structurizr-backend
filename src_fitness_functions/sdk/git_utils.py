"""
Утилиты для проверки GIT.01 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.container.check_container`` (ветка GIT.01)
без импортов structurizr_utils.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src_fitness_functions.api.techradar_cache import get_cached_infrastructure_labels

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


def _tags_list(container: Dict[str, Any]) -> List[str]:
    raw = container.get("tags", [])
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    if isinstance(raw, list):
        return [str(t).strip() for t in raw]
    return []


def _is_external_container(container: Dict[str, Any]) -> bool:
    return any("external" in t.lower() for t in _tags_list(container))


def _container_repo_url(container: Dict[str, Any]) -> str:
    url = container.get("url")
    if url:
        return str(url).strip()
    props = container.get("properties") or {}
    for key in ("url", "git", "repository"):
        val = props.get(key)
        if val:
            return str(val).strip()
    return ""


def _has_git_repo_url(url: str) -> bool:
    u = url.lower()
    return "git" in u or "nexus" in u or "harbor" in u


def _has_infrastructure_tech(technology: str, infrastructure_techs: Set[str]) -> bool:
    if not infrastructure_techs:
        return False
    tech_raw = str(technology or "").lower().strip()
    for pattern in (r"[,\t;]+", r"[ ,\t;]+"):
        for tech in re.split(pattern, tech_raw):
            token = tech.lower().strip()
            if token and token in infrastructure_techs:
                return True
    return False


def analyze_git_workspace(
    data: Dict[str, Any],
    cmdb: str,
    *,
    infrastructure_techs: Optional[Set[str]] = None,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    GIT.01: у контейнеров целевой системы (не external, не инфраструктурных по TechRadar) задан git/nexus/harbor URL.

    Returns:
        (git01_ok, rows) — словари для ``Git01Detail`` (``name`` — имя контейнера, ``git`` — URL);
        сначала ``check: true``, затем ``check: false``.
    """
    cmdb_l = _norm_cmdb(cmdb)
    system_modified = _system_modified(data, cmdb)
    infra: Set[str]
    if infrastructure_techs is not None:
        infra = infrastructure_techs
    else:
        infra = set(get_cached_infrastructure_labels())

    ok_rows: List[Dict[str, Any]] = []
    fail_rows: List[Dict[str, Any]] = []
    checked_count = 0

    for s in (data.get("model") or {}).get("softwareSystems") or []:
        if str((s.get("properties") or {}).get("cmdb", "")).lower().strip() != cmdb_l:
            continue
        for c in s.get("containers") or []:
            if _is_external_container(c):
                continue
            technology = str(c.get("technology", "") or "")
            if _has_infrastructure_tech(technology, infra):
                continue

            checked_count += 1
            cid = str(c.get("id", "") or f"container-{checked_count}")
            cname = str(c.get("name", "") or cid)
            repo_url = _container_repo_url(c)

            if repo_url and _has_git_repo_url(repo_url):
                ok_rows.append(
                    {
                        "code": cid,
                        "name": cname,
                        "git": repo_url,
                        "date": system_modified,
                        "status": "OK",
                        "check": True,
                    }
                )
            else:
                fail_rows.append(
                    {
                        "code": cid,
                        "name": cname,
                        "git": repo_url,
                        "date": system_modified,
                        "status": "FAIL",
                        "check": False,
                    }
                )
        break

    if checked_count == 0:
        return False, [
            {
                "code": "GIT.01",
                "name": "Нет контейнеров, требующих проверки git репозитория",
                "git": "",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        ]

    git01_ok = len(fail_rows) == 0
    return git01_ok, ok_rows + fail_rows
