import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.capability_utils import cpb05_quality_from_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cpb05"])


class Cpb05Request(BaseModel):
    """Тело запроса к эндпоинту CPB.05."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cpb05Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Cpb05Response(BaseModel):
    """Тело ответа эндпоинта CPB.05 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cpb05Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cpb05")
async def cpb05_check(
    body: Cpb05Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CPB.05: качество описания TC в ФДМ по критерию 101 (BeeAtlas БД), как ``check_cpb05``.
    """
    logger.info(
        "CPB.05 — callId=%s productCode=%s docId=%s",
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
        _: Dict[str, Any] = get_workspace_json_cached(docId)
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

    is_check, rows = cpb05_quality_from_db(body.productCode)
    details = [Cpb05Detail(**row) for row in rows]
    return Cpb05Response(callId=body.callId, isCheck=is_check, details=details)
