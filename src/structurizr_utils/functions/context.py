"""
Модуль для проверки правильности моделей landscape в нотации Structurizr DSL.

Основная функция:
- check_context: Проверяет корректность контекстных диаграмм системы
"""

from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from typing import List, Dict, Any
import logging

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def check_context(cmdb: str, data: Dict[str, Any], backend_url: str, 
                 share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет правильность контекстных диаграмм системы в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. CTX.01 - Создана диаграмма контекста
    2. CTX.02 - Все связи на диаграмме контекста должны быть подписаны
    3. CTX.03 - Все связи на диаграмме контекста должны иметь технологию взаимодействия
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы (не используется)
        share_url: URL для публикации диаграмм
        publish: Флаг публикации (не используется)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку контекстных диаграмм для системы CMDB: {cmdb}')
    
    # Определение критериев оценки (assessments)
    context_assessments: List[Assessment] = [
        Assessment(code='CTX.01', description='Создана диаграмма контекста'),
        Assessment(code='CTX.02', description='Все связи на диаграмме контекста должны быть подписаны'),
        Assessment(code='CTX.03', description='Все связи на диаграмме контекста должны иметь технологию взаимодействия')
    ]

    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    systems: Dict[str, Any] = {}
    model: Dict[str, Any] = data['model']
    views: Dict[str, Any] = data['views']
    
    # Инициализация переменных для assessment
    found_objects_ctx01: List[Dict[str, str]] = []
    found_objects_ctx02: List[Dict[str, str]] = []
    found_objects_ctx03: List[Dict[str, str]] = []
    
    # Построение индекса систем по ID
    logger.debug('Построение индекса систем')
    if 'softwareSystems' in model:
        software_systems: List[Dict[str, Any]] = model['softwareSystems']
        for system in software_systems:
            system_id: str = system['id']
            systems[system_id] = system
            logger.debug(f'Добавлена система в индекс: {system_id}')

    # Анализ контекстных диаграмм
    logger.debug('Анализ контекстных диаграмм')
    
    if 'systemContextViews' in views:
        context_views: List[Dict[str, Any]] = views['systemContextViews']
        logger.debug(f'Найдено {len(context_views)} контекстных диаграмм')
        
        for view in context_views:
            if 'softwareSystemId' in view:
                software_system_id: str = view['softwareSystemId']
                if software_system_id in systems:
                    system: Dict[str, Any] = systems[software_system_id]
                    logger.debug(f'Анализ контекстной диаграммы для системы: {software_system_id}')
                    
                    # Проверка CTX.01: Создана диаграмма контекста
                    view_title: str = view.get('title', 'Context Diagram')
                    view_key: str = view['key']
                    
                    # Заполнение данных для assessment CTX.01
                    found_objects_ctx01.append({view_key: f"<a href='{share_url}/diagrams#{view_key}' target='_blank'>{view_title}</a>"})
                    logger.info(f'Найдена контекстная диаграмма: {view_title}')
                        
                    # Проверка связей системы
                    logger.debug('Проверка связей системы на наличие описаний и технологий')
                    relationships: List[Dict[str, Any]] = system.get('relationships', [])
                    
                    for relationship in relationships:
                        relationship_id = relationship.get('id', f'rel_{len(found_objects_ctx02)}')
                        description: str = relationship.get('description', '')
                        technology: str = relationship.get('technology', '')
                        
                        if len(description) == 0:
                            # Заполнение данных для assessment CTX.02
                            found_objects_ctx02.append({relationship_id: description})
                            logger.debug(f'Найдена связь с описанием: {description}')
                        
                        if len(technology) == 0:
                            # Заполнение данных для assessment CTX.03
                            rel_display = f"{description} ({technology})" if description else technology
                            found_objects_ctx03.append({relationship_id: technology})
                            logger.debug(f'Найдена связь с технологией: {technology}')
    
    # Проверка CTX.01: Создана диаграмма контекста
    logger.info('Проверка CTX.01: Создана диаграмма контекста')
    if len(found_objects_ctx01) > 0:
        # Создаем AssessmentObjects как словарь
        assessment_obj_ctx01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_ctx01
        }
        result.append(FitnessStatus(
            code=context_assessments[0]["code"],
            isCheck=True,
            resultDetails="Контекстные диаграммы найдены в архитектуре",
            assessmentDescription=context_assessments[0]["description"],
            assessmentObjects=[assessment_obj_ctx01]
        ))
        logger.info('CTX.01 пройден: найдены контекстные диаграммы')
    else:
        result.append(FitnessStatus(
            code=context_assessments[0]["code"],
            isCheck=False,
            resultDetails=context_assessments[0]["description"],
            assessmentDescription=context_assessments[0]["description"],
            assessmentObjects=[]
        ))
        logger.warning('CTX.01 не пройден: не найдено контекстных диаграмм')
    
    # Проверка CTX.02: Все связи на диаграмме контекста должны быть подписаны
    logger.info('Проверка CTX.02: Все связи на диаграмме контекста должны быть подписаны')
    if len(found_objects_ctx02) ==  0:
        # Создаем AssessmentObjects как словарь
        
        result.append(FitnessStatus(
            code=context_assessments[1]["code"],
            isCheck=True,
            resultDetails="Связи с описаниями найдены",
            assessmentDescription=context_assessments[1]["description"],
            assessmentObjects=[]
        ))
        logger.info('CTX.02 пройден: найдены связи с описаниями')
    else:
        assessment_obj_ctx02: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_ctx02
        }

        result.append(FitnessStatus(
            code=context_assessments[1]["code"],
            isCheck=False,
            resultDetails="На контекстной диаграмме есть связи, не имеющие названия",
            assessmentDescription=context_assessments[1]["description"],
            assessmentObjects=[assessment_obj_ctx02]
        ))
        logger.warning('CTX.02 не пройден: не найдено связей с описаниями')

    # Проверка CTX.03: Все связи на диаграмме контекста должны иметь технологию взаимодействия
    logger.info('Проверка CTX.03: Все связи на диаграмме контекста должны иметь технологию взаимодействия')
    if len(found_objects_ctx03) == 0:
        
        result.append(FitnessStatus(
            code=context_assessments[2]["code"],
            isCheck=True,
            resultDetails="Связи с технологиями найдены",
            assessmentDescription=context_assessments[2]["description"],
            assessmentObjects=[]
        ))
        logger.info('CTX.03 пройден: найдены связи с технологиями')
    else:
        # Создаем AssessmentObjects как словарь
        assessment_obj_ctx03: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_ctx03
        }

        result.append(FitnessStatus(
            code=context_assessments[2]["code"],
            isCheck=False,
            resultDetails="На контекстной диаграмме есть связи, не имеющие технологии",
            assessmentDescription=context_assessments[2]["description"],
            assessmentObjects=[assessment_obj_ctx03]
        ))
        logger.warning('CTX.03 не пройден: не найдено связей с технологиями')
    
    logger.info(f'Проверка контекстных диаграмм завершена для системы {cmdb}. Результатов: {len(result)}')
    return result