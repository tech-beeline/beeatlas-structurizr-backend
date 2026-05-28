# Structurizr Models

Данная директория содержит модели данных и клиенты для интеграции с различными внешними системами в рамках архитектурной платформы Structurizr.

## 📁 Структура директории

```
models/
├── README.md                    # Данный файл
├── __init__.py                  # Инициализация модуля
├── models_product.py            # Модели для работы с продуктами и API
├── model_system_service.py      # 🆕 Клиент для System Service API v1.2.0
├── model_techradar.py           # Клиент и модели для TechRadar
├── model_terraform.py           # Модели для Terraform ресурсов
├── model_graph.py               # Клиент для Architect Graph Service
├── model_documents.py           # Клиент для работы с документами
├── model_camunda.py             # Клиент для Camunda BPM
├── model_arch_patterns.py      # Модели архитектурных паттернов
├── model_observability.py       # Клиент для Observability сервиса
├── model_rule_compiler.py       # Клиент для Rule Compiler сервиса
├── model_vega_vps.py           # Модели для Vega VPS API
├── models_workspace.py         # Модели для workspace данных
├── database_schema.dbml         # 📊 [DBML схема базы данных](./DBML_SCHEMA_README.md)
├── entity_relationships.dbml    # 🔗 Диаграмма связей сущностей
└── DBML_SCHEMA_README.md       # 📖 Документация DBML схем
```

## 🎯 Обзор модулей

### 1. **models_product.py** - Модели продуктов и API
**Назначение**: Содержит модели данных для работы с продуктами и их API в системе BeeAtlas.

**Основные модели:**
- `ProductDTO` - модель продукта
- `InterfaceDTO` - модель интерфейса API
- `MethodDTO` - модель метода API
- `SlaDTO` / `SlaV2DTO` - модели SLA
- `ParameterDTO` - модель параметра
- `ApiSecretDTO` - модель API секрета

**Ключевые функции:**
- `put_product_relations()` - публикация связей продукта
- `get_product_relations()` - получение связей продукта
- `get_product_by_code()` - получение продукта по коду

**Интеграция**: BeeAtlas Products API

### 2. **model_system_service.py** - System Service API v1.2.0 🆕
**Назначение**: Клиент для работы с System Service API - управление информацией о системах.

**Основные классы:**
- `SystemServiceClient` - основной клиент для работы с API
- `System` - модель системы
- `Container` - модель контейнера системы
- `Interface` - модель интерфейса системы
- `Method` - модель метода интерфейса
- `SystemPurpose` - модель назначения системы
- `SystemAssessmentResult` - модель результата оценки системы
- `MethodSLA` - модель SLA для метода

**Ключевые методы:**
- `search_systems()` - поиск систем
- `get_systems()` - получение списка систем
- `get_system()` - получение системы по коду
- `update_system()` - обновление системы
- `get_system_purpose()` - получение назначения системы
- `get_system_e2e()` - участие в Е2Е процессах
- `get_system_assessments()` - получение оценок системы
- `create_system_assessment()` - создание оценки системы
- `set_method_sla()` - установка SLA для метода

**Особенности:**
- Полная поддержка API v1.2.0
- Типизированные методы для всех операций
- Поддержка уровней детализации (systems, containers, interfaces, methods)
- Безопасная обработка ошибок с raise_for_status
- Логгирование всех запросов
- Поддержка переменных окружения для конфигурации

**Интеграция**: System Service API v1.2.0

### 3. **model_techradar.py** - TechRadar клиент
**Назначение**: Клиент для работы с TechRadar - системой управления технологиями.

**Основные классы:**
- `TechradarClient` - основной клиент для работы с API
- `TechRadarTechnology` - модель технологии
- `TechRadarCategory` - модель категории
- `TechRadarSector` - модель сектора
- `TechRadarRing` - модель кольца (Adopt, Trial, Assess, Hold)

**Ключевые методы:**
- `get_all_tech()` - получение всех технологий
- `get_product_tech()` - получение технологий продукта
- `get_tech_by_id()` - получение технологии по ID

**Интеграция**: TechRadar Backend API

### 4. **model_terraform.py** - Terraform модели
**Назначение**: Модели для работы с Terraform ресурсами и их валидации.

**Основные модели:**
- `ResourceBase` - базовая модель ресурса
- `Vm` - модель виртуальной машины
- `Database` - модель базы данных
- `LoadBalancer` - модель балансировщика нагрузки
- `Network` - модель сети
- `Storage` - модель хранилища

**Ключевые функции:**
- `check_errors()` - валидация параметров ресурса
- `parse()` - парсинг параметров ресурса

**Особенности:**
- Валидация обязательных параметров
- Поддержка различных типов ресурсов
- Проверка корректности значений

