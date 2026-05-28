import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.sequence_utils import analyze_sq02_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/sq02"])


class Sq02Request(BaseModel):
    """Тело запроса к эндпоинту SQ.02."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Sq02Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Полный код technical capability (dynamic-диаграммы TC)")
    name: str = Field(..., description="REST-вызов: id связи, description, technology")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Sq02Response(BaseModel):
    """Тело ответа эндпоинта SQ.02 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Sq02Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/sq02")
async def sq02_check(
    body: Sq02Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    SQ.02: REST-связи на sequence TC содержат HTTP-метод в description (``check_sequences``).
    """
    logger.info(
        "SQ.02 — callId=%s productCode=%s docId=%s",
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

    sq02_ok, rows_sq02 = analyze_sq02_workspace(data, body.productCode)
    return Sq02Response(
        callId=body.callId,
        isCheck=sq02_ok,
        details=[Sq02Detail(**row) for row in rows_sq02],
    )
