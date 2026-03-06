# 🏗️ Structurizr Backend API

**API для управления шагами архитектурного конвейера**

Сервис для автоматизации процессов создания, публикации и управления архитектурными workspace'ами в Structurizr, интеграции с BeeAtlas, проверки fitness functions и генерации Terraform конфигураций.

## 📋 Содержание

- [Описание проекта](#описание-проекта)
- [Архитектура](#архитектура)
- [API Endpoints](#api-endpoints)
- [Модели данных](#модели-данных)
- [Примеры использования](#примеры-использования)
- [Установка и запуск](#установка-и-запуск)
- [Мониторинг](#мониторинг)
- [Разработка](#разработка)

## 🎯 Описание проекта

Structurizr Backend - это FastAPI приложение, которое предоставляет REST API для:

- **Создания и управления workspace'ами** в Structurizr
- **Интеграции с BeeAtlas** - системой управления продуктами
- **Проверки fitness functions** архитектурных решений
- **Генерации Terraform конфигураций** на основе архитектурных моделей
- **Публикации архитектурных документов** в различных форматах
- **Интеграции с Draw.io** для создания диаграмм

### Основные возможности

- 🔄 Автоматическое создание workspace'ов в Structurizr
- 📊 Проверка архитектурных решений через fitness functions
- 🚀 Генерация инфраструктурного кода (Terraform)
- 🔗 Интеграция с внешними системами (BeeAtlas, Sparx EA)
- 📈 Мониторинг через Prometheus и Grafana
- 🐳 Контейнеризация с Docker

## 🏛️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Structurizr CLI │    │   BeeAtlas API  │
│                 │◄──►│                  │    │                 │
│  - Workspace    │    │  - Push/Pull     │    │  - Products     │
│  - Fitness      │    │  - Export        │    │  - Tech Stack   │
│  - Terraform    │    │  - Merge         │    │  - Relations    │
│  - Integration  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Prometheus    │    │   Templates      │    │   Terraform     │
│   + Grafana     │    │   (Jinja2)       │    │   Generation    │
│                 │    │                  │    │                 │
│  - Metrics      │    │  - Workspace     │    │  - Resources    │
│  - Dashboards   │    │  - Deployment    │    │  - Providers    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Компоненты системы

- **FastAPI Application** - основной веб-сервер
- **Structurizr CLI** - для работы с Structurizr API
- **Jinja2 Templates** - для генерации workspace файлов
- **Pydantic Models** - для валидации данных
- **Prometheus** - для сбора метрик
- **Grafana** - для визуализации метрик

## 🚀 API Endpoints

### 1. Workspace Management

#### `POST /workspace`
Создание нового workspace в Structurizr для продукта.

**Request Body:**
```json
{
  "code": "PRODUCT_CODE",
  "architect_name": "Имя архитектора"
}
```

**Response:**
```json
{
  "id": 123,
  "code": "PRODUCT_CODE",
  "name": "Product Name",
  "api_key": "structurizr_api_key",
  "api_secret": "structurizr_api_secret",
  "api_url": "https://structurizr.com/share/123"
}
```

#### `POST /api/v1/workspace/validate`
Валидация DSL workspace в формате base64.

**Request Body:**
```json
{
  "workspace": "base64_encoded_dsl_content"
}
```

**Response:**
```json
{
  "valid": "true"
}
```

#### `POST /api/v1/workspace/{docId}`
Публикация workspace из документа в Structurizr.

#### `POST /api/v1/workspace/{docId}/fdm`
Публикация архитектурной модели в ФДМ (Fitness Function Management).

### 2. Fitness Functions

#### `POST /api/v1/fitness-function/local/{docId}`
Локальная проверка fitness-функций для документа.

**Query Parameters:**
- `pipelineId` (optional): ID пайплайна (по умолчанию 0)

**Response:**
```json
{
  "details": "Ok",
  "dashboard": "https://dashboard-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru/systems/{cmdb}"
}
```

### 3. Terraform Generation

#### `GET /api/v1/workspace/{docId}/terraform`
Генерация Terraform конфигурации из документа.

**Query Parameters:**
- `token`: Vega VPS токен
- `environment`: Окружение развертывания

#### `POST /api/v1/workspace/terraform/generate`
Генерация Terraform конфигурации из JSON.

**Headers:**
- `X-Token`: Vega VPS токен

**Query Parameters:**
- `environment`: Окружение развертывания

**Request Body:** JSON описание архитектуры

#### `POST /api/v1/workspace/terraform/plan`
Планирование изменений Terraform.

**Request Body:** Terraform конфигурация

#### `POST /api/v1/workspace/terraform/apply`
Применение изменений Terraform.

**Request Body:** Terraform конфигурация

### 4. Integration

#### `POST /api/v1/integration/sla`
Расчет SLA метрик для API методов.

**Request Body:** Спецификация API (OpenAPI, WSDL, Proto)

**Response:**
```
"method_name" rps=100;latency=10;error_rate=0.5
```

### 5. Draw.io Integration

#### `POST /api/v1/export/drawio/{diagram_key}`
Экспорт диаграммы в формат Draw.io.

**Request Body:** JSON описание workspace

**Response:** XML диаграммы Draw.io

## 📊 Модели данных

### Основные модели

#### Product
```python
class Product(BaseModel):
    alias: str
    description: Optional[str] = None
    gitUrl: Optional[str] = None
    id: int
    name: str
    structurizrApiKey: Optional[str] = None
    structurizrApiSecret: Optional[str] = None
    structurizrApiUrl: Optional[str] = None
    structurizrWorkspaceName: Optional[str] = None
    techProducts: List[TechProduct]
    discoveredInterfaces: List[DiscoveredInterface] = []
```

#### FitnessFunctionDTO
```python
class FitnessFunctionDTO(BaseModel):
    code: str
    isCheck: bool
    resultDetails: Optional[str] = None
```

#### DiscoveredInterface
```python
class DiscoveredInterface(BaseModel):
    apiId: int
    apiLink: Optional[str] = None
    connectedInterface: Optional[Interface] = None
    connectionInterfaceId: Optional[int] = None
    context: Optional[str] = None
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    description: Optional[str] = None
    externalId: int
    id: int
    name: Optional[str] = None
    operations: List[DiscoveredOperation]
    product: Optional[Product] = None
    status: Optional[str] = None
    updatedDate: Optional[str] = None
    version: Optional[str] = None
```

## 💡 Примеры использования

### 1. Создание нового workspace

```python
import requests

# Создание workspace для продукта
workspace_data = {
    "code": "USER_SERVICE",
    "architect_name": "Иван Петров"
}

response = requests.post(
    "http://localhost:8080/workspace",
    json=workspace_data
)

if response.status_code == 200:
    workspace = response.json()
    print(f"Workspace создан: {workspace['api_url']}")
    print(f"API Key: {workspace['api_key']}")
```

### 2. Валидация workspace

```python
import requests
import base64

# Подготовка DSL контента
dsl_content = """
workspace "My System" {
    model {
        user = person "User"
        softwareSystem = softwareSystem "My System" {
            webapp = container "Web Application" {
                user -> webapp "Uses"
            }
        }
    }
}
"""

# Кодирование в base64
encoded_dsl = base64.b64encode(dsl_content.encode('utf-8')).decode('utf-8')

# Валидация
response = requests.post(
    "http://localhost:8080/api/v1/workspace/validate",
    json={"workspace": encoded_dsl}
)

if response.status_code == 200:
    result = response.json()
    print(f"Workspace валиден: {result['valid']}")
```

### 3. Публикация fitness functions

```python
import requests

# Локальная проверка fitness-функций
response = requests.post(
    "http://localhost:8080/api/v1/fitness-function/local/123",
    params={"pipelineId": 456}
)

if response.status_code == 201:
    result = response.json()
    print(f"Fitness functions проверены: {result['details']}")
    print(f"Dashboard: {result['dashboard']}")
```

### 4. Генерация Terraform конфигурации

```python
import requests

# Генерация из документа
response = requests.get(
    "http://localhost:8080/api/v1/workspace/123/terraform",
    params={
        "token": "vega_token",
        "environment": "production"
    }
)

if response.status_code == 200:
    terraform_config = response.text
    with open("main.tf", "w") as f:
        f.write(terraform_config)
    print("Terraform конфигурация сгенерирована")

# Генерация из JSON
with open("workspace.json", "r") as f:
    workspace_content = f.read()

response = requests.post(
    "http://localhost:8080/api/v1/workspace/terraform/generate",
    params={"environment": "production"},
    headers={"X-Token": "vega_token"},
    data=workspace_content
)

if response.status_code == 200:
    terraform_config = response.text
    with open("main.tf", "w") as f:
        f.write(terraform_config)
    print("Terraform конфигурация сгенерирована из JSON")
```

### 5. Планирование и применение Terraform

```python
import requests

# Планирование изменений
with open("main.tf", "r") as f:
    terraform_content = f.read()

response = requests.post(
    "http://localhost:8080/api/v1/workspace/terraform/plan",
    data=terraform_content
)

if response.status_code == 200:
    plan_output = response.text
    print("Terraform plan выполнен:")
    print(plan_output)

# Применение изменений
response = requests.post(
    "http://localhost:8080/api/v1/workspace/terraform/apply",
    data=terraform_content
)

if response.status_code == 200:
    apply_output = response.text
    print("Terraform apply выполнен:")
    print(apply_output)
```

### 6. Расчет SLA для API

```python
import requests

# Загрузка OpenAPI спецификации
with open("api-spec.yaml", "r") as f:
    api_spec = f.read()

# Расчет SLA
response = requests.post(
    "http://localhost:8080/api/v1/integration/sla",
    data=api_spec
)

if response.status_code == 200:
    sla_metrics = response.text
    print("SLA метрики рассчитаны:")
    print(sla_metrics)
```

### 7. Экспорт в Draw.io

```python
import requests

# Загрузка workspace
with open("workspace.json", "r") as f:
    workspace_content = f.read()

# Экспорт диаграммы
response = requests.post(
    "http://localhost:8080/api/v1/export/drawio/SystemContext",
    data=workspace_content
)

if response.status_code == 200:
    drawio_xml = response.text
    with open("diagram.drawio", "w") as f:
        f.write(drawio_xml)
    print("Диаграмма экспортирована в Draw.io формат")
```

### 4. Получение информации о продукте

```python
from structurizr_utils.models.models_product import get_product

# Получение продукта по CMDB коду
product = get_product("USER_SERVICE")

if product:
    print(f"Продукт: {product.name}")
    print(f"Описание: {product.description}")
    print(f"Git URL: {product.gitUrl}")
    print(f"Structurizr URL: {product.structurizrApiUrl}")
    print(f"Технологии: {len(product.techProducts)}")
    print(f"Discovered interfaces: {len(product.discoveredInterfaces)}")
```

## 🛠️ Установка и запуск

### Требования

- Python 3.8+
- Docker и Docker Compose
- Structurizr CLI
- Доступ к BeeAtlas API

### Быстрый запуск с Docker

```bash
# Клонирование репозитория
git clone <repository-url>
cd structurizr_backend

# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### Ручная установка

```bash
# Установка зависимостей
pip install -r requirements/dev.txt

# Настройка переменных окружения
cp .env_dev .env
# Отредактируйте .env файл

# Запуск приложения
python src/main.py
```

### Переменные окружения

```bash
# BeeAtlas API
URL_PRODUCTS=https://beeatlas-api.example.com

# Structurizr
STRUCTURIZR_URL=https://structurizr.example.com
STRUCTURIZR_API_KEY=your_api_key
STRUCTURIZR_API_SECRET=your_api_secret

# Vega VPS
VEGA_API_URL=https://vega-api.example.com
VEGA_API_KEY=your_vega_api_key
```

## 📈 Мониторинг

### Prometheus метрики

- **HTTP Requests Total** - общее количество HTTP запросов
- **HTTP Request Duration** - время выполнения запросов
- **Custom Business Metrics** - бизнес-метрики

### Grafana дашборды

- **API Performance** - производительность API
- **Business Metrics** - бизнес-метрики
- **System Health** - здоровье системы

### Доступ к метрикам

```bash
# Prometheus
curl http://localhost:9090

# Grafana
http://localhost:3000 (admin/admin)

# API метрики
curl http://localhost:8080/actuator/prometheus
```

## 🔧 Разработка

### Структура проекта

```
src/
├── main.py                 # Основное приложение FastAPI
├── routers/               # API роутеры
│   ├── workspace.py       # Управление workspace'ами
│   ├── fitness_functions.py # Fitness functions
│   ├── terraform.py       # Генерация Terraform
│   ├── integration.py     # Интеграции
│   └── drawio.py          # Draw.io интеграция
├── structurizr_utils/     # Утилиты
│   ├── models/            # Pydantic модели
│   ├── functions/         # Бизнес-логика
│   └── utils/             # Вспомогательные функции
└── tests/                 # Тесты
```

### Запуск тестов

```bash
# Все тесты
python -m pytest src/tests/

# Конкретный тест
python -m pytest src/tests/test_workspace.py -v

# С покрытием
python -m pytest --cov=src src/tests/
```

### Линтинг и форматирование

```bash
# Проверка кода
flake8 src/
black --check src/

# Автоформатирование
black src/
isort src/
```

### Добавление новых endpoints

1. Создайте новый роутер в `src/routers/`
2. Добавьте модели в `src/structurizr_utils/models/`
3. Подключите роутер в `src/main.py`
4. Напишите тесты
5. Обновите документацию

---

**Structurizr Backend API** - автоматизируйте ваш архитектурный конвейер! 🚀
