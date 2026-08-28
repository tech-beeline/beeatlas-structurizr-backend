import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.cx_utils import analyze_cx02_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cx02"])


class Cx02Request(BaseModel):
    """Тело запроса к эндпоинту CX.02."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cx02Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки (id контейнера)")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    technology: str = Field(default="", description="Технология контейнера (при наличии)")


class Cx02Response(BaseModel):
    """Тело ответа эндпоинта CX.02 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cx02Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cx02")
async def cx02_check(
    body: Cx02Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CX.02: технологии UI.

    По модели: среди контейнеров целевой системы, связанных с Person, есть
    контейнер, в ``technology`` которого встречается label из фиксированного
    списка UI-технологий (см. ``cx_utils._FRONTEND_LABELS``).
    """
    logger.info(
        "CX.02 — callId=%s productCode=%s docId=%s",
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

    cx_ok, rows = analyze_cx02_workspace(data, body.productCode)
    return Cx02Response(
        callId=body.callId,
        isCheck=cx_ok,
        details=[Cx02Detail(**row) for row in rows],
    )
