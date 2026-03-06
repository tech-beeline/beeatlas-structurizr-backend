"""
Модель для работы с Capability API
Управление бизнес и техническими возможностями
https://capability-backend-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru
"""

import os
import logging
import requests
from typing import TypedDict, Optional, Dict, Any, List, Literal
from urllib.parse import urljoin


# Настройка логгирования
logger = logging.getLogger(__name__)


# ==================== TypedDict схемы из спецификации ====================

class BCParentDTO(TypedDict, total=False):
    """Родительская бизнес-возможность"""
    author: str
    code: str
    createdDate: str
    description: str
    hasChildren: bool
    id: int
    isDomain: bool
    link: str
    name: str
    status: str
    updatedDate: str


class BusinessCapabilityDTO(TypedDict, total=False):
    """Бизнес-возможность"""
    author: str
    code: str
    createdDate: str
    description: str
    hasChildren: bool
    id: int
    isDomain: bool
    link: str
    name: str
    owner: str
    parents: str
    status: str


class BusinessCapabilityShortDTO(TypedDict, total=False):
    """Краткая информация о бизнес-возможности"""
    author: str
    code: str
    createdDate: str
    deletedDate: str
    description: str
    hasChildren: bool
    id: int
    isDomain: bool
    link: str
    name: str
    owner: str
    parent: BCParentDTO
    updatedDate: str


class BusinessCapabilityCriteriaDTO(TypedDict, total=False):
    """Критерий оценки бизнес-возможности"""
    comment: str
    criterion_id: int
    grade: int
    value: int


class BusinessCapabilityTreeDTO(TypedDict, total=False):
    """Дерево бизнес-возможностей"""
    author: str
    children: List['BusinessCapabilityTreeDTO']
    code: str
    createdDate: str
    criteria: List[BusinessCapabilityCriteriaDTO]
    description: str
    id: int
    isDomain: bool
    link: str
    name: str
    owner: str
    parentId: int
    status: str
    updatedDate: str


class BusinessCapabilityTreeInfoDTO(TypedDict, total=False):
    """Информация о родителе в дереве"""
    author: str
    code: str
    createdDate: str
    criteria: List[BusinessCapabilityCriteriaDTO]
    description: str
    id: int
    isDomain: bool
    link: str
    name: str
    owner: str
    parentId: int
    status: str
    updatedDate: str


class BusinessCapabilityTreeCustomDTO(TypedDict, total=False):
    """Кастомное дерево бизнес-возможностей"""
    author: str
    children: List[BusinessCapabilityTreeDTO]
    code: str
    createdDate: str
    criteria: List[BusinessCapabilityCriteriaDTO]
    description: str
    id: int
    isDomain: bool
    link: str
    name: str
    owner: str
    parent: List[BusinessCapabilityTreeInfoDTO]
    parentId: int
    status: str
    updatedDate: str


class BusinessCapabilityChildrenDTO(TypedDict, total=False):
    """Дочерние возможности"""
    businessCapabilities: List[BusinessCapabilityDTO]
    techCapabilities: List['TechCapabilityShortDTO']


class BusinessCapabilityChildrenDTOV2(TypedDict, total=False):
    """Дочерние возможности V2"""
    businessCapabilities: List[BusinessCapabilityDTO]
    techCapabilities: List['TechCapabilityShortDTOV2']


class BusinessCapabilityChildrenIdsDTO(TypedDict, total=False):
    """ID дочерних возможностей"""
    businessCapability: List[int]
    techCapability: List[int]


class CapabilityParentDTO(TypedDict, total=False):
    """Родительские возможности"""
    parents: List[int]


class TechCapabilityShortDTO(TypedDict, total=False):
    """Краткая информация о технической возможности"""
    author: str
    code: str
    createdDate: str
    deletedDate: str
    description: str
    id: int
    link: str
    name: str
    owner: str
    systemId: int
    type: str
    updatedDate: str


