"""
Модуль для проверки использования технологий из техрадара в нотации Structurizr DSL.

Основные функции:
- check_technology: Проверяет соответствие используемых технологий техрадару
- TechStatus: Класс для хранения статуса технологий
- check_tr: Проверяет технологии на соответствие техрадару
- is_https_endpoint: Проверяет использование HTTPS/TLS протоколов
"""

import re
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Set, Optional
from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.model_techradar import TechradarClient, ProductDTO , TechAdvancedDTO
from structurizr_utils.models.models_product import post_product_tech_relation

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

class TechStatus:
    """
    Класс для хранения статуса технологий при проверке соответствия техрадару.
    """
    
    def __init__(self) -> None:
        """Инициализация статуса технологий."""
        self.holded: List[str] = []  # Технологии в статусе HOLD
        self.missed: List[str] = []  # Технологии не найденные в техрадаре
        self.all: List[str] = []     # Все найденные технологии
        self.radar : List[str] = []     # Технологии из техрадара

def check_tr(technologies: Dict[str, str], value: str) -> TechStatus:
    """
    Проверяет технологии на соответствие техрадару.
    
    Args:
        technologies: Словарь технологий из техрадара {название: статус}
        value: Строка с технологиями для проверки
        
    Returns:
        TechStatus: Статус проверки технологий
    """
    result = TechStatus()
    delimiters = r'[,\t;]+'
    tlist = re.split(delimiters, value.lower())
    
    for tech in tlist:
        tech = tech.lstrip().rstrip().lower()
        found_tech = None
        result.all.append(tech)
        
        # Поиск технологии в техрадаре
        for tech_radar in technologies.keys():
            if tech.find(tech_radar.lower()) >= 0:
                found_tech = tech_radar
                if technologies[tech_radar] == 'hold':
                    result.holded.append(tech)
                break
                
        # Если технология не найдена в техрадаре
        if found_tech is None:
            if not tech.isnumeric() and len(tech) > 0:
                result.missed.append(tech)
        else:
            if not tech.isnumeric() and len(tech) > 0:
                result.radar.append(tech)    

    return result

def is_https_endpoint(value: str) -> bool:
    """
    Проверяет использование HTTPS/TLS протоколов.
    
    Args:
        value: Строка с протоколами для проверки
        
    Returns:
        bool: True если используется HTTPS/TLS
    """
    protocols = {"https", "tls"}
    delimiters = r'[ ,\t;]+'
    tlist = re.split(delimiters, value.lower())
    
    for protocol in protocols:
        for tech in tlist:
            if tech.find(protocol) == 0:
                logger.debug(f'Найден HTTPS/TLS протокол: {tech}')
                return True
    return False


class ProductTechCache:
    product_tech: Optional[List[ProductDTO]]
    techs : Optional[List[TechAdvancedDTO]]
    update_time : datetime

    def __init__(self) -> None:
        self.product_tech = None
        self.techs = None
        gmt_plus_3      = timezone(timedelta(hours=3))
        self.update_time    = datetime.now(gmt_plus_3)


    def update(self, client : TechradarClient):
        gmt_plus_3      = timezone(timedelta(hours=3))
        current_time    = datetime.now(gmt_plus_3)
        reload = False

        if not self.product_tech:
            reload = True

        if not self.techs:
            reload = True

        if self.update_time:
            time_diff = (current_time - self.update_time).total_seconds()
            if time_diff > 3600:
                reload = True

        if reload:
            self.update_time = datetime.now(gmt_plus_3)
            self.techs = client.get_all_tech(user_roles="admin")
            self.product_tech = client.get_product_tech(user_roles="admin")


product_tech_cache = ProductTechCache()

