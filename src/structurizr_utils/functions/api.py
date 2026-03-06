"""
Модуль для проверки правильности описания API и SLA в нотации Structurizr DSL.

Основные функции:
- check_api: Проверяет наличие и корректность API описаний
- ApiLoader: Класс для загрузки и парсинга API спецификаций
- publish_system: Публикует систему с API в backend
- publish_system_relations: Публикует связи системы
"""

import requests
import json
import yaml
import os
import re
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.functions.beeatlas_objects import System, Container, Interface, Method
from structurizr_utils.models.models_product import (
    ProductRelationsNewRequestDTO, ProductRelationNewDTO, InterfaceDTO, 
    MethodDTO, ParameterDTO, SLADTO, put_product_relations
)
from zeep import Client
from zeep.transports import Transport
from structurizr_utils.models.model_capability import CapabilityClient,ResponsibilityCapabilityDTO

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def parse_string_to_dict(input_string: str) -> Dict[str, str]:
    """
    Парсит строку с НФТ (неформатированными данными) в словарь.
    
    Args:
        input_string: Строка в формате "KEY1:VALUE1;KEY2:VALUE2"
        
    Returns:
        Dict[str, str]: Словарь с распарсенными данными
    """
    result_dict: Dict[str, str] = {}
    if ';' not in input_string or ':' not in input_string:
        return result_dict
    
    pairs = input_string.upper().split(';')
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)  # Разделяем только по первому ':'
            result_dict[key.strip()] = value.strip()
    return result_dict

def parse_new_string_to_dict(input_string: str) -> Dict[str, str]:
    """
    Парсит строку в новом формате в словарь.
    
    Args:
        input_string: Строка в формате "KEY1=VALUE1;KEY2=VALUE2"
        
    Returns:
        Dict[str, str]: Словарь с распарсенными данными
    """
    result_dict: Dict[str, str] = {}
    if '=' not in input_string:
        return result_dict
    
    pairs = input_string.split(';')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)  # Разделяем только по первому '='
            result_dict[key.upper().strip()] = value.upper().strip()
    return result_dict

