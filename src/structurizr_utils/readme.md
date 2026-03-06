# Structurizr Utils

Комплексная библиотека для работы с архитектурными моделями Structurizr DSL, включающая функции проверки качества архитектуры, модели данных для интеграции с внешними системами и вспомогательные утилиты.

## 📁 Структура модуля

```
structurizr_utils/
├── readme.md                    # Этот файл — документация модуля
├── functions/                   # Функции проверки архитектуры
│   ├── README.md               # Документация функций проверки
│   ├── capability.py           # Проверка технических возможностей
│   ├── context.py              # Проверка контекстных диаграмм
│   ├── deployment.py           # Проверка диаграмм размещения
│   ├── api.py                  # Проверка API и SLA
│   ├── adr.py                  # Проверка архитектурных решений
│   ├── technology.py           # Проверка технологий из TechRadar
│   ├── sequences.py            # Проверка динамических диаграмм
│   └── objects.py              # Базовые объекты для проверок
├── models/                     # Модели данных и клиенты API
│   ├── README.md              # Документация моделей данных
│   ├── models_product.py      # Модели продуктов и API
│   ├── model_techradar.py     # Клиент TechRadar
│   ├── model_terraform.py     # Модели Terraform ресурсов
│   ├── model_graph.py         # Клиент Architect Graph Service
│   ├── model_documents.py     # Клиент системы документов
│   ├── model_camunda.py       # Клиент Camunda BPM
│   ├── model_arch_patterns.py # Модели архитектурных паттернов
│   ├── model_observability.py # Клиент Observability сервиса
│   ├── model_rule_compiler.py # Клиент Rule Compiler сервиса
│   ├── model_vega_vps.py     # Модели Vega VPS API
│   └── models_workspace.py   # Модели workspace данных
└── utils/                      # Вспомогательные утилиты
    ├── README.md             # Документация утилит
    ├── structurizr.py       # Утилиты для работы с Structurizr API
    └── utils.py             # Общие утилиты
```

## 🎯 Основные возможности

### 🔍 **Функции проверки архитектуры** ([functions/](./functions/README.md))
Автоматизированные проверки качества архитектурных моделей:

- **CPB.01-05** - Проверка технических возможностей (capability.py)
- **CTX.01-03** - Проверка контекстных диаграмм (context.py)
- **DEP.01-02** - Проверка диаграмм размещения (deployment.py)
- **API.01-03** - Проверка API и SLA (api.py)
- **ADR.01** - Проверка архитектурных решений (adr.py)
- **TECH.01-06** - Проверка технологий из TechRadar (technology.py)
- **SQ.01-02** - Проверка динамических диаграмм (sequences.py)

### 🏗️ **Модели данных** ([models/](./models/README.md))
Интеграция с внешними системами:

- **BeeAtlas Products** - управление продуктами и API
- **BeeAtlas DB** - источник оценок описания TC (временно, до появления соответствующего API BeeAtlas)
- **TechRadar** - управление технологиями
- **Terraform** - управление инфраструктурой
- **Camunda BPM** - управление бизнес-процессами
- **Documents Service** - управление документами
- **Graph Service** - работа с архитектурными графами
- **Observability** - мониторинг и наблюдаемость
- **Rule Compiler** - компиляция правил
- **Vega VPS** - управление виртуальными серверами

### 🛠️ **Вспомогательные утилиты** ([utils/](./utils/README.md))
Базовые функции для работы с Structurizr:

- **structurizr.py** - Аутентификация и работа с Structurizr API
- **utils.py** - Общие утилиты для работы с данными

## 🚀 Использование

Модуль `structurizr_utils` используется из основного приложения как обычный Python‑пакет, например:

```python
from structurizr_utils.functions.capability import check_capability
from structurizr_utils.models.model_techradar import TechradarClient
from structurizr_utils.utils.utils import load_workspace

# Загрузка workspace
data = load_workspace("workspace.json")

# Проверка технических возможностей
results = check_capability(
    cmdb="MY_SYSTEM",
    data=data,
    backend_url="https://backend.example.com",
    share_url="https://structurizr.example.com",
    publish=True
)

# Работа с TechRadar
client = TechradarClient(
    base_url="https://techradar.example.com",
    auth_token="your_token"
)
technologies = client.get_all_tech()
```

## 📊 Статистика пакета