class TechCapabilityShortDTOV2(TypedDict, total=False):
    """Краткая информация о технической возможности V2"""
    author: str
    code: str
    createdDate: str
    description: str
    id: int
    link: str
    name: str
    owner: str
    product: 'GetProductsByIdsDTO'
    type: str
    updatedDate: str


class TechCapabilityDTO(TypedDict, total=False):
    """Техническая возможность"""
    author: str
    code: str
    createdDate: str
    deletedDate: str
    description: str
    id: int
    link: str
    name: str
    owner: str
    parents: List[BCParentDTO]
    systemId: int
    updatedDate: str


class CriteriaDTO(TypedDict, total=False):
    """Критерий оценки"""
    comment: str
    criteria_id: int
    grade: int
    value: int


class CapabilityDTO(TypedDict, total=False):
    """Возможность"""
    author: str
    code: str
    createdDate: str
    criteria: List[CriteriaDTO]
    description: str
    id: int
    isDomain: bool
    link: str
    name: str
    owner: str
    parentId: int
    responsibilityProductId: int
    status: str
    updatedDate: str


class ParentDTO(TypedDict, total=False):
    """Родитель"""
    code: str
    id: int
    name: str


class ParentOrMutableDTO(TypedDict, total=False):
    """Родитель или изменяемый объект"""
    code: str
    id: int
    name: str


class GetProductsByIdsDTO(TypedDict, total=False):
    """Информация о продукте"""
    alias: str
    id: int
    name: str
    struturizrURL: str


class PutBusinessCapabilityDTO(TypedDict, total=False):
    """DTO для создания/обновления бизнес-возможности"""
    author: str
    code: str
    description: str
    domain: bool
    isDomain: bool
    link: str
    name: str
    owner: str
    parent: str
    status: str


class PostBusinessCapabilityDTO(TypedDict, total=False):
    """DTO для создания бизнес-возможности"""
    author: str
    code: str
    createdDate: str
    description: str
    isDomain: bool
    link: str
    modifiedDate: str
    name: str
    owner: str
    parent: str
    status: str


class PutTechCapabilityDTO(TypedDict, total=False):
    """DTO для создания/обновления технической возможности"""
    author: str
    code: str
    description: str
    link: str
    name: str
    owner: str
    parents: List[str]
    status: str
    targetSystemCode: str


class PostTechCapabilityDTO(TypedDict, total=False):
    """DTO для создания технической возможности"""
    author: str
    code: str
    description: str
    link: str
    name: str
    owner: str
    parents: List[str]
    status: str
    targetSystemCode: str


class BusinessCapabilityOrderRequestDTO(TypedDict, total=False):
    """Запрос на публикацию каталога"""
    comment: str
    description: str
    mutableBcId: int
    name: str
    owner: str
    parentId: int


class BusinessCapabilityOrderDraftRequestDTO(TypedDict, total=False):
    """Запрос на публикацию черновика"""
    description: str
    mutableBcId: int
    name: str
    owner: str
    parentId: int


class BusinessCapabilityOrderDraftResponseDTO(TypedDict, total=False):
    """Ответ с черновиком каталога"""
    author: str
    code: str
    createdDate: str
    description: str
    id: int
    mutable: ParentOrMutableDTO
    name: str
    owner: str
    parent: ParentOrMutableDTO
    updateDate: str


class BusinessCapabilityOrderPatchRequestDTO(TypedDict, total=False):
    """Запрос на обновление каталога"""
    comment: str
    description: str
    name: str
    owner: str
    parentId: int


class BusinessCapabilityOrderDomainDTO(TypedDict, total=False):
    """Информация о домене"""
    domainName: str
    orderBcId: int


class PackageRegistrationResponseDTO(TypedDict, total=False):
    """Ответ на пакетную регистрацию"""
    packageId: int


class IdCodeDTO(TypedDict, total=False):
    """ID и код"""
    code: str
    id: int


