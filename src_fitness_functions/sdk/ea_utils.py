"""
Утилиты для проверки EA.0001 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.ea_0001.check_external_services``
без импортов structurizr_utils.
"""

from __future__ import annotations

import ipaddress
import logging
import re
from typing import Any, Dict, List, Tuple, Union

logger = logging.getLogger(__name__)

_IPV4_PATTERN = (
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)
_IPV6_PATTERN = (
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}\b|"
    r"\b[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}\b|"
    r"\b:(?::[0-9a-fA-F]{1,4}){1,7}\b|"
    r"\b::\b"
)

_PRIVATE_IPV4 = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]
_SPECIAL_IPV4 = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
]
_PRIVATE_IPV6 = [
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
    ipaddress.ip_network("2001:db8::/32"),
    ipaddress.ip_network("::ffff:0:0/96"),
    ipaddress.ip_network("64:ff9b::/96"),
    ipaddress.ip_network("2002::/16"),
]


def _system_modified(data: Dict[str, Any], cmdb: str) -> str:
    cmdb_l = str(cmdb or "").lower().strip()
    for s in (data.get("model") or {}).get("softwareSystems") or []:
        if str((s.get("properties") or {}).get("cmdb", "")).lower().strip() != cmdb_l:
            continue
        raw = (s.get("properties") or {}).get("modified")
        return str(raw) if raw is not None else ""
    return ""


def is_external_ip(ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip) if isinstance(ip, str) else ip
        networks = (_PRIVATE_IPV4 + _SPECIAL_IPV4) if ip_obj.version == 4 else _PRIVATE_IPV6
        return not any(ip_obj in network for network in networks)
    except ValueError:
        return False


def check_string_for_external_ip(text: str) -> Tuple[bool, List[str]]:
    external_ips: List[str] = []
    for match in re.finditer(_IPV4_PATTERN, text):
        ip = match.group()
        if is_external_ip(ip):
            external_ips.append(ip)
    for match in re.finditer(_IPV6_PATTERN, text):
        ip = match.group()
        if is_external_ip(ip):
            external_ips.append(ip)
    return bool(external_ips), external_ips


def _scan_deployment_node(node: Dict[str, Any]) -> List[str]:
    """Признаки выхода в интернет для узла развёртывания (как ``check_external_services``)."""
    props = node.get("properties") or {}
    name = str(node.get("name", "") or "").strip()
    evidences: List[str] = []
    already_external = False

    ip = props.get("ip")
    if ip:
        has_external, ips = check_string_for_external_ip(str(ip))
        if has_external:
            evidences.append(str(ips))
            already_external = True

    external_ip = props.get("external_ip")
    if external_ip and not already_external:
        evidences.append(f"'{external_ip}'")
        already_external = True

    host = props.get("host")
    if host and not already_external:
        host_s = str(host).strip()
        if host_s.lower().endswith(".beeline.ru"):
            evidences.append(host_s)

    if evidences:
        logger.info("EA.0001: внешний доступ у узла %s: %s", name, evidences)
    return evidences


def _collect_external_by_environment(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Признаки внешнего доступа по ``deploymentEnvironment`` (уникальные корневые environment)."""
    by_env: Dict[str, List[str]] = {}
    seen_roots: set[str] = set()

    for root in (data.get("model") or {}).get("deploymentNodes") or []:
        if not isinstance(root, dict):
            continue
        environment = str(root.get("environment", "") or "").strip()
        if not environment or environment in seen_roots:
            continue
        seen_roots.add(environment)
        by_env.setdefault(environment, [])

        stack: List[Dict[str, Any]] = [root]
        while stack:
            deployment_node = stack.pop()
            node_name = str(deployment_node.get("name", "") or "").strip() or "deployment-node"
            for evidence in _scan_deployment_node(deployment_node):
                by_env[environment].append(f"{node_name}: {evidence}")
            for child in deployment_node.get("children") or []:
                if isinstance(child, dict):
                    stack.append(child)

    return by_env


def analyze_ea_workspace(
    data: Dict[str, Any],
    cmdb: str,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    EA.0001: приложение имеет выход в интернет (внешние IP / ``external_ip`` / host ``*.beeline.ru``).

    Returns:
        (ea_ok, rows) — как в ``check_external_services``: ``isCheck=True``, если хотя бы в одном
        ``deploymentEnvironment`` найден признак выхода в интернет. В ``details`` — по одной строке
        на каждый уникальный environment: ``code`` = environment, ``status``/``check`` по стенду.
    """
    system_modified = _system_modified(data, cmdb)
    by_env = _collect_external_by_environment(data)

    if not by_env:
        return False, [
            {
                "code": "EA.0001",
                "name": "Нет deployment environment",
                "date": system_modified,
                "status": "FAIL",
                "check": False,
            }
        ]

    ok_rows: List[Dict[str, Any]] = []
    fail_rows: List[Dict[str, Any]] = []

    for environment, evidences in by_env.items():
        has_external = len(evidences) > 0
        row = {
            "code": environment,
            "name": environment,
            "date": system_modified,
            "status": "OK" if has_external else "FAIL",
            "check": has_external,
        }
        if has_external:
            row["name"] = f"{environment}: {'; '.join(evidences)}"
            ok_rows.append(row)
        else:
            row["name"] = f"{environment}: нет выхода в интернет"
            fail_rows.append(row)

    ea_ok = len(ok_rows) > 0
    return ea_ok, ok_rows + fail_rows
