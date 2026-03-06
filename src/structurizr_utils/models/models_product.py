from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Any
import os
import requests
import logging
import json
from datetime import datetime

# https://fdm-products-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru/v2/api-docs
# https://fdm-products-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru/swagger-ui/index.html
# https://fdm-products-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru
# URL_PRODUCT = os.getenv(key='URL_PRODUCTS', default='https://fdm-products-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru')
URL_PRODUCT = os.getenv(key='URL_PRODUCTS', default='https://fdm-products-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru')

class ApiSecretDTO(BaseModel):
    api_secret: str
    id: int


class ParameterDTO(BaseModel):
    name: str
    type: str


class SlaDTO(BaseModel):
    error_rate: Optional[float]
    latency: Optional[float]
    rps: Optional[float]


class SlaV2DTO(BaseModel):
    errorRate: Optional[float]
    latency: Optional[float]
    rps: Optional[float]


class MethodDTO(BaseModel):
    capabilityCode: str
    description: str
    name: str
    parameters: List[ParameterDTO]
    returnType: str
    sla: SlaDTO
    type: str


class InterfaceDTO(BaseModel):
    capabilityCode: str
    code: str
    methods: List[MethodDTO]
    name: str
    protocol: str
    sla: SlaDTO
    specification: str
    version: str


class ContainerDTO(BaseModel):
    code: str
    interfaces: List[InterfaceDTO]
    name: str
    version: str


class TechDTO(BaseModel):
    id: int
    label: str


class ProductDTO(BaseModel):
    alias: str
    product_id: int
    tech: List[TechDTO]


class ProductPutDto(BaseModel):
    description: Optional[str] = None
    gitUrl: Optional[str] = None
    name: Optional[str] = None
    structurizrApiKey: Optional[str] = None
    structurizrApiSecret: Optional[str] = None
    structurizrApiUrl: Optional[str] = None
    structurizrWorkspaceName: Optional[str] = None


class ProductTechRelationDTO(BaseModel):
    cmdb_code: str


class TechProduct(BaseModel):
    id: int
    product: Optional['Product'] = None
    techId: int
    source: Optional[str] = None
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    lastModifiedDate: Optional[str] = None


class Product(BaseModel):
    alias: str
    description: Optional[str] = None
    gitUrl: Optional[str] = None
    id: int
    name: str
    source : Optional[str] = None
    uploadSource: Optional[str] = None
    structurizrApiKey: Optional[str] = None
    structurizrApiSecret: Optional[str] = None
    structurizrApiUrl: Optional[str] = None
    structurizrWorkspaceName: Optional[str] = None
    techProducts: List[TechProduct]
    discoveredInterfaces: List['DiscoveredInterface'] = []


class GetProductDTO(BaseModel):
    alias: str
    id: int
    name: str


class ResponseEntity(BaseModel):
    body: Optional[Any] = None
    statusCode: str
    statusCodeValue: int


# Новые модели из Swagger спецификации
class ConnectionRequestDTO(BaseModel):
    archInterfaceId: int
    mapicInterfaceId: int


class DiscoveredInterfaceDTO(BaseModel):
    apiId: int
    apiLink: Optional[str] = None
    context: Optional[str] = None
    description: Optional[str] = None
    externalId: int
    id: int
    name: Optional[str] = None
    productId: int
    status: Optional[str] = None
    version: Optional[str] = None


class DiscoveredInterfaceOperationDTO(BaseModel):
    context: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    parameters: List['OperationParameterDTO']
    returnType: Optional[str] = None
    type: Optional[str] = None


class DiscoveredOperation(BaseModel):
    connectionOperationId: Optional[int] = None
    context: Optional[str] = None
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    description: Optional[str] = None
    discoveredInterface: Optional['DiscoveredInterface'] = None
    id: int
    interfaceId: int
    name: str
    parameters: List['DiscoveredParameter']
    returnType: Optional[str] = None
    type: Optional[str] = None
    updatedDate: Optional[str] = None


