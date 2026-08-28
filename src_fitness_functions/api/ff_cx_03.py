import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.cx_utils import analyze_cx03_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cx03"])


class Cx03Request(BaseModel):
    """Тело запроса к эндпоинту CX.03."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cx03Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки (полный код TC)")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Cx03Response(BaseModel):
    """Тело ответа эндпоинта CX.03 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cx03Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cx03")
async def cx03_check(
    body: Cx03Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CX.03: наличие у контейнера, связанного с Person, внутренних component
    с типом ``tc``, для которых есть связка с шагами Customer Journey.

    Связка TC ↔ шаги CJ — заглушка (TO-DO) в ``cx_utils._match_cj_steps``;
    проверяется только наличие TC в person-related контейнерах.
    """
    logger.info(
        "CX.03 — callId=%s productCode=%s docId=%s",
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

    cx_ok, rows = analyze_cx03_workspace(data, body.productCode)
    return Cx03Response(
        callId=body.callId,
        isCheck=cx_ok,
        details=[Cx03Detail(**row) for row in rows],
    )
