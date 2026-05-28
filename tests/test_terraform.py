"""
Тесты на роутер `src/routers/terraform.py`.

Покрывает:
    GET  /api/v1/workspace/{docId}/terraform
    POST /api/v1/workspace/terraform/generate
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET /api/v1/workspace/{docId}/terraform
# ---------------------------------------------------------------------------
class TestGetTerraform:
    def test_returns_hcl_for_uploaded_doc(
        self,
        client: TestClient,
        uploaded_doc_id: int,
        patch_external_services,
    ) -> None:
        response = client.get(
            f"/api/v1/workspace/{uploaded_doc_id}/terraform",
            params={"token": "vega-jwt-token", "environment": "development"},
        )
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == patch_external_services["fake_hcl"]

    def test_unknown_document_returns_404(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/workspace/99999/terraform",
            params={"token": "vega-jwt-token", "environment": "development"},
        )
        assert response.status_code == 404, response.text

    def test_missing_query_params_returns_422(self, client: TestClient, uploaded_doc_id: int) -> None:
        response = client.get(f"/api/v1/workspace/{uploaded_doc_id}/terraform")
        # FastAPI отдаёт 422 при отсутствии обязательных query-параметров;
        # в этом проекте перехвачено в обработчике RequestValidationError → 400.
        assert response.status_code in (400, 422), response.text


# ---------------------------------------------------------------------------
# POST /api/v1/workspace/terraform/generate
# ---------------------------------------------------------------------------
class TestPostTerraformGenerate:
    URL = "/api/v1/workspace/terraform/generate"

    def test_generates_hcl_from_raw_json(
        self,
        client: TestClient,
        workspace_json: dict,
        patch_external_services,
    ) -> None:
        response = client.post(
            self.URL,
            params={"environment": "development"},
            headers={"X-Token": "vega-jwt-token", "Content-Type": "text/plain"},
            content=json.dumps(workspace_json, ensure_ascii=False),
        )
        assert response.status_code == 200, response.text
        assert response.text == patch_external_services["fake_hcl"]

    def test_invalid_json_returns_400(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            self.URL,
            params={"environment": "development"},
            headers={"X-Token": "vega-jwt-token", "Content-Type": "text/plain"},
            content="this is not json",
        )
        # роутер ловит JSONDecodeError и возвращает 400 (см. routers/terraform.py).
        assert response.status_code == 400, response.text

    def test_missing_header_returns_validation_error(self, client: TestClient) -> None:
        response = client.post(
            self.URL,
            params={"environment": "development"},
            headers={"Content-Type": "text/plain"},
            content="{}",
        )
        assert response.status_code in (400, 422), response.text
