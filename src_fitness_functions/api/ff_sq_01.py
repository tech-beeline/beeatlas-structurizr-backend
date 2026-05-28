import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.sequence_utils import analyze_sq01_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/sq01"])


class Sq01Request(BaseModel):
    """Тело запроса к эндпоинту SQ.01."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Sq01Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Полный код TC (с префиксом CMDB системы)")
    name: Optional[str] = Field(None, description="Имя dynamic-диаграммы (только если диаграмма найдена)")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    plantUML: Optional[str] = Field(
        None,
        description="Сценарий dynamic-диаграммы в формате PlantUML (только если диаграмма найдена)",
    )


class Sq01Response(BaseModel):
    """Тело ответа эндпоинта SQ.01 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Sq01Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/sq01", response_model_exclude_none=True)
async def sq01_check(
    body: Sq01Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    SQ.01: для всех TC из Products API есть dynamicView (см. ``check_sequences``).
    """
    logger.info(
        "SQ.01 — callId=%s productCode=%s docId=%s",
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

    sq01_ok, rows_sq01 = analyze_sq01_workspace(data, body.productCode)
    return Sq01Response(
        callId=body.callId,
        isCheck=sq01_ok,
        details=[Sq01Detail(**row) for row in rows_sq01],
    )
