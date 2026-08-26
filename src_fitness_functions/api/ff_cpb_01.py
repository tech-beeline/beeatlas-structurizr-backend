import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.capability_utils import (
    fetch_responsibility_tech_capabilities,
    landscape_product_id_from_env,
    parse_capability_workspace,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cpb01"])


def _parents_from_payload(raw: Any) -> List[str]:
    """Нормализация родителей TC: список объектов с полем ``code``."""
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for p in raw:
        if isinstance(p, dict):
            c = p.get("code")
            if c is not None and str(c).strip():
                out.append( str(c).strip())
        elif isinstance(p, str) and p.strip():
            out.append(p.strip())
    return out


class Cpb01Request(BaseModel):
    """Тело запроса к эндпоинту CPB.01."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cpb01Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Код объекта проверки")
    name: str = Field(..., description="Наименование")
    source: str = Field(..., description="Источник данных: Landscape, Structurizr и т.п.")
    parents: str = Field(...,
        description="Родительские возможности (элементы с полем code)",
    )
    check: bool = Field(..., description="Результат проверки")


class Cpb01Response(BaseModel):
    """Тело ответа эндпоинта CPB.01 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cpb01Detail] = Field(..., description="Детализация проверки")


@router.post("/api/v1/ff/cpb01")
async def cpb01_check(
    body: Cpb01Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CPB.01: определены технические возможности продукта (Structurizr и/или landscape по Capability API).
    """
    logger.info(
        "CPB.01 — callId=%s productCode=%s docId=%s",
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

    pc = body.productCode.strip()
    analysis = parse_capability_workspace(data, pc)
    pid = landscape_product_id_from_env()
    landscape = fetch_responsibility_tech_capabilities(pid) if pid else []

    have_landscape = len(landscape) > 0
    have_struct = len(analysis.full_capabilities) > 0
    is_check = have_landscape or have_struct

    details: List[Cpb01Detail] = []
    if is_check:
        for item in landscape:
            details.append(
                Cpb01Detail(
                    code=str(item.get("code", "")),
                    name=str(item.get("name", "")),
                    source="Landscape",
                    parents=str(_parents_from_payload(item.get("parents"))),
                    check=True,
                )
            )
        for tc in analysis.full_capabilities:
            full_code = f"{pc}.{tc.code}"
            details.append(
                Cpb01Detail(
                    code=full_code,
                    name=tc.name,
                    source="Structurizr",
                    parents=str([str(p.get("code", "")).strip() for p in tc.parents if str(p.get("code", "")).strip()]),
                    check=True,
                )
            )
    else:
        details.append(
            Cpb01Detail(
                code="CPB.01",
                name="Для системы нет capability ни в Structurizr, ни в landscape",
                source="FAIL",
                parents=str([]),
                check=False,
            )
        )

    return Cpb01Response(callId=body.callId, isCheck=is_check, details=details)
