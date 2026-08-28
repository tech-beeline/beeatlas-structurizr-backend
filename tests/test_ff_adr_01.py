"""Тесты для нового пакета `src_fitness_functions` (FF Manager-совместимые эндпоинты)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


class TestFfAdr01:
    URL = "/api/v1/ff/adr01"

    def test_returns_501_when_doc_id_missing(self, client: TestClient) -> None:
        """Без query-параметра docId возвращается 501 — это поведение «not implemented»."""
        body = {"callId": str(uuid.uuid4()), "productCode": "TEST"}
        response = client.post(self.URL, json=body)
        assert response.status_code == 501, response.text
        data = response.json()
        assert data["isCheck"] is False
        assert data["countDetail"] == 0
        assert "Not implemented" in data["details"]

    def test_returns_200_when_doc_id_provided(self, client: TestClient, document_store) -> None:
        ws = {
            "model": {"properties": {"workspace_cmdb": "fdmshowcaseapp"}},
            "documentation": {
                "decisions": [
                    {"id": "1", "title": "ADR 1", "date": "2026-01-01", "status": "Accepted"}
                ]
            },
        }
        doc_id = document_store.upload(ws)
        call_id = str(uuid.uuid4())
        body = {"callId": call_id, "productCode": "FDMSHOWCASEAPP"}
        response = client.post(self.URL, params={"docId": doc_id}, json=body)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["callId"] == call_id
        assert data["isCheck"] is True
        assert isinstance(data["details"], list)
        assert len(data["details"]) >= 1
        # Структура одного элемента details
        first = data["details"][0]
        assert {"code", "name", "date", "status", "check"} <= set(first.keys())

    def test_returns_404_when_document_not_found(self, client: TestClient) -> None:
        """Когда документа нет в Document Service — отдаём 404 с FF-форматом ответа."""
        body = {"callId": str(uuid.uuid4()), "productCode": "FDMSHOWCASEAPP"}
        response = client.post(self.URL, params={"docId": 999999}, json=body)
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["isCheck"] is False
        assert "Not found" in data["details"]

    def test_invalid_body_returns_validation_error(self, client: TestClient) -> None:
        # Глобальный exception handler в src/main.py превращает 422 в 400.
        response = client.post(self.URL, params={"docId": 1}, json={"callId": "not-a-uuid"})
        assert response.status_code in (400, 422), response.text