def check_technology(cmdb: str, data: Dict[str, Any], backend_url: str, 
                     share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет использование технологий из техрадара в нотации Structurizr DSL.
    
    Функция выполняет следующие проверки:
    1. TECH.01 - Все технологии продукта есть в техрадаре
    2. TECH.02 - В продукте нет технологий в статусе HOLD
    3. TECH.03 - У всех контейнеров есть технологии
    4. TECH.04 - Приложение не использует протоколов в статусе hold
    5. TECH.05 - У всех взаимодействий указаны протоколы из техрадара
    6. TECH.06 - Технологии найденные по мониторингу продуктивной среды и Git описаны в архитектуре
    
    Args:
        cmdb: Идентификатор системы в CMDB
        data: JSON данные модели Structurizr
        backend_url: URL backend системы (не используется)
        share_url: URL для публикации (не используется)
        publish: Флаг публикации (не используется)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """
    
    # Инициализация клиента техрадара
    client = TechradarClient(
        base_url=os.environ.get("URL_TECHRADAR", "https://techradar-backend-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru"),
        auth_token="your_auth_token_here"
    )

    product_tech_cache.update(client)

    # Определение критериев оценки (assessments)
    technology_assessments: List[Assessment] = [
        Assessment(code='TECH.01', description='Все технологии продукта есть в техрадаре'),
        Assessment(code='TECH.02', description='В продукте нет технологий в статусе HOLD'),
        Assessment(code='TECH.03', description='У всех контейнеров есть технологии'),
        Assessment(code='TECH.04', description='Приложение не использует протоколов в статусе hold'),
        Assessment(code='TECH.05', description='У всех взаимодействий указаны протоколы из техрадара'),
        Assessment(code='TECH.06', description='Технологии найденные по мониторингу продуктивной среды и Git описаны в архитектуре')
    ]
    
    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    containers_wo_technology: Set[str] = set()
    found_technology: Set[str] = set()
    holded_technology: Set[str] = set()
    unknown_technology: Set[str] = set()
    holded_links: List[Dict] = []
    containers_list: List[Dict[str, Any]] = []
    
    # Инициализация переменных для assessment
    found_objects_tech01: List[Dict[str, str]] = []
    found_objects_tech02: List[Dict[str, str]] = []
    found_objects_tech03: List[Dict[str, str]] = []
    tech_container_map03  = dict()
    found_objects_tech04: List[Dict[str, str]] = []
    found_objects_tech05: List[Dict[str, str]] = []
    found_protocol_set05: Set[str] = set()
    found_objects_tech06: List[Dict[str, str]] = []

    try:
        # Загрузка технологий из техрадара
        logger.debug('Загрузка технологий из техрадара')
        techs = product_tech_cache.techs # client.get_all_tech(user_roles="admin")

        # Построение словарей статусов технологий
        tech_status: Dict[str, str] = {}
        tech_status_protocols: Dict[str, str] = {}

        for tech in techs:
            tech_label = tech.label.lower().lstrip().rstrip()
            tech_ring = tech.ring.name.lower().lstrip().rstrip() if tech.ring.name else 'adopt'
            
            # Общий статус технологий
            tech_status[tech_label] = tech_ring
            
            # Статус протоколов (сектор 3)
            if tech.ring and tech.sector and tech.sector.id == 3:
                tech_status_protocols[tech_label] = tech_ring

        # Добавление стандартных протоколов
        standard_protocols = {
            'rest': 'adopt',
            'http': 'adopt', 
            'https': 'adopt', 
            'tcp': 'adopt',
            'amqp': 'adopt',
            'soap': 'adopt',
            'udp': 'adopt'
        }
        tech_status_protocols.update(standard_protocols)
        
        logger.debug(f'Загружено {len(tech_status)} технологий из техрадара')

        
        # Анализ систем и их технологий
        logger.debug('Анализ систем и их технологий')
        systems: List[Dict[str, Any]] = data.get('model', {}).get('softwareSystems', [])
        
        for system in systems:
            system_cmdb: str = system.get('properties', {}).get('cmdb', '')
            if system_cmdb == cmdb:
                logger.debug(f'Анализ системы: {system.get("name", "")}')
                
                # Анализ связей системы
                relationships: List[Dict[str, Any]] = system.get('relationships', [])
                for relationship in relationships:
                    name: str = relationship.get('description', '')
                    technology: str = relationship.get('technology', '')
                    logger.debug(f'Проверка технологии: [{technology}] в связи [{name}]')
                    tr_result = check_tr(tech_status_protocols, technology)
                    
                    for tech in tr_result.radar:
                        found_protocol_set05.add(tech)
                    for tech in tr_result.holded:
                        logger.debug(f'Технология в статусе HOLD: [{tech}] в связи [{name}]')
                        holded_links.append({ 'name': name, 'tech': tech})
                    for tech in tr_result.missed:
                        logger.debug(f'Технология не найдена в техрадаре: [{tech}] в связи [{name}]')
                        found_objects_tech05.append({tech: f"{name} - {tech}"})

                # Анализ контейнеров системы
                https_container_ids: List[str] = []
                containers: Dict[str, Any] = {}
                containers_list: List[Dict[str, Any]] = system.get('containers', [])
                
                for container in containers_list:
                    container_id: str = container["id"]
                    containers[container_id] = container

                    # Проверка источника контейнера
                    from_landscape: bool = (container.get("properties", {}).get("source", "") == "landscape")

                    if not from_landscape:
                        technology: str = container.get('technology', '').lower().lstrip().rstrip()
                        container_name: str = container.get('name', '')
                        
                        if len(technology) == 0:
                            containers_wo_technology.add(container_name)
                            logger.debug(f'Контейнер без технологии: {container_name}')
                        else:
                            tr_result = check_tr(tech_status, technology)
                            for tech in tr_result.all:
                                found_technology.add(tech)
                                
                                # Заполнение данных для assessment TECH.01
                                found_objects_tech01.append({tech: tech_status.get(tech,'-')})
                                
                            for tech in tr_result.holded:
                                holded_technology.add(tech)
                                # Заполнение данных для assessment TECH.02
                                found_objects_tech02.append({tech: f"{tech} (Container: {container_name})"})
                                
                            for tech in tr_result.missed:
                                unknown_technology.add(tech)

                            for tech in tr_result.radar:
                                cl = f"{tech_container_map03.get(tech,'')}"
                                cl += f"{container_name}, "
                                tech_container_map03[tech] = cl

                    # Анализ связей контейнера
                    container_relationships: List[Dict[str, Any]] = container.get('relationships', [])
                    for relationship in container_relationships:
                        name: str = relationship.get('description', '')
                        technology: str = relationship.get('technology', '')

                        tr_result = check_tr(tech_status_protocols, technology)
                        
                        for tech in tr_result.radar:
                            found_protocol_set05.add(tech)

                        for tech in tr_result.holded:
                            holded_links.append({ 'name': name, 'tech': tech})
                            # Заполнение данных для assessment TECH.04
                            rel_id = relationship.get('id', f'rel_{len(holded_links)}')
                            found_objects_tech04.append({rel_id: f"{rel_id} {name} ({tech})"})
                            
                        for tech in tr_result.missed:
                            # Заполнение данных для assessment TECH.05
                            found_objects_tech05.append({tech: f"{name}"})

                        # Проверка HTTPS/TLS протоколов
                        if is_https_endpoint(technology):
                            https_container_ids.append(relationship['destinationId'])


        # Проверка технологий из мониторинга продуктивной среды
        logger.debug('Проверка технологий из мониторинга продуктивной среды')
        
        product_tech = product_tech_cache.product_tech #  client.get_product_tech(user_roles="admin")
        in_landscape_not_in_arch: Set[str] = set()
        
        for pt in [pt for pt in product_tech if pt.alias]:
            if pt.alias.lower() == cmdb.lower():
                if pt.tech:
                    for tech in pt.tech:
                        found = False
                        tech_label = tech.label.lower()
                        
                        # Прямое совпадение
                        if tech_label in found_technology:
                            found = True
                        else:
                            # Частичное совпадение
                            for found_tech in found_technology:
                                if tech_label in found_tech:
                                    found = True
                                    break
                        
                        if not found:
                            exception_set = {"HTML","CSS","SSH 2.0","Docker","Alpine Linux","HCL","Groovy","Jinja","Prometheus"}

                            if tech.label not in exception_set:
                                in_landscape_not_in_arch.add(tech.label)
                                # Заполнение данных для assessment TECH.06
                                found_objects_tech06.append({tech.label: f"{tech.label} (Monitoring)"})
                                logger.debug(f'Технология из мониторинга не найдена в архитектуре: {tech.label}')

        # Выполнение проверок fitness functions
        
        # Проверка TECH.06: Технологии из мониторинга описаны в архитектуре
        if len(in_landscape_not_in_arch) == 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech06: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_tech06
            }
            result.append(FitnessStatus(
                code=technology_assessments[5]["code"],
                isCheck=True,
                resultDetails='Не найдено расхождений архитектуры и мониторинга',
                assessmentDescription=technology_assessments[5]["description"],
                assessmentObjects=[assessment_obj_tech06]
            ))
            logger.info('TECH.06 пройден: нет расхождений с мониторингом')
        else:
            msg_techs = 'Технологии, которые есть по данным мониторинга продуктивной среды и gitlab, но отсутствуют в архитектуре<hr><ol>'
            for tech in in_landscape_not_in_arch:
                msg_techs += f"<li>{tech}</li>"
            msg_techs += '</ol>'
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech06: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_tech06
            }
            result.append(FitnessStatus(
                code=technology_assessments[5]["code"],
                isCheck=False,
                resultDetails=msg_techs,
                assessmentDescription=technology_assessments[5]["description"],
                assessmentObjects=[assessment_obj_tech06]
            ))
            logger.info(f'TECH.06 не пройден: {len(in_landscape_not_in_arch)} технологий не описаны в архитектуре')
        # Проверка TECH.01: Все технологии продукта есть в техрадаре
        if len(unknown_technology) == 0:
            # Создаем AssessmentObjects как словарь

            rs = set(key for d in found_objects_tech01 for key in d.keys())
            rl = list( {tech:tech_status.get(tech,'-')} for tech in rs )
            

            assessment_obj_tech01: AssessmentObjects = {
                "isCheck": True,
                "details": rl
            }

            result.append(FitnessStatus(
                code=technology_assessments[0]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=technology_assessments[0]["description"],
                assessmentObjects=[assessment_obj_tech01]
            ))
            logger.info('TECH.01 пройден: все технологии есть в техрадаре')
        else:
            msg_techs = '<ol>'
            rl = []
            for tech in unknown_technology:
                msg_techs += f'<li>{tech}</li>'
                rl.append({tech:"-"})
            msg_techs += '</ol>'
            # Создаем AssessmentObjects как словарь


            assessment_obj_tech01: AssessmentObjects = {
                "isCheck": False,
                "details": rl
            }
            result.append(FitnessStatus(
                code=technology_assessments[0]["code"],
                isCheck=False,
                resultDetails='У приложения есть технологии не из <a href="https://tr.vimpelcom.ru/" target="_blank">Техрадара</a>: ' + msg_techs,
                assessmentDescription=technology_assessments[0]["description"],
                assessmentObjects=[assessment_obj_tech01]
            ))
            logger.info(f'TECH.01 не пройден: {len(unknown_technology)} технологий не из техрадара')

        # Проверка TECH.02: В продукте нет технологий в статусе HOLD
        if len(holded_technology) == 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech02: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_tech02
            }
            result.append(FitnessStatus(
                code=technology_assessments[1]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=technology_assessments[1]["description"],
                assessmentObjects=[assessment_obj_tech02]
            ))
            logger.info('TECH.02 пройден: нет технологий в статусе HOLD')
        else:
            msg_techs = '<ol>'
            for tech in holded_technology:
                msg_techs += f'<li>{tech}</li>'
            msg_techs += '</ol>'
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech02: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_tech02
            }
            result.append(FitnessStatus(
                code=technology_assessments[1]["code"],
                isCheck=False,
                resultDetails='У приложения есть hold технологии: ' + msg_techs,
                assessmentDescription=technology_assessments[1]["description"],
                assessmentObjects=[assessment_obj_tech02]
            ))
            logger.info(f'TECH.02 не пройден: {len(holded_technology)} технологий в статусе HOLD')

        # Проверка TECH.03: У всех контейнеров есть технологии

        
        if len(containers_wo_technology) == 0:
            # Создаем AssessmentObjects как словарь
            rl = []
            for tech in tech_container_map03:
                rl.append({tech:tech_container_map03[tech]})

            assessment_obj_tech03: AssessmentObjects = {
                "isCheck": True,
                "details": rl
            }
            result.append(FitnessStatus(
                code=technology_assessments[2]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=technology_assessments[2]["description"],
                assessmentObjects=[assessment_obj_tech03]
            ))
            logger.info('TECH.03 пройден: у всех контейнеров есть технологии')
        else:
            msg_containers = '<ol>'
            for container in containers_wo_technology:
                msg_containers += f'<li>{container}</li>'
                # Заполнение данных для assessment TECH.03
                found_objects_tech03.append({"-":container})
            msg_containers += '</ol>'
            # Создаем AssessmentObjects как словарь

            rl = []
            for tech in tech_container_map03:
                rl.append({tech:tech_container_map03[tech]})

            assessment_obj_tech03_1: AssessmentObjects = {
                "isCheck": True,
                "details": rl
            }

            assessment_obj_tech03_2: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_tech03
            }
            result.append(FitnessStatus(
                code=technology_assessments[2]["code"],
                isCheck=False,
                resultDetails='У приложения есть контейнеры, не имеющие технологии: ' + msg_containers,
                assessmentDescription=technology_assessments[2]["description"],
                assessmentObjects=[assessment_obj_tech03_1,assessment_obj_tech03_2]
            ))
            logger.info(f'TECH.03 не пройден: {len(containers_wo_technology)} контейнеров без технологий')
        
        # Проверка TECH.04: Приложение не использует протоколов в статусе hold
        
        if len(found_objects_tech04) == 0:
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech04: AssessmentObjects = {
                "isCheck": True,
                "details": found_objects_tech04
            }
            result.append(FitnessStatus(
                code=technology_assessments[3]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=technology_assessments[3]["description"],
                assessmentObjects=[assessment_obj_tech04]
            ))
            logger.info('TECH.04 пройден: нет технологий в статусе HOLD')
        else:
            msg_techs = '<ol>'
            for tech in holded_links:
                msg_techs += f'<li>{tech["name"]} - {tech["tech"]}</li>'
            msg_techs += '</ol>'
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech04: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_tech04
            }
            result.append(FitnessStatus(
                code=technology_assessments[3]["code"],
                isCheck=False,
                resultDetails='У приложения есть технологии в статусе HOLD: ' + msg_techs,
                assessmentDescription=technology_assessments[3]["description"],
                assessmentObjects=[assessment_obj_tech04]
            ))
            logger.info(f'TECH.04 не пройден: {len(holded_links)} технологий в статусе HOLD')

        # Проверка TECH.05: У всех взаимодействий указаны протоколы из техрадара        
        if len(found_objects_tech05) == 0:
            result.append(FitnessStatus(
                code=technology_assessments[4]["code"],
                isCheck=True,
                resultDetails='OK',
                assessmentDescription=technology_assessments[4]["description"],
                assessmentObjects=[]
            ))
            logger.info('TECH.05 пройден: все взаимодействия используют протоколы из техрадара')
        else:
            # Создаем AssessmentObjects как словарь
            assessment_obj_tech05: AssessmentObjects = {
                "isCheck": False,
                "details": found_objects_tech05
            }
            result.append(FitnessStatus(
                code=technology_assessments[4]["code"],
                isCheck=False,
                resultDetails='У приложения есть взаимодействия по технологиям не из техрадара',
                assessmentDescription=technology_assessments[4]["description"],
                assessmentObjects=[assessment_obj_tech05]
            ))
            logger.info(f'TECH.05 не пройден: {len(found_objects_tech05)} взаимодействий с технологиями не из техрадара')


        # Публикуем связи приложения с техрадаром
        if publish:
            logger.info('Публикуем связи технологий с приложением')

            for tech in techs:
                tech_label = tech.label.lower().lstrip().rstrip()
                if tech_label in tech_container_map03:
                    logger.info(f'Публикуем связь {cmdb} с {tech_label} id {tech.id}')
                    post_product_tech_relation(cmdb=cmdb, techId=tech.id)


    except Exception as e:
        logger.error(f'Ошибка при проверке технологий: {e}')
        # В случае ошибки возвращаем пустой результат
        pass

    logger.info(f'Проверка технологий завершена для системы {cmdb}. Результатов: {len(result)}')
    return result