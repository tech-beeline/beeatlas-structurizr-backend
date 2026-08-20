"""
Утилиты для CPB.01–CPB.05 по JSON workspace Structurizr и внешним источникам.

Логика выровнена с ``structurizr_utils.functions.capability.check_capability`` / ``check_cpb04`` /
``check_cpb05`` без импортов structurizr_utils.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import AbstractSet, Any, Dict, List, Optional, Set, Tuple

import psycopg2

from src_fitness_functions.beeatlas_api import get_beeatlas_api

logger = logging.getLogger(__name__)

# Корень репозитория (structurizr-backend/) — для подгрузки `.env` в CPB.05 при пустом os.environ.
_PROJECT_ROOT_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_repo_dotenv_into_environ() -> None:
    """Подставляет в ``os.environ`` значения из ``.env`` / ``.env_dev``, если ключ ещё не задан."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for fname in (".env", ".env_dev"):
        load_dotenv(os.path.join(_PROJECT_ROOT_REPO, fname), override=False)


@dataclass
class StructTechCapability:
    """TC, описанная в Structurizr (компонент type=capability с code и parents)."""

    code: str
    name: str
    description: str
    container_id: str
    container_name: str
    parents: List[Dict[str, str]]


@dataclass
class Cpb04PositioningIssue:
    """Нарушение CPB.04: родительский BC с префиксом ``dmn.`` или ``grp.`` в коде."""

    tc: StructTechCapability
    rule: str
    reason: str
    severity: str


@dataclass
class Cpb02ContainerRow:
    """Контейнер целевой системы с внешним взаимодействием (для CPB.02).

    Поле ``technical_capability`` — полные коды TC в виде ``CMDB.код``.
    Поле ``external_callers`` — имена внешних систем/контейнеров по входящим и исходящим связям контейнера
    с внешней моделью (см. ``_external_interaction_names``).
    """

    container_id: str
    container_name: str
    technical_capability: List[str]
    external_callers: List[str]


@dataclass
class Cpb02RelationshipRow:
    """Одна внешняя связь контейнера (детализация CPB.02)."""

    relationship_id: str
    container_id: str
    container_name: str
    name: str
    external_party: str
    technical_capability: List[str]
    check: bool


@dataclass
class CapabilityWorkspaceAnalysis:
    """Результат разбора workspace для проверок CPB."""

    architect: str
    full_capabilities: List[StructTechCapability] = field(default_factory=list)
    incomplete_capabilities: List[StructTechCapability] = field(default_factory=list)
    containers_with_any_capability: Set[str] = field(default_factory=set)
    cpb02_satisfied_containers: List[Cpb02ContainerRow] = field(default_factory=list)
    cpb02_missing_containers: List[Cpb02ContainerRow] = field(default_factory=list)
    cpb02_relationship_rows: List[Cpb02RelationshipRow] = field(default_factory=list)


def _norm_cmdb(cmdb: str) -> str:
    return str(cmdb or "").lower().strip()


def _full_tc_code(product_cmdb: str, short_code: str) -> str:
    """
    Полное имя TC в виде ``CMDB.код`` (без повторного префикса, если код уже полный).
    """
    pc = str(product_cmdb or "").strip()
    sc = str(short_code or "").strip()
    if not sc:
        return ""
    if not pc:
        return sc
    if "." in sc and sc.lower().startswith(pc.lower() + "."):
        return sc
    return f"{pc}.{sc}"


def _container_has_external_interface(
    cid: str,
    container: Dict[str, Any],
    referenced_c: Set[str],
    external_system_ids: AbstractSet[str],
) -> bool:
    """
    Внешнее взаимодействие контейнера (как в ``check_capability`` + исходящие связи на внешнюю software system).

    Учитывается:
    - контейнер указан как ``destinationId`` у связи на элементе внешней **software system**;
    - на контейнере связь ``внешняя software system → этот контейнер``;
    - на контейнере связь ``этот контейнер → внешняя software system`` (типичный Structurizr для outbound).
    """
    if cid in referenced_c:
        return True
    for relationship in container.get("relationships") or []:
        src = str(relationship.get("sourceId", ""))
        dst = str(relationship.get("destinationId", ""))
        if src in external_system_ids and dst == cid:
            return True
        # if src == cid and dst in external_system_ids:
        #     return True
    return False