class DiscoveredParameter(BaseModel):
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    discoveredOperation: Optional['DiscoveredOperation'] = None
    id: int
    parameterName: Optional[str] = None
    parameterType: Optional[str] = None


class DiscoveredInterface(BaseModel):
    apiId: int
    apiLink: Optional[str] = None
    connectedInterface: Optional['Interface'] = None
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


class Interface(BaseModel):
    code: Optional[str] = None
    containerId: Optional[int] = None
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    description: Optional[str] = None
    id: int
    name: Optional[str] = None
    protocol: Optional[str] = None
    specLink: Optional[str] = None
    statusId: Optional[int] = None
    tcId: Optional[int] = None
    typeId: Optional[int] = None
    updatedDate: Optional[str] = None
    version: Optional[str] = None


class OperationParameterDTO(BaseModel):
    parameterName: Optional[str] = None
    parameterType: Optional[str] = None


class FitnessFunctionDTO(BaseModel):
    code: str
    isCheck: bool
    resultDetails: Optional[str] = None


class FitnessFunctionResponseDTO(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    id: int
    isCheck: bool
    resultDetails: Optional[str] = None
    status: Optional[str] = None


class AssessmentResponseDTO(BaseModel):
    assessmentId: int
    createdDate: Optional[str] = None
    fitnessFunctions: List[FitnessFunctionResponseDTO]
    productId: int
    source: Optional['SourceDTO'] = None


class SourceDTO(BaseModel):
    source_id: int
    source_type: Optional[str] = None


class PatternDTO(BaseModel):
    code: Optional[str] = None
    createDate: Optional[str] = None
    deleteDate: Optional[str] = None
    id: int
    isAntiPattern: bool
    name: Optional[str] = None
    rule: Optional[str] = None
    technologies: List['TechnologyDTO']
    updateDate: Optional[str] = None


class TechnologyDTO(BaseModel):
    id: int
    label: Optional[str] = None
    ring: Optional['RingDTO'] = None
    sector: Optional['SectorDTO'] = None


class RingDTO(BaseModel):
    id: int
    name: Optional[str] = None
    order: Optional[int] = None


class SectorDTO(BaseModel):
    id: int
    name: Optional[str] = None
    order: Optional[int] = None


class PostPatternProductDTO(BaseModel):
    code: str
    isCheck: bool
    resultDetails: str


class ContainerInterfacesDTO(BaseModel):
    code: Optional[str] = None
    id: int
    interfaces: List['InterfaceMethodDTO']
    name: Optional[str] = None


class InterfaceMethodDTO(BaseModel):
    description: Optional[str] = None
    id: int
    mapicInterface: 'MapicInterfaceDTO'
    name: Optional[str] = None
    operations: List['OperationFullDTO']
    techCapability: 'TcDTO'
    version: Optional[str] = None


class MapicInterfaceDTO(BaseModel):
    description: Optional[str] = None
    id: int
    name: Optional[str] = None


class OperationFullDTO(BaseModel):
    description: Optional[str] = None
    id: int
    mapicOperation: 'MapicOperationFullDTO'
    name: Optional[str] = None
    sla: SlaV2DTO
    techCapability: 'TcDTO'
    type: Optional[str] = None


class MapicOperationFullDTO(BaseModel):
    context: Optional[str] = None
    contextApi: Optional[str] = None
    description: Optional[str] = None
    id: int
    name: Optional[str] = None
    type: Optional[str] = None


class TcDTO(BaseModel):
    code: Optional[str] = None
    id: int
    name: Optional[str] = None


class ProductInterfaceDTO(BaseModel):
    description: Optional[str] = None
    id: int
    mapicInterface: MapicInterfaceDTO
    name: Optional[str] = None
    operations: List['OperationDTO']
    version: Optional[str] = None


class OperationDTO(BaseModel):
    description: str
    id: int
    mapicOperation: 'MapicOperationDTO'
    name: str
    type: str


class MapicOperationDTO(BaseModel):
    description: Optional[str] = None
    id: int
    name: Optional[str] = None
    type: Optional[str] = None


class ProductMapicInterfaceDTO(BaseModel):
    apiId: int
    connectInterface: MapicInterfaceDTO
    context: str
    contextProvider: str
    description: str
    externalId: int
    id: int
    name: str
    operations: List['ConnectOperationDTO']
    version: str


class ConnectOperationDTO(BaseModel):
    connectOperation: MapicOperationDTO
    description: str
    id: int
    name: str
    type: str


class ProductInfoDTO(BaseModel):
    alias: Optional[str] = None
    description: Optional[str] = None
    gitUrl: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    structurizrApiUrl: Optional[str] = None
    structurizrWorkspaceName: Optional[str] = None
    techProducts: List['TechInfoDTO']


class TechInfoDTO(BaseModel):
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    id: int
    lastModifiedDate: Optional[str] = None
    source: Optional[str] = None
    techId: int


class GetProductTechDto(BaseModel):
    products: List['GetProductsDTO']
    techId: int


class GetProductsDTO(BaseModel):
    alias: str
    description: str
    id: int
    name: str


class InfraDTO(BaseModel):
    cmdbId: Optional[str] = None
    name: Optional[str] = None
    properties: List['PropertyDTO']
    type: Optional[str] = None


class PropertyDTO(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None


class InfraRequestDTO(BaseModel):
    infra: List[InfraDTO]
    relations: List['RelationDTO']


class RelationDTO(BaseModel):
    children: List[str]
    cmdbId: Optional[str] = None


class ProductRelationDTO(BaseModel):
    cmdbId: Optional[str] = None
    name: Optional[str] = None
    properties: List[PropertyDTO]
    type: Optional[str] = None


# Модели для нового формата relations согласно примеру в комментарии
class ParameterDTO(BaseModel):
    name: str
    type: str


class SLADTO(BaseModel):
    error_rate: Optional[float]=None
    latency: Optional[float]=None
    rps: Optional[float]=None


class MethodDTO(BaseModel):
    capabilityCode: str
    description: str
    name: str
    parameters: List[ParameterDTO]
    returnType: str
    sla: SLADTO
    type: str


class InterfaceDTO(BaseModel):
    capabilityCode: str
    code: str
    methods: List[MethodDTO]
    name: str
    protocol: str
    sla: SLADTO
    specification: str
    version: str


class ProductRelationNewDTO(BaseModel):
    code: str
    interfaces: List[InterfaceDTO]
    name: str
    version: str


class ProductRelationsRequestDTO(BaseModel):
    infra: List[ProductRelationDTO]
    relations: List[RelationDTO]


# Новая модель для соответствия примеру в комментарии
class ProductRelationsNewRequestDTO(BaseModel):
    relations: List[ProductRelationNewDTO]


class ProductRelationsResponseDTO(BaseModel):
    infra: List[ProductRelationDTO]
    relations: List[RelationDTO]


class PublishedApiDTO(BaseModel):
    apiContext: Optional[str] = None
    apiId: int
    id: int
    statusName: Optional[str] = None

class ErrorEntityDTO(BaseModel):
    containerError: Optional[List[str]] = None
    interfaceError: Optional[List[str]] = None
    methodError: Optional[List[str]] = None
    parameterError: Optional[List[str]] = None


SourceType = Literal["pipeline", "script"]


# Функции для работы с API
def get_product(cmdb: str) -> Optional[Product]:
    """
    Получить продукт по cmdb коду
    
    :param cmdb: cmdb код продукта
    :return: Объект продукта или None в случае ошибки
    """
    #logging.warning(f'# Load product {cmdb}')
    url = URL_PRODUCT+'/api/v1/product/'+cmdb
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    response = requests.get(url, headers=headers, verify=False)
    #logging.warning(f'# url {url}')

    if response.status_code == 200:
        #logging.warning(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        return Product.model_validate(response.json())
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')

    return None


def get_products() -> List[Product]:
    """
    Получить все продукты пользователя
    
    :return: Список продуктов пользователя
    """
    logging.info('# Load user products')
    url = URL_PRODUCT + '/api/v1/user/product'
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    response = requests.get(url, headers=headers, verify=False)
    logging.info(f'# url {url}')

    if response.status_code == 200:
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        products_data = response.json()
        return [Product.model_validate(product) for product in products_data]
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return []


def patch_product(cmdb: str, product: ProductPutDto) -> bool:
    logging.info(f'# Publishing product {cmdb}')
    url = URL_PRODUCT+'/api/v1/product/'+cmdb+'/workspace'
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}

    json_request = product.model_dump_json()

    response = requests.patch(url, data=json_request.encode(
        'utf-8'), headers=headers, verify=False)
    logging.info(f'# url {url}')

    if response.status_code in [200, 204]:  # 200 OK и 204 No Content считаются успешными
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        return True
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return False


def put_product(cmdb: str, product: ProductPutDto):
    logging.info(f'# Put product {cmdb}')
    url = URL_PRODUCT+'/api/v1/product/'+cmdb
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}

    json_request = product.model_dump_json()

    response = requests.put(url, data=json_request.encode(
        'utf-8'), headers=headers, verify=False)
    logging.info(f'# url {url}')

    response.raise_for_status()



