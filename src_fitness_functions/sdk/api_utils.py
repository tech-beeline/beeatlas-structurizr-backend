"""
Утилиты для проверок API.01–API.03 по JSON workspace Structurizr.

Логика соответствует ``structurizr_utils.functions.api.check_api`` (без публикации
и без импортов из structurizr_utils): обход систем/контейнеров/API-компонентов,
загрузка спецификаций, разбор SLA из properties и customElements.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)


def parse_string_to_dict(input_string: str) -> Dict[str, str]:
    """Парсит строку вида ``KEY1:VALUE1;KEY2:VALUE2`` (как в api.py)."""
    result_dict: Dict[str, str] = {}
    if not input_string or ";" not in input_string or ":" not in input_string:
        return result_dict
    pairs = input_string.upper().split(";")
    for pair in pairs:
        if ":" in pair:
            key, value = pair.split(":", 1)
            result_dict[key.strip()] = value.strip()
    return result_dict


def parse_new_string_to_dict(input_string: str) -> Dict[str, str]:
    """Парсит строку вида ``KEY1=VALUE1;KEY2=VALUE2`` (как в api.py)."""
    result_dict: Dict[str, str] = {}
    if not input_string or "=" not in input_string:
        return result_dict
    pairs = input_string.split(";")
    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            result_dict[key.upper().strip()] = value.upper().strip()
    return result_dict


def is_float(s: Any) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


@dataclass
class MethodRecord:
    name: Optional[str] = None
    rps: Optional[float] = None
    latency: Optional[float] = None
    error_rate: Optional[float] = None
    implements: Optional[str] = None
    description: Optional[str] = None


@dataclass
class InterfaceWork:
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    protocol: Optional[str] = None
    implements: Optional[str] = None
    specification: Optional[str] = None
    methods: List[MethodRecord] = field(default_factory=list)


class ApiSpecLoader:
    """Загрузка и разбор OpenAPI / proto / WSDL (как ``ApiLoader`` в api.py)."""

    def __init__(self, http: Optional[Any] = None) -> None:
        self.is_local: bool = False
        if http is not None:
            self._http = http
        else:
            from src_fitness_functions.beeatlas_api import get_beeatlas_api

            self._http = get_beeatlas_api()

    def download_swagger(self, url: str) -> str:
        try:
            parsed_uri = urlparse(url)
            if parsed_uri.scheme == "file":
                logger.info("Загрузка swagger из файла: %s", parsed_uri.netloc)
                with open(parsed_uri.netloc, encoding="utf-8") as f:
                    self.is_local = True
                    return f.read()
            if parsed_uri.scheme in ("http", "https"):
                logger.info("Загрузка swagger из URL: %s", url)
                text = self._http.download_http_text(
                    url,
                    timeout=5,
                    headers={"PRIVATE-TOKEN": "PRIVATE-TOKEN"},
                    verify=False,
                )
                return text
            if os.path.exists(url):
                logger.info("Загрузка swagger из локального файла: %s", url)
                with open(url, encoding="utf-8") as file:
                    self.is_local = True
                    return file.read()
            logger.warning("Файл не найден: %s", url)
            self.is_local = True
        except Exception as e:
            logger.error("Ошибка при загрузке спецификации: %s", e)
        return ""

    def get_api_methods_wsdl(self, file_path: str) -> List[MethodRecord]:
        result: List[MethodRecord] = []
        try:
            from zeep import Client  # type: ignore[import-untyped]
            from zeep.transports import Transport  # type: ignore[import-untyped]

            transport = Transport(timeout=3)
            client = Client(file_path, transport=transport)
            for service in client.wsdl.services.values():
                for port in service.ports.values():
                    operations = port.binding._operations.values()
                    for operation in operations:
                        method_name = f"{service.name}.{operation.name}"
                        result.append(MethodRecord(name=method_name))
        except Exception as e:
            logger.warning("Ошибка парсинга WSDL %s: %s", file_path, e)
            parsed_uri = urlparse(file_path)
            if parsed_uri.scheme not in ("http", "https"):
                self.is_local = True
        return result

    def get_api_methods_proto(self, file_path: str) -> List[MethodRecord]:
        result: List[MethodRecord] = []
        data = self.download_swagger(file_path)
        if len(data) == 0:
            logger.error("Unable to download proto file %s", file_path)
            return result
        try:
            services = re.findall(r"service\s+(\w+)\s*{([^}]*)}", data, re.DOTALL)
            for service_name, methods_block in services:
                methods = re.findall(
                    r"rpc\s+(\w+)\s*\(([^)]*)\)\s*returns\s*\(([^)]*)\)",
                    methods_block,
                )
                for method_name, _in_t, _out_t in methods:
                    result.append(MethodRecord(name=f"{service_name}.{method_name}"))
        except Exception as e:
            logger.warning("Unable to parse proto file %s: %s", file_path, e)
        return result

    def get_api_methods_rest(self, file_path: str) -> List[MethodRecord]:
        result: List[MethodRecord] = []
        data = self.download_swagger(file_path)
        if len(data) == 0:
            logger.error("Unable to download swagger file %s", file_path)
            return result
        try:
            spec = json.loads(data)
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method, _details in methods.items():
                    result.append(MethodRecord(name=f"{method.upper()} {path}"))
            return result
        except json.JSONDecodeError:
            logger.warning("Unable to parse json file %s", file_path)
        try:
            api_spec = yaml.safe_load(data)
            paths = api_spec.get("paths", {})
            for path, methods in paths.items():
                for method, _details in methods.items():
                    result.append(MethodRecord(name=f"{method.upper()} {path}"))
            return result
        except Exception as e:
            logger.warning("Unable to parse yaml file %s: %s", file_path, e)
        return result

    def get_api_methods(self, file_path: str, protocol: str) -> List[MethodRecord]:
        p = (protocol or "").lower()
        if p == "rest":
            return self.get_api_methods_rest(file_path=file_path)
        if p == "grpc":
            return self.get_api_methods_proto(file_path=file_path)
        if p in ("soap", "wsdl"):
            return self.get_api_methods_wsdl(file_path=file_path)
        return []


def fill_sla_methods(
    data: dict,
    component: dict,
    iface: InterfaceWork,
    structurizr_id: Optional[str],
) -> bool:
    """Заполняет SLA по customElements и properties компонента (как ``fill_sla_methods`` в api.py)."""
    has_sla = False

    raw_ce = data.get("model", {}).get("customElements")
    custom_elements: List[Any]
    if isinstance(raw_ce, list):
        custom_elements = raw_ce
    else:
        custom_elements = []

    for ce in custom_elements:
        if not isinstance(ce, dict) or "metadata" not in ce:
            continue
        metadata = parse_string_to_dict(ce["metadata"])
        if "ID" not in metadata:
            continue
        cid = metadata["ID"]
        if structurizr_id is None or cid != str(structurizr_id):
            continue
        props = ce.get("properties", {})
        if not isinstance(props, dict):
            continue
        for p in props:
            method_name_origin = str(p).strip()
            method_name = method_name_origin.upper().strip()
            rps, latency, error_rate = None, None, None
            raw_val = props[p]
            if raw_val is None:
                continue
            values = parse_string_to_dict(str(raw_val))
            if is_float(values.get("RPS", "")):
                rps = float(values.get("RPS"))
            if is_float(values.get("LATENCY", "")):
                latency = float(values.get("LATENCY"))
            if is_float(values.get("ERROR_RATE", "")):
                error_rate = float(values.get("ERROR_RATE"))
            implements = values.get("TC", None)
            found_method = False
            has_sla = True
            for method in iface.methods:
                if method.name and method.name.upper().strip() == method_name:
                    method.rps = rps
                    method.latency = latency
                    method.error_rate = error_rate
                    method.implements = implements
                    found_method = True
            if not found_method:
                iface.methods.append(
                    MethodRecord(
                        name=method_name_origin,
                        rps=rps,
                        latency=latency,
                        error_rate=error_rate,
                        implements=implements,
                    )
                )

    properties = component.get("properties", {})
    if not isinstance(properties, dict):
        return has_sla

    pattern = r"^.*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) .*$"
    for key in properties:
        value_raw = properties[key]
        if value_raw is None:
            continue
        value = str(value_raw).lower().strip()
        property_method = False
        if bool(re.match(pattern, key.upper())):
            property_method = True
        elif ("." in key) and (("rpc" in value) or ("latency" in value) or ("error_rate" in value)):
            property_method = True
        if not property_method:
            continue
        rps_n, latency_n, error_rate_n = None, None, None
        try:
            values = parse_new_string_to_dict(value)
            if is_float(values.get("RPS", "")):
                rps_n = float(values.get("RPS"))
            if is_float(values.get("LATENCY", "")):
                latency_n = float(values.get("LATENCY"))
            if is_float(values.get("ERROR_RATE", "")):
                error_rate_n = float(values.get("ERROR_RATE"))
            implements_n = values.get("TC", None)
            found_method = False
            has_sla = True
            for method in iface.methods:
                if method.name and method.name.upper().strip() == key.upper().strip():
                    method.rps = rps_n
                    method.latency = latency_n
                    method.error_rate = error_rate_n
                    method.implements = implements_n
                    found_method = True
            if not found_method:
                iface.methods.append(
                    MethodRecord(
                        name=key,
                        rps=rps_n,
                        latency=latency_n,
                        error_rate=error_rate_n,
                        implements=implements_n,
                    )
                )
        except Exception as ex:
            logger.error("Error adding SLA %s->%s : %s", key, value, ex)
    return has_sla


def _slug_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("   ", "_").replace(".", "_")


def analyze_api_workspace(
    data: Dict[str, Any],
    cmdb: str,
) -> Tuple[bool, bool, bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Выполняет обход workspace для проверок API.01, API.02, API.03.

    Returns:
        (api01_ok, api02_ok, api03_ok, rows_api01, rows_api02, rows_api03)
        Словари в ``rows_*`` содержат поля для Pydantic Detail, включая расширения:
        API.01 — ``spec`` (api_url); API.02 — ``rps``, ``latency``, ``error_rate``;
        API.03 — ``technical_capability``, ``interface_code``, ``api_url``.
    """
    entries_api01: List[Dict[str, Any]] = []
    entries_api02: List[Dict[str, Any]] = []
    entries_api03_ok: List[Dict[str, str]] = []
    violations_api03: List[Dict[str, str]] = []
    api_errors: List[Dict[str, str]] = []

    systems: List[Dict[str, Any]] = data.get("model", {}).get("softwareSystems", [])
    cmdb_l = cmdb.lower().strip()

    for system in systems:
        system_cmdb = str(system.get("properties", {}).get("cmdb", "")).lower().strip()
        if system_cmdb != cmdb_l:
            continue

        containers: List[Dict[str, Any]] = system.get("containers", [])
        for container in containers:
            container_source = str(container.get("properties", {}).get("source", "")).lower()
            if container_source == "landscape":
                continue

            external_name_container = container.get("properties", {}).get("external_name", None)
            container_code: Optional[str] = None

            if external_name_container is not None:
                container_code = f"{external_name_container}.{cmdb}"
            else:
                cname = container.get("name", None)
                if cname:
                    container_code = f"ext_{_slug_name(str(cname))}.{cmdb}"
                    container_has_api = False
                    for component in container.get("components", []):
                        if str(component.get("properties", {}).get("type", "")).lower() == "api":
                            container_has_api = True
                            break
                    if container_has_api:
                        api_errors.append(
                            {
                                str(cname): (
                                    f"нет external_name у контейнера, используем {container_code}"
                                )
                            }
                        )

            components: List[Dict[str, Any]] = container.get("components", [])

            for component in components:
                if str(component.get("properties", {}).get("type", "")).lower() != "api":
                    continue

                external_name_interface = component.get("properties", {}).get("external_name", None)
                iface = InterfaceWork()
                if external_name_interface:
                    if container_code:
                        iface.code = f"{external_name_interface}.{container_code}"
                    else:
                        api_errors.append(
                            {
                                str(component.get("name", "")): (
                                    "нет external_name у родительского контейнера"
                                )
                            }
                        )
                else:
                    comp_name = component.get("name", None)
                    if comp_name and container_code:
                        iface.code = (
                            f"ext_{_slug_name(str(comp_name))}.{container_code}"
                        )
                        api_errors.append(
                            {
                                str(comp_name): (
                                    f"нет external_name у интерфейса, используем {iface.code}"
                                )
                            }
                        )
                    else:
                        api_errors.append(
                            {
                                str(component.get("name", "")): (
                                    "нет external_name у интерфейса"
                                )
                            }
                        )

                iface.name = component.get("name", None)
                iface.description = component.get("description", None)
                props = component.get("properties", {}) or {}
                iface.version = props.get("version", None)
                iface.status = props.get("status", None)
                iface.protocol = props.get("protocol", None)
                iface.implements = props.get("tc", None)
                iface.specification = props.get("api_url", None)

                if iface.specification:
                    loader = ApiSpecLoader()
                    iface.methods = loader.get_api_methods(
                        file_path=iface.specification,
                        protocol=str(iface.protocol or ""),
                    )
                else:
                    iface.methods = []

                fill_sla_methods(
                    data=data,
                    component=component,
                    iface=iface,
                    structurizr_id=component.get("id", None),
                )

                if iface.methods and len(iface.methods) > 0 and iface.code:
                    ic = iface.code or iface.name or "unknown"
                    iname = iface.name or "Unknown Interface"
                    spec_url = str(iface.specification or "")
                    entries_api01.append(
                        {
                            "interface_code": ic,
                            "summary": f"{ic} {iname} ({len(iface.methods)} methods)",
                            "spec": spec_url,
                        }
                    )

                if iface.methods and iface.code:
                    for method in iface.methods:
                        if (
                            method.rps is not None
                            or method.latency is not None
                            or method.error_rate is not None
                        ):
                            method_name = method.name or "Unknown Method"
                            interface_name = iface.name or "Unknown Interface"
                            entries_api02.append(
                                {
                                    "method_name": method_name,
                                    "interface_code": iface.code or "",
                                    "interface_name": interface_name,
                                    "rps": method.rps,
                                    "latency": method.latency,
                                    "error_rate": method.error_rate,
                                }
                            )

                if iface.implements and iface.specification and iface.code:
                    entries_api03_ok.append(
                        {
                            "technical_capability": str(iface.implements),
                            "interface_code": str(iface.code),
                            "api_url": str(iface.specification),
                        }
                    )

                if iface.implements and not iface.specification and iface.code:
                    ic = iface.code or iface.name or "unknown"
                    iname = iface.name or "Unknown Interface"
                    tc_code = str(iface.implements or "Unknown TC")
                    violations_api03.append(
                        {
                            "interface_code": ic,
                            "technical_capability": tc_code,
                            "summary": (
                                f"{ic} {iname} (TC: {tc_code}, нет api_url / спецификации)"
                            ),
                        }
                    )

    api01_ok = len(entries_api01) > 0
    api02_ok = len(entries_api02) > 0
    api03_ok = len(violations_api03) == 0

    rows_api01: List[Dict[str, Any]] = []
    if api01_ok:
        for e in entries_api01:
            rows_api01.append(
                {
                    "code": e["interface_code"],
                    "name": e["summary"],
                    "date": "",
                    "status": "OK",
                    "check": True,
                    "spec": e.get("spec", ""),
                }
            )
        for err in api_errors:
            for key, value in err.items():
                rows_api01.append(
                    {
                        "code": str(key),
                        "name": str(value),
                        "date": "",
                        "status": "WARN",
                        "check": True,
                        "spec": "",
                    }
                )
    else:
        for err in api_errors:
            for key, value in err.items():
                rows_api01.append(
                    {
                        "code": str(key),
                        "name": str(value),
                        "date": "",
                        "status": "FAIL",
                        "check": False,
                        "spec": "",
                    }
                )
        if not rows_api01:
            rows_api01.append(
                {
                    "code": "API.01",
                    "name": "У приложения нет ни одного API с загруженными методами",
                    "date": "",
                    "status": "FAIL",
                    "check": False,
                    "spec": "",
                }
            )

    rows_api02: List[Dict[str, Any]] = []
    if api02_ok:
        for e in entries_api02:
            row: Dict[str, Any] = {
                "code": e["method_name"],
                "name": f"{e['method_name']} ({e['interface_name']})",
                "date": "",
                "status": "OK",
                "check": True,
                "rps": e.get("rps"),
                "latency": e.get("latency"),
                "error_rate": e.get("error_rate"),
            }
            rows_api02.append(row)
    else:
        rows_api02.append(
            {
                "code": "API.02",
                "name": "Ни для одного метода не определён SLA (RPS/Latency/Error rate)",
                "date": "",
                "status": "FAIL",
                "check": False,
                "rps": None,
                "latency": None,
                "error_rate": None,
            }
        )

    rows_api03: List[Dict[str, Any]] = []
    if api03_ok:
        if entries_api03_ok:
            for e in entries_api03_ok:
                tc = e["technical_capability"]
                ic = e["interface_code"]
                url = e["api_url"]
                rows_api03.append(
                    {
                        "code": ic,
                        "name": f"TC {tc} → интерфейс {ic}, api_url задан",
                        "date": "",
                        "status": "OK",
                        "check": True,
                        "technical_capability": tc,
                        "interface_code": ic,
                        "api_url": url,
                    }
                )
        else:
            rows_api03.append(
                {
                    "code": "API.03",
                    "name": "Нет интерфейсов с TC и api_url; нарушений (TC без спецификации) нет",
                    "date": "",
                    "status": "OK",
                    "check": True,
                    "technical_capability": "",
                    "interface_code": "",
                    "api_url": "",
                }
            )
    else:
        for v in violations_api03:
            rows_api03.append(
                {
                    "code": v["interface_code"],
                    "name": v["summary"],
                    "date": "",
                    "status": "FAIL",
                    "check": False,
                    "technical_capability": v["technical_capability"],
                    "interface_code": v["interface_code"],
                    "api_url": "",
                }
            )

    return api01_ok, api02_ok, api03_ok, rows_api01, rows_api02, rows_api03