def _external_interaction_names(
    cid: str,
    container: Dict[str, Any],
    callers_from_external_ss: Dict[str, Set[str]],
    external_system_ids: AbstractSet[str],
    system_name_by_id: Dict[str, str],
    container_name_by_id: Dict[str, str],
    target_container_ids: AbstractSet[str],
) -> List[str]:
    """
    Имена внешних software system / контейнеров в связях с данным контейнером.

    Включает:
    - входящие на контейнер (``destinationId`` = контейнер): источник — внешняя система или другой контейнер;
    - связи на узле внешней software system, у которых ``destinationId`` = этот контейнер (имя той системы);
    - исходящие с контейнера (``sourceId`` = контейнер) на внешнюю software system или на контейнер **вне** целевой системы.
    """
    names: Set[str] = set()
    names.update(callers_from_external_ss.get(cid, ()))
    for rel in container.get("relationships") or []:
        src = str(rel.get("sourceId", ""))
        dst = str(rel.get("destinationId", ""))
        if dst == cid and src and src != cid:
            if src in external_system_ids:
                label = system_name_by_id.get(src, "").strip()
                if label:
                    names.add(label)
            elif src in container_name_by_id:
                label = container_name_by_id[src].strip()
                if label:
                    names.add(label)
        if src == cid and dst and dst != cid:
            if dst in external_system_ids:
                label = system_name_by_id.get(dst, "").strip()
                if label:
                    names.add(label)
            elif dst in container_name_by_id and dst not in target_container_ids:
                label = container_name_by_id[dst].strip()
                if label:
                    names.add(label)
    return sorted(names)


def _collect_cpb02_relationship_rows(
    cid: str,
    cname: str,
    container: Dict[str, Any],
    *,
    check: bool,
    technical_capability: List[str],
    external_system: Dict[str, Any],
    callers_from_external_ss: Dict[str, Set[str]],
    external_system_ids: AbstractSet[str],
    system_name_by_id: Dict[str, str],
    container_name_by_id: Dict[str, str],
    target_container_ids: AbstractSet[str],
) -> List[Cpb02RelationshipRow]:
    """Собрать строки детализации CPB.02 по каждой внешней связи контейнера."""
    rows: List[Cpb02RelationshipRow] = []
    seen: Set[str] = set()

    def _add(
        relationship_id: str,
        external_party: str,
        direction: str,
        description: str,
    ) -> None:
        rid = relationship_id.strip() or f"{cid}-rel-{len(rows)}"
        if rid in seen:
            return
        seen.add(rid)
        party = external_party.strip() or "внешний участник"
        desc = description.strip()
        if desc:
            label = f"{cname} — {direction} «{party}»: {desc}"
        else:
            label = f"{cname} — {direction} «{party}»"
        rows.append(
            Cpb02RelationshipRow(
                relationship_id=rid,
                container_id=cid,
                container_name=cname,
                name=label,
                external_party=party,
                technical_capability=list(technical_capability),
                check=check,
            )
        )

    for ss_id, ss in external_system.items():
        party = system_name_by_id.get(ss_id, ss_id).strip() or ss_id
        for rel in ss.get("relationships") or []:
            if str(rel.get("destinationId", "")) != cid:
                continue
            rid = str(rel.get("id", f"ss-{ss_id}-in-{cid}"))
            _add(rid, party, "входящая связь", str(rel.get("description", "") or ""))

    for rel in container.get("relationships") or []:
        src = str(rel.get("sourceId", ""))
        dst = str(rel.get("destinationId", ""))
        desc = str(rel.get("description", "") or "")
        rid = str(rel.get("id", ""))

        if dst == cid and src in external_system_ids:
            party = system_name_by_id.get(src, src)
            _add(rid or f"{src}-in-{cid}", party, "входящая связь", desc)
        elif src == cid and dst in external_system_ids:
            party = system_name_by_id.get(dst, dst)
            _add(rid or f"{cid}-out-{dst}", party, "исходящая связь", desc)
        elif dst == cid and src in container_name_by_id and src not in target_container_ids:
            party = container_name_by_id[src]
            _add(rid or f"{src}-in-{cid}", party, "входящая связь", desc)
        elif src == cid and dst in container_name_by_id and dst not in target_container_ids:
            party = container_name_by_id[dst]
            _add(rid or f"{cid}-out-{dst}", party, "исходящая связь", desc)

    for party in sorted(callers_from_external_ss.get(cid, ())):
        synthetic = f"ext-ss-in-{cid}-{party}"
        if synthetic not in seen:
            _add(synthetic, party, "входящая связь (внешняя система)", "")

    if not rows:
        for party in _external_interaction_names(
            cid,
            container,
            callers_from_external_ss,
            external_system_ids,
            system_name_by_id,
            container_name_by_id,
            target_container_ids,
        ):
            synthetic = f"ext-{cid}-{party}"
            if synthetic not in seen:
                _add(synthetic, party, "внешнее взаимодействие", "")

    if not rows:
        _add(cid, "", "внешнее взаимодействие", "")

    return rows


