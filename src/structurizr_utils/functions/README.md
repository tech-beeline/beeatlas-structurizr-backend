# Structurizr Fitness Functions

Данная директория содержит модули для проверки корректности архитектурных моделей в нотации Structurizr DSL. Каждый модуль реализует набор fitness functions (функций пригодности) для оценки качества архитектурного описания.

## 📁 Структура директории

```
functions/
├── README.md                    # Данный файл
├── objects.py                   # Базовые классы и типы данных
├── beeatlas_objects.py          # Модели данных для BeeAtlas
├── capability.py                # Проверка технических возможностей
├── context.py                   # Проверка контекстных диаграмм
├── deployment.py                # Проверка диаграмм размещения
├── api.py                       # Проверка API и SLA
├── adr.py                       # Проверка архитектурных решений
├── technology.py                # Проверка технологий из техрадара
├── sequences.py                 # Проверка динамических диаграмм
└── container.py                 # Проверка контейнерной модели
```

## 🎯 Обзор модулей проверки

### 1. **capability.py** - Проверка технических возможностей
**Назначение**: Проверяет наличие и корректность технических возможностей (capabilities) в C4 модели продукта.

**Основные проверки:**
- `CPB.01` - Определены технические возможности продукта
- `CPB.02` - Для всех внешних интеграций определены TC
- `CPB.03` - Есть capability в Structurizr
- `CPB.04` - Опубликованные TC правильно спозиционированы в ФДМ
- `CPB.05` - Описания TC сформированны в соответствии с методикой

**Ключевые функции:**
- `check_capability()` - основная функция проверки
- `publish_capabilities()` - публикация найденных capabilities
- `load_capabilities()` - загрузка существующих capabilities

### 2. **context.py** - Проверка контекстных диаграмм
**Назначение**: Проверяет правильность моделей landscape и контекстных диаграмм системы.

**Основные проверки:**
- `CTX.01` - Создана диаграмма контекста
- `CTX.02` - Все связи на диаграмме контекста должны быть подписаны
- `CTX.03` - Все связи на диаграмме контекста должны иметь технологию взаимодействия

**Ключевые функции:**
- `check_context()` - проверка контекстных диаграмм

### 3. **deployment.py** - Проверка диаграмм размещения
**Назначение**: Проверяет корректность диаграмм развертывания системы.

**Основные проверки:**
- `DEP.01` - Наличие хотя бы одного Deployment Environment
- `DEP.02` - Наличие хотя бы одной Deployment диаграммы
- `DEP.03` - DeploymentEnvironment ссылается на мнемонику экземпляра в CMDB (TODO)
- `DEP.04` - Правильно задана макросегментация Protected/DMZ STD/NST Operations/RND (TODO)

**Ключевые функции:**
- `check_deployment()` - проверка диаграмм размещения

### 4. **api.py** - Проверка API и SLA
**Назначение**: Проверяет правильность описания API и SLA в нотации Structurizr DSL.

**Основные проверки:**
- `API.01` - У приложения есть опубликованные API
- `API.02` - Для некоторых методов определен SLA
- `API.03` - Для всех TC есть спецификация

**Ключевые функции:**
- `check_api()` - основная функция проверки API
- `ApiLoader` - класс для загрузки и парсинга API спецификаций
- `publish_system()` - публикация системы с API
- `publish_system_relations()` - публикация связей системы

**Поддерживаемые форматы API:**
- REST API (Swagger/OpenAPI JSON/YAML)
- gRPC (Protocol Buffers)
- SOAP (WSDL)

### 5. **adr.py** - Проверка архитектурных решений
**Назначение**: Проверяет наличие ADR (Architecture Decision Records) в документации.

**Основные проверки:**
- `ADR.01` - Наличие хотя бы одного ADR

**Ключевые функции:**
- `check_adr()` - проверка наличия архитектурных решений

### 6. **technology.py** - Проверка технологий из техрадара
**Назначение**: Проверяет соответствие используемых технологий техрадару.

**Основные проверки:**
- `TECH.01` - Все технологии продукта есть в техрадаре
- `TECH.02` - В продукте нет технологий в статусе HOLD
- `TECH.03` - У всех контейнеров есть технологии
- `TECH.04` - Приложение не использует протоколов в статусе hold
- `TECH.05` - У всех взаимодействий указаны протоколы из техрадара
- `TECH.06` - Технологии найденные по мониторингу продуктивной среды и Git описаны в архитектуре

**Ключевые функции:**
- `check_technology()` - основная функция проверки технологий
- `check_tr()` - проверка технологий на соответствие техрадару
- `is_https_endpoint()` - проверка использования HTTPS/TLS протоколов
- `TechStatus` - класс для хранения статуса технологий