# Метод для публикации relations продукта
# Пример JSON тела
# [
#   {
#     "code": "string",
#     "interfaces": [
#       {
#         "capabilityCode": "string",
#         "code": "string",
#         "methods": [
#           {
#             "capabilityCode": "string",
#             "description": "string",
#             "name": "string",
#             "parameters": [
#               {
#                 "name": "string",
#                 "type": "string"
#               }
#             ],
#             "returnType": "string",
#             "sla": {
#               "error_rate": 0,
#               "latency": 0,
#               "rps": 0
#             },
#             "type": "string"
#           }
#         ],
#         "name": "string",
#         "protocol": "string",
#         "sla": {
#           "error_rate": 0,
#           "latency": 0,
#           "rps": 0
#         },
#         "specification": "string",
#         "version": "string"
#       }
#     ],
#     "name": "string",
#     "version": "string"
#   }
# ]

def get_product_infra(name: str) -> List[str]:
    #//api/v1/product/infra
    logging.debug(f'# Get product product infra {name}')
    url = f"{URL_PRODUCT}/api/v1/product/infra?name={name}"

    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    

    response = requests.get(url, headers = headers, verify=False)
    
    logging.info(f'# url {url}')

    if response.status_code in [200, 204]:  # 200 OK и 204 No Content считаются успешными
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        #logging.info(f'\u001b[32m# result {response.json().get("parentSystems",[])}\u001b[37m')
        return response.json().get("parentSystems",[])
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return []