def fetch_responsibility_tech_capabilities(product_id: int, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    GET ``/api/v1/tech-capabilities/product/{id}`` — список ``responsibility`` (как ``load_capabilities``).
    При ошибке сети или HTTP возвращает пустой список.

    Реализация — ``BeeAtlasAPI.fetch_capability_responsibility`` (см. ``beeatlas_api``).
    """
    return get_beeatlas_api().fetch_capability_responsibility(product_id, timeout=timeout)


def parse_capability_workspace(data: Dict[str, Any], cmdb: str) -> CapabilityWorkspaceAnalysis:
    """
    Разбор внешних систем, ссылок на контейнеры и TC-компонентов целевой системы (как в ``check_capability``).

    Для CPB.02: ``cpb02_satisfied_containers`` — контейнеры с внешним взаимодействием и полной TC;
    ``cpb02_missing_containers`` — с внешним взаимодействием без полной TC (code + parents).
    """
    cmdb_l = _norm_cmdb(cmdb)
    architect = str(((data.get("model") or {}).get("properties") or {}).get("architect", "-"))
    systems: List[Dict[str, Any]] = (data.get("model") or {}).get("softwareSystems") or []

    system_name_by_id: Dict[str, str] = {}
    container_name_by_id: Dict[str, str] = {}
    for system in systems:
        sid = str(system.get("id", ""))
        if sid:
            system_name_by_id[sid] = str(system.get("name", "")).strip()
        for c in system.get("containers") or []:
            ccid = str(c.get("id", ""))
            if ccid:
                container_name_by_id[ccid] = str(c.get("name", "")).strip()

    target_container_ids: Set[str] = set()
    for system in systems:
        if _norm_cmdb(str((system.get("properties") or {}).get("cmdb", ""))) != cmdb_l:
            continue
        for c in system.get("containers") or []:
            tcid = str(c.get("id", ""))
            if tcid:
                target_container_ids.add(tcid)

    external_system: Dict[str, Any] = {}
    referenced_c: Set[str] = set()
    callers_from_external_ss: Dict[str, Set[str]] = {}

    for system in systems:
        scmdb = _norm_cmdb(str((system.get("properties") or {}).get("cmdb", "")))
        if scmdb == cmdb_l:
            continue
        sid = str(system.get("id", ""))
        ext_label = str(system.get("name", "")).strip()
        if sid:
            external_system[sid] = system
        for relationship in system.get("relationships") or []:
            did = relationship.get("destinationId")
            if did is not None and str(did):
                ds = str(did)
                referenced_c.add(ds)
                if ext_label:
                    callers_from_external_ss.setdefault(ds, set()).add(ext_label)

    external_system_ids = frozenset(external_system.keys())

    full_capabilities: List[StructTechCapability] = []
    incomplete_capabilities: List[StructTechCapability] = []
    containers_with_any_capability: Set[str] = set()
    cpb02_missing: Dict[str, Cpb02ContainerRow] = {}
    cpb02_satisfied: Dict[str, Cpb02ContainerRow] = {}
    cpb02_relationship_rows: List[Cpb02RelationshipRow] = []

    for system in systems:
        scmdb = _norm_cmdb(str((system.get("properties") or {}).get("cmdb", "")))
        if scmdb != cmdb_l:
            continue
        props_sys = system.get("properties") or {}
        product_cmdb_display = str(props_sys.get("cmdb", cmdb)).strip() or str(cmdb).strip()

        for container in system.get("containers") or []:
            cid = str(container.get("id", ""))
            cname = str(container.get("name", ""))
            need_capability = True
            has_capability_component = False
            tc_codes_in_container: List[str] = []

            for component in container.get("components") or []:
                props = component.get("properties") or {}
                ctype = str(props.get("type", ""))
                ccode = str(props.get("code", "")).strip()
                cparents_raw = props.get("parents", "")
                cparents = str(cparents_raw).strip() if cparents_raw is not None else ""

                if ctype == "capability":
                    has_capability_component = True
                    if ccode:
                        tc_codes_in_container.append(_full_tc_code(product_cmdb_display, ccode))
                if ctype == "capability" and ccode and cparents:
                    need_capability = False
                    delimiters = r"[ ,\t;]+"
                    parents = [{"code": p.strip()} for p in re.split(delimiters, cparents) if p.strip()]
                    full_capabilities.append(
                        StructTechCapability(
                            code=ccode,
                            name=str(component.get("name", "Default capability name")),
                            description=str(
                                component.get("description", "Default capability description")
                            ),
                            container_id=cid,
                            container_name=cname,
                            parents=parents,
                        )
                    )
                elif ctype == "capability":
                    delimiters = r"[ ,\t;]+"
                    parents_partial = (
                        [{"code": p.strip()} for p in re.split(delimiters, cparents) if p.strip()]
                        if cparents
                        else []
                    )
                    comp_id = str(component.get("id", "")).strip()
                    incomplete_capabilities.append(
                        StructTechCapability(
                            code=ccode or comp_id or f"incomplete_{cid}",
                            name=str(component.get("name", "Capability (неполное описание)")),
                            description=str(
                                component.get("description", "Default capability description")
                            ),
                            container_id=cid,
                            container_name=cname,
                            parents=parents_partial,
                        )
                    )

            if has_capability_component and cid:
                containers_with_any_capability.add(cid)

            technical_capability = list(dict.fromkeys(tc_codes_in_container))

            if not cid:
                continue

            has_external = _container_has_external_interface(
                cid, container, referenced_c, external_system_ids
            )

            if not has_external:
                continue

            external_callers = _external_interaction_names(
                cid,
                container,
                callers_from_external_ss,
                external_system_ids,
                system_name_by_id,
                container_name_by_id,
                target_container_ids,
            )

            row = Cpb02ContainerRow(
                container_id=cid,
                container_name=cname,
                technical_capability=technical_capability,
                external_callers=external_callers,
            )
            container_check = not need_capability
            if need_capability:
                cpb02_missing[cid] = row
            else:
                cpb02_satisfied[cid] = row

            cpb02_relationship_rows.extend(
                _collect_cpb02_relationship_rows(
                    cid,
                    cname,
                    container,
                    check=container_check,
                    technical_capability=technical_capability,
                    external_system=external_system,
                    callers_from_external_ss=callers_from_external_ss,
                    external_system_ids=external_system_ids,
                    system_name_by_id=system_name_by_id,
                    container_name_by_id=container_name_by_id,
                    target_container_ids=target_container_ids,
                )
            )

    return CapabilityWorkspaceAnalysis(
        architect=architect,
        full_capabilities=full_capabilities,
        incomplete_capabilities=incomplete_capabilities,
        containers_with_any_capability=containers_with_any_capability,
        cpb02_satisfied_containers=list(cpb02_satisfied.values()),
        cpb02_missing_containers=list(cpb02_missing.values()),
        cpb02_relationship_rows=cpb02_relationship_rows,
    )


def landscape_product_id_from_env() -> Optional[int]:
    """Числовой id продукта в FDM для Capability API (опционально ``CAPABILITY_PRODUCT_ID``)."""
    raw = os.getenv("CAPABILITY_PRODUCT_ID", "").strip()
    if not raw:
        return None
    try:
        pid = int(raw)
        return pid if pid > 0 else None
    except ValueError:
        return None


def cpb04_mispositioned(full_caps: List[StructTechCapability]) -> List[Cpb04PositioningIssue]:
    """
    TC с родителем, в коде которого встречается ``dmn.`` или ``grp.`` (нижний регистр).

    Для каждого нарушения возвращаются ``rule``, ``reason`` и ``severity`` (``error``).
    """
    out: List[Cpb04PositioningIssue] = []
    for tc in full_caps:
        has_dmn = False
        has_grp = False
        bad_parent_codes: List[str] = []
        for p in tc.parents:
            raw = str(p.get("code", "")).strip()
            lower = raw.lower()
            hit_dmn = "dmn." in lower
            hit_grp = "grp." in lower
            if hit_dmn:
                has_dmn = True
            if hit_grp:
                has_grp = True
            if (hit_dmn or hit_grp) and raw:
                bad_parent_codes.append(raw)
        if not (has_dmn or has_grp):
            continue
        seen: Set[str] = set()
        uniq_parents: List[str] = []
        for c in bad_parent_codes:
            if c not in seen:
                seen.add(c)
                uniq_parents.append(c)
        rule_parts: List[str] = []
        if has_dmn:
            rule_parts.append("CPB.04_PARENT_DMN")
        if has_grp:
            rule_parts.append("CPB.04_PARENT_GRP")
        rule = "+".join(rule_parts)
        bits: List[str] = []
        if has_dmn:
            bits.append("dmn.")
        if has_grp:
            bits.append("grp.")
        parents_join = ", ".join(uniq_parents)
        reason = (
            f"Родительский BC с недопустимым префиксом ({', '.join(bits)}) в коде: {parents_join}"
        )
        out.append(
            Cpb04PositioningIssue(
                tc=tc,
                rule=rule,
                reason=reason,
                severity="error",
            )
        )
    return out


def cpb05_quality_from_db(cmdb: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Оценка качества описания TC по БД BeeAtlas (критерий 101), как ``check_cpb05``.

    Returns:
        (is_check, detail_rows) — detail_rows для ``Cpb05Detail``: code, name, status, check.
    """
    _load_repo_dotenv_into_environ()
    fdm_vars = {
        "FDMDB_SERVER": os.getenv("FDMDB_SERVER", ""),
        "FDMDB_DB": os.getenv("FDMDB_DB", ""),
        "FDMDB_USERNAME": os.getenv("FDMDB_USERNAME", ""),
        "FDMDB_PASS": os.getenv("FDMDB_PASS", ""),
    }
    missing = [k for k, v in fdm_vars.items() if not v.strip()]
    if missing:
        logger.warning(
            "CPB.05: не заданы или пусты переменные окружения: %s",
            ", ".join(missing),
        )
        human = ", ".join(missing)
        return True, [
            {
                "code": "CPB.05",
                "name": (
                    "Проверка пропущена: не заданы или пусты переменные окружения BeeAtlas БД — "
                    f"{human}. Задайте их в окружении процесса (например `.env_dev` / `env_file` в compose)."
                ),
                "status": "SKIP",
                "check": True,
            }
        ]
    server = fdm_vars["FDMDB_SERVER"]
    db = fdm_vars["FDMDB_DB"]
    user = fdm_vars["FDMDB_USERNAME"]
    password = fdm_vars["FDMDB_PASS"]

    sql = """
        SELECT tc.code, tc.name, tc.description, ctc.criterion_id, ctc.value, ctc.grade, ctc.comment
        FROM capability.criterias_tc ctc, capability.tech_capability tc, product.product p
        WHERE ctc.tc_id = tc.id
        AND p.id = tc.responsibility_product_id
        AND ctc.criterion_id = 101
        AND p.Alias = lower(%s)
        ORDER BY p.Alias
    """
    marks = [0, 0, 0, 0, 0, 0]
    try:
        conn = psycopg2.connect(
            host=server,
            port=5432,
            database=db,
            user=user,
            password=password,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (cmdb,))
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        logger.error("CPB.05: ошибка БД: %s", e)
        return True, [
            {
                "code": "CPB.05",
                "name": f"Проверка пропущена из-за ошибки БД: {e}",
                "status": "SKIP",
                "check": True,
            }
        ]

    if not rows:
        logger.info("CPB.05: нет строк критерия 101 для alias=%s", cmdb)
        return True, [
            {
                "code": "CPB.05",
                "name": "Нет оценённых TC по критерию 101 для продукта",
                "status": "OK",
                "check": True,
            }
        ]

    for row in rows:
        if len(row) < 7:
            continue
        grade = row[5]
        try:
            gi = int(grade)
        except (TypeError, ValueError):
            continue
        if 0 <= gi <= 5:
            marks[gi] += 1

    cmdb_l = _norm_cmdb(cmdb)
    detail_rows: List[Dict[str, Any]] = []
    for i in range(6):
        if marks[i] > 0:
            detail_rows.append(
                {
                    "code": f"grade_{i}",
                    "name": f"Количество TC с оценкой {i}: {marks[i]}",
                    "status": "FAIL" if i <= 2 else "OK",
                    "check": i > 2,
                }
            )

    low = marks[0] + marks[1] + marks[2]
    is_ok = low == 0
    link = f"{os.getenv('URL_TCQUALITY')}/tcquality.php?cmdb={cmdb_l}"
    summary_name = (
        f"Описание возможностей не соответствует методике (см. {link})."
        if not is_ok
        else f"Описание в целом соответствует методике (см. {link})."
    )
    detail_rows.insert(
        0,
        {
            "code": "CPB.05",
            "name": summary_name,
            "status": "OK" if is_ok else "FAIL",
            "check": is_ok,
        },
    )
    return is_ok, detail_rows