class ApiLoader:
    """
    Класс для загрузки и парсинга API спецификаций различных форматов.
    
    Поддерживаемые форматы:
    - REST API (Swagger/OpenAPI JSON/YAML)
    - gRPC (Protocol Buffers)
    - SOAP (WSDL)
    """
    
    def __init__(self) -> None:
        """Инициализация загрузчика API."""
        self.is_local: bool = False

    def download_swagger(self, url: str) -> str:
        """
        Загружает API спецификацию из различных источников.
        
        Args:
            url: URL или путь к файлу спецификации
            
        Returns:
            str: Содержимое спецификации или пустая строка при ошибке
        """
        try:
            parsed_uri = urlparse(url)
            
            if parsed_uri.scheme == 'file':
                logger.info(f'Загрузка swagger из файла: {parsed_uri.netloc}')
                with open(parsed_uri.netloc, 'r', encoding='utf-8') as f:
                    result = f.read()
                    self.is_local = True
                    return result
                
            elif parsed_uri.scheme in ['http', 'https']:
                logger.info(f'Загрузка swagger из URL: {url}')
                headers = {'PRIVATE-TOKEN': 'PRIVATE-TOKEN'}
                response = requests.get(url, headers=headers, verify=False, timeout=5)
                    
                if response.status_code == 200:
                    logger.debug(f'Успешно загружена спецификация: {response.status_code}')
                    return response.text
                else:
                    logger.warning(f'Ошибка загрузки спецификации: {response.status_code} {response.reason}')
                    logger.warning(f'Детали ошибки: {response.text}')
                return ""
                
            elif os.path.exists(url):
                logger.info(f'Загрузка swagger из локального файла: {url}')
                with open(url, 'r', encoding='utf-8') as file:
                    result = file.read()
                    self.is_local = True
                    return result
            else:
                logger.warning(f'Файл не найден: {url}')
                self.is_local = True
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке спецификации: {e}")

        return ""

    def get_api_methods_wsdl(self, file_path: str) -> List[Method]:
        """
        Парсит WSDL файл и извлекает методы SOAP сервисов.
        
        Args:
            file_path: Путь к WSDL файлу
            
        Returns:
            List[Method]: Список найденных методов
        """
        result: List[Method] = []
        try:
            transport = Transport(timeout=3)
            client = Client(file_path, transport=transport)

            # Получить список операций
            for service in client.wsdl.services.values():
                for port in service.ports.values():
                    operations = port.binding._operations.values()
                    for operation in operations:
                        method_name = f"{service.name}.{operation.name}"
                        logger.debug(f"Найден WSDL метод: {method_name}")
                        result.append(Method(name=method_name))
                        
        except Exception as e:
            logger.warning(f"Ошибка парсинга WSDL файла {file_path}: {e}")
            parsed_uri = urlparse(file_path)
            if parsed_uri.scheme not in ['http', 'https']:
                self.is_local = True
                
        return result

    def get_api_methods_proto(self, file_path: str) -> List[Method]:
        result = list()
        data = self.download_swagger(file_path)

        if len(data) ==0:
            logging.error(f"# ERROR: Unable to download proto file {file_path}")
            return result
        try:
            services = re.findall(r'service\s+(\w+)\s*{([^}]*)}', data, re.DOTALL)
        
            for service_name, methods_block in services:
                methods = re.findall(r'rpc\s+(\w+)\s*\(([^)]*)\)\s*returns\s*\(([^)]*)\)', methods_block)
                for method_name, input_type, output_type in methods:
                    logging.debug(f"# Found proto: {method_name} ({input_type} -> {output_type})")
                    result.append(Method(name = f"{service_name}.{method_name}"))
        except Exception as e:
            logging.warning(f"#### ERROR: Unable to parse proto file {file_path}")

        return result

    def get_api_methods_rest(self, file_path: str) -> List[Method]:

        result = list()
        data = self.download_swagger(file_path)

        if len(data) ==0:
            logging.error(f"# ERROR: Unable to download swagger file {file_path}")
            return result
        
        try:
            # Попытка десериализации как JSON
            data = json.loads(data)
            logging.info("# Файл является JSON.")
            paths = data.get('paths', {})

            for path, methods in paths.items():
                for method, details in methods.items():
                    # Добавляем endpoint в формате METHOD PATH
                    logging.debug(f'# Found endpoint:  {method.upper()} {path}')
                    result.append(Method(name = f"{method.upper()} {path}"))
            return result
        except json.JSONDecodeError:
            logging.warning(f"# ERROR: Unable to parse json file {file_path}")

        try:
            api_spec = yaml.safe_load(data)
            logging.info("# Файл является YAML.")
            paths = api_spec.get('paths', {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    logging.debug(f'# Found endpoint {method.upper()} {path}')
                    result.append( Method(name = f"{method.upper()} {path}"))
            return result
        except Exception as e:
            logging.warning(f"# ERROR: Unable to parse yaml file {file_path}")

        return result
    
    def get_api_methods(self, file_path: str, type: str) -> List[Method]:
        if type == "rest":
            return self.get_api_methods_rest(file_path=file_path)
        if type == "grpc":
            return self.get_api_methods_proto(file_path=file_path)
        if type == "soap" or type == "wsdl":
            return self.get_api_methods_wsdl(file_path=file_path)
        return list()


# Метод для публикации системы используя put_product_relations
# Метод конвертирует System в ProductRelationsNewRequestDTO и отправляет в API
def publish_system_relations(cmdb: str, system : System, from_on_premises : bool):
    logging.info(f'# Publishing system relations')
    def process_code(s):
        if s is None:
            return ""
        elif '.' in s:
            return s.split('.')[0]
        else:
            return s
            
    # Конвертируем System в ProductRelationsNewRequestDTO
    product_relations = []

    logging.debug(f'# System containers {system.containers}')
    
    if system.containers:
        logging.info(f'# System containers length {len(system.containers)}')

        for container in system.containers:
            # Конвертируем интерфейсы контейнера
            interfaces = []
            if container.interfaces:
                for interface in container.interfaces:
                    # Конвертируем методы интерфейса
                    methods = []
                    if interface.methods:
                        for method in interface.methods:
                            # Создаем SLA объект
                            sla = SLADTO(
                                error_rate=method.error_rate,
                                latency=method.latency,
                                rps=method.rps
                            )
                            
                            # Создаем метод DTO
                            method_dto = MethodDTO(
                                capabilityCode=method.implements or "",
                                description=method.description or "",
                                name=method.name or "",
                                parameters=[],  # Пока пустой список, можно расширить при необходимости
                                returnType="",  # Пока пустая строка, можно расширить при необходимости
                                sla=sla,
                                type=""  # Пока пустая строка, можно расширить при необходимости
                            )
                            methods.append(method_dto)
                    
                    # Создаем SLA для интерфейса (используем значения по умолчанию)
                    interface_sla = SLADTO(error_rate=None, latency=None, rps=None)
                    
                    # Создаем интерфейс DTO

                    logging.debug(f"interface {interface.code} -> {process_code(interface.code)}")

                    interface_dto = InterfaceDTO(
                        capabilityCode=interface.implements or "",
                        code=process_code(interface.code),
                        methods=methods,
                        name=interface.name or "",
                        protocol=interface.protocol or "",
                        sla=interface_sla,
                        specification=interface.specification or "",
                        version=interface.version or ""
                    )
                    interfaces.append(interface_dto)
            
            # Создаем relation DTO для контейнера
            # if container.code and len(container.code) > 0:
            # if container.interfaces:
            relation_dto = ProductRelationNewDTO(
                    code=process_code(container.code),
                    interfaces=interfaces,
                    name=container.name or "",
                    version=container.version or ""
                )
            product_relations.append(relation_dto)
    
    # Создаем запрос
    product_relations_request = ProductRelationsNewRequestDTO(
        relations=product_relations
    )
    
    logging.debug(f'# Product relations request {product_relations_request}')
    # Отправляем запрос
    put_product_relations(cmdb=cmdb, relations=product_relations_request, from_on_premises = from_on_premises)


def publish_system(cmdb: str, system : System, backend_url: str):
    logging.info(f'# Publishing system')

    if system.containers is None:
        logging.warning(f' # Skipping - empty containers')
        return

    url = backend_url+'/api/v4/systems/'+system.code
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    json_request = system.model_dump_json()
    logging.info(f'# url {url}')
    logging.info(f'#  {json_request}')
    response = requests.put(url, data=json_request.encode('utf-8') , headers=headers, verify= False, timeout=300)

    if response.status_code == 200:
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def fill_sla_methods(data: dict, component : dict, beeatlas_interface : Interface, strucutrizr_id : str) -> bool:

    # get old style from custom component
    has_sla = False
    
    for ce in data.get('model',dict()).get('customElements',dict()):
        if 'metadata' in ce:
            metadata = parse_string_to_dict(ce['metadata'])
            if 'ID' in metadata:
                id = metadata['ID']
                if id == strucutrizr_id:
                    for p in ce.get('properties',list()):
                        method_name_origin = p.strip()
                        method_name = p.upper().strip()
                        rps, latency, error_rate = [None,None,None]
                        values = parse_string_to_dict(ce['properties'][p])
                        if is_float(values.get('RPS','')):
                            rps = float(values.get('RPS',None))
                        if is_float(values.get('LATENCY','')):
                            latency = float(values.get('LATENCY',None))
                        if is_float(values.get('ERROR_RATE','')):
                            error_rate = float(values.get('ERROR_RATE',None))
                        implements = values.get('TC',None)   
                        found_method = False
                        has_sla = True

                        for method in beeatlas_interface.methods:
                            if method.name.upper().strip() == method_name: 
                                method.rps = rps
                                method.latency = latency
                                method.error_rate = error_rate
                                method.implements = implements
                                found_method = True

                        if not found_method:
                            #logging.warning(f"# Not found method in specs {method_name_origin}, force adding")
                            beeatlas_interface.methods.append(Method(name=method_name_origin,rps=rps,latency=latency,error_rate=error_rate,implements = implements))

    
    # new style
    properties = component.get('properties',dict())
    for key in properties:
        value = properties[key].lower().strip()
        pattern = r'^.*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) .*$'

        property_method = False
        if bool(re.match(pattern, key.upper())):
            property_method = True
        elif ("." in key) and (("rpc" in value) or ("latency" in value) or ("error_rate" in value)):
            property_method = True

        
        if property_method:
            rps_n, latency_n, error_rate_n = [None,None,None]
            try:
                values = parse_new_string_to_dict(value)
                
                if is_float(values.get('RPS','')):
                    rps_n = float(values.get('RPS',None))
                if is_float(values.get('LATENCY','')):
                    latency_n = float(values.get('LATENCY',None))
                if is_float(values.get('ERROR_RATE','')):
                    error_rate_n = float(values.get('ERROR_RATE',None))
                implements_n = values.get('TC',None)

                found_method = False
                has_sla = True

                for method in beeatlas_interface.methods:
                    if method.name.upper().strip() == key.upper().strip():
                        method.rps = rps_n
                        method.latency = latency_n
                        method.error_rate = error_rate_n
                        method.implements = implements_n
                        found_method = True
                        
                if not found_method:
                    #logging.warning(f"# Not found method in specs {key}, force adding")
                    beeatlas_interface.methods.append(Method(name=key,rps=rps_n,latency=latency_n,error_rate=error_rate_n,implements=implements_n))
            except Exception as ex:
                logging.error(f"# Error adding SLA {key}->{value} : {ex}")
    return has_sla

def check_api(cmdb: str, data: Dict[str, Any], backend_url: str, 
              share_url: str, publish: bool, from_on_premises: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет правильность описания API и SLA в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. API.01 - У приложения есть опубликованные API
    2. API.02 - Для некоторых методов определен SLA
    3. API.03 - Для всех TC есть спецификация
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы
        share_url: URL для публикации (не используется)
        publish: Флаг публикации найденных API
        from_on_premises: Флаг работы с локальными спецификациями
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку API для системы CMDB: {cmdb}')
    
    # Определение критериев оценки (assessments)
    api_assessments: List[Assessment] = [
        Assessment(code='API.01', description='У приложения есть опубликованные API'),
        Assessment(code='API.02', description='Для некоторых методов определен SLA'),
        Assessment(code='API.03', description='Для всех TC есть спецификация')
    ]
    
    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    beeatlas_system = System(code=cmdb)

    # Инициализация флагов состояния
    has_api: bool = False
    has_sla: bool = False
    has_local_specs: bool = False
    
    # Инициализация переменных для assessment
    found_objects_api01: List[Dict[str, str]] = []
    found_objects_api02: List[Dict[str, str]] = []
    found_objects_api03: List[Dict[str, str]] = []

    api_errors : List[Dict[str, str]] = []

    # Анализ интерфейсов системы
    logger.debug(f'Анализ интерфейсов системы [{cmdb}]')
    systems: List[Dict[str, Any]] = data.get('model', {}).get('softwareSystems', [])
    
    for system in systems:
        system_cmdb: str = system.get('properties', {}).get('cmdb', '')
        if system_cmdb.lower().strip() == cmdb.lower().strip():
            # Заполнение метаданных системы
            beeatlas_system.name = system.get('name', '')
            beeatlas_system.description = system.get('description', None)
            beeatlas_system.version = system.get('properties', {}).get('version', None)
            beeatlas_system.status = system.get('properties', {}).get('status', None)
            beeatlas_system.author = system.get('properties', {}).get('author', None)
            
            logger.debug(f'Обработка системы: {beeatlas_system.name}')
            
            # Анализ контейнеров системы
            containers: List[Dict[str, Any]] = system.get('containers', [])
            for container in containers:  
                container_source: str = container.get('properties', {}).get('source', '').lower()
                if container_source != 'landscape':
                    # Создание объекта контейнера
                    external_name_container: Optional[str] = container.get('properties', {}).get('external_name', None)
                    beeatlas_container = Container(code=None)

                    #logger.info(f"Container: {container.get('properties', {})}")
                    
                    if external_name_container is not None:
                        beeatlas_container.code = f"{external_name_container}.{cmdb}"
                    else:
                        if container.get('name', None):
                            beeatlas_container.code = f"ext_{container.get('name').lower().replace(' ','_').replace('   ','_').replace('.','_')}.{cmdb}"
                            container_has_api = False
                            for component in container.get('components', []):
                                if  component.get('properties', {}).get('type', '').lower() == "api":
                                    container_has_api = True
                                    break
                            if container_has_api:
                                api_errors.append({f"{container.get('name', None)}" : f"нет external_name у контейнера, используем {beeatlas_container.code}"})
                        # structurizr_identifier = container.get('properties', {}).get('st
                        pass
                        # example structurizr.dsl.identifier is my_system.gateway
                        # we need to extrace "gateway" part
                        # api_errors.append({f"{container.get('name', None)}" : "нет <a href='https://docs.bw.vimpelcom.ru/workflow/ptr/3.6%20%D0%9D%D0%B5%D1%84%D1%83%D0%BD%D0%BA%D1%86%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5%20%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F/' target='_'>external_name</a> у контейнера"})
                        # structurizr_identifier = container.get('properties', {}).get('structurizr.dsl.identifier', None)
                        # if structurizr_identifier:
                        #     structurizr_identifier = structurizr_identifier.split('.')[-1]
                        #     beeatlas_container.code = f"ext_{structurizr_identifier}.{cmdb}"
 
                    
                    beeatlas_container.name = container.get('name', None)
                    beeatlas_container.description = container.get('description', None)
                    beeatlas_container.version = container.get('properties', {}).get('version', None)
                    
                    logger.debug(f'Обработка контейнера: {beeatlas_container.name}')
                    logger.debug(f'Количество компонент: {len(container.get("components", []))}')

                    # Анализ компонентов контейнера
                    components: List[Dict[str, Any]] = container.get('components', [])
                    for component in components:
                        logger.debug(f'Обработка компонента: {component.get("name", None)}')
                        component_type: str = component.get('properties', {}).get('type', '').lower()
                            
                        if component_type == 'api':
                            # Создание объекта интерфейса
                            
                            external_name_interface: Optional[str] = component.get('properties', {}).get('external_name', None)
                            beeatlas_interface = Interface(code=None)
                            #logger.info(f"Interface: {component.get('properties', {})}")

                            if external_name_interface:
                                if beeatlas_container.code:
                                    beeatlas_interface.code = f"{external_name_interface}.{beeatlas_container.code}"
                                else:
                                    api_errors.append({f"{component.get('name', None)}" : "нет <a href='https://docs.bw.vimpelcom.ru/workflow/ptr/3.6%20%D0%9D%D0%B5%D1%84%D1%83%D0%BD%D0%BA%D1%86%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5%20%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F/' target='_'>external_name</a> у родительского контейнера"})
                            else:
                                # example structurizr.dsl.identifier is my_system.gateway
                                # we need to extrace "gateway" part
                                if component.get('name',None):
                                    beeatlas_interface.code = f"ext_{ component.get('name').lower().replace(' ','_').replace('   ','_').replace('.','_')}.{beeatlas_container.code}"
                                    api_errors.append({f"{component.get('name', None)}" : f"нет external_name у интерфейса, используем {beeatlas_interface.code}"})
                                else:
                                    api_errors.append({f"{component.get('name', None)}" : "нет <a href='https://docs.bw.vimpelcom.ru/workflow/ptr/3.6%20%D0%9D%D0%B5%D1%84%D1%83%D0%BD%D0%BA%D1%86%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5%20%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F/' target='_'>external_name</a> у интерфейса"})
                                # structurizr_identifier = component.get('properties', {}).get('structurizr.dsl.identifier', None)
                                # if structurizr_identifier:
                                #     structurizr_identifier = structurizr_identifier.split('.')[-1]
                                #     beeatlas_interface.code = f"ext_{structurizr_identifier}.{beeatlas_container.code}"

                            
                            # Заполнение метаданных интерфейса
                            beeatlas_interface.name = component.get('name', None)
                            beeatlas_interface.description = component.get('description', None)
                            beeatlas_interface.version = component.get('properties', {}).get('version', None)
                            beeatlas_interface.status = component.get('properties', {}).get('status', None)
                            beeatlas_interface.protocol = component.get('properties', {}).get('protocol', None)
                            beeatlas_interface.implements = component.get('properties', {}).get('tc', None)
                            beeatlas_interface.specification = component.get('properties', {}).get('api_url', None)
                            
                            logger.debug(f'Обработка API компонента: name {beeatlas_interface.name} code {beeatlas_interface.code}')

                            # Загрузка методов API из спецификации
                            if beeatlas_interface.specification is not None:
                                loader = ApiLoader()
                                beeatlas_interface.methods = loader.get_api_methods(
                                    file_path=beeatlas_interface.specification,
                                    type=beeatlas_interface.protocol
                                )
                                if loader.is_local:
                                    has_local_specs = True
                                    logger.debug(f'Использована локальная спецификация: {beeatlas_interface.specification}')
                            else:
                                beeatlas_interface.methods = []
                                logger.debug('Спецификация API не указана')

                            # Заполнение SLA для методов
                            has_sla = fill_sla_methods(
                                data=data,
                                component=component,
                                beeatlas_interface=beeatlas_interface,
                                strucutrizr_id=component.get('id', None)
                            ) or has_sla

                            # Добавление интерфейса к контейнеру
                            if beeatlas_container.interfaces is None:
                                beeatlas_container.interfaces = []

                            if beeatlas_interface.code:
                                beeatlas_container.interfaces.append(beeatlas_interface)
                                has_api = True
                            
                            # Заполнение данных для assessment API.01 - интерфейсы с методами
                            if beeatlas_interface.methods and len(beeatlas_interface.methods) > 0 and beeatlas_interface.code:
                                interface_code = beeatlas_interface.code or beeatlas_interface.name or "unknown"
                                interface_name = beeatlas_interface.name or "Unknown Interface"
                                found_objects_api01.append({interface_code: f"{interface_code} {interface_name} ({len(beeatlas_interface.methods)} methods)"})
                                logger.debug(f'Добавлен API интерфейс с методами: {beeatlas_interface.name} (методов: {len(beeatlas_interface.methods)})')
                            else:
                                logger.debug(f'Пропущен API интерфейс без методов: {beeatlas_interface.name}')
                            
                            # Заполнение данных для assessment API.02 - методы с SLA
                            if beeatlas_interface.methods and beeatlas_interface.code:
                                for method in beeatlas_interface.methods:
                                    if method.rps is not None or method.latency is not None or method.error_rate is not None:
                                        method_name = method.name or "Unknown Method"
                                        interface_name = beeatlas_interface.name or "Unknown Interface"
                                        found_objects_api02.append({method_name: f"{method_name} ({interface_name})"})
                                        logger.debug(f'Найден метод с SLA: {method_name} в интерфейсе {interface_name}')
                            
                            # Заполнение данных для assessment API.03 - интерфейсы с TC но без спецификации
                            if beeatlas_interface.implements and not beeatlas_interface.specification and beeatlas_interface.code:
                                interface_code = beeatlas_interface.code or beeatlas_interface.name or "unknown"
                                interface_name = beeatlas_interface.name or "Unknown Interface"
                                tc_code = beeatlas_interface.implements or "Unknown TC"
                                found_objects_api03.append({interface_code: f"{interface_code} {interface_name} (TC: {tc_code}, no specification)"})
                                logger.debug(f'Найден интерфейс с TC но без спецификации: {beeatlas_interface.name} (TC: {beeatlas_interface.implements})')
                            
                            logger.debug(f'Добавлен API интерфейс: {beeatlas_interface.name}')
                        
                    # Добавление контейнера к системе
                    if beeatlas_system.containers is None:
                        beeatlas_system.containers = []
                    
                    # add only if container has more then zero interfaces
                    if beeatlas_container.interfaces and beeatlas_container.code:
                        if len(beeatlas_container.interfaces) > 0:
                            beeatlas_system.containers.append(beeatlas_container)

   
    # Публикация системы если требуется
    if publish:
        has_local_specs = False
        if from_on_premises and has_local_specs:
            logger.warning("Пропуск публикации API из-за локальных спецификаций")
        else:
            
            # preprocess containers and interfaces
            for container in beeatlas_system.containers:
                if container.code is None: # check if we need external code
                    has_interfaces = False
                    if container.interfaces is not None:
                        has_interfaces = (len(container.interfaces) > 0)
                    if has_interfaces:
                        container.code = f"ext_{container.name.lower().replace(' ','_').replace('   ','_').replace('.','_')}.{cmdb}"
            beeatlas_system.containers = [container for container in beeatlas_system.containers if hasattr(container, 'code') and container.code is not None  ]

            # Fix container names
            for container in beeatlas_system.containers:
                if container.interfaces is not None:
                    for i in container.interfaces:
                        if i.code is None:
                            i.code = f"ext_{i.name.lower().replace(' ','_').replace('   ','_').replace('.','_')}.{container.code}"

            # Fix capability
            try:
                client = CapabilityClient()
                responsibility = client.get_tech_capability_resp(product_id)
                if responsibility["responsibility"]:
                    capability_set = set()
                    for cpb in responsibility["responsibility"]:
                        capability_set.add(cpb["code"])
                            
                    def fix_capability(cmdb: str, capability_set : set, capability: str) -> str:
                        if capability in capability_set:
                            logging.warning(f"# Found capability {capability}")
                            return capability
                        elif f"{cmdb}.{capability}" in capability_set:
                            logging.warning(f"# Found capability {capability}")
                            logging.warning(f"# Correct capability {capability} -> {cmdb}.{capability}")
                            return f"{cmdb}.{capability}"
                        else:
                            logging.warning(f"# Not found capability {capability} -> erase from interface")
                            return None
                        
                    for container in beeatlas_system.containers:
                        if container.interfaces is not None:
                            for i in container.interfaces:
                                if i.implements is not None:
                                    i.implements =  fix_capability(cmdb=cmdb,capability_set=capability_set,capability=i.implements)
                                if i.methods is not None:    
                                    for m in i.methods:
                                        if m.implements is not None:
                                            m.implements =  fix_capability(cmdb=cmdb,capability_set=capability_set,capability=m.implements)

            except Exception as ex:
                logging.warning("# System has no capabilities defined")

            logger.info('Публикация системы с API в BeeAtlas')
            publish_system_relations(cmdb=cmdb, system=beeatlas_system, from_on_premises = from_on_premises)
            
            if backend_url:
                logger.info(f'Публикация системы с API в Sparx: {backend_url}')
                publish_system(cmdb=cmdb, system=beeatlas_system, backend_url=backend_url)

            


    # Выполнение проверок fitness functions
    if from_on_premises and has_local_specs:
        logger.warning("Пропуск проверок fitness functions из-за локальных спецификаций")
    else:
        # Проверка API.01: У приложения есть опубликованные API
        logger.info('Проверка API.01: У приложения есть опубликованные API')
        if len(found_objects_api01) > 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_api01: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_api01
            }

            assessment_obj_api02: AssessmentObjects = {
                "isCheck": False,
                "details": api_errors
            }
            
            result.append(FitnessStatus(
                code=api_assessments[0]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=api_assessments[0]["description"],
                assessmentObjects=[assessment_obj_api01,assessment_obj_api02]
            ))
            logger.info('API.01 пройден: найдены опубликованные API')
        else:
            # Создаем AssessmentObjects как словарь
            assessment_obj_api01: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_api01
            }

            assessment_obj_api02: AssessmentObjects = {
                "isCheck": False,
                "details": api_errors
            }
            result.append(FitnessStatus(
                code=api_assessments[0]["code"],
                isCheck=False,
                resultDetails='У приложения нет ни одного API',
                assessmentDescription=api_assessments[0]["description"],
                assessmentObjects=[assessment_obj_api01,assessment_obj_api02]
            ))
            logger.warning('API.01 не пройден: отсутствуют API')

        # Проверка API.02: Для некоторых методов определен SLA
        logger.info('Проверка API.02: Для некоторых методов определен SLA')
        if len(found_objects_api02) > 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_api02: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_api02
            }
            result.append(FitnessStatus(
                code=api_assessments[1]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=api_assessments[1]["description"],
                assessmentObjects=[assessment_obj_api02]
            ))
            logger.info('API.02 пройден: определен SLA для методов')
        else:
            # Создаем AssessmentObjects как словарь
            assessment_obj_api02: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_api02
            }
            result.append(FitnessStatus(
                code=api_assessments[1]["code"],
                isCheck=False,
                resultDetails='Ни для одного метода не определен SLA',
                assessmentDescription=api_assessments[1]["description"],
                assessmentObjects=[assessment_obj_api02]
            ))
            logger.warning('API.02 не пройден: отсутствует SLA для методов')

        # Проверка API.03: Для всех TC есть спецификация
        logger.info('Проверка API.03: Для всех TC есть спецификация')
        if len(found_objects_api03) == 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_api03: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_api03
            }
            result.append(FitnessStatus(
                code=api_assessments[2]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=api_assessments[2]["description"],
                assessmentObjects=[assessment_obj_api03]
            ))
            logger.info('API.03 пройден: для всех TC есть спецификация')
        else:
            msg_tc = '<ol>'
            for obj in found_objects_api03:
                for key, value in obj.items():
                    msg_tc += f'<li>{value}</li>'
            msg_tc += '</ol>'
            # Создаем AssessmentObjects как словарь
            assessment_obj_api03: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_api03
            }
            result.append(FitnessStatus(
                code=api_assessments[2]["code"],
                isCheck=False,
                resultDetails='У приложения есть интерфейсы с TC, но без спецификации: ' + msg_tc,
                assessmentDescription=api_assessments[2]["description"],
                assessmentObjects=[assessment_obj_api03]
            ))
            logger.warning(f'API.03 не пройден: {len(found_objects_api03)} интерфейсов с TC но без спецификации')

    logger.info(f'Проверка API завершена для системы {cmdb}. Результатов: {len(result)}')
    return result