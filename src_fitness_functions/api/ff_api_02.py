import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.api_utils import analyze_api_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/api02"])


class Api02Request(BaseModel):
    """Тело запроса к эндпоинту API.02."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Api02Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    rps: Optional[float] = Field(default=None, description="RPS метода, если задан")
    latency: Optional[float] = Field(default=None, description="Latency метода, если задана")
    error_rate: Optional[float] = Field(
        default=None,
        description="Error rate метода, если задан",
    )


class Api02Response(BaseModel):
    """Тело ответа эндпоинта API.02 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Api02Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/api02")
async def api02_check(
    body: Api02Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    API.02: для некоторых методов определён SLA (RPS / Latency / Error rate).
    """
    logger.info(
        "API.02 — callId=%s productCode=%s docId=%s",
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

    _a1, api02_ok, _a3, _r1, rows_api02, _r3 = analyze_api_workspace(data, body.productCode)
    return Api02Response(
        callId=body.callId,
        isCheck=api02_ok,
        details=[Api02Detail(**row) for row in rows_api02],
    )
