import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/adr01"])


# ── Pydantic-модели ──────────────────────────────────────────────────────────


class Adr01Request(BaseModel):
    """Тело запроса к эндпоинту ADR.01."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class AdrDetail(BaseModel):
    """Один ADR в списке деталей."""
    code: str = Field(..., description="Код ADR")
    name: str = Field(..., description="Наименование ADR")
    date: str = Field(..., description="Дата ADR")
    status: str = Field(..., description="Статус ADR")
    check: bool = Field(..., description="Результат проверки")


class Adr01Response(BaseModel):
    """Тело ответа эндпоинта ADR.01 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[AdrDetail] = Field(..., description="Список ADR (код, имя, дата, статус)")


# ── Эндпоинт ─────────────────────────────────────────────────────────────────


@router.post("/api/v1/ff/adr01")
async def adr01_check(
    body: Adr01Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    ADR.01: наличие хотя бы одного ADR в `documentation.decisions` (как в `check_adr`).
    """
    logger.info(
        "ADR.01 — callId=%s productCode=%s docId=%s",
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

    decisions: List[Dict[str, Any]] = data.get("documentation", {}).get("decisions", []) or []
    details: List[AdrDetail] = []
    for i, adr in enumerate(decisions):
        adr_id = adr.get("id", f"adr_{i}")
        adr_title = adr.get("title", f"ADR {i + 1}")
        title_str = adr_title.strip() if isinstance(adr_title, str) else str(adr_title)
        details.append(
            AdrDetail(
                code=str(adr_id),
                name=title_str,
                date=str(adr.get("date", "")),
                status=str(adr.get("status", "")),
                check=True,
            )
        )

    is_check = len(details) > 0
    return Adr01Response(callId=body.callId, isCheck=is_check, details=details)

