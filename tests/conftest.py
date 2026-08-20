"""
Общий pytest-конфиг для тестов Structurizr Backend.

Что здесь происходит:

1. Перед загрузкой `src/main.py` выставляются env-переменные, которые
   обязательны на этапе импорта модуля `src/structurizr.py`
   (`ONPREMISES_PASSWORD`, `URL_ONPREMISES_*`).
2. В sys.path добавляются `src/` (для `routers`, `structurizr_utils`, `structurizr`)
   и корень репозитория (для пакета `src_fitness_functions`).
3. Поднимается FastAPI-приложение из `src/main.py` (через `import main`) и
   оборачивается в `TestClient`.
4. Внешние сервисы (Document Service, BeeAtlas, Structurizr CLI, Vega VPS,
   FF Manager, Sparx) подменяются in-memory заглушками. Фикстуры строго
   соответствуют разделам R/E из README:
     - `document_store` — in-memory хранилище документов;
     - `uploaded_doc_id` — выполняет реальный `POST /api/v1/workspace/conversion2doc`,
       возвращает `doc_id` для последующих тестов c этим документом.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# 1. ENV-переменные для импорта src/structurizr.py
# ---------------------------------------------------------------------------
os.environ.setdefault("ONPREMISES_PASSWORD", "test-password")
os.environ.setdefault("URL_ONPREMISES_WORKSPACE", "https://structurizr.test/api/workspace")
os.environ.setdefault("URL_ONPREMISES_BASE", "https://structurizr.test/api")
os.environ.setdefault("URL_PRODUCTS", "https://products.test")
os.environ.setdefault("URL_DOCUMENTS", "https://documents.test")
os.environ.setdefault("URL_VEGA", "https://vega.test")
os.environ.setdefault("URL_TECHRADAR", "https://techradar.test")
os.environ.setdefault("URL_TECHRADAR_UI", "https://techradar-ui.test")
os.environ.setdefault("CAPABILITY_API_URL", "https://capability.test")
os.environ.setdefault("GATEWAY_URL", "https://gateway.test")
os.environ.setdefault("URL_BEEATLAS", "https://beeatlas.test")
os.environ.setdefault("URL_TCQUALITY", "https://tcquality.test")
os.environ.setdefault("RABBIT_HOSTS", "rabbit.test")
os.environ.setdefault("IDM_FREEIPA_CMDB")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("API_SECRET", "test-api-secret")
# Явно гасим URL_SPARX, чтобы не уходить в Sparx из fitness_check.
os.environ.pop("URL_SPARX", None)

# ---------------------------------------------------------------------------
# 2. sys.path: src/ и корень репозитория
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

for _path in (str(PROJECT_ROOT), str(SRC_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ---------------------------------------------------------------------------
# 3. Импорт приложения (после настройки путей и env)
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main as backend_main  # type: ignore  # noqa: E402
from structurizr_utils.models.models_product import Product  # type: ignore  # noqa: E402

WORKSPACE_JSON_PATH = TESTS_DIR / "workspace.json"
WORKSPACE_DSL_PATH = TESTS_DIR / "workspace.dsl"


# ---------------------------------------------------------------------------
# Базовые фикстуры
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def workspace_json() -> Dict[str, Any]:
    """Фикстурный workspace.json из tests/ (источник для подмены CLI-конвертации)."""
    with open(WORKSPACE_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def workspace_cmdb(workspace_json: Dict[str, Any]) -> str:
    """CMDB код из тестового workspace (используется в моках BeeAtlas)."""
    return workspace_json["model"]["properties"]["workspace_cmdb"]


@pytest.fixture(scope="session")
def workspace_dsl_b64() -> str:
    """Base64-кодированный DSL для эндпоинтов validate / conversion / conversion2doc / dsl2fdm."""
    text = WORKSPACE_DSL_PATH.read_text(encoding="utf-8")
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


@pytest.fixture(scope="session")
def workspace_dsl_text() -> str:
    return WORKSPACE_DSL_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# In-memory Document Service
# ---------------------------------------------------------------------------
class FakeDocumentStore:
    """Простая in-memory замена Document Service для тестов."""

    def __init__(self) -> None:
        self.docs: Dict[int, Dict[str, Any]] = {}
        self.next_id: int = 1000

    def upload(self, json_dict: Dict[str, Any]) -> int:
        doc_id = self.next_id
        self.docs[doc_id] = json_dict
        self.next_id += 1
        return doc_id

    def get(self, document_id: int) -> Dict[str, Any]:
        from fastapi import HTTPException

        if int(document_id) not in self.docs:
            raise HTTPException(status_code=404, detail="Document not found")
        return self.docs[int(document_id)]


@pytest.fixture
def document_store() -> FakeDocumentStore:
    return FakeDocumentStore()


# ---------------------------------------------------------------------------
# Стабовый Product из BeeAtlas
# ---------------------------------------------------------------------------
def _make_product(
    *,
    code: str,
    with_structurizr: bool = True,
) -> Product:
    return Product(
        alias=code,
        description="Test product",
        gitUrl="https://git.test/showcase",
        id=42,
        name="Test Product",
        structurizrApiKey="test-key" if with_structurizr else None,
        structurizrApiSecret="test-secret" if with_structurizr else None,
        structurizrApiUrl="https://structurizr.test/workspace/42" if with_structurizr else None,
        structurizrWorkspaceName="showcase" if with_structurizr else None,
        techProducts=[],
        discoveredInterfaces=[],
    )


@pytest.fixture
def fake_product(workspace_cmdb: str) -> Product:
    return _make_product(code=workspace_cmdb, with_structurizr=True)


@pytest.fixture
def fake_product_without_workspace(workspace_cmdb: str) -> Product:
    return _make_product(code=workspace_cmdb, with_structurizr=False)


# ---------------------------------------------------------------------------
# Главный autouse-патчинг внешних сервисов
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def patch_external_services(
    monkeypatch: pytest.MonkeyPatch,
    document_store: FakeDocumentStore,
    workspace_json: Dict[str, Any],
    fake_product: Product,
) -> Dict[str, Any]:
    """
    Перехватывает все вызовы во внешние системы и заменяет на in-memory заглушки.
    Возвращает словарь с экземплярами заглушек для прямого использования в тестах.
    """

    # ---- Document Service ----
    def fake_get_document(document_id: int, user_id: Optional[int] = None, user_roles: Optional[str] = None) -> Dict[str, Any]:
        return document_store.get(int(document_id))

    def fake_upload_workspace_json(json_dict: Dict[str, Any], is_public: bool = True, user_id: Optional[int] = None) -> int:
        return document_store.upload(json_dict)

    # Эти атрибуты импортированы в роутеры через `from ... import ...`,
    # поэтому патчим их по месту использования.
    monkeypatch.setattr("routers.workspace.upload_workspace_json", fake_upload_workspace_json)
    monkeypatch.setattr("routers.fitness_functions.get_document", fake_get_document)
    monkeypatch.setattr("routers.terraform.get_document", fake_get_document)
    # Source-of-truth тоже подменяем — на случай других импортов.
    monkeypatch.setattr("structurizr_utils.models.model_documents.get_document", fake_get_document)
    monkeypatch.setattr("structurizr_utils.models.model_documents.upload_workspace_json", fake_upload_workspace_json)

    def fake_bee_get_workspace_document(
        self: Any,
        document_id: int,
        user_id: Optional[str] = None,
        user_roles: Optional[str] = None,
    ) -> Dict[str, Any]:
        uid = int(user_id) if user_id is not None else None
        return fake_get_document(document_id, user_id=uid, user_roles=user_roles)

    monkeypatch.setattr(
        "src_fitness_functions.beeatlas_api.BeeAtlasAPI.get_workspace_document",
        fake_bee_get_workspace_document,
    )

    # ---- DSL→JSON конвертация (Structurizr CLI) ----
    def fake_convert_dsl2json(dsl: str) -> Dict[str, Any]:
        return {"errors": None, "json": workspace_json}

    monkeypatch.setattr("routers.workspace.convert_dsl2json", fake_convert_dsl2json)
    monkeypatch.setattr("routers.fitness_functions.convert_dsl2json", fake_convert_dsl2json)
    monkeypatch.setattr("routers.utils.convert_dsl2json", fake_convert_dsl2json)

    # ---- BeeAtlas product ----
    product_overrides: Dict[str, Optional[Product]] = {}

    def fake_get_product(code: str) -> Optional[Product]:
        if code is None or code == "":
            return None
        if code in product_overrides:
            return product_overrides[code]
        return fake_product

    monkeypatch.setattr("routers.workspace.get_product", fake_get_product)
    monkeypatch.setattr("routers.fitness_functions.get_product", fake_get_product)
    monkeypatch.setattr("routers.terraform.get_product", fake_get_product)
    monkeypatch.setattr("structurizr_utils.models.models_product.get_product", fake_get_product)

    # ---- Structurizr CLI / On-Premises ----
    def fake_post_workspace() -> Dict[str, Any]:
        return {
            "id": 4242,
            "apiKey": "new-api-key",
            "apiSecret": "new-api-secret",
            "name": "showcase",
            "description": "",
            "privateUrl": "/workspace/4242",
            "publicUrl": "/share/4242",
        }

    monkeypatch.setattr("routers.workspace.post_workspace", fake_post_workspace)
    monkeypatch.setattr("routers.workspace.patch_product", lambda cmdb, product: True)
    monkeypatch.setattr("structurizr_utils.models.models_product.patch_product", lambda cmdb, product: True)

    monkeypatch.setattr("routers.workspace.publish_default_workspace", lambda *a, **kw: True)
    monkeypatch.setattr("routers.fitness_functions.publish_json_workspace", lambda *a, **kw: True)

    # ---- Fitness checks ----
    # safe_execution возвращает пустой список — checks не запускаются,
    # FitnessFunctionClient.post_fitness_functions получает пустой список.
    monkeypatch.setattr("routers.fitness_functions.safe_execution", lambda *a, **kw: [])

    class FakeFitnessFunctionClient:
        def post_fitness_functions(self, **kwargs):
            return {"status": "ok"}

        def get_fitness_functions(self, *args, **kwargs):
            return {}

    monkeypatch.setattr("routers.fitness_functions.FitnessFunctionClient", FakeFitnessFunctionClient)

    # ---- Terraform / Vega VPS ----
    fake_hcl = (
        "# Generated by tests\n"
        'resource "vega_server" "gateway" {\n'
        '  name = "gateway"\n'
        '  flavor = "cpu2ram2"\n'
        "}\n"
    )

    monkeypatch.setattr(
        "routers.terraform.generate_terraform_content",
        lambda **kwargs: fake_hcl,
    )

    class FakeVegaVPSClient:
        def __init__(self, *args, **kwargs):
            self.base_url = kwargs.get("base_url", "https://vega.test")

    monkeypatch.setattr("routers.terraform.VegaVPSClient", FakeVegaVPSClient)

    # ---- src_fitness_functions SDK (HTTPClient) ----
    class FakeHTTPClient:
        last_calls: list = []

        def __init__(self, *args, **kwargs):
            FakeHTTPClient.last_calls.append({"args": args, "kwargs": kwargs})

        def get(self, path: str, **kwargs):
            return {"alias": "TEST-PRODUCT", "name": "Test Product"}

        def post(self, path: str, data=None, **kwargs):
            return {"status": "ok"}

    monkeypatch.setattr("src_fitness_functions.api.ff_adr_01.HTTPClient", FakeHTTPClient)

    return {
        "document_store": document_store,
        "product_overrides": product_overrides,
        "fake_hcl": fake_hcl,
        "FakeHTTPClient": FakeHTTPClient,
    }


# ---------------------------------------------------------------------------
# TestClient и app
# ---------------------------------------------------------------------------
@pytest.fixture
def app():
    return backend_main.app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Главный workflow: залить документ через /conversion2doc, отдать doc_id
# ---------------------------------------------------------------------------
@pytest.fixture
def uploaded_doc_id(client: TestClient, workspace_dsl_b64: str) -> int:
    """
    Заливает тестовый workspace.dsl через `POST /api/v1/workspace/conversion2doc`,
    возвращает `doc_id` для последующих тестов (см. README, раздел R).
    """
    response = client.post(
        "/api/v1/workspace/conversion2doc",
        json={"workspace": workspace_dsl_b64},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "doc_id" in body, body
    return int(body["doc_id"])