### 5. **model_graph.py** - Architect Graph Service
**Назначение**: Клиент для работы с Architect Graph Service.

**Основные классы:**
- `GraphService` - сервис для работы с графами

**Ключевые методы:**
- `global_graph()` - получение глобального графа
- `local_graph()` - получение локального графа
- `graph_by_elements()` - получение графа по элементам

**Интеграция**: Architect Graph Service API

### 6. **model_documents.py** - Документы
**Назначение**: Клиент для работы с системой документов.

**Ключевые функции:**
- `get_document()` - получение документа по ID
- `upload_file()` - загрузка файла
- `delete_document()` - удаление документа

**Интеграция**: Documents Service API

### 7. **model_camunda.py** - Camunda BPM
**Назначение**: Клиент для работы с Camunda BPM системой.

**Ключевые функции:**
- `get_bpm_process_status()` - получение статуса процесса
- `start_camunda_process()` - запуск процесса Camunda

**Интеграция**: Camunda BPM API

### 8. **model_arch_patterns.py** - Архитектурные паттерны
**Назначение**: Модели для работы с архитектурными паттернами.

**Основные модели:**
- `ArchitecturePattern` - модель архитектурного паттерна
- `ArchitecturePatterns` - коллекция паттернов

**Ключевые функции:**
- `load_patterns_from_json()` - загрузка паттернов из JSON

### 9. **model_observability.py** - Observability
**Назначение**: Клиент для публикации дашбордов наблюдаемости.

**Основные классы:**
- `Observability` - клиент для работы с observability

**Ключевые методы:**
- `publish_dashboard()` - публикация дашборда

**Интеграция**: Observability Service

### 10. **model_rule_compiler.py** - Rule Compiler
**Назначение**: Клиент для компиляции правил в Cypher запросы.

**Ключевые функции:**
- `get_cypher_query()` - компиляция правила в Cypher запрос

**Интеграция**: Rule Compiler Service

### 11. **model_vega_vps.py** - Vega VPS
**Назначение**: Модели для работы с Vega VPS API.

**Основные модели:**
- `Address` - модель IP-адреса
- `Server` - модель сервера
- `Volume` - модель тома
- `Network` - модель сети
- `Error` - модель ошибки

**Особенности:**
- Полная модель VPS инфраструктуры
- Поддержка создания, обновления и удаления ресурсов
- Валидация данных через Pydantic

**Интеграция**: Vega VPS API

### 12. **models_workspace.py** - Workspace модели
**Назначение**: Модели для работы с workspace данными.

**Основные модели:**
- `RestProduct` - модель продукта для REST API
- `RestWorkspace` - модель workspace для REST API

## 🔧 Использование

### Пример использования TechRadar клиента:

```python
from structurizr_utils.models.model_techradar import TechradarClient

# Инициализация клиента
client = TechradarClient(
    base_url="https://techradar.example.com",
    auth_token="your_token"
)

# Получение всех технологий
technologies = client.get_all_tech(user_roles="admin")

# Получение технологий продукта
product_tech = client.get_product_tech(user_roles="admin")
```

### Пример использования System Service клиента:

```python
from structurizr_utils.models.model_system_service import SystemServiceClient

# Инициализация клиента
client = SystemServiceClient()

# Поиск систем
response = client.search_systems("test")
if response['success']:
    systems = response['data']
    print(f"Найдено систем: {len(systems)}")

# Получение списка систем с детализацией
response = client.get_systems(level="interfaces")
if response['success']:
    for system in response['data']:
        print(f"Система: {system['name']} ({system['code']})")

# Получение конкретной системы
response = client.get_system("SYSTEM_CODE", level="methods")
if response['success']:
    system_data = response['data']
    print(f"Система: {system_data['name']}")

# Создание оценки системы
assessment = {
    "system_code": "SYSTEM_CODE",
    "fitness_function_code": "TEST-FUNC",
    "assessment_date": "2024-01-01T00:00:00Z",
    "assessment_description": "Описание оценки",
    "status": 0,
    "result_details": "Детали результата"
}
response = client.create_system_assessment("SYSTEM_CODE", assessment)
```

### Пример использования Product моделей:

```python
from structurizr_utils.models.models_product import (
    ProductRelationsNewRequestDTO,
    ProductRelationNewDTO,
    InterfaceDTO,
    MethodDTO,
    put_product_relations
)

# Создание модели продукта
product_relations = ProductRelationsNewRequestDTO(
    relations=[
        ProductRelationNewDTO(
            code="my-container",
            name="My Container",
            interfaces=[
                InterfaceDTO(
                    code="my-api",
                    name="My API",
                    methods=[
                        MethodDTO(
                            name="GET /users",
                            description="Get users",
                            capabilityCode="USER_MGMT"
                        )
                    ]
                )
            ]
        )
    ]
)

# Публикация связей
put_product_relations(cmdb="MY_SYSTEM", relations=product_relations)
```

