"""
Модуль для проверки динамических диаграмм (sequence diagrams) в нотации Structurizr DSL.

Основные функции:
- check_sequences: Проверяет корректность динамических диаграмм
- validate_format_with_http_request: Проверяет формат HTTP запросов
- is_rest: Проверяет использование REST технологий
"""

from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.models_product import get_product_containers
from structurizr_utils.models.model_capability import CapabilityClient
from typing import List, Dict, Any, Set
import requests
import re
import logging

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def validate_format_with_http_request(text: str) -> bool:
    """
    Проверяет формат HTTP запроса в описании.
    
    Args:
        text: Текст для проверки
        
    Returns:
        bool: True если текст содержит корректный HTTP запрос
    """
    # Регулярное выражение для проверки формата HTTP методов
    pattern = r'[\s\S]*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) .*$'
    return bool(re.match(pattern, text))

def is_rest(technology: str) -> bool:
    """
    Проверяет использование REST технологий.
    
    Args:
        technology: Строка с технологией для проверки
        
    Returns:
        bool: True если используется REST технология
    """
    pattern = r'HTTP|HTTPS|REST'
    # Проверяем, содержит ли строка одну из подстрок
    if re.search(pattern, technology, re.IGNORECASE):  # re.IGNORECASE для игнорирования регистра
        logger.debug(f'Найдена REST технология: {technology}')
        return True
    else:
        return False


def get_product_capabilities(cmdb : str) -> Dict[str,List[str]]: # get capabilities codes
    result = dict()

    data = get_product_containers(cmdb)

    if data and len(data)>0:
        for cnt in data:
            cnt_name = cnt.get("code","-")
            if "interfaces" in cnt and len(cnt.get("interfaces",[])) >0 :
                for interface in cnt.get("interfaces",[]):
                    interface_code = interface.get("code","")
                    if "techCapability" in interface and interface.get("techCapability",None) is not None:
                        code = interface.get("techCapability",None).get("code",None)
                        if code in result:
                            result[code].append(f"Реализуется в контейнере {cnt_name}, интерфейсе {interface_code}")
                        else:
                            result[code] = [f"Реализуется в контейнере {cnt_name}, интерфейсе {interface_code}"]

                        if "operations" in interface and len(interface.get("operations",[]))>0:
                            for operation in interface.get("operations",[]):
                                if operation.get("techCapability",None):
                                    code = str(operation.get("techCapability",None).get("code",None))
                                    name = operation.get("name","")
                                    if code in result:
                                        result[code].append(f"Реализуется в контейнере {cnt_name}, api {name}")
                                    else:
                                        result[code] = [f"Реализуется в контейнере {cnt_name}, api {name}"]
                    else:         
                        if "operations" in interface and len(interface.get("operations",[]))>0:
                            for operation in interface.get("operations",[]):
                                if operation.get("techCapability",None):
                                    code = str(operation.get("techCapability",None).get("code",None))
                                    name = operation.get("name","")
                                    if code:
                                        if code in result:
                                            result[code].append(f"Реализуется в контейнере {cnt_name}, api {name}")
                                        else:
                                            result[code] = [f"Реализуется в контейнере {cnt_name}, api {name}"]
                                        
    return result

def pretty_print_msg(values: List) -> str:
    msg = ""
    for v in values:
        msg += f"{v}</br>"
    return msg

