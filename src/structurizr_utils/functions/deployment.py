"""
Модуль для проверки правильности диаграмм размещения в нотации Structurizr DSL.

Основная функция:
- check_deployment: Проверяет корректность диаграмм развертывания системы
"""

from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.models_product import get_product_infra

from typing import List, Dict, Any, Set
import logging

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def check_deployment(cmdb: str, data: Dict[str, Any], backend_url: str, 
                    share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет правильность диаграмм размещения системы в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. DEP.01 - Наличие хотя бы одного Deployment Environment
    2. DEP.02 - Наличие хотя бы одной Deployment диаграммы
    3. DEP.03 - DeploymentEnvironment ссылается на мнемонику экземпляра в CMDB
    4. DEP.04 - Правильно задана макросегментация Protected/DMZ STD/NST Operations/RND
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы (не используется)
        share_url: URL для публикации диаграмм
        publish: Флаг публикации (не используется)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку диаграмм размещения для системы CMDB: {cmdb}')
    
    # Определение критериев оценки (assessments)
    deployment_assessments: List[Assessment] = [
        Assessment(code='DEP.01', description='Наличие хотя бы одного Deployment Environment'),
        Assessment(code='DEP.02', description='Наличие хотя бы одной Deployment диаграммы'),
        Assessment(code='DEP.03', description='DeploymentEnvironment ссылается на мнемонику экземпляра в CMDB'),
        Assessment(code='DEP.04', description='Правильно задана макросегментация Protected/DMZ STD/NST Operations/RND'),
    ]
    
    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    
    # Инициализация переменных для assessment
    found_objects_dep01: List[Dict[str, str]] = []
    found_objects_dep02: List[Dict[str, str]] = []

    # Анализ deployment environments
    logger.debug('Анализ deployment environments')
    environments: Set[str] = set()
    deployment_nodes: List[Dict[str, Any]] = data.get('model', {}).get('deploymentNodes', [])
    
    for deployment_node in deployment_nodes:
        environment: str = deployment_node.get('environment', '')
        if environment:
            environments.add(environment)
            
            # Заполнение данных для assessment DEP.01
            node_name = deployment_node.get('name', f'Node {len(found_objects_dep01) + 1}')
            found_objects_dep01.append({environment: f"{environment} {node_name}"})
            
            logger.debug(f'Найден deployment environment: {environment}')

    # Проверка DEP.01: Наличие хотя бы одного Deployment Environment
    logger.info('Проверка DEP.01: Наличие хотя бы одного Deployment Environment')
    if len(found_objects_dep01) > 0:
        # Создаем AssessmentObjects как словарь
        assessment_obj_dep01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_dep01
        }
        msg_res: str = '<ol>'
        for env_dict in found_objects_dep01:
            for env_key, env_value in env_dict.items():
                msg_res += f"<li>{env_key}</li>"
        msg_res += '</ol>'
        result.append(FitnessStatus(
            code=deployment_assessments[0]["code"],
            isCheck=True,
            resultDetails=msg_res,
            assessmentDescription=deployment_assessments[0]["description"],
            assessmentObjects=[assessment_obj_dep01]
        ))
        logger.info(f'DEP.01 пройден: найдено {len(environments)} deployment environments')
    else:
        result.append(FitnessStatus(
            code=deployment_assessments[0]["code"],
            isCheck=False,
            resultDetails='У приложения нет ни одного deployment environment',
            assessmentDescription=deployment_assessments[0]["description"],
            assessmentObjects=[]
        ))
        logger.warning('DEP.01 не пройден: отсутствуют deployment environments')
    
    # Анализ deployment views
    logger.debug('Анализ deployment views')
    deployment_views: List[Dict[str, Any]] = data.get('views', {}).get('deploymentViews', [])

    # Проверка DEP.02: Наличие хотя бы одной Deployment диаграммы
    logger.info('Проверка DEP.02: Наличие хотя бы одной Deployment диаграммы')
    if len(deployment_views) > 0:
        msg_res: str = ''
        for view in deployment_views:
            view_title: str = view.get('title', f'Deployment Diagram {len(found_objects_dep02) + 1}')
            view_key: str = view['key']
            
            # Заполнение данных для assessment DEP.02
            found_objects_dep02.append({view_key: f"<a href='{share_url}/diagrams#{view_key}' target='_blank'>{view_title}</a>"})
            
            msg_res += f"<a href='{share_url}/diagrams#{view_key}' target='_blank'>{view_title}</a><br>"
        
        # Создаем AssessmentObjects как словарь
        assessment_obj_dep02: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_dep02
        }
        result.append(FitnessStatus(
            code=deployment_assessments[1]["code"],
            isCheck=True,
            resultDetails=msg_res,
            assessmentDescription=deployment_assessments[1]["description"],
            assessmentObjects=[assessment_obj_dep02]
        ))
        logger.info(f'DEP.02 пройден: найдено {len(deployment_views)} deployment диаграмм')
    else:
        result.append(FitnessStatus(
            code=deployment_assessments[1]["code"],
            isCheck=False,
            resultDetails='У приложения нет ни одной deployment диаграммы',
            assessmentDescription=deployment_assessments[1]["description"],
            assessmentObjects=[]
        ))
        logger.warning('DEP.02 не пройден: отсутствуют deployment диаграммы')

    # TODO: Реализовать проверки DEP.03 и DEP.04
    # DEP.03: DeploymentEnvironment ссылается на мнемонику экземпляра в CMDB
    result.append(cmdb_deployment_compare(cmdb=cmdb,data=data,backend_url=backend_url,share_url=share_url))

    logger.info(f'Проверка диаграмм размещения завершена для системы {cmdb}. Результатов: {len(result)}')
    return result


