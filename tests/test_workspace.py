"""
Тесты на роутер `src/routers/workspace.py`.

Покрывает все эндпоинты раздела R README:
    POST /api/v1/workspace/validate
    POST /api/v1/workspace/conversion
    POST /api/v1/workspace/conversion2doc
    POST /workspace, /api/v1/workspace
"""
from __future__ import annotations

import base64
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /api/v1/workspace/validate
# ---------------------------------------------------------------------------
class TestValidate:
    URL = "/api/v1/workspace/validate"

    def test_valid_dsl_returns_valid_true(self, client: TestClient, workspace_dsl_b64: str) -> None:
        response = client.post(self.URL, json={"workspace": workspace_dsl_b64})
        assert response.status_code == 200, response.text
        assert response.json() == {"valid": "true"}

    def test_empty_workspace_returns_400(self, client: TestClient) -> None:
        response = client.post(self.URL, json={"workspace": ""})
        assert response.status_code == 400, response.text
        detail = response.json()["detail"]
        assert detail["valid"] == "false"

    def test_missing_workspace_key_returns_400(self, client: TestClient) -> None:
        # Тело без обязательного поля `workspace` — глобальный обработчик
        # `RequestValidationError` в src/main.py превращает 422 в 400 со строкой.
        response = client.post(self.URL, json={})
        assert response.status_code == 400, response.text
        assert response.json() == {"detail": "Some of parameters is empty or missing"}

    def test_invalid_base64_returns_400(self, client: TestClient) -> None:
        # Длина не кратна 4 (после padding) → binascii.Error → decode_base64 → None.
        response = client.post(self.URL, json={"workspace": "XXXXX"})
        assert response.status_code == 400, response.text
        detail = response.json()["detail"]
        assert detail["valid"] == "false"
        assert "base64" in detail["error"].lower() or "не является" in detail["error"].lower()


# ---------------------------------------------------------------------------
# POST /api/v1/workspace/conversion
# ---------------------------------------------------------------------------
class TestConversion:
    URL = "/api/v1/workspace/conversion"

    def test_returns_workspace_json(self, client: TestClient, workspace_dsl_b64: str, workspace_json: dict) -> None:
        response = client.post(self.URL, json={"workspace": workspace_dsl_b64})
        assert response.status_code == 200, response.text
        body = response.json()
        # Конвертация замокана и должна вернуть тот же workspace.json.
        assert body["model"]["properties"]["workspace_cmdb"] == workspace_json["model"]["properties"]["workspace_cmdb"]

    def test_invalid_base64_returns_400(self, client: TestClient) -> None:
        response = client.post(self.URL, json={"workspace": "XXXXX"})
        assert response.status_code == 400, response.text


# ---------------------------------------------------------------------------
# POST /api/v1/workspace/conversion2doc — главный сценарий «залить как документ»
# ---------------------------------------------------------------------------
class TestConversion2Doc:
    URL = "/api/v1/workspace/conversion2doc"

    def test_returns_doc_id(self, client: TestClient, workspace_dsl_b64: str, patch_external_services) -> None:
        response = client.post(self.URL, json={"workspace": workspace_dsl_b64})
        assert response.status_code == 200, response.text
        body = response.json()
        assert "doc_id" in body
        doc_id = int(body["doc_id"])
        # Документ реально лежит в in-memory store.
        store = patch_external_services["document_store"]
        assert doc_id in store.docs

    def test_two_uploads_produce_distinct_ids(self, client: TestClient, workspace_dsl_b64: str) -> None:
        first = client.post(self.URL, json={"workspace": workspace_dsl_b64}).json()["doc_id"]
        second = client.post(self.URL, json={"workspace": workspace_dsl_b64}).json()["doc_id"]
        assert first != second

    def test_invalid_base64_returns_400(self, client: TestClient) -> None:
        response = client.post(self.URL, json={"workspace": "XXXXX"})
        assert response.status_code == 400, response.text


# ---------------------------------------------------------------------------
# POST /workspace, POST /api/v1/workspace
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["/workspace", "/api/v1/workspace"])
class TestCreateWorkspace:
    def test_creates_workspace_for_fresh_product(
        self,
        client: TestClient,
        path: str,
        monkeypatch: pytest.MonkeyPatch,
        workspace_cmdb: str,
        fake_product_without_workspace,
    ) -> None:
        # Подменяем get_product так, чтобы продукт ещё не имел Structurizr workspace.
        def _get_product(code: str):
            if code == workspace_cmdb:
                return fake_product_without_workspace
            return None

        monkeypatch.setattr("routers.workspace.get_product", _get_product)

        response = client.post(
            path,
            json={"code": workspace_cmdb, "architect_name": "Test Architect"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == workspace_cmdb
        # Поля созданного workspace взяты из fake_post_workspace.
        assert body["api_key"] == "new-api-key"
        assert body["api_secret"] == "new-api-secret"
        assert body["id"] == 4242
        assert "/share/4242" in body["api_url"]

    def test_missing_parameters_returns_400(self, client: TestClient, path: str) -> None:
        response = client.post(path, json={"code": "", "architect_name": ""})
        assert response.status_code == 400, response.text

    def test_unknown_product_returns_404(
        self,
        client: TestClient,
        path: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("routers.workspace.get_product", lambda code: None)
        response = client.post(
            path,
            json={"code": "UNKNOWN", "architect_name": "X"},
        )
        assert response.status_code == 404, response.text
        assert "not found" in response.json()["detail"].lower()

    def test_product_with_existing_workspace_returns_422(
        self,
        client: TestClient,
        path: str,
        workspace_cmdb: str,
        fake_product,  # уже c structurizrApiUrl
    ) -> None:
        response = client.post(
            path,
            json={"code": workspace_cmdb, "architect_name": "X"},
        )
        assert response.status_code == 422, response.text
        assert "already" in response.json()["detail"].lower()