### 7. **sequences.py** - Проверка динамических диаграмм
**Назначение**: Проверяет корректность динамических диаграмм (sequence diagrams).

**Основные проверки:**
- `SQ.01` - Для всех technical capability указаны sequence
- `SQ.02` - Все вызовы содержат HTTP запросы

**Ключевые функции:**
- `check_sequences()` - проверка динамических диаграмм
- `validate_format_with_http_request()` - проверка формата HTTP запросов
- `is_rest()` - проверка использования REST технологий

### 8. **container.py** - Проверка контейнерной модели
**Назначение**: Проверяет контейнерную модель системы в нотации Structurizr DSL.

**Основные проверки:**
- `CNT.01` - Наличие в модели контейнеров для системы
- `CNT.02` - Наличие в хотя бы одной диаграммы контейнеров
- `CNT.03` - Все вызовы между контейнерами имеют технологию
- `SEC.01` - Интеграция frontend/api gateway с IDM системой
- `GIT.01` - Наличие в модели git репозитория

**Ключевые функции:**
- `check_container()` - проверка контейнерной модели

## 🏗️ Базовые модели данных

### **objects.py**
Содержит базовые классы и типы данных для всех проверок:

- `FitnessStatus` - результат проверки (fitness assessment)
- `Assessment` - критерий оценки
- `assesment_pass()` - функция для успешной проверки
- `assesment_fail()` - функция для неуспешной проверки
- `safe_execution()` - безопасное выполнение функций

**Структура FitnessStatus:**
```python
FitnessStatus = TypedDict('FitnessStatus', {
    'system_code': str,                    # Код системы в CMDB
    'fitness_function_code': str,          # Код проверки (например, 'CPB.01')
    'assessment_date': str,                # Дата проведения проверки
    'assessment_description': str,          # Описание проверки
    'status': int,                         # Статус: 0 - успех, >0 - ошибка
    'result_details': str,                 # Детали результата
    'total_objects_count': int,             # Общее количество объектов для проверки
    'found_objects_count': int,             # Количество найденных объектов
    'found_objects': Dict[str, str]        # Словарь найденных объектов {id: description}
})
```

### **beeatlas_objects.py**
Содержит модели данных для интеграции с BeeAtlas:

- `TechnicalCapability` - техническая возможность
- `SystemPurpose` - назначение системы
- `System` - система
- `Container` - контейнер
- `Interface` - интерфейс
- `Method` - метод API
- `Capability` - возможность
- `Term` - термин
- `Glossary` - глоссарий

## 🔧 Использование

### Пример использования функции проверки:

```python
from structurizr_utils.functions.capability import check_capability
from structurizr_utils.functions.objects import safe_execution

# Безопасное выполнение проверки
results = safe_execution(
    check_capability,
    cmdb="MY_SYSTEM",
    data=structurizr_data,
    backend_url="https://backend.example.com",
    share_url="https://structurizr.example.com",
    publish=False
)

# Обработка результатов
for result in results:
    if result['status'] == 0:
        print(f"✅ {result['assessment_description']}: {result['result_details']}")
        print(f"   Найдено объектов: {result['found_objects_count']}/{result['total_objects_count']}")
    else:
        print(f"❌ {result['assessment_description']}: {result['result_details']}")
        print(f"   Найдено объектов: {result['found_objects_count']}/{result['total_objects_count']}")
        
        # Детальная информация о найденных объектах
        if result['found_objects']:
            print("   Найденные объекты:")
            for obj_id, obj_desc in result['found_objects'].items():
                print(f"     - {obj_id}: {obj_desc}")
```

### Настройка логгирования:

