import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.capability_utils import cpb04_mispositioned, parse_capability_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cpb04"])


class Cpb04Request(BaseModel):
    """Тело запроса к эндпоинту CPB.04."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cpb04Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    rule: str = Field(..., description="Код правила (CPB.04 / CPB.04_PARENT_DMN / CPB.04_PARENT_GRP)")
    reason: str = Field(..., description="Пояснение к результату")
    severity: str = Field(..., description="Уровень: ok при успехе, error при нарушении")


class Cpb04Response(BaseModel):
    """Тело ответа эндпоинта CPB.04 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cpb04Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cpb04")
async def cpb04_check(
    body: Cpb04Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CPB.04: позиционирование TC в ФДМ — у родительских BC не должно быть префиксов dmn. / grp. в коде.
    """
    logger.info(
        "CPB.04 — callId=%s productCode=%s docId=%s",
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
    bad = cpb04_mispositioned(analysis.full_capabilities)
    is_check = len(bad) == 0

    details: List[Cpb04Detail] = []
    if is_check:
        details.append(
            Cpb04Detail(
                code="CPB.04",
                name="Позиционирование технических возможностей в ФДМ выполнено корректно",
                status="OK",
                check=True,
                rule="CPB.04",
                reason="Родительские BC не содержат в коде подстрок dmn. / grp.",
                severity="ok",
            )
        )
    else:
        for issue in bad:
            tc = issue.tc
            code = f"{pc}.{tc.code}"
            details.append(
                Cpb04Detail(
                    code=code,
                    name=f"{tc.code} {tc.name}",
                    status="FAIL",
                    check=False,
                    rule=issue.rule,
                    reason=issue.reason,
                    severity=issue.severity,
                )
            )

    return Cpb04Response(callId=body.callId, isCheck=is_check, details=details)