class ResponsibilityCapabilityDTO(TypedDict, total=False):
    """Ответственная возможность"""
    code: str
    description: str
    id: int
    name: str


class ResponsibilityTcDTO(TypedDict, total=False):
    """Ответственность технической возможности"""
    implemented: List[ResponsibilityCapabilityDTO]
    responsibility: List[ResponsibilityCapabilityDTO]


class EnumCriteria(TypedDict, total=False):
    """Критерий"""
    description: str
    id: int
    interval: int
    maxDesc: str
    minDesc: str
    name: str
    revers: bool
    threshold: int
    type: str


class EntityType(TypedDict, total=False):
    """Тип сущности"""
    id: int
    name: str
    title: str


class TypeDTO(TypedDict, total=False):
    """Тип"""
    id: int
    name: str
    title: str


class PostCapabilityMapDTO(TypedDict, total=False):
    """DTO для создания карты возможностей"""
    description: str
    name: str
    typeId: int


class CreateCapabilityMapResponseDTO(TypedDict, total=False):
    """Ответ на создание карты"""
    id: int


class NameAndDescriptionDTO(TypedDict, total=False):
    """Название и описание"""
    description: str
    name: str
    type: TypeDTO


class ShortCapabilityMapDTO(TypedDict, total=False):
    """Краткая информация о карте"""
    createdDate: str
    description: str
    id: int
    name: str
    type: EntityType
    updatedDate: str


class ChildrenGroupDTO(TypedDict, total=False):
    """Группа дочерних элементов"""
    capabilityId: List[int]
    childrenGroupId: int
    nameGroup: str


class PatchCapabilityMapDTO(TypedDict, total=False):
    """DTO для обновления карты"""
    capabilityIds: List[int]
    childrenGroups: List[ChildrenGroupDTO]
    id: int
    nameGroup: str


class GetChildrenGroupsDTO(TypedDict, total=False):
    """Группы дочерних элементов"""
    capability: List[CapabilityDTO]
    groupId: int
    nameGroup: str
    parentId: int


class GroupDTO(TypedDict, total=False):
    """Группа"""
    capability: List[CapabilityDTO]
    childrenGroup: List[GetChildrenGroupsDTO]
    groupId: int
    nameGroup: str


class GetCapabilityMapByIdDTO(TypedDict, total=False):
    """Карта возможностей по ID"""
    description: str
    groups: List[GroupDTO]
    name: str
    type: EntityType


class CapabilityExportDTO(TypedDict, total=False):
    """Экспорт возможностей"""
    docId: int


class CapabilitySubscribedDTO(TypedDict, total=False):
    """Подписка на возможность"""
    code: str
    description: str
    id: int
    isDomain: bool
    name: str
    owner: str


class SearchCapabilityDTO(TypedDict, total=False):
    """Результат поиска"""
    code: str
    description: str
    id: int
    name: str
    type: str


class VersionInfoDTO(TypedDict, total=False):
    """Информация о версии"""
    author: str
    modified_date: str
    version: int


class GetHistoryByIdDTO(TypedDict, total=False):
    """История по ID"""
    version_info: VersionInfoDTO


class HistoryCapabilityDTO(TypedDict, total=False):
    """История бизнес-возможности"""
    author: str
    code: str
    deletedDate: str
    description: str
    id: int
    is_domain: bool
    link: str
    modifiedDate: str
    name: str
    owner: str
    parent: ParentDTO
    status: str
    version: int


class GetBcHistoryVersionDTO(TypedDict, total=False):
    """Версия истории бизнес-возможности"""
    capability: HistoryCapabilityDTO


class HistoryTechCapabilityDTO(TypedDict, total=False):
    """История технической возможности"""
    author: str
    code: str
    deletedDate: str
    description: str
    id: int
    link: str
    modifiedDate: str
    name: str
    owner: str
    parents: List[ParentDTO]
    status: str
    systemId: int
    version: int