| Директория | Файлов | Строк кода | Основное назначение |
|------------|--------|------------|-------------------|
| **functions/** | 8 | 2,000+ | Проверки архитектуры |
| **models/** | 12 | 3,000+ | Модели данных и API |
| **utils/** | 2 | 200+ | Вспомогательные утилиты |
| **Всего** | **22** | **5,200+** | **Архитектурная платформа** |

## 🔧 Архитектурные проверки

### Система оценок (Fitness Functions)

Все проверки возвращают объекты `FitnessStatus` с оценками:
- ✅ **PASS** - проверка пройдена
- ❌ **FAIL** - проверка не пройдена
- ⚠️ **WARN** - предупреждение
- ℹ️ **INFO** - информационное сообщение

## 📋 Детальное описание Fitness Functions

Система проверки качества архитектуры включает в себя комплексный набор функций пригодности (Fitness Functions), каждая из которых проверяет определенный аспект архитектурной модели в расширенной C4 Structurizr DSL нотации.

### 🎯 **Технические возможности (Capability Functions)**

#### **CPB.01** - Определены технические возможности продукта
**Логика проверки**: Система анализирует компоненты контейнеров с типом `capability` в properties. Проверяет наличие компонентов с:
- `properties.type = "capability"`
- `properties.code` - код технической возможности
- `properties.parents` - родительские возможности
- `properties.version` - версия возможности
- `properties.goal_from` и `properties.goal_to` - цели от и до

Также проверяет наличие опубликованных capabilities в landscape через API `/api/v4/systems/{cmdb}/purpose`.

#### **CPB.02** - Для всех внешних интеграций определены TC
**Логика проверки**:
1. Анализирует все внешние системы (с `properties.cmdb != текущая_система`)
2. Находит контейнеры с исходящими связями к внешним системам
3. Проверяет наличие компонентов типа `capability` в этих контейнерах
4. Проверяет контейнеры с входящими связями от внешних систем

#### **CPB.03** - Есть capability в Structurizr
**Логика проверки**: Проверяет наличие хотя бы одного компонента с типом `capability` в модели Structurizr. При публикации добавляет префикс `{cmdb}.` к кодам capabilities.

#### **CPB.04** - Опубликованные TC правильно спозиционированы в ФДМ
**Логика проверки**: Проверяет установленных для TC родителей. Если родителем является группировка или домен - фиксирует ошибку.

#### **CPB.05** - Описания TC сформированны в соответствии с методикой
**Логика проверки**: Проверяет наличие TC с оценками "0","1","2" в DB BeeAtlas. если нахожит - фиксирует ошибку. Если все TC имеют оценки > 2, фиксирует прохождение ФФ. Если оцененных TC нет - проверка не проводится.

### 🏗️ **Контекстные диаграммы (Context Functions)**

#### **CTX.01** - Создана диаграмма контекста
**Логика проверки**: Ищет в `views.systemContextViews` диаграммы контекста для целевой системы. Проверяет наличие:
- `softwareSystemId` соответствующий целевой системе
- `title` - название диаграммы
- `key` - уникальный ключ диаграммы

#### **CTX.02** - Все связи на диаграмме контекста должны быть подписаны
**Логика проверки**: Анализирует все `relationships` системы и проверяет наличие непустого поля `description` для каждой связи.

#### **CTX.03** - Все связи на диаграмме контекста должны иметь технологию взаимодействия
**Логика проверки**: Анализирует все `relationships` системы и проверяет наличие непустого поля `technology` для каждой связи.

### 🚀 **Диаграммы размещения (Deployment Functions)**

#### **DEP.01** - Наличие хотя бы одного Deployment Environment
**Логика проверки**: Анализирует `model.deploymentNodes` и проверяет наличие непустого поля `environment` для каждого узла развертывания.

#### **DEP.02** - Наличие хотя бы одной Deployment диаграммы
**Логика проверки**: Ищет в `views.deploymentViews` диаграммы развертывания. Проверяет наличие:
- `title` - название диаграммы
- `key` - уникальный ключ диаграммы

#### **DEP.03** - DeploymentEnvironment ссылается на мнемонику экземпляра в CMDB
**Логика проверки**: *В разработке* - планируется проверка соответствия environment именования с CMDB.

#### **DEP.04** - Правильно задана макросегментация Protected/DMZ STD/NST Operations/RND
**Логика проверки**: *В разработке* - планируется проверка правильности сегментации окружений.

### 🔌 **API и SLA (API Functions)**

#### **API.01** - У приложения есть опубликованные API
**Логика проверки**: Ищет компоненты с `properties.type = "api"` в контейнерах. Проверяет:
- Наличие `properties.api_url` - URL спецификации API
- Наличие `properties.protocol` - тип протокола (rest, grpc, soap, wsdl)
- Загрузку методов из спецификации через `ApiLoader`

#### **API.02** - Для некоторых методов определен SLA
**Логика проверки**: Анализирует properties компонентов API на наличие SLA метрик:
- Старый формат: `metadata` в `customElements` с ключами RPS, LATENCY, ERROR_RATE
- Новый формат: properties вида `METHOD PATH=RPS=100;LATENCY=50;ERROR_RATE=0.01;TC=capability_code`



### 📋 **Архитектурные решения (ADR Functions)**

#### **ADR.01** - Наличие хотя бы одного ADR
**Логика проверки**: Анализирует `documentation.decisions` и проверяет наличие хотя бы одного архитектурного решения с:
- `id` - уникальный идентификатор
- `title` - название решения
- `content` - содержание решения

### 🛠️ **Технологии (Technology Functions)**

#### **TECH.01** - Все технологии продукта есть в техрадаре
**Логика проверки**:
1. Загружает все технологии из TechRadar API
2. Анализирует `technology` поля в контейнерах и связях
3. Проверяет соответствие технологий с техрадаром
4. Исключает контейнеры с `properties.source = "landscape"`

#### **TECH.02** - В продукте нет технологий в статусе HOLD
**Логика проверки**: Проверяет, что все используемые технологии имеют статус отличный от "hold" в техрадаре.

#### **TECH.03** - У всех контейнеров есть технологии
**Логика проверки**: Анализирует все контейнеры (кроме внешних) и проверяет наличие непустого поля `technology`.

#### **TECH.04** - Приложение не использует протоколов в статусе hold
**Логика проверки**: Анализирует технологии в связях (`relationships.technology`) и проверяет их статус в техрадаре (сектор 3 - протоколы).

#### **TECH.05** - У всех взаимодействий указаны протоколы из техрадара
**Логика проверки**: Проверяет, что все технологии в связях присутствуют в техрадаре в секторе протоколов.

#### **TECH.06** - Технологии найденные по мониторингу продуктивной среды и Git описаны в архитектуре
**Логика проверки**:
1. Загружает технологии из мониторинга через `/api/v4/products/{cmdb}/tech`
2. Сравнивает с технологиями, найденными в архитектурной модели
3. Проверяет соответствие технологий из мониторинга с описанными в архитектуре

### 🔄 **Динамические диаграммы (Sequence Functions)**

#### **SQ.01** - Для всех technical capability указаны sequence
**Логика проверки**:
1. Загружает technical capabilities из `/api/v4/systems/{cmdb}/purpose`
2. Ищет соответствующие `dynamicViews` в `views.dynamicViews`
3. Проверяет соответствие ключей диаграмм с кодами capabilities

#### **SQ.02** - Все вызовы содержат HTTP запросы
**Логика проверки**:
1. Анализирует `dynamicViews.relationships` для REST технологий
2. Проверяет формат описания через регулярное выражение `(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) .*`
3. Валидирует корректность HTTP endpoint описаний

### 📦 **Контейнерная модель (Container Functions)**

#### **CNT.01** - Наличие в модели контейнеров для системы
**Логика проверки**: Анализирует `containers` целевой системы и проверяет наличие хотя бы одного контейнера.

#### **CNT.02** - Наличие в хотя бы одной диаграммы контейнеров
**Логика проверки**: Ищет в `views.containerViews` диаграммы контейнеров для целевой системы по `softwareSystemId`.

#### **CNT.03** - Все вызовы между контейнерами имеют технологию
**Логика проверки**: Анализирует все `relationships` контейнеров и системы, проверяя наличие непустого поля `technology`.

#### **SEC.01** - Интеграция frontend/api gateway с IDM системой
**Логика проверки**:
1. Определяет список IDM систем по CMDB кодам
2. Анализирует связи контейнеров с IDM системами
3. Проверяет наличие интеграции с системами аутентификации

#### **GIT.01** - Наличие в модели git репозитория
**Логика проверки**:
1. Исключает контейнеры с инфраструктурными технологиями
2. Проверяет наличие `url` поля с git репозиторием
3. Анализирует `properties.structurizr.dsl.identifier` для генерации кодов

### 🔍 **Расширения C4 Structurizr DSL**

Система поддерживает расширения базовой C4 модели через properties компонентов:

- **`properties.type`** - тип компонента (capability, api, etc.)
- **`properties.code`** - уникальный код компонента
- **`properties.parents`** - родительские элементы
- **`properties.tc`** - код технической возможности
- **`properties.api_url`** - URL API спецификации
- **`properties.protocol`** - тип протокола (rest, grpc, soap, wsdl)
- **`properties.source`** - источник компонента (landscape, external)
- **`properties.external_name`** - внешнее имя для интеграции
- **`properties.structurizr.dsl.identifier`** - DSL идентификатор
- **SLA properties** - метрики производительности в формате `METHOD PATH=RPS=100;LATENCY=50;ERROR_RATE=0.01`

### Примеры проверок

```python
# Проверка технических возможностей
capability_results = check_capability(
    cmdb="MY_SYSTEM",
    data=workspace_data,
    backend_url="https://backend.example.com",
    share_url="https://structurizr.example.com",
    publish=True
)

# Проверка технологий
tech_results = check_technology(
    cmdb="MY_SYSTEM",
    data=workspace_data,
    backend_url="https://backend.example.com",
    share_url="https://structurizr.example.com",
    publish=False
)

# Анализ результатов
for result in capability_results:
    print(f"{result.status}: {result.message}")
    if result.url:
        print(f"Ссылка: {result.url}")
```

## 🌐 Интеграции

### Внешние системы
- **Structurizr** - основная платформа архитектурного моделирования
- **BeeAtlas** - система управления продуктами
- **TechRadar** - управление технологиями
- **Terraform** - управление инфраструктурой
- **Camunda** - бизнес-процессы
- **Vega VPS** - виртуальные серверы

### Поддерживаемые форматы
- **Structurizr DSL** - основной формат моделей
- **JSON** - обмен данными
- **YAML** - конфигурация
- **OpenAPI/Swagger** - спецификации API
- **WSDL** - SOAP сервисы
- **Protocol Buffers** - gRPC сервисы

## 📝 Конфигурация

### Переменные окружения

```bash
# Structurizr
STRUCTURIZR_API_URL=https://structurizr.example.com
STRUCTURIZR_API_KEY=your_api_key
STRUCTURIZR_API_SECRET=your_api_secret

# Backend сервисы
URL_PRODUCTS=https://products.example.com
URL_DOCUMENTS=https://documents.example.com
GRAPH_BASE_URL=https://graph.example.com
RULE_COMPILER_URL=https://compiler.example.com

# TechRadar
TECHRADAR_URL=https://techradar.example.com
TECHRADAR_TOKEN=your_token

# Camunda
CAMUNDA_URL=https://camunda.example.com
CAMUNDA_USER=username
CAMUNDA_PASSWORD=password


# DB BeeAtlas
FDMDB_SERVER=host
FDMDB_DB=db_name
FDMDB_USERNAME=username
FDMDB_PASS=password


```

## 🧪 Тестирование

### Запуск проверок

```bash
# Проверка всех аспектов архитектуры
python fitness_check.py

# Проверка конкретного аспекта
python -c "
from structurizr_utils.functions.capability import check_capability
from structurizr_utils.utils.utils import load_workspace

data = load_workspace('workspace.json')
results = check_capability('MY_SYSTEM', data, 'https://backend.example.com', 'https://structurizr.example.com', True)
for r in results:
    print(f'{r.status}: {r.message}')
"
```

## 📚 Документация

### Подробная документация по модулям:

- 📖 **[Functions](./functions/README.md)** - Функции проверки архитектуры
- 📖 **[Models](./models/README.md)** - Модели данных и API клиенты
- 📖 **[Utils](./utils/README.md)** - Вспомогательные утилиты

### Дополнительные ресурсы:

- [Structurizr DSL Documentation](https://structurizr.com/dsl)
- [C4 Model](https://c4model.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

## 🔒 Безопасность

### Аутентификация
- HMAC-SHA256 для Structurizr API
- Bearer токены для внешних сервисов
- Поддержка различных методов аутентификации

### SSL/TLS
- Используется `verify=False` для HTTPS (требует настройки)
- Рекомендуется настроить SSL сертификаты

## 🚀 Производительность

### Оптимизации
- Кэширование результатов запросов
- Параллельная обработка проверок
- Ленивая загрузка данных
- Оптимизированные HTTP клиенты

### Мониторинг
- Структурированное логгирование
- Метрики производительности
- Обработка ошибок


### Известные проблемы
- Требуется настройка SSL сертификатов
- Некоторые проверки требуют доступа к внешним сервисам
- Производительность зависит от размера архитектурных моделей

---

**Structurizr Utils** - комплексное решение для обеспечения качества архитектурных моделей и интеграции с внешними системами в рамках платформы Structurizr.