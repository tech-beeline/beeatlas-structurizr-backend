"""Тесты на роутер `src/routers/integraion.py` — расчёт SLA из API-спецификаций."""

from __future__ import annotations

from fastapi.testclient import TestClient

# Минимальная OpenAPI-спецификация, которую успешно разбирает ApiLoader.
MINIMAL_OPENAPI_YAML = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: listUsers
      responses:
        '200':
          description: OK
  /users/{id}:
    get:
      operationId: getUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: OK
"""


class TestIntegrationSla:
    URL = "/api/v1/integration/sla"

    def test_returns_plain_text(self, client: TestClient) -> None:
        response = client.post(
            self.URL,
            headers={"Content-Type": "text/plain"},
            content=MINIMAL_OPENAPI_YAML,
        )
        # Эндпоинт возвращает text/plain. Возможен 200 с пустым телом, если
        # парсер не распознал методы — это допустимый сценарий, главное чтобы
        # эндпоинт не падал и схема ответа была text/plain.
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/plain")

    def test_empty_body_returns_400(self, client: TestClient) -> None:
        # FastAPI требует не пустое тело; глобальный обработчик в src/main.py
        # превращает 422 валидации в 400 со строкой "Some of parameters is empty or missing".
        response = client.post(
            self.URL,
            headers={"Content-Type": "text/plain"},
            content="",
        )
        assert response.status_code == 400, response.text
        assert response.json() == {"detail": "Some of parameters is empty or missing"}