def check_sequences(cmdb: str, data: Dict[str, Any], backend_url: str, 
                   share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет корректность динамических диаграмм (sequence diagrams) в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. SQ.01 - Для всех technical capability указаны sequence
    2. SQ.02 - Все вызовы содержат HTTP запросы
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы
        share_url: URL для публикации диаграмм
        publish: Флаг публикации (не используется)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку динамических диаграмм для системы CMDB: {cmdb}')
    
    # Определение критериев оценки (assessments)
    sequence_assessments: List[Assessment] = [
        Assessment(code='SQ.01', description='Для всех technical capability указаны sequence'),
        Assessment(code='SQ.02', description='Все вызовы содержат HTTP запросы')
    ]
    
    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    
    # Инициализация переменных для assessment
    found_objects_sq01: List[Dict[str, str]] = []
    found_objects_sq02: List[Dict[str, str]] = []
    found_objects_sq02_error: List[Dict[str, str]] = []

    caps_list = get_product_capabilities(cmdb)

    if caps_list and len(caps_list) > 0:          
        # Создание словаря capabilities (последняя часть кода как ключ)
        capabilities_short: Dict[str, str] = {
            item.split('.')[-1]: item if '.' in item else item 
            for item in caps_list.keys()
        }
        capabilities: Dict[str, str] = {item: item for item in caps_list.keys()}
            
        # Инициализация переменных для анализа
        sequences: Dict[str, str] = {}
        links_errors: List[str] = []
        relationships: Dict[str, str] = {} 

        # Анализ связей в системах и контейнерах
        logger.debug('Анализ связей в системах и контейнерах')
        systems: List[Dict[str, Any]] = data.get("model", {}).get("softwareSystems", [])
            
        for system in systems:
            # Связи системы
            system_relationships: List[Dict[str, Any]] = system.get("relationships", [])
            for rel in system_relationships:
                relationships[rel["id"]] = rel.get("technology", "")

            # Связи контейнеров
            containers: List[Dict[str, Any]] = system.get("containers", [])
            for container in containers:
                container_relationships: List[Dict[str, Any]] = container.get("relationships", [])
                for rel in container_relationships:
                    relationships[rel["id"]] = rel.get("technology", "")

        # Анализ динамических диаграмм
        logger.debug('Анализ динамических диаграмм')
        dynamic_views: List[Dict[str, Any]] = data.get('views', {}).get('dynamicViews', [])
        
        for view in dynamic_views:
            key: str = view.get('key', '')
            is_tc_view: bool = False
            
            founded_cap = capabilities.get(key, capabilities_short.get(key, ''))
            
            if founded_cap:
                sequences[key] = founded_cap
                
                # Заполнение данных для assessment SQ.01
                found_objects_sq01.append({founded_cap: pretty_print_msg(caps_list.get(founded_cap,[]))})
                
                if key in capabilities.keys():
                    capabilities.pop(key)
                
                if founded_cap in capabilities.keys():
                        capabilities.pop(founded_cap)

                if key in capabilities_short.keys():
                    capabilities_short.pop(key)

                if founded_cap in capabilities_short.keys():
                        capabilities_short.pop(founded_cap)
                    
                is_tc_view = True
                logger.debug(f'Найдена sequence диаграмма для capability: {key}')


                if is_tc_view:
                    view_relationships: List[Dict[str, Any]] = view.get("relationships", [])
                    
                    for rel in view_relationships:
                        description: str = rel.get('description', '')
                        tech: str = relationships.get(rel['id'], '')
                        
                        if is_rest(tech):
                            if validate_format_with_http_request(description):
                                # Заполнение данных для assessment SQ.02
                                rel_id = rel.get('id', f'rel_{len(found_objects_sq02)}')
                                found_objects_sq02.append({key: f"{rel_id} {description} ({tech})"})
                                logger.debug(f'Найден корректный HTTP запрос: {description} ({tech})')
                            else:
                                error_msg = f"Для <b>{key}</b> не найден HTTP-endpoint в запросе <i>{description}</i>"
                                links_errors.append(error_msg)
                                # Заполнение данных для assessment SQ.02 (ошибки)
                                rel_id = rel.get('id', f'rel_error_{len(links_errors)}')
                                found_objects_sq02_error.append({key: f"{rel_id} {description} ({tech})"})
                                logger.debug(f'Ошибка HTTP endpoint: {error_msg}')
                
            # Выполнение проверок fitness functions
            
        # Проверка SQ.02: Все вызовы содержат HTTP запросы
        logger.info('Проверка SQ.02: Все вызовы содержат HTTP запросы')
        if len(links_errors) == 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_sq02: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_sq02
            }
            result.append(FitnessStatus(
                code=sequence_assessments[1]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=sequence_assessments[1]["description"],
                assessmentObjects=[assessment_obj_sq02]
            ))
            logger.info('SQ.02 пройден: все HTTP вызовы корректны')
        else:
            msg = '<ol>'
            for error in links_errors:
                msg += f"<li>{error}</li>"
            msg += '</ol>'
            # Создаем AssessmentObjects как словарь
            assessment_obj_sq02: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_sq02
            }

            assessment_obj_sq02_error: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_sq02_error
            }

            result.append(FitnessStatus(
                code=sequence_assessments[1]["code"],
                isCheck=False,
                resultDetails=msg,
                assessmentDescription=sequence_assessments[1]["description"],
                assessmentObjects=[assessment_obj_sq02, assessment_obj_sq02_error]
            ))
            logger.warning(f'SQ.02 не пройден: {len(links_errors)} ошибок HTTP endpoints')

        # Проверка SQ.01: Для всех technical capability указаны sequence
        logger.info('Проверка SQ.01: Для всех technical capability указаны sequence')
        total_capabilities_count = len(caps_list)
        found_sequences_count = len(found_objects_sq01)
        
        if total_capabilities_count == 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_sq01: AssessmentObjects = {
                "isCheck": False,
                "details": []
            }
            result.append(FitnessStatus(
                code=sequence_assessments[0]["code"],
                isCheck=False,
                resultDetails='Нет определенных capability',
                assessmentDescription=sequence_assessments[0]["description"],
                assessmentObjects=[assessment_obj_sq01]
            ))
            logger.warning('SQ.01 не пройден: нет определенных capability')
        else:
            if found_sequences_count >= total_capabilities_count:

                # Создаем AssessmentObjects как словарь
                assessment_obj_sq01: AssessmentObjects = {
                    "isCheck": True,
                    "details": found_objects_sq01
                }
                result.append(FitnessStatus(
                    code=sequence_assessments[0]["code"],
                    isCheck=True,
                    resultDetails="Для всех технических возможностей найдены динамические диаграммы",
                    assessmentDescription=sequence_assessments[0]["description"],
                    assessmentObjects=[assessment_obj_sq01]
                ))
                logger.info('SQ.01 пройден: для всех capabilities есть sequence диаграммы')
            else:
                # Создаем AssessmentObjects как словарь
                assessment_obj_sq01: AssessmentObjects = {
                    "isCheck": True,
                    "details": found_objects_sq01
                }

                bad_list = [ { capability : pretty_print_msg(caps_list.get(capability,[]))} for capability in capabilities.values()]
                assessment_obj_sq01_not_found: AssessmentObjects = {
                    "isCheck": False,
                    "details": bad_list
                }
                result.append(FitnessStatus(
                    code=sequence_assessments[0]["code"],
                    isCheck=False,
                    resultDetails="Не для всех технических возможностей существуют динамические диаграммы",
                    assessmentDescription=sequence_assessments[0]["description"],
                    assessmentObjects=[assessment_obj_sq01,assessment_obj_sq01_not_found]
                ))
                logger.warning(f'SQ.01 не пройден: {found_sequences_count} диаграм для {total_capabilities_count} capabilities')

    else:
        logger.info(f"Не найдено реализованных TC")
            
    logger.info(f'Проверка динамических диаграмм завершена для системы {cmdb}. Результатов: {len(result)}')
    return result