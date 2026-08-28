"""Тесты эндпоинта CX.02 — технологии UI (по списку label из xlsx)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from ff_cx_builder import make_cx_workspace


class TestFfCx02:
    URL = "/api/v1/ff/cx02"
    PRODUCT_CODE = "FDMSHOWCASEAPP"

    def _post(self, client: TestClient, doc_id: int, product_code: str = PRODUCT_CODE):
        return client.post(
            self.URL,
            params={"docId": doc_id},
            json={"callId": str(uuid.uuid4()), "productCode": product_code},
        )

    def test_returns_501_when_doc_id_missing(self, client: TestClient) -> None:
        body = {"callId": str(uuid.uuid4()), "productCode": self.PRODUCT_CODE}
        response = client.post(self.URL, json=body)
        assert response.status_code == 501, response.text
        data = response.json()
        assert data["isCheck"] is False
        assert "Not implemented" in data["details"]

    def test_returns_404_when_document_not_found(self, client: TestClient) -> None:
        response = self._post(client, doc_id=999999)
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["isCheck"] is False
        assert "Not found" in data["details"]

    def test_happy_path(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace())
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is True
        assert len(data["details"]) == 1
        row = data["details"][0]
        assert row["code"] == "2"
        assert row["name"] == "Web интерфейс"
        assert row["status"] == "OK"
        assert row["check"] is True
        assert row["technology"] == "React, TypeScript, JavaScript"

    def test_ok_with_angular_label(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace(container_tech="Angular"))
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is True
        assert data["details"][0]["check"] is True

    def test_fail_when_no_frontend_tech(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace(container_tech="Spring Boot, Java"))
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is False
        row = data["details"][0]
        assert row["status"] == "FAIL"
        assert row["check"] is False
        assert "технологиями UI" in row["name"]

    def test_not_required_when_no_person_related_containers(
        self, client: TestClient, document_store
    ) -> None:
        doc_id = document_store.upload(make_cx_workspace(person_relationship=False))
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is True
        row = data["details"][0]
        assert row["status"] == "OK"
        assert row["check"] is True
        assert "не требовалась" in row["name"]

    def test_fail_when_system_not_found(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace())
        response = self._post(client, doc_id, product_code="UNKNOWN")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is False
        row = data["details"][0]
        assert row["status"] == "FAIL"
        assert "Система не найдена" in row["name"]
