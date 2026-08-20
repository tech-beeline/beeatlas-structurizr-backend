# Руководство по тестированию API Fitness Functions

## 1. Введение

### 1.1. Цель документа

Данное руководство описывает подходы к тестированию HTTP-эндпоинтов пакета `src_fitness_functions`. Эндпоинты реализуют фитнес-функции (Fitness Functions) для архитектурного контроля приложений — автоматические проверки соответствия архитектуры продукта заданным правилам (ADR, API, контейнеры, capability, deployment, технологии и т.д.).

### 1.2. Общая архитектура

```
FF Manager (внешняя система)
    │
    │ POST /api/v1/ff/{code}  (callId, productCode)
    ▼
┌─────────────────────────────────────┐
│  FastAPI (src_fitness_functions)    │
│  ┌───────────────────────────────┐  │
│  │  ff_*.py (роутеры)            │  │
│  │  - парсинг запроса            │  │
│  │  - вызов SDK / beeatlas_api   │  │
│  │  - формирование ответа        │  │
│  └──────────┬────────────────────┘  │
│             │                       │
│  ┌──────────▼────────────────────┐  │
│  │  SDK (src_fitness_functions/  │  │
│  │       sdk/)                   │  │
│  │  - бизнес-логика проверок     │  │
│  └──────────┬────────────────────┘  │
│             │                       │
│  ┌──────────▼────────────────────┐  │
│  │  beeatlas_api.py              │  │
│  │  - HTTP-клиенты к внешним     │  │
│  │    сервисам (Document Service,│  │
│  │    Capability API, Products   │  │
│  │    API, TechRadar)            │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
    │
    │ Response: {callId, isCheck, details}
    ▼
FF Manager
```

### 1.3. Технологии тестирования

- **pytest** — фреймворк для написания и запуска тестов
- **FastAPI TestClient** — HTTP-клиент для тестирования эндпоинтов без запуска сервера
- **monkeypatch** (pytest) — подмена внешних зависимостей (HTTP-вызовы, SDK)
- **unittest.mock** — создание mock-объектов

### 1.4. Конфигурация тестов

Тесты расположены в директории `tests/`. Конфигурация pytest:

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

Фикстуры и моки внешних сервисов — в `tests/conftest.py`.

---

## 2. Общая схема тестирования

### 2.1. Единый формат запроса

Все эндпоинты (кроме `/health`) принимают **POST**-запросы с одинаковой структурой тела:

```json
{
    "callId": "UUID-строка",
    "productCode": "мнемоника продукта"
}
```

И опциональным query-параметром:

| Параметр | Тип | Обязательность | Описание |
|---|---|---|---|
| `docId` | `int` | Опционально | Идентификатор документа workspace в Document Service |

### 2.2. Единый формат ответа

```json
{
    "callId": "UUID-строка (зеркало входного)",
    "isCheck": true/false,
    "details": [ ... ]
}
```

#### 2.2.1. Семантика `isCheck`

| Значение | Смысл |
|---|---|
| `isCheck = true` | Проверка пройдена **полностью**. Все элементы в `details` имеют `check = true`. |
| `isCheck = false` | Проверка **не пройдена**. Хотя бы один элемент в `details` имеет `check = false`. При этом **часть элементов может быть успешной** (`check = true`), а часть — нет (`check = false`). |

#### 2.2.2. Семантика `details[].check`

| Значение | Смысл |
|---|---|
| `check = true` | Конкретный элемент проверки пройден успешно |
| `check = false` | Конкретный элемент проверки нарушен |

#### 2.2.3. HTTP-статусы ответа

| Код | Описание | Условие |
|---|---|---|
| `200` | Успешная проверка | Документ найден, проверка выполнена |
| `404` | Документ не найден | `docId` не существует в Document Service |
| `501` | Не реализовано | `docId` не передан (query-параметр отсутствует) |
| `422` | Ошибка валидации | Невалидный `callId`, отсутствуют обязательные поля |
| `400` | Ошибка запроса | Невалидный JSON, ошибка парсинга |

### 2.3. Структура `details` по эндпоинтам

Каждый эндпоинт возвращает свой набор полей в `details`. Ниже приведён полный справочник с примерами JSON для каждого элемента массива `details`.

---

#### ADR.01 — Наличие ADR в документации

Pydantic-модель: `Adr01Detail`