### Пример использования Terraform моделей:

```python
from structurizr_utils.models.model_terraform import Vm

# Создание VM ресурса
vm = Vm()
properties = {
    "flavor": "small",
    "image": "ubuntu-20.04",
    "volume_size": "20"
}

# Валидация параметров
errors = vm.check_errors(properties, "my-vm", 1, "region1", "project1")
if errors:
    print(f"Validation errors: {errors}")

# Парсинг параметров
vm.parse(properties, "my-vm", 1, "region1", "project1")
```

## 🌐 Интеграции

### Внешние системы:
- **BeeAtlas Products** - управление продуктами и API
- **System Service** - управление информацией о системах (v1.2.0) 🆕
- **TechRadar** - управление технологиями
- **Terraform** - управление инфраструктурой
- **Camunda BPM** - управление бизнес-процессами
- **Documents Service** - управление документами
- **Graph Service** - работа с архитектурными графами
- **Observability** - мониторинг и наблюдаемость
- **Rule Compiler** - компиляция правил
- **Vega VPS** - управление виртуальными серверами

### Поддерживаемые форматы:
- **JSON** - основной формат обмена данными
- **Pydantic** - валидация и сериализация
- **REST API** - HTTP клиенты для всех сервисов
- **Multipart** - загрузка файлов

## 📊 Статистика моделей

| Модуль | Количество моделей | Основное назначение |
|--------|-------------------|-------------------|
| models_product.py | 15+ | Продукты и API |
| model_system_service.py | 15+ | 🆕 Управление системами |
| model_techradar.py | 10+ | Технологии |
| model_terraform.py | 8+ | Инфраструктура |
| model_graph.py | 3+ | Графы |
| model_documents.py | 5+ | Документы |
| model_camunda.py | 3+ | BPM процессы |
| model_arch_patterns.py | 2+ | Паттерны |
| model_observability.py | 1+ | Наблюдаемость |
| model_rule_compiler.py | 1+ | Компилятор правил |
| model_vega_vps.py | 20+ | VPS инфраструктура |
| models_workspace.py | 2+ | Workspace |

**Всего моделей**: 85+ моделей данных

## 🚀 Особенности реализации

### Pydantic модели
Большинство моделей используют Pydantic для:
- Валидации данных
- Сериализации/десериализации
- Автодополнения в IDE
- Документации API

### TypedDict модели
Некоторые модели (например, System Service API) используют TypedDict для:
- Легковесной типизации
- Совместимости с JSON API
- Гибкости при работе с внешними API
- Производительности при больших объемах данных

### HTTP клиенты
- Единообразный подход к HTTP запросам
- Обработка ошибок через HTTPException
- Поддержка аутентификации
- Retry механизмы где необходимо

### Конфигурация
- Использование переменных окружения для URL
- Централизованная конфигурация
- Поддержка различных окружений

### Логгирование
- Структурированное логгирование
- Различные уровни детализации
- Контекстная информация

## 📊 DBML Схемы базы данных

### Схемы данных
- **📊 [database_schema.dbml](./database_schema.dbml)** - Полная схема базы данных со всеми таблицами
- **🔗 [entity_relationships.dbml](./entity_relationships.dbml)** - Диаграмма связей между основными сущностями
- **📖 [DBML_SCHEMA_README.md](./DBML_SCHEMA_README.md)** - Подробная документация DBML схем

### Особенности схемы:
- **35+ таблиц** для всех модулей системы
- **50+ связей** между сущностями
- **PostgreSQL** как основная СУБД
- **JSONB поля** для гибкого хранения параметров
- **Каскадное удаление** для связанных данных
- **Уникальные индексы** для предотвращения дублирования

### Использование:
```bash
# Генерация SQL скрипта
dbml2sql database_schema.dbml --postgres -o schema.sql

# Просмотр схемы онлайн
# Откройте database_schema.dbml в dbdiagram.io
```

## 📝 Примечания

1. **Безопасность**: Используется `verify=False` для HTTPS (требует настройки SSL)
2. **Аутентификация**: Поддержка различных методов аутентификации
3. **Производительность**: Кэширование где возможно
4. **Обработка ошибок**: Единообразная обработка через HTTPException
5. **DBML схемы**: Документирование структуры базы данных

## 🔗 Связанные модули

- **functions/** - использует модели для проверок
- **utils/** - вспомогательные утилиты
- **main** - точка входа приложения

