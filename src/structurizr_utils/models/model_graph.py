"""
Модель для работы с Architect Graph Service API
"""
import os
import re
from typing import TypedDict, Optional, List
import requests


# DTO типы на основе спецификации
class SearchSoftwareSystemDTO(TypedDict, total=False):
    cmdb: str
    name: str


class DeploymentNodeDTO(TypedDict, total=False):
    id: int
    deploymentName: str
    cmdb: str
    environmentName: str
    ip: str
    host: str


class ContainerNodeDTO(TypedDict, total=False):
    containerName: str
    cmdb: str


class InfluenceResponseDTO(TypedDict, total=False):
    dependentSystems: List[str]
    influencingSystems: List[str]


class TaskCacheDTO(TypedDict, total=False):
    id: int
    taskKey: str
    status: str
    type: str
    cachedAt: str


class ProductInfluenceDTO(TypedDict, total=False):
    dependentSystems: List[str]
    influencingSystems: List[str]


class DiagramElementDTO(TypedDict, total=False):
    id: int
    name: str
    dependentCount: int
    cmdb: str
    critical: str
    ownerName: str


class GraphService:
    """Класс для работы с API Architect Graph Service"""
    
    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Инициализация клиента Graph Service
        
        Args:
            url: URL сервиса (если не указан, берется из переменной окружения URL_GRAPH)
            token: Bearer токен для аутентификации (опционально)
        """
        self.base_url = (url or os.getenv("URL_GRAPH") or 
                        "https://architect-graph-service-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru").rstrip('/')
        self.session = requests.Session()
        self.session.verify = False  # Отключаем проверку сертификатов
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Вспомогательный метод для выполнения HTTP запросов
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Эндпоинт API (без базового URL)
            **kwargs: Дополнительные параметры для requests
            
        Returns:
            Response объект
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    # Graph Controller методы
    
    def global_graph(self, doc_id: int) -> str:
        """
        Добавление системы из указанного документа в глобальный граф
        (все вершины и связи помечаются graphTag: Global)
        
        Args:
            doc_id: ID документа
            
        Returns:
            Ответ API
        """
        response = self._request('POST', f'/api/v1/graph/{doc_id}')
        return response.text
    
    def local_graph(self, doc_id: int) -> str:
        """
        Пересоздание локального графа, используя документ, в котором описывается система
        (все вершины и связи помечаются graphTag: Local)
        
        Args:
            doc_id: ID документа
            
        Returns:
            Ответ API
        """
        response = self._request('POST', f'/api/v1/graph/local/{doc_id}')
        return response.text
    
    def get_software_system(self, search: str) -> List[SearchSoftwareSystemDTO]:
        """
        Поиск software system
        
        Args:
            search: Строка поиска
            
        Returns:
            Список найденных систем
        """
        response = self._request('GET', '/api/v1/search/software-system', params={'search': search})
        return response.json()
    
    def get_deployment_node(self, search: str) -> List[DeploymentNodeDTO]:
        """
        Поиск deploymentNode
        
        Args:
            search: Строка поиска
            
        Returns:
            Список найденных deployment nodes
        """
        response = self._request('GET', '/api/v1/search/deployment-node', params={'search': search})
        return response.json()
    
    def get_container_node(self, search: Optional[str] = None) -> List[ContainerNodeDTO]:
        """
        Поиск containerNode
        
        Args:
            search: Строка поиска (опционально)
            
        Returns:
            Список найденных контейнеров
        """
        params = {}
        if search is not None:
            params['search'] = search
        response = self._request('GET', '/api/v1/search/container', params=params)
        return response.json()
    
    def get_container_influence(self, cmdb: str, name: str) -> InfluenceResponseDTO:
        """
        Получить системы связанные с контейнером
        
        Args:
            cmdb: CMDB код
            name: Имя контейнера
            
        Returns:
            Информация о связанных системах
        """
        response = self._request('GET', '/api/v1/influence', 
                                params={'cmdb': cmdb, 'name': name})
        return response.json()
    
    def get_graph_by_task(self, graph_type: str, task_id: str) -> TaskCacheDTO:
        """
        Получение статуса графа по taskKey и типу графа
        
        Args:
            graph_type: Тип графа
            task_id: ID задачи
            
        Returns:
            Информация о статусе задачи
        """
        response = self._request('GET', f'/api/v1/graph/{graph_type}/task/{task_id}')
        return response.json()
    
    def get_influence(self, cmdb: str) -> ProductInfluenceDTO:
        """
        Метод для получения связанных систем
        
        Args:
            cmdb: CMDB код продукта
            
        Returns:
            Информация о связанных системах
        """
        response = self._request('GET', f'/api/v1/graph/product/{cmdb}/influence')
        return response.json()
    
    def get_deployment_influence(self, cmdb: str, name: str, env: str) -> ProductInfluenceDTO:
        """
        Метод для получения связанных систем деплоймента
        
        Args:
            cmdb: CMDB код
            name: Имя deployment
            env: Окружение
            
        Returns:
            Информация о связанных системах
        """
        response = self._request('GET', f'/api/v1/graph/deployment/{cmdb}/influence',
                                params={'name': name, 'env': env})
        return response.json()
    
    def get_elements(self, cypher_query: str) -> dict:
        """
        Получение элементов по Cypher запросу
        
        Args:
            cypher_query: Cypher запрос
            
        Returns:
            Результат запроса
        """
        # Нормализуем запрос: убираем переносы строк и лишние пробелы
        # для корректной передачи в HTTP заголовке
        normalized_query = re.sub(r'\s+', ' ', cypher_query.strip())
        response = self._request('GET', '/api/v1/elements',
                                headers={'CYPHER-QUERY': normalized_query})
        return response.json()
    
    def compare_with_current(self, cmdb: str, first_version: int) -> str:
        """
        Сравнение указанной версии системы с текущей (последней/актуальной)
        
        Args:
            cmdb: CMDB код
            first_version: Первая версия для сравнения
            
        Returns:
            Результат сравнения
        """
        response = self._request('GET', f'/api/v1/diff/{cmdb}/{first_version}')
        return response.text
    
    def compare_versions(self, cmdb: str, first_version: int, second_version: int) -> str:
        """
        Сравнение двух версий указанной системы
        
        Args:
            cmdb: CMDB код
            first_version: Первая версия
            second_version: Вторая версия
            
        Returns:
            Результат сравнения
        """
        response = self._request('GET', f'/api/v1/diff/{cmdb}/{first_version}/{second_version}')
        return response.text
    
    # Diagram Controller методы
    
    def get_influence_elements(self, id: int) -> str:
        """
        Получение элементов от которых зависит элемент инфраструктуры
        
        Args:
            id: ID элемента
            
        Returns:
            JSON строка с элементами
        """
        response = self._request('GET', '/api/v1/influence/elements', params={'id': id})
        return response.text
    
    def get_influence_dot(self, id: int) -> str:
        """
        Получение DOT диаграммы влияния
        
        Args:
            id: ID элемента
            
        Returns:
            DOT диаграмма в виде строки
        """
        response = self._request('GET', '/api/v1/influence/dot', params={'id': id})
        return response.text
    
    def get_diagram_deployment_elements(self, id: int) -> DiagramElementDTO:
        """
        Построение elements для deployment диаграммы
        
        Args:
            id: ID deployment
            
        Returns:
            Элементы диаграммы
        """
        response = self._request('GET', '/api/v1/diagram/elements', params={'id': id})
        return response.json()
    
    def get_diagram_deployment_dot(self, id: int) -> str:
        """
        Построение Deployment диаграммы dot
        
        Args:
            id: ID deployment
            
        Returns:
            DOT диаграмма в виде строки
        """
        response = self._request('GET', '/api/v1/diagram/dot', params={'id': id})
        return response.text
    
    def get_diagram_deployment(self, cmdb: str, env: str, deployment_name: str, 
                              rank_direction: Optional[str] = None) -> str:
        """
        Построение Deployment диаграммы
        
        Args:
            cmdb: CMDB код
            env: Окружение
            deployment_name: Имя deployment
            rank_direction: Направление ранжирования (опционально)
            
        Returns:
            Диаграмма в виде строки
        """
        params = {'cmdb': cmdb, 'env': env, 'deployment-name': deployment_name}
        if rank_direction:
            params['rank-direction'] = rank_direction
        response = self._request('GET', '/api/v1/diagram/deployment', params=params)
        return response.text
    
    def get_context_diagram_v2(self, cmdb: str, communication_direction: str,
                               rank_direction: Optional[str] = None) -> str:
        """
        Построение context диаграммы V2
        
        Args:
            cmdb: CMDB код
            communication_direction: Направление коммуникации
            rank_direction: Направление ранжирования (опционально)
            
        Returns:
            Диаграмма в виде строки
        """
        params = {'cmdb': cmdb, 'communicationDirection': communication_direction}
        if rank_direction:
            params['rankDirection'] = rank_direction
        response = self._request('GET', '/api/v1/diagram/context', params=params)
        return response.text
    
    def get_deployment_diagram(self, environment: str, software_system_mnemonic: str,
                               rank_direction: str) -> str:
        """
        Генерация json с описанием deploymentView
        
        Args:
            environment: Окружение
            software_system_mnemonic: Мнемоника программной системы
            rank_direction: Направление ранжирования
            
        Returns:
            JSON с описанием deployment view
        """
        response = self._request('GET', 
                                f'/api/v1/deployment/{environment}/{software_system_mnemonic}',
                                params={'rankDirection': rank_direction})
        return response.text
    
    def get_context_diagram(self, software_system_mnemonic: str,
                           rank_direction: Optional[str] = None) -> str:
        """
        Генерация json с описанием contextView
        
        Args:
            software_system_mnemonic: Мнемоника программной системы
            rank_direction: Направление ранжирования (опционально)
            
        Returns:
            JSON с описанием context view
        """
        params = {}
        if rank_direction:
            params['rankDirection'] = rank_direction
        response = self._request('GET', f'/api/v1/context/{software_system_mnemonic}', params=params)
        return response.text
    
    def get_c4_diagram(self, software_system_mnemonic: str, container_mnemonic: str,
                       rank_direction: Optional[str] = None) -> str:
        """
        Генерация json с описанием containerView
        
        Args:
            software_system_mnemonic: Мнемоника программной системы
            container_mnemonic: Мнемоника контейнера
            rank_direction: Направление ранжирования (опционально)
            
        Returns:
            JSON с описанием container view
        """
        params = {}
        if rank_direction:
            params['rankDirection'] = rank_direction
        response = self._request('GET', 
                                f'/api/v1/context/{software_system_mnemonic}/{container_mnemonic}',
                                params=params)
        return response.text
    
    def get_context_influence_elements(self, cmdb: str) -> str:
        """
        Получение список влияющих систем
        
        Args:
            cmdb: CMDB код
            
        Returns:
            JSON строка с элементами
        """
        response = self._request('GET', '/api/v1/context/influence/elements',
                                params={'cmdb': cmdb})
        return response.text
    
    def get_context_influence_dot(self, cmdb: str) -> str:
        """
        Построение Deployment диаграммы с влияемыми системами в формате DOT
        
        Args:
            cmdb: CMDB код
            
        Returns:
            DOT диаграмма в виде строки
        """
        response = self._request('GET', '/api/v1/context/influence/dot', params={'cmdb': cmdb})
        return response.text
    
    def get_context_elements(self, cmdb: str) -> DiagramElementDTO:
        """
        Построение elements для context диаграммы
        
        Args:
            cmdb: CMDB код
            
        Returns:
            Элементы диаграммы
        """
        response = self._request('GET', '/api/v1/context/elements', params={'cmdb': cmdb})
        return response.json()
    
    def get_context_dot(self, cmdb: str) -> str:
        """
        Построение Deployment диаграммы с зависимыми системами в формате DOT
        
        Args:
            cmdb: CMDB код
            
        Returns:
            DOT диаграмма в виде строки
        """
        response = self._request('GET', '/api/v1/context/dot', params={'cmdb': cmdb})
        return response.text
    
    def close(self):
        """Закрытие сессии"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
