import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.container_utils import analyze_cnt_workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cnt03"])


class Cnt03Request(BaseModel):
    """Тело запроса к эндпоинту CNT.03."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cnt03Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    source_name: str = Field(default="", description="Имя контейнера-источника связи")
    target_name: str = Field(
        default="",
        description="Имя приёмника по destinationId: контейнер, иначе softwareSystem, иначе id",
    )


class Cnt03Response(BaseModel):
    """Тело ответа эндпоинта CNT.03 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cnt03Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cnt03")
async def cnt03_check(
    body: Cnt03Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CNT.03: у всех связей между контейнерами задана технология (см. ``check_container``).
    """
    logger.info(
        "CNT.03 — callId=%s productCode=%s docId=%s",
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

    _c1, _c2, cnt03_ok, _r1, _r2, rows_cnt03 = analyze_cnt_workspace(data, body.productCode)
    return Cnt03Response(
        callId=body.callId,
        isCheck=cnt03_ok,
        details=[Cnt03Detail(**row) for row in rows_cnt03],
    )