def get_product_containers(cmdb : str) -> Dict:
    logging.debug(f'# Get product pcontainers {cmdb}')
    url = f"{URL_PRODUCT}/api/v1/product/{cmdb}/container"

    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    

    response = requests.get(url, headers = headers, verify=False)
    
    logging.info(f'# url {url}')

    if response.status_code in [200, 204]:  # 200 OK и 204 No Content считаются успешными
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        #logging.info(f'\u001b[32m# result {response.json().get("parentSystems",[])}\u001b[37m')
        return response.json()
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return {}

def get_product_tc_implementation(product_id: int) -> List[int]:
    #//api/v1/product/infra
    logging.debug(f'# Get product product tc implementation {product_id}')
    url = f"{URL_PRODUCT}/api/v1/product/{product_id}/tc-implementation"

    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    

    response = requests.get(url, headers = headers, verify=False)
    
    logging.info(f'# url {url}')

    if response.status_code in [200, 204]:  # 200 OK и 204 No Content считаются успешными
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        #logging.info(f'\u001b[32m# result {response.json().get("parentSystems",[])}\u001b[37m')
        return [int(item) for item in response.json()]
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return []

def post_product_tech_relation(cmdb: str, techId: int):
    logging.debug(f'# Post product tech relations {cmdb}')
    url = f"{URL_PRODUCT}/api/v1/product-tech-relation/{techId}"
    params = { "cmdb_code" : f"{cmdb}" }
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    
    json_request = json.dumps(params)

    response = requests.post(url, data=json_request.encode('utf-8'), headers = headers, verify=False)
    
    logging.info(f'# url {url}')

    if response.status_code in [200, 204]:  # 200 OK и 204 No Content считаются успешными
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        return None
    elif response.status_code == 207:
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        result = ErrorEntityDTO.model_validate(response.json().get('errorEntity', {}))
        logging.info(f"{result.__dict__}")
        return result
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return None