```json
{
  "code": "adr_001",
  "name": "Выбор базы данных",
  "date": "2024-01-15",
  "status": "Accepted",
  "check": true
}
```

---

#### API.01 — Наличие опубликованных API

Pydantic-модель: `Api01Detail`

```json
{
  "code": "api-gateway",
  "name": "API Gateway",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "spec": "https://api.example.com/spec"
}
```

---

#### API.02 — SLA для методов (RPS / Latency / Error rate)

Pydantic-модель: `Api02Detail`

```json
{
  "code": "method_1",
  "name": "GET /users",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "rps": 1000.0,
  "latency": 200.0,
  "error_rate": 0.01
}
```

Поля `rps`, `latency`, `error_rate` — опциональны (`null`, если не заданы).

---

#### API.03 — Спецификации для всех TC

Pydantic-модель: `Api03Detail`

```json
{
  "code": "TC.001",
  "name": "Управление пользователями",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "technical_capability": "TC.001",
  "interface_code": "IF-001",
  "api_url": "https://api.example.com/v1/users"
}
```

Поля `technical_capability`, `interface_code`, `api_url` — опциональны (пустая строка при нарушении).

---

#### CNT.01 — Наличие контейнеров

Pydantic-модель: `Cnt01Detail`

```json
{
  "code": "container-1",
  "name": "backend-service",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "technology": "Python / FastAPI",
  "tags": ["backend", "api"]
}
```

Поле `tags` — список строк (может быть пустым).

---

#### CNT.02 — Наличие containerView

Pydantic-модель: `Cnt02Detail`

