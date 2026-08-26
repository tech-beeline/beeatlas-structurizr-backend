import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.capability_utils import parse_capability_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cpb03"])


class Cpb03Request(BaseModel):
    """Тело запроса к эндпоинту CPB.03."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cpb03Detail(BaseModel):
    """Один элемент в списке деталей (тот же набор полей, что у CPB.01)."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    source: str = Field(..., description="Источник: Structurizr / FAIL")
    parents: str = Field(..., description="Перечень родительских возможностей [ 'code', 'code', ... ]")
    check: bool = Field(..., description="Результат проверки")


class Cpb03Response(BaseModel):
    """Тело ответа эндпоинта CPB.03 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cpb03Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cpb03")
async def cpb03_check(
    body: Cpb03Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CPB.03: в Structurizr описаны technical capability (компонент type=capability с непустыми code и parents).
    """
    logger.info(
        "CPB.03 — callId=%s productCode=%s docId=%s",
        body.callId,
        body.productCode,
        docId,
    )

    if docId is None:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "callId": str(body.callId),
                "isCheck": False,
                "details": "Not implemented: docId is required",
                "countDetail": 0,
                "successDetail": 0,
            },
        )

    try:
        data: Dict[str, Any] = get_workspace_json_cached(docId)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            logger.error("Document not found: docId=%s", docId)
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "callId": str(body.callId),
                    "isCheck": False,
                    "details": f"Not found: document {docId} not found",
                    "countDetail": 0,
                    "successDetail": 0,
                },
            )
        raise

    pc = body.productCode.strip()
    analysis = parse_capability_workspace(data, pc)
    caps = analysis.full_capabilities
    incomplete = analysis.incomplete_capabilities
    is_check = len(caps) > 0

    details: List[Cpb03Detail] = []
    for tc in caps:
        full_code = f"{pc}.{tc.code}"
        details.append(
            Cpb03Detail(
                code=full_code,
                name=tc.name,
                source="Structurizr",
                parents=str([
                    str(p.get("code", "")).strip()
                    for p in tc.parents
                    if str(p.get("code", "")).strip()
                ]),
                check=True,
            )
        )
    for tc in incomplete:
        raw_code = tc.code.strip()
        if raw_code and "." in raw_code:
            full_code = raw_code
        elif raw_code:
            full_code = f"{pc}.{raw_code}"
        else:
            full_code = f"{pc}.{tc.container_id}.incomplete"
        parents_list = [
            str(p.get("code", "")).strip()
            for p in tc.parents
            if str(p.get("code", "")).strip()
        ]
        reason: List[str] = []
        if not tc.code.strip():
            reason.append("нет code")
        if not parents_list:
            reason.append("нет parents")
        suffix = f" ({', '.join(reason)})" if reason else ""
        details.append(
            Cpb03Detail(
                code=full_code,
                name=f"{tc.name}{suffix}",
                source="Structurizr",
                parents=str(parents_list),
                check=False,
            )
        )

    if not details:
        details.append(
            Cpb03Detail(
                code="CPB.03",
                name=f"Отсутствуют описанные technical capability для системы cmdb={pc}",
                source="FAIL",
                parents=str([]),
                check=False,
            )
        )

    return Cpb03Response(callId=body.callId, isCheck=is_check, details=details)
