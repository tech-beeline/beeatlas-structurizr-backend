"""
Модуль для проверки наличия ADR (Architecture Decision Records) в нотации Structurizr DSL.

Основная функция:
- check_adr: Проверяет наличие архитектурных решений (ADR) в документации
"""

from structurizr_utils.functions.objects import FitnessStatus, Assessment , AssessmentObjects
from typing import List, Dict, Any
import requests
import logging

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def check_adr(cmdb: str, data: Dict[str, Any], backend_url: str, 
              share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет наличие ADR (Architecture Decision Records) в документации системы.
    
    Функция выполняет следующие проверки:
    1. ADR.01 - Наличие хотя бы одного ADR
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы (не используется)
        share_url: URL для публикации решений
        publish: Флаг публикации (не используется)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    logger.info(f'Начинаем проверку ADR для системы CMDB: {cmdb}')
    
    # Определение критериев оценки (assessments)
    assessments: List[Assessment] = [
        Assessment(code = 'ADR.01', description = 'Наличие хотя бы одного ADR')
    ]
    
    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []

    # Анализ архитектурных решений (ADR)
    logger.debug('Анализ архитектурных решений (ADR)')
    adrs: List[Dict[str, Any]] = []
    decisions: List[Dict[str, Any]] = data.get('documentation', {}).get('decisions', [])
    
    for decision in decisions:
        adrs.append(decision)
        logger.info(f'Найдено ADR: {decision.get("title", "Без названия")}')

    # Проверка ADR.01: Наличие хотя бы одного ADR
    logger.info('Проверка ADR.01: Наличие хотя бы одного ADR')
    
    found_objects = []
    # Заполнение списка найденных объектов

    for i, adr in enumerate(adrs):
        adr_id = adr.get('id', f'adr_{i}')
        adr_title = adr.get('title', f'ADR {i+1}')
        found_objects.append({adr_id: f"<a href='{share_url}/decisions#{adr_id}' target='_blank'>{adr_title}</a>"})
    
    if len(found_objects) > 0:
        logger.info('Формируем результат')
        # Создаем AssessmentObjects как словарь (TypedDict нельзя вызывать как класс)
        assessment_obj: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects
        }
        result.append(FitnessStatus(code = assessments[0]["code"],
                                    isCheck = True,
                                    resultDetails= "ADR Найдены в архитектуре",
                                    assessmentDescription = assessments[0]["description"],
                                    assessmentObjects = [assessment_obj]))

 
    else:
       result.append(FitnessStatus(code = assessments[0]["code"],
                                    isCheck = False,
                                    assessmentDescription = assessments[0]["description"],
                                    resultDetails = "ADR не найдены в архитектуре",
                                    assessmentObjects = []))
    
    logger.info(f'Проверка ADR завершена для системы {cmdb}. Результатов: {len(result)}')
    return result