```json
{
  "code": "containerView-1",
  "name": "Container View",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### CNT.03 — Технологии у связей контейнеров

Pydantic-модель: `Cnt03Detail`

```json
{
  "code": "relationship-1",
  "name": "backend -> database",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "source_name": "backend-service",
  "target_name": "postgresql"
}
```

---

#### CPB.01 — Технические возможности продукта

Pydantic-модель: `Cpb01Detail`

```json
{
  "code": "TEST.TC.001",
  "name": "Управление пользователями",
  "source": "Structurizr",
  "parents": [
    {"code": "BC.001"},
    {"code": "BC.002"}
  ],
  "check": true
}
```

Поле `parents` — список объектов с полем `code`. При отсутствии TC — `source: "FAIL"`, `check: false`.

---

#### CPB.02 — TC для внешних контейнеров

Pydantic-модель: `Cpb02Detail`

```json
{
  "code": "rel-001",
  "name": "backend -> external-api",
  "status": "OK",
  "check": true,
  "container_name": "backend-service",
  "technical_capability": ["TEST.TC.001", "TEST.TC.002"],
  "external_callers": ["external-system"]
}
```

Поля `technical_capability` и `external_callers` — списки строк.

---

#### CPB.03 — Полнота описания TC

Pydantic-модель: `Cpb03Detail`

```json
{
  "code": "TEST.TC.001",
  "name": "Управление пользователями",
  "source": "Structurizr",
  "parents": [
    {"code": "BC.001"}
  ],
  "check": true
}
```

Для неполных TC в `name` добавляется суффикс с причиной, например: `"Управление (нет code, нет parents)"`.

---

#### CPB.04 — Позиционирование TC в ФДМ

Pydantic-модель: `Cpb04Detail`

```json
{
  "code": "TEST.TC.001",
  "name": "TC.001 Управление пользователями",
  "status": "FAIL",
  "check": false,
  "rule": "CPB.04_PARENT_DMN",
  "reason": "Родительская BC содержит префикс dmn.",
  "severity": "error"
}
```

При успехе: `status: "OK"`, `check: true`, `severity: "ok"`.

---

#### CPB.05 — Качество описания TC

Pydantic-модель: `Cpb05Detail`

```json
{
  "code": "TC.001",
  "name": "Управление пользователями",
  "status": "OK",
  "check": true
}
```

---

#### CTX.01 — Наличие contextView

Pydantic-модель: `Ctx01Detail`

```json
{
  "code": "contextView-1",
  "name": "System Context View",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### CTX.02 — Подписи связей на контекстной диаграмме

Pydantic-модель: `Ctx02Detail`

```json
{
  "code": "relationship-1",
  "name": "system -> external-api",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### CTX.03 — Технологии у связей контекста

Pydantic-модель: `Ctx03Detail`

```json
{
  "code": "relationship-1",
  "name": "system -> external-api",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "target_name": "external-system",
  "technology": "REST / HTTPS"
}
```

---

#### DEP.01 — Наличие Deployment Environment

Pydantic-модель: `Dep01Detail`

```json
{
  "code": "deployment-1",
  "name": "Production",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### DEP.02 — Наличие deploymentView

Pydantic-модель: `Dep02Detail`

```json
{
  "code": "deploymentView-1",
  "name": "Deployment View",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### DEP.03 — Сверка deployment с CMDB

Pydantic-модель: `Dep03Detail`

```json
{
  "code": "node-1",
  "name": "app-server-01",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```
---

#### EA.0001 — Выход в интернет

Pydantic-модель: `Ea0001Detail`

```json
{
  "code": "ea-check-1",
  "name": "Проверка внешних сервисов",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### GIT.01 — Git/Nexus/Harbor URL

Pydantic-модель: `Git01Detail`

```json
{
  "code": "container-1",
  "name": "backend-service",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "git": "https://git.example.com/backend-service"
}
```

---

#### SQ.01 — DynamicView для TC

Pydantic-модель: `Sq01Detail`

```json
{
  "code": "TEST.TC.001",
  "name": "Управление пользователями — sequence",
  "date": "2024-01-15",
  "status": "OK",
  "check": true,
  "plantUML": "@startuml\nactor User\n..."
}
```

Поля `name` и `plantUML` — опциональны (`null`, если диаграмма не найдена).

---

#### SQ.02 — HTTP-методы в sequence

Pydantic-модель: `Sq02Detail`

```json
{
  "code": "TEST.TC.001",
  "name": "REST-вызов: rel-001, GET /users, HTTP",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### TECH.01 — Технологии в TechRadar

Pydantic-модель: `Tech01Detail`

```json
{
  "code": "tech-1",
  "name": "Python",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### TECH.02 — Нет HOLD-технологий

Pydantic-модель: `Tech02Detail`

```json
{
  "code": "tech-1",
  "name": "Python",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### TECH.03 — Поле technology у контейнеров

Pydantic-модель: `Tech03Detail`

```json
{
  "code": "container-1",
  "name": "backend-service",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### TECH.04 — Нет HOLD-протоколов

Pydantic-модель: `Tech04Detail`

```json
{
  "code": "protocol-1",
  "name": "HTTPS",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### TECH.05 — Протоколы из TechRadar

Pydantic-модель: `Tech05Detail`

```json
{
  "code": "protocol-1",
  "name": "HTTPS",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

#### TECH.06 — Технологии мониторинга

Pydantic-модель: `Tech06Detail`

```json
{
  "code": "monitoring-1",
  "name": "Prometheus",
  "date": "2024-01-15",
  "status": "OK",
  "check": true
}
```

---

## 3. Категории тестов

Для каждого эндпоинта должны быть написаны тесты следующих категорий.

### 3.1. Функциональные тесты (корректные данные)

#### 3.1.1. Успешная проверка (`isCheck = true`)

Проверяет, что при корректных входных данных и валидном workspace-документе:
- HTTP-статус = `200`
- `callId` в ответе совпадает с `callId` в запросе
- `isCheck = true`
- `details` — непустой список
- Каждый элемент `details` содержит все обязательные поля
- У каждого элемента `details.check = true`

#### 3.1.2. Частичный провал (`isCheck = false`, часть `details` успешна)

Проверяет, что при workspace-документе, где часть элементов проходит проверку, а часть — нет:
- HTTP-статус = `200`
- `isCheck = false`
- В `details` есть элементы как с `check = true`, так и с `check = false`
- Количество успешных и проваленных элементов соответствует ожиданиям

#### 3.1.3. Полный провал (`isCheck = false`, все `details` провалены)

Проверяет, что при workspace-документе с тотальным нарушением правила:
- HTTP-статус = `200`
- `isCheck = false`
- Все элементы `details` имеют `check = false`

#### 3.1.4. Пустой `details`

Проверяет, что при отсутствии объектов проверки (например, нет контейнеров с внешним взаимодействием):
- HTTP-статус = `200`
- `details` может быть пустым списком или содержать один элемент-заглушку
- `isCheck` может быть `true` (если пустой список — это норма) или `false`

### 3.2. Тесты с некорректными данными

#### 3.2.1. `docId` не передан

- HTTP-статус = `501`
- `isCheck = false`
- `details` содержит сообщение "Not implemented"

#### 3.2.2. `docId` не существует

- HTTP-статус = `404`
- `isCheck = false`
- `details` содержит сообщение "Not found"

#### 3.2.3. Невалидный `callId`

- `callId` = строка, не являющаяся UUID (например, `"not-a-uuid"`)
- HTTP-статус = `422` (или `400`, если настроен глобальный exception handler)

#### 3.2.4. Пустой `productCode`

- `productCode` = пустая строка
- HTTP-статус = `404` (продукт не найден) или `400`

#### 3.2.5. Невалидный JSON в теле запроса

- Тело запроса — невалидный JSON (например, `{"callId": }`)
- HTTP-статус = `422` (или `400`)

#### 3.2.6. Отсутствие обязательных полей

- Тело запроса без поля `callId` или `productCode`
- HTTP-статус = `422`

### 3.3. Тесты граничных случаев

#### 3.3.1. Большое количество элементов в `details`

- Workspace-документ с максимальным количеством объектов проверки
- Проверка, что ответ не превышает ожидаемый размер и не приводит к таймауту

#### 3.3.2. Спецсимволы в полях

- `code`, `name` и другие строковые поля содержат спецсимволы: кавычки, обратные слеши, Unicode, эмодзи
- Проверка корректной сериализации в JSON

#### 3.3.3. Очень длинные строки

- Поля `code`, `name` содержат строки длиной > 1000 символов
- Проверка, что ответ не обрезается и не вызывает ошибок

#### 3.3.4. `callId` с разным регистром

- UUID в верхнем/нижнем регистре
- Проверка, что `callId` в ответе совпадает с входным (как строка)

---

## 4. Матрица соответствия «вход → выход» для каждого эндпоинта

### 4.1. ADR.01 — Наличие ADR в документации

| Сценарий | Вход (body) | Вход (query) | Выход (isCheck) | Выход (details) | Выход (HTTP) |
|---|---|---|---|---|---|
| Есть ADR | `{callId, productCode}` | `docId=1` | `true` | `[{code, name, date, status, check=true}, ...]` | 200 |
| Нет ADR | `{callId, productCode}` | `docId=1` | `false` | `[]` | 200 |
| docId не передан | `{callId, productCode}` | — | `false` | `"Not implemented"` | 501 |
| docId не существует | `{callId, productCode}` | `docId=99999` | `false` | `"Not found"` | 404 |
| Невалидный callId | `{callId: "bad", productCode}` | `docId=1` | — | — | 422 |

### 4.2. API.01 — Наличие опубликованных API

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Есть API | `true` | `[{code, name, date, status, check=true, spec}, ...]` |
| Нет API | `false` | `[{code, name, date, status, check=false, spec}, ...]` |

### 4.3. API.02 — SLA для методов (RPS / Latency / Error rate)

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| У всех методов есть SLA | `true` | `[{code, name, date, status, check=true, rps, latency, error_rate}, ...]` |
| Есть методы без SLA | `false` | Смешанный список: часть `check=true`, часть `check=false` |
| Нет методов | `false` | `[{code, name, date, status, check=false, ...}]` |

### 4.4. API.03 — Спецификации для всех TC

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| У всех TC есть api_url | `true` | `[{code, name, date, status, check=true, technical_capability, interface_code, api_url}, ...]` |
| Есть TC без api_url | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.5. CNT.01 — Наличие контейнеров

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Есть контейнеры | `true` | `[{code, name, date, status, check=true, technology, tags}, ...]` |
| Нет контейнеров | `false` | `[{code, name, date, status, check=false, ...}]` |

### 4.6. CNT.02 — Наличие containerView

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Есть containerView | `true` | `[{code, name, date, status, check=true}, ...]` |
| Нет containerView | `false` | `[{code, name, date, status, check=false}, ...]` |

### 4.7. CNT.03 — Технологии у связей контейнеров

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| У всех связей есть technology | `true` | `[{code, name, date, status, check=true, source_name, target_name}, ...]` |
| Есть связи без technology | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.8. CPB.01 — Технические возможности продукта

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| TC есть в Structurizr и/или Landscape | `true` | `[{code, name, source, parents, check=true}, ...]` |
| TC нет нигде | `false` | `[{code: "CPB.01", name: "...", source: "FAIL", parents: [], check=false}]` |

### 4.9. CPB.02 — TC для внешних контейнеров

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Все внешние контейнеры с TC | `true` | `[{code, name, status, check=true, container_name, technical_capability, external_callers}, ...]` |
| Есть контейнеры без TC | `false` | Смешанный список: часть `check=true`, часть `check=false` |
| Нет внешних контейнеров | `true` | `[{code: "CPB.02", name: "Нет контейнеров...", status: "OK", check=true, ...}]` |

### 4.10. CPB.03 — Полнота описания TC

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Все TC полные | `true` | `[{code, name, source, parents, check=true}, ...]` |
| Есть неполные TC | `false` | Смешанный список: полные `check=true`, неполные `check=false` |
| Нет TC | `false` | `[{code: "CPB.03", name: "Отсутствуют...", source: "FAIL", parents: [], check=false}]` |

### 4.11. CPB.04 — Позиционирование TC в ФДМ

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Позиционирование корректно | `true` | `[{code: "CPB.04", name: "...", status: "OK", check=true, rule: "CPB.04", reason: "...", severity: "ok"}]` |
| Есть ошибки позиционирования | `false` | `[{code, name, status: "FAIL", check=false, rule, reason, severity: "error"}, ...]` |

### 4.12. CPB.05 — Качество описания TC

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Качество OK | `true` | `[{code, name, status, check=true}, ...]` |
| Есть нарушения | `false` | `[{code, name, status, check=false}, ...]` |

### 4.13. CTX.01 — Наличие contextView

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Есть contextView | `true` | `[{code, name, date, status, check=true}, ...]` |
| Нет contextView | `false` | `[{code, name, date, status, check=false}, ...]` |

### 4.14. CTX.02 — Подписи связей на контекстной диаграмме

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Все связи подписаны | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть связи без описания | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.15. CTX.03 — Технологии у связей контекста

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| У всех связей есть technology | `true` | `[{code, name, date, status, check=true, target_name, technology}, ...]` |
| Есть связи без technology | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.16. DEP.01 — Наличие Deployment Environment

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Есть deployment environment | `true` | `[{code, name, date, status, check=true}, ...]` |
| Нет deployment environment | `false` | `[{code, name, date, status, check=false}, ...]` |

### 4.17. DEP.02 — Наличие deploymentView

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Есть deploymentView | `true` | `[{code, name, date, status, check=true}, ...]` |
| Нет deploymentView | `false` | `[{code, name, date, status, check=false}, ...]` |

### 4.18. DEP.03 — Сверка deployment с CMDB

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| CMDB совпадает | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть расхождения | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.19. DEP.04 — Макросегментация (stub - не реализовано)

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Всегда (stub) | `true` | `[{code: "DEP.04", name: "...", date: "", status: "stub", check=true}]` |

### 4.20. EA.0001 — Выход в интернет

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Выход в интернет описан | `true` | `[{code, name, date, status, check=true}, ...]` |
| Выход в интернет не описан | `false` | `[{code, name, date, status, check=false}, ...]` |

### 4.21. GIT.01 — Git/Nexus/Harbor URL

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| У всех контейнеров есть git URL | `true` | `[{code, name, date, status, check=true, git}, ...]` |
| Есть контейнеры без git URL | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.22. SQ.01 — DynamicView для TC

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Для всех TC есть dynamicView | `true` | `[{code, name, date, status, check=true, plantUML}, ...]` |
| Есть TC без dynamicView | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.23. SQ.02 — HTTP-методы в sequence

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Все REST связи с HTTP-методом | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть связи без HTTP-метода | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.24. TECH.01 — Технологии в TechRadar

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Все технологии из TechRadar | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть технологии не из TechRadar | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.25. TECH.02 — Нет HOLD-технологий

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Нет HOLD | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть HOLD | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.26. TECH.03 — Поле technology у контейнеров

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| У всех контейнеров есть technology | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть контейнеры без technology | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.27. TECH.04 — Нет HOLD-протоколов

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Нет HOLD протоколов | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть HOLD протоколы | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.28. TECH.05 — Протоколы из TechRadar

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Все протоколы из TechRadar | `true` | `[{code, name, date, status, check=true}, ...]` |
| Есть протоколы не из TechRadar | `false` | Смешанный список: часть `check=true`, часть `check=false` |

### 4.29. TECH.06 — Технологии мониторинга

| Сценарий | Выход (isCheck) | Выход (details) |
|---|---|---|
| Мониторинг описан | `true` | `[{code, name, date, status, check=true}, ...]` |
| Мониторинг не описан | `false` | `[{code, name, date, status, check=false}, ...]` |

---


## 5. Настройка окружения



Переменные окружения, необходимые для импорта модулей:

```python
os.environ.setdefault("ONPREMISES_PASSWORD", "test-password")
os.environ.setdefault("URL_ONPREMISES_WORKSPACE", "https://structurizr.test/api/workspace")
os.environ.setdefault("URL_DOCUMENTS", "https://documents.test")
os.environ.setdefault("URL_PRODUCTS", "https://products.test")
os.environ.setdefault("GATEWAY_URL", "https://gateway.test")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("API_SECRET", "test-api-secret")
# ... и т.д.
```


---

## 6. Приложение: Список всех эндпоинтов

| № | Эндпоинт | Файл роутера | Описание |
|---|---|---|---|
| 1 | `POST /api/v1/ff/adr01` | `ff_adr_01.py` | Наличие ADR в документации |
| 2 | `POST /api/v1/ff/api01` | `ff_api_01.py` | Наличие опубликованных API |
| 3 | `POST /api/v1/ff/api02` | `ff_api_02.py` | SLA для методов (RPS/Latency/Error rate) |
| 4 | `POST /api/v1/ff/api03` | `ff_api_03.py` | Спецификации для всех TC |
| 5 | `POST /api/v1/ff/cnt01` | `ff_cnt_01.py` | Наличие контейнеров |
| 6 | `POST /api/v1/ff/cnt02` | `ff_cnt_02.py` | Наличие containerView |
| 7 | `POST /api/v1/ff/cnt03` | `ff_cnt_03.py` | Технологии у связей контейнеров |
| 8 | `POST /api/v1/ff/cpb01` | `ff_cpb_01.py` | Технические возможности продукта |
| 9 | `POST /api/v1/ff/cpb02` | `ff_cpb_02.py` | TC для внешних контейнеров |
| 10 | `POST /api/v1/ff/cpb03` | `ff_cpb_03.py` | Полнота описания TC |
| 11 | `POST /api/v1/ff/cpb04` | `ff_cpb_04.py` | Позиционирование TC в ФДМ |
| 12 | `POST /api/v1/ff/cpb05` | `ff_cpb_05.py` | Качество описания TC |
| 13 | `POST /api/v1/ff/ctx01` | `ff_ctx_01.py` | Наличие contextView |
| 14 | `POST /api/v1/ff/ctx02` | `ff_ctx_02.py` | Подписи связей на контекстной диаграмме |
| 15 | `POST /api/v1/ff/ctx03` | `ff_ctx_03.py` | Технологии у связей контекста |
| 16 | `POST /api/v1/ff/dep01` | `ff_dep_01.py` | Наличие Deployment Environment |
| 17 | `POST /api/v1/ff/dep02` | `ff_dep_02.py` | Наличие deploymentView |
| 18 | `POST /api/v1/ff/dep03` | `ff_dep_03.py` | Сверка deployment с CMDB |
| 19 | `POST /api/v1/ff/dep04` | `ff_dep_04.py` | Макросегментация (stub) |
| 20 | `POST /api/v1/ff/ea0001` | `ff_ea_0001.py` | Выход в интернет |
| 21 | `POST /api/v1/ff/git01` | `ff_git_01.py` | Git/Nexus/Harbor URL |
| 22 | `POST /api/v1/ff/sq01` | `ff_sq_01.py` | DynamicView для TC |
| 23 | `POST /api/v1/ff/sq02` | `ff_sq_02.py` | HTTP-методы в sequence |
| 24 | `POST /api/v1/ff/tech01` | `ff_tech_01.py` | Технологии в TechRadar |
| 25 | `POST /api/v1/ff/tech02` | `ff_tech_02.py` | Нет HOLD-технологий |
| 26 | `POST /api/v1/ff/tech03` | `ff_tech_03.py` | Поле technology у контейнеров |
| 27 | `POST /api/v1/ff/tech04` | `ff_tech_04.py` | Нет HOLD-протоколов |
| 28 | `POST /api/v1/ff/tech05` | `ff_tech_05.py` | Протоколы из TechRadar |
| 29 | `POST /api/v1/ff/tech06` | `ff_tech_06.py` | Технологии мониторинга |
| 30 | `GET /health` | `health.py` | Healthcheck |
