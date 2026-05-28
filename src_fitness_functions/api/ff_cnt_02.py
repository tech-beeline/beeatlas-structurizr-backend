import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.container_utils import analyze_cnt_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cnt02"])


class Cnt02Request(BaseModel):
    """Тело запроса к эндпоинту CNT.02."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cnt02Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Cnt02Response(BaseModel):
    """Тело ответа эндпоинта CNT.02 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cnt02Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cnt02")
async def cnt02_check(
    body: Cnt02Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CNT.02: есть хотя бы одна containerView для данной системы (см. ``check_container``).
    """
    logger.info(
        "CNT.02 — callId=%s productCode=%s docId=%s",
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

    _c1, cnt02_ok, _c3, _r1, rows_cnt02, _r3 = analyze_cnt_workspace(data, body.productCode)
    return Cnt02Response(
        callId=body.callId,
        isCheck=cnt02_ok,
        details=[Cnt02Detail(**row) for row in rows_cnt02],
    )
