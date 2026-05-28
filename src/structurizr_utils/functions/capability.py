"""
Модуль для проверки наличия и корректности технических возможностей (capabilities) 
в C4 модели продукта в нотации Structurizr DSL.

Основные функции:
- check_capability: Проверяет наличие компонентов с типом 'capability' в модели
- publish_capabilities: Публикует найденные capabilities в backend
- load_capabilities: Загружает существующие capabilities из landscape
"""

from structurizr_utils.functions.beeatlas_objects import TechnicalCapability, SystemPurpose
from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.model_capability import CapabilityClient,ResponsibilityCapabilityDTO,PutTechCapabilityDTO
from datetime import datetime
from typing import List, Optional, Dict, Any, Set,TypedDict
import requests
import json
import re
import logging
import psycopg2
import os

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def publish_capabilities_sparx(cmdb: str, found_capabilities: List[TechnicalCapability], backend_url: str) -> None:
    """
    Публикует найденные технические возможности в backend систему.
    
    Args:
        found_capabilities: Список технических возможностей для публикации
        backend_url: URL backend системы для публикации
        
    Raises:
        requests.RequestException: При ошибках HTTP запросов
    """

    logger.info(f'Публикация {len(found_capabilities)} технических возможностей')
    
    for tc in found_capabilities: 
        url = f'{backend_url}/api/v4/tc/{cmdb}.{tc.code}'
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        request_tc = tc.copy()
        request_tc.code = f"{cmdb}.{tc.code}"
        json_request = json.dumps(request_tc.dict(), ensure_ascii=False, default=str)
        
        try:
            response = requests.put(url, data=json_request.encode('utf-8'), 
                                  headers=headers, verify=False, timeout=30)
            
            logger.info(f'URL запроса Sparx: {url}')
            logger.info(f'Данные запроса Sparx: {json_request}')

            #continue
            
            if response.status_code == 200:
                logger.info(f'Успешно опубликована TC {tc.code}: {response.status_code} {response.reason}')
            else:
                logger.error(f'Ошибка публикации TC {tc.code}: {response.status_code} {response.reason}')
                logger.error(f'Детали ошибки: {response.text}')
                
        except requests.RequestException as e:
            logger.error(f'Ошибка HTTP запроса для TC {tc.code}: {e}')

def load_capabilities_sparx(cmdb: str, backend_url: str) -> SystemPurpose:
    """
    Загружает существующие технические возможности системы из landscape.
    
    Args:
        cmdb: Идентификатор системы в CMDB
        backend_url: URL backend системы
        
    Returns:
        SystemPurpose: Объект с информацией о назначении системы и её capabilities
    """
    logger.info(f'Загрузка capabilities из landscape для системы {cmdb}')
    url = f'{backend_url}/api/v4/systems/{cmdb}/purpose'
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        logger.debug(f'URL запроса: {url}')

        if response.status_code == 200:
            logger.info(f'Успешно загружены capabilities: {response.status_code} {response.reason}')
            return SystemPurpose.model_validate(response.json())
        else:
            logger.error(f'Ошибка загрузки capabilities: {response.status_code} {response.reason}')
            logger.error(f'Детали ошибки: {response.text}')
            
    except requests.RequestException as e:
        logger.error(f'Ошибка HTTP запроса при загрузке capabilities: {e}')
    except Exception as e:
        logger.error(f'Ошибка при обработке ответа: {e}')

    return SystemPurpose()


def publish_capabilities(cmdb: str, found_capabilities: List[TechnicalCapability]) -> None:
    try:
        client = CapabilityClient()
        

        for cap in found_capabilities:
            dto  = PutTechCapabilityDTO()
            dto["author"]       = cap.author
            dto["code"]         = f"{cmdb}.{cap.code}"
            dto["description"]  = cap.description
            dto["name"]         = cap.name
            dto["owner"]        = cap.owner
            dto["status"]       = cap.status
            dto['targetSystemCode'] = cmdb

            dto["parents"] = []
            for pi in cap.parents:
                dto["parents"].append(pi['code'])
            
            logging.info(f"Публикую TC :[{dto}]")
            client.put_tech_capability(techCapability=dto,source="structurizr")

            
    except requests.RequestException as e:
        logger.error(f'Ошибка HTTP запроса при загрузке capabilities: {e}')
    except Exception as e:
        logger.error(f'Ошибка при обработке ответа: {e}')
    return 

