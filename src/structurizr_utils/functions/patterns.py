from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.model_graph import GraphService
from structurizr_utils.models.model_techradar import TechradarClient
import os
from typing import List, Dict, Any
import logging

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def check_patterns(cmdb: str, data: Dict[str, Any], backend_url: str, 
                    share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет наличие и корректность архитектурных паттернов в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. PAT.01 - Отсутствие взаимодействия между системами через db_link

    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы
        share_url: URL для публикации (не используется)
        publish: Флаг публикации (не используется)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку архитектурных паттернов для системы CMDB: {cmdb}')
    

    techradar_client = TechradarClient(url=os.getenv("URL_TECHRADAR"), token=os.getenv("TOKEN_TECHRADAR",""))
    patterns = techradar_client.get_all_patterns()

    found_rule = None
    for pattern in patterns:
        #logging.info(f"pattern: {pattern.code} - {pattern.name} - {pattern.rule}")
        if pattern.code == 'PATTERN.000001':
            found_rule = pattern.rule
            break
        
    # Определение критериев оценки (assessments)
    patterns_assessments: List[Assessment] = [
        Assessment(code='PAT.01', description='Наличие хотя бы одного архитектурного паттерна')
    ]

    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []

    if found_rule:
        patterns_mask = found_rule.replace("{cmdb}", cmdb)
        logging.info(f"patterns_mask: {patterns_mask}")

        graph_service = GraphService(url=os.getenv("URL_GRAPH"), token=os.getenv("TOKEN_GRAPH",""))

        result_graph = graph_service.get_elements(patterns_mask)
        
        found_broken_links = []
        logger.info(f'result_graph: {result_graph}')
        if result_graph:
            for item in result_graph:
                found_broken_links.append({f'{item.get("name","")}' : f'{item.get("details","")}' })

        # remove duplicates
        found_broken_links_cleared = []
        for item in found_broken_links:
            if item not in found_broken_links_cleared:
                found_broken_links_cleared.append(item)

        assessment_obj_pattern: AssessmentObjects = {
                "isCheck": False,
                "details": found_broken_links_cleared
            }
        if len(found_broken_links_cleared) > 0:
            result.append(FitnessStatus(
                code=patterns_assessments[0]["code"],
                isCheck=False,
                resultDetails='Найдены антипаттерны',
                assessmentDescription=patterns_assessments[0]["description"],
                assessmentObjects=[assessment_obj_pattern]
            ))
        else:
            result.append(FitnessStatus(
                    code=patterns_assessments[0]["code"],
                    isCheck=True,
                    resultDetails='Ничего не нашли',
                    assessmentDescription=patterns_assessments[0]["description"],
                    assessmentObjects=[]
                ))
    return result