def cmdb_deployment_compare(cmdb : str, data: Dict[str, Any], backend_url: str, share_url: str) -> FitnessStatus:
    environments: Set[str] = set()
    queue = list()

    found_systems: List[Dict[str, str]] = []
    not_found_systems: List[Dict[str, str]] = []

    for deployment_node in data.get('model', {}).get('deploymentNodes', []):
        environment: str = deployment_node.get('environment', '')
        if environment:
            parents = get_product_infra(environment)
            if parents and len(parents)>0:
                environments.add(environment)

                for child in deployment_node.get('children',[]):
                    queue.append(child)
                        
                logger.info(f'Найден deployment environment в CMDB: {environment}')
            else:
                logger.info(f'Не найден deployment environment в CMDB: {environment}')

    while len(queue) > 0:
        deployment_node = queue.pop(0)
        deployment_node_type = deployment_node.get('properties',{}).get('type',None)
        is_has_instances = len(deployment_node.get('containerInstances',[]))>0

        is_in_k8s = deployment_node.get('is_in_k8s',False) or (deployment_node_type and deployment_node_type == 'k8s')

        if is_has_instances:
            if not is_in_k8s:
                # check VM
                name = deployment_node.get('name','')
                environment = deployment_node.get('environment','')
                logger.info(f"{environment}: deployment_node {name} на VM")
                parents = get_product_infra(name)
                if cmdb.lower() in parents:
                    logging.info(f"Найдено в CMDB {name}")
                    found_systems.append({'deployment node' : f'Стенд {environment} Узел {name}'})
                else:
                    not_found_systems.append({'deployment node' : f'Стенд {environment} Узел {name}'})
        elif (deployment_node_type and deployment_node_type == 'k8s'):
            # Check k8s namespace
            name = deployment_node.get('name','')
            environment = deployment_node.get('environment','')
            logger.info(f"{environment}: k8s namespace {name}")
            parents = get_product_infra(name)
            if cmdb.lower() in parents:
                logging.info(f"Найдено в CMDB {name}")
                found_systems.append({'k8s namespace' : f'Стенд {environment} Узел {name}'})
            else:
                not_found_systems.append({'k8s namespace' : f'Стенд {environment} Узел {name}'})


        for child in deployment_node.get('children',[]):
                child['is_in_k8s'] = is_in_k8s
                queue.append(child)

    assessment_obj_found: AssessmentObjects = {
        "isCheck": True,
        "details": found_systems
    }

    assessment_obj_not_found: AssessmentObjects = {
        "isCheck": False,
        "details": not_found_systems
    }

    result_total = False
    if len(not_found_systems)==0:
        result_total = True
    

    result_message = 'Диаграмма развертывания соответствует CMDB'
    if not result_total:
        result_message = 'Диаграмма развертывания не соответствует CMDB'
    
    return FitnessStatus(
        code="DEP.03",
        isCheck=result_total,
        resultDetails=result_message,
        assessmentDescription='Deployment environment соответствует CMDB',
        assessmentObjects=[assessment_obj_found,assessment_obj_not_found]
    )