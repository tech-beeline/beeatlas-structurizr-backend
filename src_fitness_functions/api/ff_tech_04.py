import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.technology_utils import analyze_tech04_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/tech04"])


class Tech04Request(BaseModel):
    """Тело запроса к эндпоинту TECH.04."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Tech04Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Tech04Response(BaseModel):
    """Тело ответа эндпоинта TECH.04 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Tech04Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/tech04")
async def tech04_check(
    body: Tech04Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    TECH.04: нет протоколов связей контейнеров в статусе HOLD.
    """
    logger.info(
        "TECH.04 — callId=%s productCode=%s docId=%s",
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

    tech04_ok, rows = analyze_tech04_workspace(data, body.productCode)
    return Tech04Response(
        callId=body.callId,
        isCheck=tech04_ok,
        details=[Tech04Detail(**row) for row in rows],
    )
