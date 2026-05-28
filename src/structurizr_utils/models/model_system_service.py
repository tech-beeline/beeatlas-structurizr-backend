"""
Модель для работы с API system-service v1.2.0
Управление информацией о системах
https://dashboard-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru/swagger-ui/system-service/swagger.json
"""

import os
import logging
import requests
from typing import TypedDict, Optional, Dict, Any, List, Literal
from urllib.parse import urljoin


# Настройка логгирования
logger = logging.getLogger(__name__)


# ==================== TypedDict схемы из спецификации ====================

class Method(TypedDict, total=False):
    """Метод интерфейса"""
    name: str  # Имя метода
    description: Optional[str]  # Описание метода
    rps: Optional[float]  # Максимальная нагрузка (запросов в секунду)
    latency: Optional[float]  # Максимальное время отклика (ms)
    error_rate: Optional[float]  # Максимальное количество отказов (%)
    implements: Optional[str]  # Код возможности, которую реализует метод


class Interface(TypedDict, total=False):
    """Интерфейс системы"""
    code: str  # Код интерфейса
    name: str  # Имя интерфейса
    description: Optional[str]  # Описание интерфейса
    version: Optional[str]  # Версия интерфейса
    status: Optional[str]  # Статус интерфейса
    protocol: Optional[str]  # Протокол
    implements: Optional[str]  # Код технической возможности
    specification: Optional[str]  # Ссылка на спецификацию
    methods: Optional[List[Method]]  # Методы интерфейса
    self: Optional[str]  # Ссылка на интерфейс


class Container(TypedDict, total=False):
    """Контейнер системы"""
    code: str  # Код контейнера
    name: str  # Название контейнера
    description: Optional[str]  # Описание контейнера
    version: Optional[str]  # Версия контейнера
    interfaces: Optional[List[Interface]]  # Интерфейсы контейнера


class System(TypedDict, total=False):
    """Система"""
    code: str  # Код системы в CMDB
    name: str  # Название системы
    description: Optional[str]  # Описание системы
    version: Optional[str]  # Версия системы
    author: Optional[str]  # Кто создал систему
    ea_guid: Optional[str]  # Уникальный идентификатор системы
    FQName: Optional[str]  # Полное имя системы
    status: Optional[str]  # Статус системы
    modifiedDate: Optional[str]  # Дата последнего изменения
    containers: Optional[List[Container]]  # Контейнеры системы
    links: Optional[Dict[str, str]]  # Ресурсы, связанные с системой


class SystemPurpose(TypedDict, total=False):
    """Назначение системы"""
    name: str  # Код возможности
    type: str  # Тип возможности (Domain, Capability, TechnicalCapability)
    children: Optional[List['SystemPurpose']]  # Дочерние возможности
    href: Optional[str]  # Ссылка на описание возможности


class ProcessInfo(TypedDict, total=False):
    """Информация о процессе"""
    name: str  # Название процесса
    uid: str  # Идентификатор процесса
    href: str  # Ссылка на описание процесса


class BusinessInteraction(TypedDict, total=False):
    """Шаг Е2Е процесса (Business Interaction)"""
    name: str  # Название шага
    uid: str  # Идентификатор шага
    href: str  # Ссылка на описание процесса


class Operation(TypedDict, total=False):
    """Описание метода, используемого во взаимодействии"""
    name: str  # Название метода
    uid: str  # Идентификатор метода
    interface: Optional[Dict[str, str]]  # Описание интерфейса


class Message(TypedDict, total=False):
    """Описание взаимодействия, в котором участвует система"""
    name: str  # Название взаимодействия
    operation: Optional[Operation]  # Описание метода


class SystemE2EParticipation(TypedDict, total=False):
    """Участие системы в Е2Е процессах"""
    process: ProcessInfo  # Е2Е Процесс
    bi: Optional[BusinessInteraction]  # Шаг Е2Е процесса
    message: Optional[Message]  # Описание взаимодействия
    system: Optional[Dict[str, str]]  # Информация о системе


class SystemAssessmentResult(TypedDict, total=False):
    """Результат оценки системы"""
    system_code: str  # Код системы (CMDB мнемоника)
    fitness_function_code: str  # Код выполненной проверки
    assessment_date: str  # Время проверки
    assessment_description: str  # Описание проведенной проверки
    status: int  # Статус проверки (0 - проверка прошла успешно)
    result_details: str  # Детальное описание результатов проверки


class SystemMonitoringResult(TypedDict, total=False):
    """Настройки наблюдаемости системы"""
    system_code: str  # Код системы (CMDB мнемоника)


class MethodSLA(TypedDict, total=False):
    """SLA для метода"""
    rps: str  # Трафик, запросы в минуту
    latency: str  # Максимальное время отклика, миллисекунды
    error_rate: str  # Допустимый процент ошибок
    method_name: str  # Имя метода
    interface_code: str  # Код интерфейса
    interface_uid: str  # Уникальный идентификатор интерфейса