def load_capabilities(product_id : int) -> List[ResponsibilityCapabilityDTO]:
    try:
        client = CapabilityClient()
        responsibility = client.get_tech_capability_resp(product_id)
        if responsibility["responsibility"]:
            return responsibility["responsibility"]
        else:
            return []
            
    except requests.RequestException as e:
        logger.error(f'Ошибка HTTP запроса при загрузке capabilities: {e}')
    except Exception as e:
        logger.error(f'Ошибка при обработке ответа: {e}')

    return []

def check_capability(cmdb: str, data: Dict[str, Any], backend_url: str, 
                    share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет наличие и корректность технических возможностей (capabilities) 
    в C4 модели продукта в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. CPB.01 - Определены технические возможности продукта
    2. CPB.02 - Для всех внешних интеграций определены TC
    3. CPB.03 - Есть capability в Structurizr
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы
        share_url: URL для публикации (не используется)
        publish: Флаг публикации найденных capabilities
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку capabilities для системы CMDB: {cmdb}')
    
    # Определение критериев оценки (assessments)
    capability_assessments: List[Assessment] = [
        Assessment(code='CPB.01', description='Определены технические возможности продукта'),
        Assessment(code='CPB.02', description='Для всех внешних интеграций определены TC'),
        Assessment(code='CPB.03', description='Есть capability в Structurizr')
    ]

    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    found_capability: bool = False
    external_system: Dict[str, Any] = {}  # реестр внешних систем
    referenced_c: Set[str] = set()        # контейнеры для которых должны быть tc
    tc_containers: Set[str] = set()       # контейнеры без tc
    found_capabilities: List[TechnicalCapability] = []
    
    # Инициализация переменных для assessment
    found_objects_cpb01: List[Dict[str, str]] = []
    found_objects_cpb02: List[Dict[str, str]] = []
    found_objects_cpb03: List[Dict[str, str]] = []
    
    # Переменные для CPB.02
    # containers_with_external_relations: Set[str] = set()  # контейнеры с исходящими связями к внешним системам
    containers_with_capability: Set[str] = set()  # контейнеры с capability компонентами

    # Извлечение метаданных модели
    author: str = data.get('model', {}).get('properties', {}).get('architect', '-')
    modify_date: datetime = datetime.now()

    # Анализ внешних систем и их связей
    logger.debug('Анализ внешних систем и их связей с целевой системой')
    systems: List[Dict[str, Any]] = data.get('model', {}).get('softwareSystems', [])
    
    for system in systems:
        system_cmdb: str = system.get('properties', {}).get('cmdb', '').lower()
        if system_cmdb != cmdb.lower():
            # Система является внешней
            system_id: str = system.get('id', '')
            external_system[system_id] = system
            logger.debug(f'Найдена внешняя система: {system_id} (CMDB: {system_cmdb})')
            
            # Анализ связей внешней системы
            relationships: List[Dict[str, Any]] = system.get('relationships', [])
            for relationship in relationships:
                destination_id: str = relationship.get('destinationId', '')
                if destination_id:
                    referenced_c.add(destination_id)
                    logger.info(f'Внешняя система {system_id} ссылается на контейнер {destination_id}')

    # Анализ целевой системы и поиск capabilities
    logger.debug('Анализ целевой системы и поиск capabilities в компонентах')
    
    for system in systems:
        system_cmdb: str = system.get('properties', {}).get('cmdb', '').lower()
        if system_cmdb == cmdb.lower():
            logger.debug(f'Анализируем целевую систему: {system.get("id", "")}')
            containers: List[Dict[str, Any]] = system.get('containers', [])
            
            for container in containers:
                container_id: str = container.get('id', '')
                container_name: str = container.get('name', '')
                need_capability: bool = True
                
                logger.debug(f'Анализ контейнера: {container_name} (ID: {container_id})')
                
                # Поиск компонентов с типом 'capability'
                components: List[Dict[str, Any]] = container.get('components', [])
                has_capability_component: bool = False
                
                for component in components:
                    component_props: Dict[str, Any] = component.get('properties', {})
                    component_type: str = component_props.get('type', '')
                    component_code: str = component_props.get('code', '')
                    component_parents: str = component_props.get('parents', '')
                    
                    # Проверка, является ли компонент capability
                    if component_type == 'capability':
                        has_capability_component = True
                    
                    # Проверка, является ли компонент capability с полными данными
                    if (component_type == 'capability' and 
                        len(component_code) > 0 and 
                        len(component_parents) > 0):
                        
                        found_capability = True
                        need_capability = False
                        
                        logger.info(f'Найден capability компонент: {component_code} в контейнере {container_name}')
                        
                        # Парсинг родительских capabilities
                        delimiters = r'[ ,\t;]+'
                        parents = [{"code": code.strip()} 
                                 for code in re.split(delimiters, component_parents)]
                        
                        # Создание объекта TechnicalCapability
                        tc = TechnicalCapability(
                            code=component_code,
                            name=component.get('name', 'Default capability name'),
                            description=component.get('description', 'Default capability description'),
                            author=author,
                            status="Approved",
                            parents=parents,
                            system={"code": cmdb},
                            owner=author,
                            version=component_props.get('version', '1.0'),
                            goal_from=component_props.get('goal_from', ''),
                            goal_to=component_props.get('goal_to', '')
                        )
                        found_capabilities.append(tc)
                        
                        # Заполнение данных для assessment
                        capability_name = component.get('name', f'Capability {component_code}')
                        # found_objects_cpb01.append({f"{cmdb}.{tc.code}": f"<a href='https://beeatlas.vimpelcom.ru/models/search?request={cmdb}.{tc.code}' target='_blank'>{capability_name}</a><br>"})
                        found_objects_cpb03.append({f"{cmdb}.{tc.code}": f"<a href='https://beeatlas.vimpelcom.ru/models/search?request={cmdb}.{tc.code}' target='_blank'>{capability_name}</a><br>"})
                
                # Отслеживание контейнеров с capability компонентами
                if has_capability_component:
                    containers_with_capability.add(container_id)
                   # found_objects_cpb02.append({container_id: f"{container_id} {container_name}"})
                
                # Проверка необходимости capability для контейнера
                if need_capability:
                    logger.debug(f'Контейнер {container_name} не имеет capability компонентов')
                    
                    # Проверка связей от внешних систем к контейнеру
                    if container_id in referenced_c:
                        tc_containers.add(container_name)
                        found_objects_cpb02.append({container_id: f"{container_id} {container_name}"})
                        logger.debug(f'Контейнер {container_name} имеет входящие связи от внешних систем')
                    
                    # Проверка связей от контейнера к внешним системам
                    container_relationships: List[Dict[str, Any]] = container.get('relationships', [])
                    for relationship in container_relationships:
                        destination_id: str = relationship.get('destinationId', '')
                        source_id : str = relationship.get('sourceId','')
                        if source_id in external_system.keys() and destination_id == container_id:
                            #tc_containers.add(container_name)
                            #containers_with_external_relations.add(container_id)
                            found_objects_cpb02.append({container_id: f"{container_id} {container_name}"})
                            logger.debug(f'Контейнер {container_name} имеет исходящие связи к внешним системам')
                            break

    # Загрузка существующих capabilities из landscape
    # Проверка наличия опубликованных capabilities
    logger.debug('Загрузка существующих capabilities из landscape')
    have_published_capability = False
    for cpb in  load_capabilities(product_id=product_id):
        have_published_capability = True
        found_capability = True
        found_objects_cpb01.append({f"{cpb['code']}": f"<a href='https://beeatlas.vimpelcom.ru/models/search?request={cpb['code']}' target='_blank'>{cpb['name']}</a><br>"})



    # Проверка CPB.01: Определены технические возможности продукта
    logger.info('Проверка CPB.01: Определены технические возможности продукта')
    if have_published_capability or found_capability:
        msg: str = 'Есть capability в landscape' if have_published_capability else 'Есть capability в structurizr'
        # Создаем AssessmentObjects как словарь
        assessment_obj_cpb01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_cpb01
        }
        result.append(FitnessStatus(
            code=capability_assessments[0]["code"],
            isCheck=True,
            resultDetails=msg,
            assessmentDescription=capability_assessments[0]["description"],
            assessmentObjects=[assessment_obj_cpb01]
        ))
        logger.info(f'CPB.01 пройден: {msg}')
    else:
        result.append(FitnessStatus(
            code=capability_assessments[0]["code"],
            isCheck=False,
            resultDetails='Для системы нет capability ни в structurizr, ни в landscape',
            assessmentDescription=capability_assessments[0]["description"],
            assessmentObjects=[]
        ))
        logger.warning('CPB.01 не пройден: отсутствуют capabilities')

    # Проверка CPB.03: Есть capability в Structurizr
    logger.info('Проверка CPB.03: Есть capability в Structurizr')
    if len(found_objects_cpb03) == 0:
        result.append(FitnessStatus(
            code=capability_assessments[2]["code"],
            isCheck=False,
            resultDetails=f'Отсутствуют описанные technical capability для системы cmdb={cmdb}',
            assessmentDescription=capability_assessments[2]["description"],
            assessmentObjects=[]
        ))
        logger.warning('CPB.03 не пройден: отсутствуют capabilities в Structurizr')
    else:
                
        # Создаем AssessmentObjects как словарь
        assessment_obj_cpb03: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_cpb03
        }
        result.append(FitnessStatus(
            code=capability_assessments[2]["code"],
            isCheck=True,
            resultDetails=f"В structurizr определено {len(found_objects_cpb03)} технических возможностей",
            assessmentDescription=capability_assessments[2]["description"],
            assessmentObjects=[assessment_obj_cpb03]
        ))
        logger.info('CPB.03 пройден: найдены capabilities в Structurizr')
        
        # Публикация capabilities если требуется
        if publish:

            logger.info('Публикации capabilities Beeatlas')
            publish_capabilities(cmdb=cmdb, found_capabilities=found_capabilities)
            
            if backend_url:
                logger.info('Запуск публикации capabilities Sparx')
                publish_capabilities_sparx(cmdb=cmdb, found_capabilities=found_capabilities, backend_url=backend_url)
    
    # Проверка CPB.02: Для всех внешних интеграций определены TC
    logger.info('Проверка CPB.02: Для всех внешних интеграций определены TC')
    

    if len(found_objects_cpb02) > 0:

        # Создаем AssessmentObjects как словарь
        assessment_obj_cpb02: AssessmentObjects = {
            "isCheck": False,
            "details": found_objects_cpb02
        }
        result.append(FitnessStatus(
            code=capability_assessments[1]["code"],
            isCheck=False,
            resultDetails=f'Отсутствуют TC для контейнеров с внешним взаимодействием {msg}',
            assessmentDescription=capability_assessments[1]["description"],
            assessmentObjects=[assessment_obj_cpb02]
        ))
        logger.warning(f'CPB.02 не пройден: {len(found_objects_cpb02)} контейнеров без TC')
    else:
        # Создаем AssessmentObjects как словарь
        assessment_obj_cpb02: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_cpb02
        }
        result.append(FitnessStatus(
            code=capability_assessments[1]["code"],
            isCheck=True,
            resultDetails='Для всех кнтейнеров, предоставляющих внешние интерфейсы, определены tc',
            assessmentDescription=capability_assessments[1]["description"],
            assessmentObjects=[assessment_obj_cpb02]
        ))
        logger.info('CPB.02 пройден: все контейнеры с внешними интеграциями имеют TC')

    # Проверка CPB.04:  Проверяет позиционирование TC.
    result += check_cpb04(cmdb, found_capabilities)
    
    # Проверка CPB.05:  Проверяет качество описания TC.
    result += check_cpb05(cmdb)
    
    logger.info(f'Проверка capabilities завершена для системы {cmdb}. Результатов: {len(result)}')
    return result