```python
import logging

# Настройка уровня логгирования
logging.basicConfig(level=logging.INFO)

# Для детального логгирования
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Статистика проверок

| Модуль | Количество проверок | Статус |
|--------|-------------------|--------|
| capability.py | 5 | ✅ Готово |
| context.py | 3 | ✅ Готово |
| deployment.py | 2 (4 планируется) | ✅ Частично |
| api.py | 3 | ✅ Готово |
| adr.py | 1 | ✅ Готово |
| technology.py | 6 | ✅ Готово |
| sequences.py | 2 | ✅ Готово |
| container.py | 5 | ✅ Готово |

**Всего проверок**: 27 (25 реализовано, 2 в планах)

## 🚀 Особенности реализации

### Унифицированное логгирование
Все модули используют единый подход к логгированию:
- Модульный логгер: `logger = logging.getLogger(__name__)`
- Различные уровни: DEBUG, INFO, WARNING, ERROR
- Структурированные сообщения с контекстом

### Аннотации типов
Все функции имеют полные аннотации типов:
- Параметры функций
- Возвращаемые значения
- Локальные переменные
- Импорты из `typing`

### Обработка ошибок
- Безопасное выполнение с `safe_execution()`
- Try-catch блоки для критических операций
- Логирование ошибок с контекстом

### Документация
- Подробные docstring для всех функций
- Inline комментарии для сложной логики
- Описание параметров и возвращаемых значений

### Детализированные Assessment данные
Все проверки теперь заполняют расширенные поля assessment:

**Поля assessment:**
- `total_objects_count` - общее количество объектов для проверки
- `found_objects_count` - количество найденных объектов
- `found_objects` - словарь с детальной информацией о найденных объектах

**Примеры использования по модулям:**

**capability.py:**
- CPB.01: `total_objects_count` = общее количество capabilities, `found_objects_count` = найденные capabilities
- CPB.02: `total_objects_count` = контейнеры с внешними связями, `found_objects_count` = контейнеры с capability
- CPB.03: аналогично CPB.01

**api.py:**
- API.01: `total_objects_count` = общее количество API компонентов, `found_objects_count` = интерфейсы с методами
- API.02: аналогично API.01

**technology.py:**
- TECH.01: `total_objects_count` = общее количество технологий, `found_objects_count` = технологии в техрадаре
- TECH.02: `total_objects_count` = общее количество технологий, `found_objects_count` = технологии в статусе HOLD
- TECH.03: `total_objects_count` = общее количество контейнеров, `found_objects_count` = контейнеры с технологиями
- TECH.04: `total_objects_count` = общее количество технологий, `found_objects_count` = технологии в статусе HOLD
- TECH.05: `total_objects_count` = общее количество связей, `found_objects_count` = корректные связи
- TECH.06: `total_objects_count` = технологии из мониторинга, `found_objects_count` = найденные в архитектуре

**container.py:**
- CNT.01: `total_objects_count` = общее количество контейнеров, `found_objects_count` = найденные контейнеры
- CNT.02: `total_objects_count` = общее количество диаграмм, `found_objects_count` = найденные диаграммы контейнеров
- CNT.03: `total_objects_count` = общее количество связей, `found_objects_count` = связи с технологиями
- SEC.01: `total_objects_count` = общее количество связей с IDM, `found_objects_count` = найденные связи с IDM
- GIT.01: `total_objects_count` = общее количество контейнеров, `found_objects_count` = контейнеры с git репозиторием

**context.py, deployment.py, sequences.py, adr.py:**
- Аналогично заполняют поля assessment для каждой проверки
- `found_objects` содержит ID объектов и их описания

## 🔗 Интеграции

### Внешние системы:
- **BeeAtlas** - публикация capabilities и API
- **TechRadar** - проверка технологий
- **CMDB** - идентификация систем
- **Structurizr** - источник архитектурных данных
- **БД BeeAtlas** - источник оценок описания TC

### Поддерживаемые форматы:
- **Structurizr DSL** - основной формат
- **Swagger/OpenAPI** - спецификации API
- **WSDL** - SOAP сервисы
- **Protocol Buffers** - gRPC сервисы

## 📝 Примечания

1. **TODO**: В `deployment.py` не реализованы проверки DEP.03 и DEP.04
2. **Зависимости**: Требуется доступ к внешним системам (BeeAtlas, TechRadar)
3. **Производительность**: Некоторые проверки выполняют HTTP запросы
4. **Безопасность**: Используется `verify=False` для HTTPS запросов (требует настройки)
5. **Assessment данные**: Все модули обновлены для заполнения полей `total_objects_count`, `found_objects_count`, `found_objects`
6. **Детализация**: Поле `found_objects` содержит словарь с ID объектов и их описаниями для детального анализа

## 🔄 Последние изменения

### Версия 2.1 - Добавлена проверка Git репозиториев
- ✅ Добавлена новая проверка `GIT.01` в модуль `container.py`
- ✅ Проверка наличия git репозиториев у контейнеров системы
- ✅ Обновлена статистика проверок: container.py теперь содержит 5 проверок
- ✅ Обновлена документация с описанием новой проверки GIT.01

### Версия 2.0 - Расширенные Assessment данные
- ✅ Добавлены поля `total_objects_count`, `found_objects_count`, `found_objects` во все проверки
- ✅ Обновлены все модули: `adr.py`, `api.py`, `capability.py`, `container.py`, `context.py`, `deployment.py`, `sequences.py`, `technology.py`
- ✅ Исправлена логика подсчета объектов для корректного отображения статистики
- ✅ Добавлена детальная информация о найденных объектах в `found_objects`
- ✅ Обновлена документация с примерами использования новых полей

