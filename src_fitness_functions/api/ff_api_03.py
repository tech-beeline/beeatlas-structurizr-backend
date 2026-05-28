import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.api_utils import analyze_api_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/api03"])


class Api03Request(BaseModel):
    """Тело запроса к эндпоинту API.03."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Api03Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    technical_capability: str = Field(
        default="",
        description="Код technical capability (TC)",
    )
    interface_code: str = Field(
        default="",
        description="Код интерфейса в модели",
    )
    api_url: str = Field(
        default="",
        description="api_url / спецификация (пусто при нарушении API.03)",
    )


class Api03Response(BaseModel):
    """Тело ответа эндпоинта API.03 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Api03Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/api03")
async def api03_check(
    body: Api03Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    API.03: для всех TC задана спецификация (нет интерфейса с TC без api_url).
    """
    logger.info(
        "API.03 — callId=%s productCode=%s docId=%s",
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

    _a1, _a2, api03_ok, _r1, _r2, rows_api03 = analyze_api_workspace(data, body.productCode)
    return Api03Response(
        callId=body.callId,
        isCheck=api03_ok,
        details=[Api03Detail(**row) for row in rows_api03],
    )