def check_cpb04(cmdb: str, product_capabilities: List[TechnicalCapability]) -> List[FitnessStatus]:    
    """
    Проводит оценку правильности позиционирования TC.
    
    
    Args:
        cmdb: Идентификатор системы в CMDB
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info('Проверка CPB.04: Проверка позиционирования TC')
    # Инициализация переменных для assessment
    result: List[FitnessStatus] = []
    assessmentObjects_cpb04 : List[AssessmentObjects] = []
    
    codeFF = "CPB.04"
    nameFF = "Позиционирование в ФДМ выполнено корректно"
    isFFCheck = True
    
    
    for tc in product_capabilities:
        for bc in tc.parents:
            if 'dmn.' in bc['code'].lower() or 'grp.' in bc['code'].lower() :
                isFFCheck = False #считаем не пройденной если хоть 1 TC неверно спозиционирована
                assessmentObjects_cpb04.append( AssessmentObjects(
                        isCheck=False, 
                        details= [{f'TC cпозиционирована в ФДМ неверно': f"{tc.code} {tc.name}"}]
                        ) )
                        
    if isFFCheck:  
        descr = ("Позиционирование технических возможностей проведено корректно")
    else:
        descr = ("Следующие технические возможности содержат ошибки в позиционировании в ФДМ:")
        
    result.append(FitnessStatus(
                    code=codeFF,
                    isCheck=isFFCheck,
                    resultDetails=descr,
                    assessmentDescription=descr,
                    assessmentObjects=assessmentObjects_cpb04
                    ))
    

    logger.info(f'Проверка CPB.04: Проверка позиционирования TC завершена. Обработано tc: {len(product_capabilities)}.')
    return result
    
def check_cpb05(cmdb: str) -> List[FitnessStatus]:
    """
    Проводит обработку результатов проверки качества описания TC с помощью Ai Tool.
    
    Note: извлекает данные из БД BeeAtlas, для этого требует установленных переменных окружения
    
    Args:
        cmdb: Идентификатор системы в CMDB
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info('Проверка CPB.05: Проверка качества описания TC')

    # Инициализация переменных для assessment
    result: List[FitnessStatus] = []
    

    # Получение переменных окружения
    server = os.getenv('FDMDB_SERVER')
    db = os.getenv('FDMDB_DB')
    user = os.getenv('FDMDB_USERNAME')
    password = os.getenv('FDMDB_PASS')
    
    if not all([server, db, user, password]):
        logger.error("Не все необходимые переменные окружения установлены")
        return result
    
    
    db_manager = DatabaseManager(server, db, user, password)
    try:
        # Подключение к базе данных
        db_manager.connect()
        
                        
        # SQL запрос
        sql = """
        SELECT tc.code, tc.name, tc.description, ctc.criterion_id, ctc.value, ctc.grade, ctc.comment 
        FROM capability.criterias_tc ctc, capability.tech_capability tc, product.product p 
        WHERE ctc.tc_id = tc.id 
        AND p.id = tc.responsibility_product_id 
        AND ctc.criterion_id = 101 
        AND p.Alias = lower(%s)
        ORDER BY p.Alias
        """
        
        # Выполнение запроса
        rows = db_manager.execute_query(sql,cmdb)
        if len(rows) > 0:
            # Обработка результатов
            marks = [0, 0, 0, 0, 0, 0]  # Mark0-Mark5
            assessmentObjects_cpb05 : List[AssessmentObjects] = []
           
            for row in rows:
                code, name, description, criterion_id, value, grade, comment = row
                # Подсчет оценок
                if 0 <= grade <= 5:
                    marks[grade] += 1
                    
            
            # Обработка продукта
            codeFF = "CPB.05"
            nameFF = "Качество описания TC продукта в ФДМ соответствует методике"
            for i in range(6):
                        if marks[i] > 0:
                            assessmentObjects_cpb05.append( AssessmentObjects(
                            isCheck= ( True if i>2 else False), # считаем что проверка не пройдена если есть tc c оценкой 0-2
                            details= [{f'Количество TC с оценкой {i}': f"{marks[i]}"}]
                            ) )



            isCheck = True
            descr = ''
            
            if marks[0]+ marks[1] + marks[2] > 0:  # считаем что проверка не пройдена если есть tc c оценкой 0-2
                descr = (f"Описание возможностей не соответствует методике "
                         f"(см. <a href='https://ms-seaapp001.bee.vimpelcom.ru:83/tcquality.php?cmdb={cmdb}'>детали</a>). " )
                isCheck = False

            else:
                descr = (f"Описание в целом соответствует методике "
                         f"(см. <a href='https://ms-seaapp001.bee.vimpelcom.ru:83/tcquality.php?cmdb={cmdb}'>детали</a>).")
                
            result.append(FitnessStatus(
                            code=codeFF,
                            isCheck=isCheck,
                            resultDetails=descr,
                            assessmentDescription=descr,
                            assessmentObjects=assessmentObjects_cpb05
            ))
        else:
            logger.info("Не найдено оцененных TC для расчета результатов.")    
    except Exception as e:
        logger.error(f"Ошибка выполнения: {e}")
    finally:
        db_manager.disconnect()
    


    logger.info(f'Проверка CPB.05: Проверка качества описания TC завершена.')
    return result


class DatabaseManager:
    def __init__(self, server: str, db: str, user: str, password: str):
        self.connection_params = {
            'host': server,
            'port': 5432,
            'database': db,
            'user': user,
            'password': password
        }
        self.connection = None
        
    def connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            logger.info('Соединение с базой данных установлено')
        except psycopg2.Error as e:
            logger.error(f'Ошибка подключения к базе данных: {e}')
            raise
            
    def disconnect(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info('Соединение с базой данных закрыто')
            
    def execute_query(self, query: str, param: str):
        """Выполняет SQL запрос и возвращает результат"""
        if not self.connection:
            raise Exception('Соединение с базой данных не установлено')
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (param,))
            return cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f'Ошибка выполнения запроса: {e}')
            raise