class SystemApiMetricTemplate(TypedDict, total=False):
    """Шаблон для настройки метрик"""
    apiMetricTemplate: str  # Ссылка на шаблон получения метрик


class SystemProvidedApi(TypedDict, total=False):
    """Предоставляемый API системы"""
    uid: str  # UID интерфейса
    name: str  # Название интерфейса
    apiMetricTemplate: str  # Ссылка на шаблон для настройки метрик


# ==================== Вспомогательные типы ====================

SystemQueryLevel = Literal["systems", "containers", "interfaces", "methods"]


class SystemServiceConfig(TypedDict, total=False):
    """Конфигурация для system-service API"""
    base_url: str
    timeout: int
    headers: Dict[str, str]


class SystemServiceResponse(TypedDict, total=False):
    """Базовый ответ от system-service API"""
    status_code: int
    data: Any
    message: str
    success: bool


class SystemServiceError(TypedDict):
    """Ошибка от system-service API"""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]]


class SystemServiceClient:
    """
    Клиент для работы с system-service API v1.2.0
    Управление информацией о системах
    
    Поддерживает:
    - Передачу URL через параметр или переменную окружения
    - Логгирование всех запросов
    - Обработку ошибок с raise_for_status
    - Настраиваемые таймауты и заголовки
    - Все эндпоинты из спецификации API
    """
    
    def __init__(
        self, 
        base_url: Optional[str] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL API. Если не указан, берется из переменной окружения SYSTEM_SERVICE_URL
            timeout: Таймаут запросов в секундах
            headers: Дополнительные заголовки для запросов
        """
        self.base_url = base_url or os.getenv('SYSTEM_SERVICE_URL', 
            'https://dashboard-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru')
        
        if not self.base_url:
            raise ValueError("Base URL должен быть указан либо через параметр, либо через переменную окружения SYSTEM_SERVICE_URL")
        
        # Убираем trailing slash если есть
        self.base_url = self.base_url.rstrip('/')
        
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            **(headers or {})
        }
        
        logger.info(f"SystemServiceClient v1.2.0 инициализирован с base_url: {self.base_url}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SystemServiceResponse:
        """
        Выполнение HTTP запроса
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Конечная точка API
            data: Данные для отправки в теле запроса
            params: Параметры запроса
            **kwargs: Дополнительные параметры для requests
            
        Returns:
            SystemServiceResponse: Ответ от API
            
        Raises:
            requests.RequestException: При ошибках HTTP запроса
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        request_kwargs = {
            'timeout': self.timeout,
            'headers': self.headers,
            **kwargs
        }
        
        if data is not None:
            request_kwargs['json'] = data
        
        if params is not None:
            request_kwargs['params'] = params
        
        logger.info(f"Выполнение {method} запроса к {url}")
        if data:
            logger.debug(f"Данные запроса: {data}")
        if params:
            logger.debug(f"Параметры запроса: {params}")
        
        try:
            response = requests.request(method, url, **request_kwargs, verify=False)
            
            # Логируем статус ответа
            logger.info(f"Получен ответ со статусом {response.status_code}")
            
            # Проверяем статус ответа
            response.raise_for_status()
            
            # Пытаемся распарсить JSON
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text
            
            return SystemServiceResponse(
                status_code=response.status_code,
                data=response_data,
                message="Success",
                success=True
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при выполнении запроса к {url}: {str(e)}")
            
            # Пытаемся извлечь детали ошибки из ответа
            error_details = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                except ValueError:
                    error_details = {"raw_response": e.response.text}
            
            return SystemServiceResponse(
                status_code=getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0,
                data=None,
                message=str(e),
                success=False
            )
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> SystemServiceResponse:
        """GET запрос"""
        return self._make_request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> SystemServiceResponse:
        """POST запрос"""
        return self._make_request('POST', endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> SystemServiceResponse:
        """PUT запрос"""
        return self._make_request('PUT', endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> SystemServiceResponse:
        """DELETE запрос"""
        return self._make_request('DELETE', endpoint, **kwargs)
    
    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> SystemServiceResponse:
        """PATCH запрос"""
        return self._make_request('PATCH', endpoint, data=data, **kwargs)
    
    # ==================== API методы согласно спецификации ====================
    
    def search_systems(self, terms: str) -> SystemServiceResponse:
        """
        Поиск системы
        
        Args:
            terms: Поисковая строка
            
        Returns:
            SystemServiceResponse: Список найденных систем
        """
        return self.get('/api/v4/system-search', params={'terms': terms})
    
    def get_systems(
        self, 
        level: Optional[SystemQueryLevel] = None,
        add_removed: Optional[bool] = None
    ) -> SystemServiceResponse:
        """
        Получение списка систем
        
        Args:
            level: Уровень детализации (systems, containers, interfaces, methods)
            add_removed: Загружать информацию об удаленных объектах
            
        Returns:
            SystemServiceResponse: Список систем
        """
        params = {}
        if level is not None:
            params['level'] = level
        if add_removed is not None:
            params['add-removed'] = add_removed
        
        return self.get('/api/v4/systems', params=params)
    
    def get_system(
        self, 
        code: str,
        level: Optional[SystemQueryLevel] = None,
        add_removed: Optional[bool] = None
    ) -> SystemServiceResponse:
        """
        Получение описания системы по ее коду
        
        Args:
            code: Код системы
            level: Уровень детализации
            add_removed: Загружать информацию об удаленных объектах
            
        Returns:
            SystemServiceResponse: Описание системы
        """
        params = {}
        if level is not None:
            params['level'] = level
        if add_removed is not None:
            params['add-removed'] = add_removed
        
        return self.get(f'/api/v4/systems/{code}', params=params)
    
    def update_system(self, code: str, system_data: System) -> SystemServiceResponse:
        """
        Обновление описания системы
        
        Args:
            code: Код системы
            system_data: Данные системы для обновления
            
        Returns:
            SystemServiceResponse: Обновленное описание системы
        """
        return self.put(f'/api/v4/systems/{code}', data=system_data)
    
    def get_system_purpose(self, code: str) -> SystemServiceResponse:
        """
        Получение назначения системы
        
        Args:
            code: Код системы
            
        Returns:
            SystemServiceResponse: Назначение системы
        """
        return self.get(f'/api/v4/systems/{code}/purpose')
    
    def get_system_e2e(self, code: str) -> SystemServiceResponse:
        """
        Получение информации о том, в каких Е2Е процессах участвует система
        
        Args:
            code: Код системы
            
        Returns:
            SystemServiceResponse: Информация об участии в Е2Е процессах
        """
        return self.get(f'/api/v4/systems/{code}/e2e')
    
    def get_system_assessments(self, code: str) -> SystemServiceResponse:
        """
        Получение актуальной оценки системы
        
        Args:
            code: Код системы
            
        Returns:
            SystemServiceResponse: Результаты оценки системы
        """
        return self.get(f'/api/v4/systems/{code}/assessments')
    
    def create_system_assessment(self, code: str, assessment: SystemAssessmentResult) -> SystemServiceResponse:
        """
        Публикация результата оценки системы архитектурной фитнес-функцией
        
        Args:
            code: Код системы
            assessment: Результат оценки системы
            
        Returns:
            SystemServiceResponse: Опубликованный результат оценки
        """
        return self.post(f'/api/v4/systems/{code}/assessments', data=assessment)
    
    def get_system_monitoring(self, code: str) -> SystemServiceResponse:
        """
        Получение настроек наблюдаемости системы
        
        Args:
            code: Код системы
            
        Returns:
            SystemServiceResponse: Настройки наблюдаемости
        """
        return self.get(f'/api/v4/systems/{code}/monitoring')
    
    def update_system_monitoring(self, code: str, template: SystemApiMetricTemplate) -> SystemServiceResponse:
        """
        Изменение ссылки на шаблон для настройки метрик
        
        Args:
            code: Код системы
            template: Шаблон для настройки метрик
            
        Returns:
            SystemServiceResponse: Результат обновления
        """
        return self.post(f'/api/v4/systems/{code}/monitoring', data=template)
    
    def get_system_provided_apis(self, code: str) -> SystemServiceResponse:
        """
        Получение предоставляемых API системы
        
        Args:
            code: Код системы
            
        Returns:
            SystemServiceResponse: Список предоставляемых API
        """
        return self.get(f'/api/v4/systems/{code}/p-api')
    
    def set_method_sla(self, sla: MethodSLA) -> SystemServiceResponse:
        """
        Установка SLA для метода
        
        Args:
            sla: SLA для метода
            
        Returns:
            SystemServiceResponse: Установленный SLA
        """
        return self.post('/api/v4/methods-sla', data=sla)


# Пример использования
if __name__ == "__main__":
    # Настройка логгирования для примера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создание клиента
    client = SystemServiceClient()
    
    # Примеры использования API
    try:
        # Поиск систем
        print("=== Поиск систем ===")
        response = client.search_systems("test")
        if response['success']:
            print(f"Найдено систем: {len(response['data']) if isinstance(response['data'], list) else 'N/A'}")
        else:
            print(f"Ошибка поиска: {response['message']}")
        
        # Получение списка систем
        print("\n=== Получение списка систем ===")
        response = client.get_systems(level="systems")
        if response['success']:
            print(f"Получено систем: {len(response['data']) if isinstance(response['data'], list) else 'N/A'}")
        else:
            print(f"Ошибка получения списка: {response['message']}")
        
        # Получение конкретной системы
        print("\n=== Получение системы по коду ===")
        response = client.get_system("SYSTEM_CODE", level="containers")
        if response['success']:
            system_data = response['data']
            print(f"Система: {system_data.get('name', 'N/A')} ({system_data.get('code', 'N/A')})")
        else:
            print(f"Ошибка получения системы: {response['message']}")
            
    except Exception as e:
        print(f"Критическая ошибка: {e}")
