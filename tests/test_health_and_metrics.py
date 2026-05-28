"""Тесты служебных эндпоинтов: /health, /actuator/prometheus, /openapi.json."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health — простая liveness-проверка пакета src_fitness_functions."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_prometheus_metrics_exposed(client: TestClient) -> None:
    """GET /actuator/prometheus возвращает метрики в формате Prometheus."""
    # Сначала генерируем хотя бы один запрос, чтобы метрики не были пустыми.
    client.get("/health")

    response = client.get("/actuator/prometheus")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


def test_openapi_schema_available(client: TestClient) -> None:
    """OpenAPI-схема доступна и содержит наши маршруты."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Structurizr Backend API"
    paths = set(schema["paths"].keys())
    # Несколько маршрутов из раздела R README:
    for expected in (
        "/api/v1/workspace/validate",
        "/api/v1/workspace/conversion",
        "/api/v1/workspace/conversion2doc",
        "/api/v1/workspace/{docId}",
        "/api/v1/workspace/{docId}/fdm",
        "/api/v1/dsl2fdm",
        "/api/v1/fitness-function/local/{docId}",
        "/api/v1/workspace/{docId}/terraform",
        "/api/v1/workspace/terraform/generate",
        "/api/v1/integration/sla",
        "/api/v1/ff/adr01",
        "/health",
    ):
        assert expected in paths, f"missing route in OpenAPI schema: {expected}"