class GetTcHistoryVersionDTO(TypedDict, total=False):
    """Версия истории технической возможности"""
    tech_capability: HistoryTechCapabilityDTO


class ResponseEntity(TypedDict, total=False):
    """Ответ API"""
    body: Any
    statusCode: str
    statusCodeValue: int


# ==================== Клиент для работы с API ====================

class CapabilityClient:
    """
    Клиент для работы с Capability API
    Управление бизнес и техническими возможностями
    
    Поддерживает:
    - Передачу URL через параметр или переменную окружения
    - Логгирование всех запросов
    - Обработку ошибок с raise_for_status
    - Отключение проверки сертификатов
    - Настраиваемые таймауты и заголовки
    - Все эндпоинты из спецификации API
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None
    ):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL API. Если не указан, берется из переменной окружения CAPABILITY_API_URL
            timeout: Таймаут запросов в секундах
            headers: Дополнительные заголовки для запросов
            token: Bearer токен для аутентификации
        """
        self.base_url = base_url or os.getenv(
            'CAPABILITY_API_URL',
            'https://capability-backend-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru'
        )
        
        if not self.base_url:
            raise ValueError(
                "Base URL должен быть указан либо через параметр, "
                "либо через переменную окружения CAPABILITY_API_URL"
            )
        
        # Убираем trailing slash если есть
        self.base_url = self.base_url.rstrip('/')
        
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            **(headers or {})
        }
        
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
        
        logger.info(f"Инициализирован CapabilityClient с базовым URL: {self.base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        Выполнение HTTP запроса
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE, PATCH)
            endpoint: Конечная точка API
            data: Данные для отправки в теле запроса
            params: Параметры запроса
            headers: Дополнительные заголовки
            **kwargs: Дополнительные параметры для requests
            
        Returns:
            Ответ от API (распарсенный JSON или текст)
            
        Raises:
            requests.HTTPError: При ошибках HTTP (401, 403, 404, 500 и т.д.)
            requests.RequestException: При ошибках сети
            
        Возможные коды ошибок:
            - 401: Unauthorized - требуется аутентификация
            - 403: Forbidden - недостаточно прав доступа
            - 404: Not Found - ресурс не найден
            - 500: Internal Server Error - внутренняя ошибка сервера
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)
        
        request_kwargs = {
            'timeout': self.timeout,
            'headers': request_headers,
            'verify': False,  # Отключаем проверку сертификатов
            **kwargs
        }
        
        if data is not None:
            request_kwargs['json'] = data
        
        if params is not None:
            request_kwargs['params'] = params
        
        logger.info(f"Выполнение {method} запроса к {url}")
        if data:
            logger.info(f"Данные запроса: {data}")
        if params:
            logger.info(f"Параметры запроса: {params}")
        
        response = requests.request(method, url, **request_kwargs)
        
        # Логируем статус ответа
        logger.info(f"Получен ответ со статусом {response.status_code}")
        
        # Проверяем статус ответа (вызывает исключение при ошибке)
        response.raise_for_status()
        
        # Пытаемся распарсить JSON
        try:
            return response.json()
        except ValueError:
            return response.text
    
    # ==================== Business Capability Controller ====================
    
    def get_business_capabilities(
        self,
        findBy: Optional[str] = "ALL",
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[BusinessCapabilityShortDTO]:
        """
        Получение бизнес возможностей
        
        Args:
            findBy: Фильтр поиска (по умолчанию "ALL")
            limit: Лимит результатов
            offset: Смещение для пагинации
            
        Returns:
            Список бизнес-возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {}
        if findBy:
            params['findBy'] = findBy
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        
        return self._make_request('GET', '/api/v1/business-capability', params=params)
    
    def put_business_capability(
        self,
        capability: PutBusinessCapabilityDTO,
        source: Optional[str] = None,
        user_id: Optional[str] = None,
        user_permission: Optional[str] = None,
        user_products_ids: Optional[str] = None,
        user_roles: Optional[str] = None
    ) -> ResponseEntity:
        """
        Создание/Обновление бизнес возможности
        
        Args:
            capability: Данные бизнес-возможности
            source: Источник запроса
            user_id: ID пользователя
            user_permission: Права пользователя
            user_products_ids: ID продуктов пользователя
            user_roles: Роли пользователя
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        headers = {}
        if source:
            headers['source'] = source
        if user_id:
            headers['user-id'] = user_id
        if user_permission:
            headers['user-permission'] = user_permission
        if user_products_ids:
            headers['user-products-ids'] = user_products_ids
        if user_roles:
            headers['user-roles'] = user_roles
        
        return self._make_request('PUT', '/api/v1/business-capability', data=capability, headers=headers)
    
    def get_business_capability_by_id(self, id: int) -> BusinessCapabilityShortDTO:
        """
        Получение бизнес возможности по идентификатору
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Бизнес-возможность
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/{id}')
    
    def delete_business_capability(self, code: str) -> ResponseEntity:
        """
        Удаление записи из таблицы find_name_sort_table со статусом BC
        
        Args:
            code: Код бизнес-возможности
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        return self._make_request('DELETE', f'/api/v1/business-capability/{code}')
    
    def get_business_capability_children(self, id: int) -> BusinessCapabilityChildrenDTO:
        """
        Получение всех дочерних бизнес возможностей
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Дочерние возможности
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/{id}/children')
    
    def get_business_capability_children_all(self, id: int) -> BusinessCapabilityChildrenIdsDTO:
        """
        Получение всех дочерних бизнес возможностей (только ID)
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            ID дочерних возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/{id}/children/all')
    
    def get_business_capability_parents(self, id: int) -> CapabilityParentDTO:
        """
        Получение всех родительских бизнес возможностей
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Родительские возможности
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/{id}/parents')
    
    def get_business_capability_tree(self) -> List[BusinessCapabilityTreeDTO]:
        """
        Построение дерева бизнес-возможностей
        
        Returns:
            Дерево бизнес-возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', '/api/v1/business-capability/tree')
    
    def get_business_capability_tree_by_id(self, id: int) -> BusinessCapabilityTreeCustomDTO:
        """
        Построение дерева по идентификатору возможности
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Дерево бизнес-возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/tree/{id}')
    
    def post_business_capability_public(self, id: int) -> ResponseEntity:
        """
        Публикация бизнес-возможности
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', f'/api/v1/business-capability/public/{id}')
    
    def get_business_capability_history(self, id: int) -> List[GetHistoryByIdDTO]:
        """
        Получение списка версий бизнес-возможности
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Список версий
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/history/{id}')
    
    def get_business_capability_history_version(
        self,
        id: int,
        version: int,
        other_version: Optional[int] = None
    ) -> List[GetBcHistoryVersionDTO]:
        """
        Получение выбранных версий бизнес-возможности
        
        Args:
            id: ID бизнес-возможности
            version: Версия
            other_version: Другая версия для сравнения
            
        Returns:
            Список версий
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {}
        if other_version is not None:
            params['other_version'] = other_version
        
        return self._make_request(
            'GET',
            f'/api/v1/business-capability/history/compare/{id}/{version}',
            params=params
        )
    
    # ==================== Business Capability Controller V2 ====================
    
    def get_business_capability_children_v2(self, id: int) -> BusinessCapabilityChildrenDTOV2:
        """
        Получение всех дочерних бизнес возможностей (V2)
        
        Args:
            id: ID бизнес-возможности
            
        Returns:
            Дочерние возможности (V2)
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v2/business-capability/{id}/children')
    
    # ==================== Business Capability Order Controller ====================
    
    def post_business_capability_order(
        self,
        request: BusinessCapabilityOrderRequestDTO
    ) -> ResponseEntity:
        """
        Публикация каталога Capability
        
        Args:
            request: Данные запроса
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', '/api/v1/business-capability/order', data=request)
    
    def post_business_capability_order_domains(
        self,
        ids: List[int]
    ) -> List[BusinessCapabilityOrderDomainDTO]:
        """
        Информации о доменах по списку id
        
        Args:
            ids: Список ID
            
        Returns:
            Список доменов
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', '/api/v1/business-capability/order/domains', data=ids)
    
    def get_business_capability_order_draft(self) -> List[BusinessCapabilityOrderDraftResponseDTO]:
        """
        Получение черновика каталога
        
        Returns:
            Список черновиков
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', '/api/v1/business-capability/order/draft')
    
    def post_business_capability_order_draft(
        self,
        request: BusinessCapabilityOrderDraftRequestDTO
    ) -> ResponseEntity:
        """
        Публикация черновика каталога
        
        Args:
            request: Данные запроса
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', '/api/v1/business-capability/order/draft', data=request)
    
    def patch_business_capability_order_draft(
        self,
        id: int,
        request: BusinessCapabilityOrderRequestDTO,
        publish: Optional[bool] = None
    ) -> ResponseEntity:
        """
        Управление каталогом Capability (черновик)
        
        Args:
            id: ID каталога
            request: Данные запроса
            publish: Опубликовать
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        params = {}
        if publish is not None:
            params['publish'] = publish
        
        return self._make_request(
            'PATCH',
            f'/api/v1/business-capability/order/draft/{id}',
            data=request,
            params=params
        )
    
    def get_business_capability_order_by_id(self, id: int) -> BusinessCapabilityOrderDraftResponseDTO:
        """
        Получение данных по идентификатору каталога
        
        Args:
            id: ID каталога
            
        Returns:
            Данные каталога
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/business-capability/order/{id}')
    
    def patch_business_capability_order(
        self,
        id: int,
        request: BusinessCapabilityOrderPatchRequestDTO,
        statusAlias: Optional[str] = None
    ) -> ResponseEntity:
        """
        Управление каталогом Capability
        
        Args:
            id: ID каталога
            request: Данные запроса
            statusAlias: Алиас статуса
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        params = {}
        if statusAlias:
            params['statusAlias'] = statusAlias
        
        return self._make_request(
            'PATCH',
            f'/api/v1/business-capability/order/{id}',
            data=request,
            params=params
        )
    
    # ==================== Tech Capability Controller ====================
    
    def get_tech_capabilities(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[TechCapabilityDTO]:
        """
        Получение технических возможностей
        
        Args:
            limit: Лимит результатов
            offset: Смещение для пагинации
            
        Returns:
            Список технических возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        
        return self._make_request('GET', '/api/v1/tech-capabilities', params=params)
    
    def put_tech_capability(
        self,
        techCapability: PutTechCapabilityDTO,
        source: Optional[str] = None
    ) -> ResponseEntity:
        """
        Создание/Обновление технической возможности
        
        Args:
            techCapability: Данные технической возможности
            source: Источник запроса
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        headers = {}
        if source:
            headers['source'] = source
        
        return self._make_request('PUT', '/api/v1/tech-capabilities', data=techCapability, headers=headers)
    
    def get_tech_capability_by_id(self, id: int) -> TechCapabilityDTO:
        """
        Получение технической возможности
        
        Args:
            id: ID технической возможности
            
        Returns:
            Техническая возможность
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/tech-capabilities/{id}')
    
    def delete_tech_capability(self, code: str) -> ResponseEntity:
        """
        Удаление записи из таблицы find_name_sort_table со статусом TC
        
        Args:
            code: Код технической возможности
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        return self._make_request('DELETE', f'/api/v1/tech-capabilities/{code}')
    
    def get_tech_capability_parents(self, id: int) -> CapabilityParentDTO:
        """
        Получение всех родительских технических возможностей
        
        Args:
            id: ID технической возможности
            
        Returns:
            Родительские возможности
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/tech-capabilities/{id}/parents')
    
    def get_all_tech_ids_by_codes(self, codes: List[str]) -> List[IdCodeDTO]:
        """
        Получение списка id технической возможности по списку code
        
        Args:
            codes: Список кодов
            
        Returns:
            Список ID и кодов
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {'codes': codes}
        return self._make_request('GET', '/api/v1/tech-capabilities/by-code', params=params)
    
    def get_array_tech_by_ids(self, ids: List[int]) -> List[ParentDTO]:
        """
        Получение списка технических возможностей
        
        Args:
            ids: Список ID
            
        Returns:
            Список технических возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {'ids': ids}
        return self._make_request('GET', '/api/v1/tech-capabilities/list/by-ids', params=params)
    
    def get_tech_capability_resp(self, id: int) -> ResponsibilityTcDTO:
        """
        Получение списка ТС которые реализованы в продукте и за которые система ответственна
        
        Args:
            id: ID продукта
            
        Returns:
            Ответственность технической возможности
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/tech-capabilities/product/{id}')
    
    def get_tech_capability_history(self, id: int) -> List[GetHistoryByIdDTO]:
        """
        Получение списка версий технической возможности
        
        Args:
            id: ID технической возможности
            
        Returns:
            Список версий
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/tech-capabilities/history/{id}')
    
    def get_tech_capability_history_version(
        self,
        id: int,
        version: int,
        other_version: Optional[int] = None
    ) -> List[GetTcHistoryVersionDTO]:
        """
        Получение выбранных версий технической возможности
        
        Args:
            id: ID технической возможности
            version: Версия
            other_version: Другая версия для сравнения
            
        Returns:
            Список версий
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {}
        if other_version is not None:
            params['other_version'] = other_version
        
        return self._make_request(
            'GET',
            f'/api/v1/tech-capabilities/history/compare/{id}/{version}',
            params=params
        )
    
    # ==================== Tech Capability Calculate Controller ====================
    
    def calculate_total_tech_capabilities_count(self) -> ResponseEntity:
        """
        Запустить процесс общего расчета критериев для тепловых карт
        
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', '/api/v1/calculate-total-tech-capabilities')
    
    def get_tech_recalculation_process(self) -> ResponseEntity:
        """
        Вызов процесса пересчета качества описания ТС
        
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', '/api/v1/tech-capability/recount-quality')
    
    # ==================== Package Capability Controller ====================
    
    def pack_load_business_capabilities(
        self,
        businessCapabilities: List[PostBusinessCapabilityDTO]
    ) -> PackageRegistrationResponseDTO:
        """
        Пакетная загрузка бизнес возможностей
        
        Args:
            businessCapabilities: Список бизнес-возможностей
            
        Returns:
            Ответ с ID пакета
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request(
            'POST',
            '/api/v1/package-business-capabilities',
            data=businessCapabilities
        )
    
    def pack_load_tech_capabilities(
        self,
        techCapabilities: List[PostTechCapabilityDTO]
    ) -> PackageRegistrationResponseDTO:
        """
        Пакетная загрузка технических возможностей
        
        Args:
            techCapabilities: Список технических возможностей
            
        Returns:
            Ответ с ID пакета
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request(
            'POST',
            '/api/v1/package-tech-capabilities',
            data=techCapabilities
        )
    
    # ==================== Capability Map Controller ====================
    
    def get_capability_maps(self) -> List[ShortCapabilityMapDTO]:
        """
        Получение всех карт пользователя
        
        Returns:
            Список карт возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', '/api/v1/maps')
    
    def create_capability_map(
        self,
        postCapabilityMapDTO: PostCapabilityMapDTO
    ) -> CreateCapabilityMapResponseDTO:
        """
        Создание карты возможностей
        
        Args:
            postCapabilityMapDTO: Данные карты
            
        Returns:
            Ответ с ID созданной карты
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', '/api/v1/maps', data=postCapabilityMapDTO)
    
    def get_capability_map_by_id(self, Id: int) -> GetCapabilityMapByIdDTO:
        """
        Получение карты по id
        
        Args:
            Id: ID карты
            
        Returns:
            Карта возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', f'/api/v1/maps/{Id}')
    
    def delete_capability_map(self, mapId: int) -> ResponseEntity:
        """
        Удаление карты пользователя
        
        Args:
            mapId: ID карты
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        return self._make_request('DELETE', f'/api/v1/maps/{mapId}')
    
    def patch_name_and_description_capability_map(
        self,
        mapId: int,
        nameAndDescriptionDTO: NameAndDescriptionDTO
    ) -> ResponseEntity:
        """
        Изменение названия и описания карты
        
        Args:
            mapId: ID карты
            nameAndDescriptionDTO: Новые название и описание
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        return self._make_request(
            'PATCH',
            f'/api/v1/maps/{mapId}',
            data=nameAndDescriptionDTO
        )
    
    def patch_capability_map(
        self,
        mapId: int,
        patchCapabilityMapDTO: List[PatchCapabilityMapDTO]
    ) -> ResponseEntity:
        """
        Обновления карты пользователя
        
        Args:
            mapId: ID карты
            patchCapabilityMapDTO: Данные для обновления
            
        Returns:
            Ответ с результатом операции
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
        """
        return self._make_request(
            'PATCH',
            f'/api/v1/maps/groups/{mapId}',
            data=patchCapabilityMapDTO
        )
    
    # ==================== Capability Map Types Controller ====================
    
    def get_capability_map_types(self) -> List[EntityType]:
        """
        Получение всех типов карт
        
        Returns:
            Список типов карт
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('GET', '/api/v1/capability/type')
    
    # ==================== Criteria Controller ====================
    
    def get_criteria_list(self, filter: Optional[str] = None) -> List[EnumCriteria]:
        """
        Получение критерий
        
        Args:
            filter: Фильтр поиска
            
        Returns:
            Список критериев
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {}
        if filter:
            params['filter'] = filter
        
        return self._make_request('GET', '/api/v1/criterias', params=params)
    
    # ==================== Capability Export Controller ====================
    
    def post_export_business_capabilities(self, doc_id: int) -> CapabilityExportDTO:
        """
        Export Business Capabilities
        
        Args:
            doc_id: ID документа
            
        Returns:
            Ответ с ID документа
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', f'/api/v1/export/business-capability/{doc_id}')
    
    def post_export_tech_capabilities(self, doc_id: int) -> CapabilityExportDTO:
        """
        Export Tech Capabilities
        
        Args:
            doc_id: ID документа
            
        Returns:
            Ответ с ID документа
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        return self._make_request('POST', f'/api/v1/export/tech-capability/{doc_id}')
    
    # ==================== Search Capability Controller ====================
    
    def search_capability(
        self,
        search: str,
        findBy: Optional[str] = "ALL"
    ) -> List[SearchCapabilityDTO]:
        """
        Поиск по сущностям
        
        Args:
            search: Строка поиска
            findBy: Фильтр поиска (по умолчанию "ALL")
            
        Returns:
            Список найденных возможностей
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {'search': search}
        if findBy:
            params['findBy'] = findBy
        
        return self._make_request('GET', '/api/v1/find', params=params)
    
    # ==================== Subscribe Controller ====================
    
    def get_capabilities_subscribed(
        self,
        entity_type: Literal["BUSINESS_CAPABILITY", "TECH_CAPABILITY"]
    ) -> List[CapabilitySubscribedDTO]:
        """
        Получение подписок на возможности
        
        Args:
            entity_type: Тип сущности (BUSINESS_CAPABILITY или TECH_CAPABILITY)
            
        Returns:
            Список подписок
            
        Возможные коды ошибок:
            - 401: Unauthorized
            - 403: Forbidden
            - 404: Not Found
        """
        params = {'entity-type': entity_type}
        return self._make_request('GET', '/api/v1/capabilities-subscribed', params=params)

