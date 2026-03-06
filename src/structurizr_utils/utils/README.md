# Structurizr Utils - Вспомогательные утилиты

Данная директория содержит вспомогательные утилиты для работы с Structurizr API и общие функции обработки данных.

## 📁 Структура директории

```
utils/
├── README.md           # Данный файл
├── structurizr.py      # Утилиты для работы с Structurizr API
└── utils.py           # Общие утилиты
```

## 🎯 Обзор модулей

### 1. **structurizr.py** - Structurizr API утилиты
**Назначение**: Содержит функции для аутентификации и работы с Structurizr API.

**Основные функции:**
- `_number_once()` - генерация временной метки в миллисекундах
- `_hmac_hex()` - создание HMAC-SHA256 хеша
- `_md5()` - создание MD5 хеша
- `_base64_str()` - кодирование в base64
- `_message_digest()` - создание digest для аутентификации

**Основные классы:**
- `Workspace` - класс для представления workspace в Structurizr

**Ключевые методы Workspace:**
- `get_workspace()` - получение workspace по ID
- `put_workspace()` - обновление workspace
- `delete_workspace()` - удаление workspace
- `get_workspace_share()` - получение ссылки на workspace

**Особенности:**
- HMAC-SHA256 аутентификация
- Поддержка различных HTTP методов
- Обработка ошибок API

### 2. **utils.py** - Общие утилиты
**Назначение**: Содержит общие функции для работы с данными и обработки ошибок.

**Основные функции:**
- `get_workspace_cmdb()` - извлечение CMDB кода из данных workspace
- `load_workspace()` - загрузка данных workspace из JSON файла
- `run_structurizr_cli()` - запуск Structurizr CLI

**Основные классы:**
- `StructurizrError` - исключение для ошибок Structurizr

**Особенности:**
- Обработка JSON файлов
- Запуск внешних команд
- Извлечение метаданных из workspace

## 🔧 Использование

### Пример работы с Structurizr API:

```python
from structurizr_utils.utils.structurizr import Workspace

# Инициализация workspace
workspace = Workspace(
    api_url="https://structurizr.example.com",
    api_key="your_api_key",
    api_secret="your_api_secret"
)

# Получение workspace
data = workspace.get_workspace(workspace_id=12345)

# Обновление workspace
workspace.put_workspace(workspace_id=12345, content="workspace content")

# Получение ссылки на workspace
share_url = workspace.get_workspace_share(workspace_id=12345)
```

### Пример работы с общими утилитами:

```python
from structurizr_utils.utils.utils import (
    load_workspace, 
    get_workspace_cmdb,
    StructurizrError
)

try:
    # Загрузка workspace из файла
    data = load_workspace("workspace.json")
    
    # Извлечение CMDB кода
    cmdb = get_workspace_cmdb(data)
    print(f"CMDB код: {cmdb}")
    
except StructurizrError as e:
    print(f"Ошибка Structurizr: {e}")
```

### Пример запуска Structurizr CLI:

```python
from structurizr_utils.utils.utils import run_structurizr_cli

# Запуск CLI команды
result = run_structurizr_cli(
    command=["push", "-workspace", "12345", "-file", "workspace.dsl"]
)

if result.returncode == 0:
    print("Команда выполнена успешно")
else:
    print(f"Ошибка: {result.stderr}")
```

## 🔐 Аутентификация

### HMAC-SHA256 аутентификация

Structurizr использует HMAC-SHA256 для аутентификации API запросов:

```python
# Создание digest для аутентификации
digest = _message_digest(
    http_verb="GET",
    uri_path="/api/workspace/12345",
    definition_md5="hash_of_workspace_content",
    content_type="application/json",
    nonce="timestamp"
)

# Создание HMAC подписи
signature = _hmac_hex(secret="your_api_secret", digest=digest)
```

### Заголовки аутентификации

```python
headers = {
    "Authorization": f"HMAC-SHA256 Username={api_key}, DateTime={nonce}, Nonce={nonce}, Digest={signature}",
    "Content-Type": "application/json"
}
```

## 📊 Статистика модулей

| Модуль | Функций | Классов | Строк кода | Основное назначение |
|--------|---------|---------|------------|-------------------|
| **structurizr.py** | 8+ | 1 | 130+ | Structurizr API |
| **utils.py** | 3+ | 1 | 70+ | Общие утилиты |
| **Всего** | **11+** | **2** | **200+** | **Вспомогательные функции** |

## 🌐 Интеграции

### Structurizr API
- **REST API** - основной интерфейс
- **HMAC аутентификация** - безопасность
- **JSON формат** - обмен данными
- **CLI интеграция** - командная строка

### Поддерживаемые операции
- **GET** - получение данных
- **PUT** - обновление данных
- **DELETE** - удаление данных
- **POST** - создание данных

## 🚀 Особенности реализации

### Обработка ошибок
- Специализированные исключения
- Детальные сообщения об ошибках
- Логгирование ошибок

### Производительность
- Кэширование результатов
- Оптимизированные HTTP запросы
- Асинхронная обработка где возможно

### Безопасность
- HMAC-SHA256 аутентификация
- Валидация входных данных
- Защита от инъекций

## 📝 Конфигурация

### Переменные окружения

```bash
# Structurizr API
STRUCTURIZR_API_URL=https://structurizr.example.com
STRUCTURIZR_API_KEY=your_api_key
STRUCTURIZR_API_SECRET=your_api_secret

# CLI настройки
STRUCTURIZR_CLI_PATH=/usr/local/bin/structurizr
```

### Настройка аутентификации

```python
import os

# Получение настроек из переменных окружения
api_url = os.getenv("STRUCTURIZR_API_URL")
api_key = os.getenv("STRUCTURIZR_API_KEY")
api_secret = os.getenv("STRUCTURIZR_API_SECRET")

# Инициализация workspace
workspace = Workspace(
    api_url=api_url,
    api_key=api_key,
    api_secret=api_secret
)
```

## 🧪 Тестирование

### Примеры тестов

```python
import unittest
from structurizr_utils.utils.structurizr import Workspace
from structurizr_utils.utils.utils import get_workspace_cmdb

class TestStructurizrUtils(unittest.TestCase):
    
    def test_workspace_initialization(self):
        workspace = Workspace(
            api_url="https://test.example.com",
            api_key="test_key",
            api_secret="test_secret"
        )
        self.assertEqual(workspace.api_url, "https://test.example.com")
    
    def test_cmdb_extraction(self):
        data = {
            "model": {
                "properties": {
                    "workspace_cmdb": "TEST_SYSTEM"
                }
            }
        }
        cmdb = get_workspace_cmdb(data)
        self.assertEqual(cmdb, "TEST_SYSTEM")
```

## 📚 Дополнительные ресурсы

### Документация
- [Structurizr API Documentation](https://structurizr.com/help/api)
- [Structurizr CLI Documentation](https://structurizr.com/help/cli)
- [HMAC Authentication](https://en.wikipedia.org/wiki/HMAC)

### Связанные модули
- **[functions/](../functions/README.md)** - использует утилиты для проверок
- **[models/](../models/README.md)** - использует утилиты для API клиентов



## 📞 Поддержка

### Известные ограничения
- Требуется настройка SSL сертификатов для HTTPS
- CLI команды зависят от установленного Structurizr CLI
- Производительность зависит от размера workspace

### Рекомендации
- Используйте кэширование для часто запрашиваемых данных
- Обрабатывайте ошибки сети и таймауты
- Логируйте все операции для отладки
