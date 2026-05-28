import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src_fitness_functions.beeatlas_api import get_workspace_json_cached
from src_fitness_functions.sdk.capability_utils import (
    Cpb02RelationshipRow,
    parse_capability_workspace,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["/api/v1/ff/cpb02"])


class Cpb02Request(BaseModel):
    """Тело запроса к эндпоинту CPB.02."""
    callId: UUID = Field(..., description="UUID вызова от FF Manager")
    productCode: str = Field(..., description="Мнемоника продукта (поле app из run)")


class Cpb02Detail(BaseModel):
    """Один элемент в списке деталей."""
    code: str = Field(..., description="Идентификатор связи или контейнера")
    name: str = Field(..., description="Краткое описание строки проверки")
    status: str = Field(..., description="Статус")
    check: bool = Field(..., description="Результат проверки")
    container_name: str = Field(default="", description="Имя контейнера")
    technical_capability: List[str] = Field(
        default_factory=list,
        description="Полные коды TC (CMDB.код) в контейнере",
    )
    external_callers: List[str] = Field(
        default_factory=list,
        description="Внешний участник связи (один элемент — контрагент по связи)",
    )


class Cpb02Response(BaseModel):
    """Тело ответа эндпоинта CPB.02 в формате, ожидаемом FF Manager."""
    callId: UUID = Field(..., description="Должен совпадать с callId из запроса")
    isCheck: bool = Field(..., description="Прошла ли проверка")
    details: List[Cpb02Detail] = Field(..., description="Детализация проверки")


def _cpb02_detail_from_rel(row: Cpb02RelationshipRow, *, check: bool) -> Cpb02Detail:
    return Cpb02Detail(
        code=row.relationship_id,
        name=row.name,
        status="OK" if check else "FAIL",
        check=check,
        container_name=row.container_name,
        technical_capability=list(row.technical_capability),
        external_callers=[row.external_party] if row.external_party else [],
    )


@router.post("/api/v1/ff/cpb02")
async def cpb02_check(
    body: Cpb02Request,
    docId: Optional[int] = Query(None, description="Идентификатор документа (опционально)"),
):
    """
    CPB.02: для всех контейнеров с внешним взаимодействием в модели заданы TC (компонент capability с code и parents).
    """
    logger.info(
        "CPB.02 — callId=%s productCode=%s docId=%s",
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

    analysis = parse_capability_workspace(data, body.productCode)
    rel_ok = [r for r in analysis.cpb02_relationship_rows if r.check]
    rel_fail = [r for r in analysis.cpb02_relationship_rows if not r.check]
    is_check = len(analysis.cpb02_missing_containers) == 0

    details: List[Cpb02Detail] = []
    for row in rel_ok:
        details.append(_cpb02_detail_from_rel(row, check=True))
    for row in rel_fail:
        details.append(_cpb02_detail_from_rel(row, check=False))

    if not details:
        details.append(
            Cpb02Detail(
                code="CPB.02",
                name="Нет контейнеров с внешним взаимодействием в области проверки CPB.02",
                status="OK",
                check=True,
                container_name="",
                technical_capability=[],
                external_callers=[],
            )
        )

    return Cpb02Response(callId=body.callId, isCheck=is_check, details=details)
