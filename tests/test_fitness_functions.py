"""
Тесты на роутер `src/routers/fitness_functions.py`.

Каждый тест следует сценарию из ТЗ: тестовый workspace.dsl сначала
заливается через `/api/v1/workspace/conversion2doc`, полученный `doc_id`
передаётся в проверяемый эндпоинт.

Покрывает:
    POST /api/v1/workspace/{docId}            (publish to Structurizr)
    POST /api/v1/workspace/{docId}/fdm        (full FDM cycle)
    POST /api/v1/dsl2fdm                      (DSL → FDM)
    POST /api/v1/fitness-function/local/{docId}
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /api/v1/workspace/{docId}
# ---------------------------------------------------------------------------
class TestUploadWorkspaceStructurizr:
    def test_successful_publish(self, client: TestClient, uploaded_doc_id: int) -> None:
        response = client.post(f"/api/v1/workspace/{uploaded_doc_id}")
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["details"] == "Ok"
        # workspace_id извлекается из последнего сегмента structurizrApiUrl
        # fake_product: https://structurizr.test/workspace/42
        assert body["workspace_id"] == "42"

    def test_unknown_document_returns_404(self, client: TestClient) -> None:
        # 99999 нет в in-memory store → fake_get_document бросает HTTPException(404)
        response = client.post("/api/v1/workspace/99999")
        assert response.status_code == 404, response.text

    def test_unknown_product_returns_404(
        self,
        client: TestClient,
        uploaded_doc_id: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("routers.fitness_functions.get_product", lambda code: None)
        response = client.post(f"/api/v1/workspace/{uploaded_doc_id}")
        assert response.status_code == 404, response.text
        assert "not found" in response.json()["detail"].lower()

    def test_publish_failure_returns_409(
        self,
        client: TestClient,
        uploaded_doc_id: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # publish_json_workspace возвращает False → ответ 409
        monkeypatch.setattr("routers.fitness_functions.publish_json_workspace", lambda *a, **kw: False)
        response = client.post(f"/api/v1/workspace/{uploaded_doc_id}")
        assert response.status_code == 409, response.text


# ---------------------------------------------------------------------------
# POST /api/v1/workspace/{docId}/fdm
# ---------------------------------------------------------------------------
class TestUploadWorkspaceFdm:
    def test_successful_run(self, client: TestClient, uploaded_doc_id: int) -> None:
        response = client.post(f"/api/v1/workspace/{uploaded_doc_id}/fdm")
        assert response.status_code == 201, response.text
        assert response.json() == {"details": "Ok"}

    def test_unknown_document_returns_404(self, client: TestClient) -> None:
        response = client.post("/api/v1/workspace/99999/fdm")
        assert response.status_code == 404, response.text

    def test_unknown_product_returns_404(
        self,
        client: TestClient,
        uploaded_doc_id: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("routers.fitness_functions.get_product", lambda code: None)
        response = client.post(f"/api/v1/workspace/{uploaded_doc_id}/fdm")
        assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# POST /api/v1/dsl2fdm
# ---------------------------------------------------------------------------
class TestDsl2Fdm:
    URL = "/api/v1/dsl2fdm"

    def test_successful_run(self, client: TestClient, workspace_dsl_b64: str) -> None:
        response = client.post(self.URL, json={"workspace": workspace_dsl_b64})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["details"] == "Ok"
        # Эндпоинт возвращает также workspace_id, извлечённый из structurizrApiUrl.
        assert body.get("workspace_id") == "42"

    def test_invalid_base64_returns_400(self, client: TestClient) -> None:
        response = client.post(self.URL, json={"workspace": "XXXXX"})
        assert response.status_code == 400, response.text

    def test_unknown_product_returns_404(
        self,
        client: TestClient,
        workspace_dsl_b64: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("routers.fitness_functions.get_product", lambda code: None)
        response = client.post(self.URL, json={"workspace": workspace_dsl_b64})
        assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# POST /api/v1/fitness-function/local/{docId}
# ---------------------------------------------------------------------------
class TestFitnessFunctionLocal:
    def test_successful_run(self, client: TestClient, uploaded_doc_id: int) -> None:
        response = client.post(f"/api/v1/fitness-function/local/{uploaded_doc_id}")
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["details"] == "Ok"

    def test_with_pipeline_id_query(self, client: TestClient, uploaded_doc_id: int) -> None:
        response = client.post(
            f"/api/v1/fitness-function/local/{uploaded_doc_id}",
            params={"pipelineId": 12345},
        )
        assert response.status_code == 201, response.text

    def test_unknown_document_returns_404(self, client: TestClient) -> None:
        response = client.post("/api/v1/fitness-function/local/99999")
        assert response.status_code == 404, response.text

    def test_unknown_product_returns_404(
        self,
        client: TestClient,
        uploaded_doc_id: int,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("routers.fitness_functions.get_product", lambda code: None)
        response = client.post(f"/api/v1/fitness-function/local/{uploaded_doc_id}")
        assert response.status_code == 404, response.text
