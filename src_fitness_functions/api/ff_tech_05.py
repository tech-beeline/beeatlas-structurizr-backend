import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.technology_utils import analyze_tech05_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/tech05"])


class Tech05Request(BaseModel):
    """Тело запроса к эндпоинту TECH.05."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Tech05Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Tech05Response(BaseModel):
    """Тело ответа эндпоинта TECH.05 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Tech05Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/tech05")
async def tech05_check(
    body: Tech05Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    TECH.05: протоколы связей из TechRadar.
    """
    logger.info(
        "TECH.05 — callId=%s productCode=%s docId=%s",
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

    tech05_ok, rows = analyze_tech05_workspace(data, body.productCode)
    return Tech05Response(
        callId=body.callId,
        isCheck=tech05_ok,
        details=[Tech05Detail(**row) for row in rows],
    )
