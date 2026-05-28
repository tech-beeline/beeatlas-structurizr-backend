import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.api_utils import analyze_api_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/api01"])


class Api01Request(BaseModel):
    """Тело запроса к эндпоинту API.01."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Api01Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    spec: str = Field(
        default="",
        description="Ссылка на спецификацию (api_url из модели)",
    )


class Api01Response(BaseModel):
    """Тело ответа эндпоинта API.01 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Api01Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/api01")
async def api01_check(
    body: Api01Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    API.01: у приложения есть опубликованные API (см. ``check_api`` / загрузка методов из спецификации).
    """
    logger.info(
        "API.01 — callId=%s productCode=%s docId=%s",
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

    api01_ok, _a2, _a3, rows_api01, _r2, _r3 = analyze_api_workspace(data, body.productCode)
    return Api01Response(
        callId=body.callId,
        isCheck=api01_ok,
        details=[Api01Detail(**row) for row in rows_api01],
    )
