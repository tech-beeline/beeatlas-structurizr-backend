import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/dep04"])


class Dep04Request(BaseModel):
    """Тело запроса к эндпоинту DEP.04."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Dep04Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    date: str = Field(..., description="Дата (при наличии)")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")


class Dep04Response(BaseModel):
    """Тело ответа эндпоинта DEP.04 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Dep04Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/dep04")
async def dep04_check(
    body: Dep04Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    Заглушка DEP.04: Правильно задана макросегментация Protected/DMZ STD/NST Operations/RND
    """
    logger.info(
        "DEP.04 stub — callId=%s productCode=%s docId=%s",
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

    logger.debug("Workspace loaded docId=%s sample_keys=%s", docId, list(data.keys())[:5])

    return Dep04Response(
        callId=body.callId,
        isCheck=True,
        details=[
            Dep04Detail(
                code="DEP.04",
                name="Правильно задана макросегментация Protected/DMZ STD/NST Operations/RND",
                date="",
                status="stub",
                check=True,
            ),
        ],
    )