def put_product_relations(cmdb: str, relations: ProductRelationsNewRequestDTO, from_on_premises : bool) -> Optional[ErrorEntityDTO]:
    """
    Обновление relations продукта
    
    :param cmdb: cmdb код продукта
    :param relations: данные relations для обновления
    :return: True в случае успеха, False в случае ошибки
    """
    logging.debug(f'# Put product relations {cmdb}')
    url = URL_PRODUCT + '/api/v1/product/' + cmdb + '/relations'

    if from_on_premises:
        url += "?source=script"
    else:
        url += "?source=pipeline"
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}

    # Отправляем массив relations напрямую, как показано в примере комментария
    # Преобразуем список relations в JSON
    relations_list = [relation.model_dump() for relation in relations.relations]
    json_request = json.dumps(relations_list)

    # logging.info(f'# Relations list {json_request.encode(
    #     'utf-8')}')
    
    # return
    logging.info(f"PUT {url}")

    response = requests.put(url, data=json_request.encode(
        'utf-8'), headers=headers, verify=False)
    
    # with open("request.json","w") as f:
    #     f.write(f"{json_request.encode('utf-8')}")

    logging.info(f'# url {url}')

    if response.status_code in [200, 204]:  # 200 OK и 204 No Content считаются успешными
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        return None
    elif response.status_code == 207:
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        result = ErrorEntityDTO.model_validate(response.json().get('errorEntity', {}))
        logging.info(f"{result.__dict__}")
        return result
    else:
        logging.error(f'\u001b[31m# result {response.status_code} {response.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {response.text}\u001b[37m')
        return None


class FitnessFunctionClient:
    def __init__(self, api_key: str = None, verify_ssl: bool = False):
        """
        Инициализация клиента для работы с fitness-functions API

        :param api_key: API ключ для аутентификации (опционально)
        :param verify_ssl: Проверять SSL сертификаты (по умолчанию False)
        """
        self.base_url = URL_PRODUCT.rstrip('/')
        self.session = requests.Session()
        self.session.verify = verify_ssl
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def get_fitness_functions(self, cmdb: str, source_type: Optional[SourceType] = None, source_id: Optional[int] = None) -> Dict:
        """
        Получение результатов фитнесс-функций

        :param cmdb: cmdb продукта
        :param source_type: Тип источника (опционально)
        :param source_id: ID источника (опционально)
        :return: Словарь с результатами
        """
        url = f"{self.base_url}/api/v1/product/{cmdb}/fitness-function"
        params = {}
        if source_id:
            params['source_id'] = source_id
        if source_type:
            params['source_type'] = source_type

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def post_fitness_functions(self, cmdb: str, source_type: SourceType, requests: List[FitnessFunctionDTO], source_id: Optional[int] = None):
        """
        Публикация результатов фитнесс-функций

        :param cmdb: cmdb продукта
        :param source_type: Тип источника
        :param requests: Список фитнесс-функций
        :param source_id: ID источника (опционально)
        :return: Словарь с результатом операции
        """
        url = f"{self.base_url}/api/v1/product/{cmdb}/fitness-function/{source_type}"
        params = {}
        if source_id:
            params['source_id'] = source_id
            
        logging.info(f"POST {url}")
        response = self.session.post(url, json=requests, params=params)
        logging.info(f'# url {url}')
        response.raise_for_status()
        logging.info(f'\u001b[32m# result {response.status_code} {response.reason}\u001b[37m')
        return 

    def close(self):
        """Закрытие сессии"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Разрешаем циклические ссылки
Product.model_rebuild()
DiscoveredInterface.model_rebuild()
DiscoveredOperation.model_rebuild()
DiscoveredParameter.model_rebuild()
