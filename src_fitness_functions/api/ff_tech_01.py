import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.technology_utils import analyze_tech01_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/tech01"])


class Tech01Request(BaseModel):
    """Тело запроса к эндпоинту TECH.01."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Tech01Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Tech01Response(BaseModel):
    """Тело ответа эндпоинта TECH.01 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Tech01Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/tech01")
async def tech01_check(
    body: Tech01Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    TECH.01: технологии контейнеров есть в TechRadar (см. ``check_technology``).
    """
    logger.info(
        "TECH.01 — callId=%s productCode=%s docId=%s",
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

    tech01_ok, rows = analyze_tech01_workspace(data, body.productCode)
    return Tech01Response(
        callId=body.callId,
        isCheck=tech01_ok,
        details=[Tech01Detail(**row) for row in rows],
    )
