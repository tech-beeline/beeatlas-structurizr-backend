"""Тесты эндпоинта CX.01 — взаимодействие пользователя с системой (по модели)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from ff_cx_builder import make_cx_workspace


class TestFfCx01:
    URL = "/api/v1/ff/cx01"
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
        assert data["countDetail"] == 0
        assert "Not implemented" in data["details"]

    def test_returns_404_when_document_not_found(self, client: TestClient) -> None:
        response = self._post(client, doc_id=999999)
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["isCheck"] is False
        assert data["countDetail"] == 0
        assert "Not found" in data["details"]

    def test_happy_path(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace())
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is True
        assert len(data["details"]) == 1
        row = data["details"][0]
        assert row["code"] == "10"
        assert row["name"] == "Пользователь"
        assert row["status"] == "OK"
        assert row["check"] is True

    def test_person_related_to_system_direction(self, client: TestClient, document_store) -> None:
        """Person связан с системой (не с контейнером) — всё равно UI-Person."""
        doc_id = document_store.upload(make_cx_workspace(person_relation_destination="1"))
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is True
        assert data["details"][0]["code"] == "10"

    def test_fail_when_no_person_relation(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace(person_relationship=False))
        response = self._post(client, doc_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is False
        assert len(data["details"]) == 1
        row = data["details"][0]
        assert row["status"] == "FAIL"
        assert row["check"] is False
        assert "Нет персон" in row["name"]

    def test_fail_when_system_not_found(self, client: TestClient, document_store) -> None:
        doc_id = document_store.upload(make_cx_workspace())
        response = self._post(client, doc_id, product_code="UNKNOWN")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["isCheck"] is False
        row = data["details"][0]
        assert row["status"] == "FAIL"
        assert row["check"] is False
        assert "Система не найдена" in row["name"]
