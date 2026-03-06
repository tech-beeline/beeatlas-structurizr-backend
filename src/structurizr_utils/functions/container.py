from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.model_techradar import TechradarClient
import logging
import os
import re
from typing import Dict, List, Any, Optional

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

def check_container(cmdb: str, data: Dict[str, Any], backend_url: str, share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:
    """
    Проверяет контейнерную модель системы в нотации Structurizr DSL.
    
    Функция выполняет комплексную проверку контейнерной архитектуры системы,
    включая наличие контейнеров, диаграмм, технологий в связях и интеграцию с IDM.
    
    Args:
        cmdb (str): Идентификатор системы в CMDB
        data (Dict[str, Any]): JSON данные модели Structurizr
        backend_url (str): URL бэкенда (не используется в текущей реализации)
        share_url (str): URL для публикации (не используется в текущей реализации)
        publish (bool): Флаг публикации (не используется в текущей реализации)
        
    Returns:
        List[FitnessStatus]: Список результатов проверок (fitness assessments)
    """

    logger.info(f"Начинаем проверку контейнерной модели для системы CMDB: {cmdb}")
    
    # Определение критериев оценки (assessments)
    container_assessments: List[Assessment] = [
        Assessment(code='CNT.01', description='Наличие в модели контейнеров для системы'),
        Assessment(code='CNT.02', description='Наличие в хотя бы одной диаграммы контейнеров'),
        Assessment(code='CNT.03', description='Все вызовы между контейнерами имеют технологию'),
        Assessment(code='SEC.01', description='Интеграция frontend/api gateway с IDM системой'),
        Assessment(code='GIT.01', description='Наличие в модели git репозитория')
    ]
    
    # Инициализация переменных для сбора результатов
    result: List[FitnessStatus] = []
    relationships: Dict[str, Any] = {}
    relationships_wo_tech: List[str] = []
    has_containers: bool = False
    system_id: int = -1
    
    # Инициализация переменных для assessment
    total_containers_git_count: int = 0
    found_containers_with_git_count: int = 0
    found_objects_cnt01: List[Dict[str, str]] = []
    found_objects_cnt02: List[Dict[str, str]] = []
    found_objects_cnt03: List[Dict[str, str]] = []
    found_objects_sec01: List[Dict[str, str]] = []
    found_objects_git01: List[Dict[str, Any]] = []
    not_found_objects_git01: List[Dict[str, Any]] = []

    # Загрузка технологий из техрадара
    logger.debug('Загрузка технологий из техрадара')
    # Инициализация клиента техрадара
    techradar_client = TechradarClient(
        base_url=os.environ.get("URL_TECHRADAR", "https://techradar-backend-prod-eafdmmart.apps.yd-m3-k21.vimpelcom.ru"),
        auth_token="your_auth_token_here"
    )
    techs = techradar_client.get_all_tech(user_roles="admin")

    infrastructure_sectors = ['Управление данными','Платформа и инфраструктура']
    indrastructure_techs = [tech.label.lower().lstrip().rstrip() for tech in techs if tech.sector.name in infrastructure_sectors]

    
    logger.info(f"Найдено {len(indrastructure_techs)} технологий из инфраструктурных секторов")



    # Извлечение данных модели из JSON структуры
    systems: List[Dict[str, Any]] = data.get('model', {}).get('softwareSystems', [])
    containers: Dict[str, Any] = {}

    # Поиск целевой системы по CMDB идентификатору
    logger.debug(f"Поиск системы с CMDB: {cmdb} среди {len(systems)} систем")
    for s in systems:
        if s.get('properties', {}).get('cmdb', '').lower() == cmdb.lower():
            system_id = s.get('id', 0)
            logger.info(f"Найдена система с ID: {system_id}")
            
            # Сбор контейнеров и их связей
            for c in s.get('containers', []):
                has_containers = True
                containers[c['id']] = c

                # Проверка наличия git репозитория
                # Получаем строку с технологиями из контейнера, они могут быть перечисленны через запятую или точку с запятой
                technology: str = c.get('technology', '').lower().lstrip().rstrip()
                delimiters = r'[,\t;]+'
                tlist = re.split(delimiters, technology)
                has_infrastructure_tech :bool = False

                for tech in tlist:
                    if tech.lower().strip() in indrastructure_techs:
                        has_infrastructure_tech = True
                        break

                if not has_infrastructure_tech:
                    delimiters = r'[ ,\t;]+'
                    tlist = re.split(delimiters, technology)
                    for tech in tlist:
                        if tech.lower().strip() in indrastructure_techs:
                            has_infrastructure_tech = True
                            break

                logger.debug(f"Tech [{tlist}] is infrastructure {has_infrastructure_tech}")

                tags = c.get('tags', [])
                
                if not has_infrastructure_tech and 'external' not in tags:
                    logger.info(f"Container name: {c.get('name', '')} has infrastructure tech: {has_infrastructure_tech} tech: {tlist}")

                    total_containers_git_count += 1
                    has_git = False

                    if 'url' in c:
                        url = c.get('url','')
                        logger.debug(f"Проверка наличия git репозитория: {url}")
                        if url.find('git') != -1 or url.find('nexus') != -1 or url.find('harbor') != -1:
                            found_containers_with_git_count += 1
                            container_props = c.get('properties', {}) or {}
                            found_objects_git01.append({ 
                                'git': c.get('url'), 
                            })
                            logger.debug(f"++++ Has git repo: {url}")
                            has_git = True
                    if not has_git:
                        container_props = c.get('properties', {}) or {}
                        not_found_objects_git01.append({ 
                            'container': c.get('name')
                        })
                # Заполнение данных для assessment CNT.01
                container_name = c.get('name', f'Container {len(found_objects_cnt01) + 1}')
                found_objects_cnt01.append({c['id']: f"{c['id']} {container_name}"})
                
                logger.debug(f"Добавлен контейнер: {container_name} (ID: {c['id']})")
                
                # Сбор связей контейнеров
                for r in c.get('relationships', []):
                    relationships[r['id']] = r
                    relationships[r['id']]["source_name"] = container_name


            # Сбор связей на уровне системы
            # for r in s.get('relationships', []):
            #     relationships[r['id']] = r

            # Проверка связей на наличие технологий
            for r in relationships:
                if relationships[r].get('technology', '') == '':
                    relationships_wo_tech.append(r)
                    logger.warning(f"Связь без технологии: {relationships[r].get('description', 'Unknown')}")
                    found_objects_cnt03.append({relationships[r].get('source_name', ''): f"{relationships[r].get('description', 'Описание связи отсутствует')}"}) 
                      
    # Поиск IDM систем в модели
    logger.info("Поиск IDM систем в модели")
    idm_system_ids: Dict[str, str] = {}
    idm_cmdb_list = [
        'MICROSOFT_ACTIVE_DIRECTORY_FEDERATION_SERVICE',
        'RU.DEVOPSTOOLS.KEYCLOAK.PRODLIKE-OPERATION',
        'RU.MICROSERVICES.KEYCLOAK.PROD',
        'RU.DEVOPSTOOLS.ADLDS.PROD',
        'UNIXLDAP',
        'RU.IDP.IDP-PROD',
        'IDP',
        'RU.YDC.FREEIPA-TEST-CL01.VEGA.CLOUD.VIMPELCOM.RU'
    ]
    
    for s in systems:
        cmdb_name = s.get('properties', {}).get('cmdb', '').upper()
        if cmdb_name in idm_cmdb_list:
            idm_system_ids[s.get('id', '')] = cmdb_name
            logger.info(f"Найдена IDM система: {cmdb_name}")
    
    # Проверка интеграции контейнеров с IDM системами
    logger.info("Проверка интеграции контейнеров с IDM системами")
    found_idm_relationships: bool = False
    found_idm_system_names: str = ""

    for c in containers:
        for r in containers[c].get('relationships', []):
            if r.get('destinationId', '') in idm_system_ids:
                logger.info(f"Найдена связь с IDM: {r.get('description', 'Unknown')}")
                found_idm_relationships = True
                found_idm_system_names += f" {len(found_objects_sec01) + 1}. Интеграция с {idm_system_ids[r.get('destinationId', '')] } <br> "
                
                # Заполнение данных для assessment SEC.01
                rel_desc = r.get('description', f'IDM Relationship {r.get("id", "")}')
                idm_system_name = idm_system_ids[r.get('destinationId', '')]
                found_objects_sec01.append({r.get('id', ''): f"{r.get('id', '')} {rel_desc} -> {idm_system_name}"})

    # Оценка интеграции с IDM (SEC.01)
    logger.info('Проверка SEC.01: Интеграция frontend/api gateway с IDM системой')
    if found_idm_relationships:
        # Создаем AssessmentObjects как словарь
        assessment_obj_sec01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_sec01
        }
        result.append(FitnessStatus(
            code=container_assessments[3]["code"],
            isCheck=True,
            resultDetails=found_idm_system_names,
            assessmentDescription=container_assessments[3]["description"],
            assessmentObjects=[assessment_obj_sec01]
        ))
        logger.info("SEC.01 пройден: Интеграция с IDM найдена")
    else:
        result.append(FitnessStatus(
            code=container_assessments[3]["code"],
            isCheck=False,
            resultDetails='Не найдено связей с системами IDM',
            assessmentDescription=container_assessments[3]["description"],
            assessmentObjects=[]
        ))
        logger.warning("SEC.01 не пройден: Интеграция с IDM не найдена")

    # Проверка наличия контейнерных диаграмм
    logger.info("Проверка наличия контейнерных диаграмм")
    has_view: bool = False
    container_views = data.get('views', {}).get('containerViews', [])
    
    for v in container_views:
        if v.get('softwareSystemId', 0) == system_id:
            has_view = True
            
            # Заполнение данных для assessment CNT.02
            view_title = v.get('title', f'Container View {len(found_objects_cnt02) + 1}')
            view_key = v.get('key', v.get('id', f'view_{len(found_objects_cnt02) + 1}'))
            found_objects_cnt02.append({view_key: f"<a href='{share_url}/diagrams#{view_key}' target='_blank'>{view_title}</a>"})
            
            logger.debug(f"Найдена контейнерная диаграмма для системы {system_id}")

    # Оценка наличия контейнеров (CNT.01)
    logger.info('Проверка CNT.01: Наличие в модели контейнеров для системы')
    if len(found_objects_cnt01) > 0:
        # Создаем AssessmentObjects как словарь
        assessment_obj_cnt01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_cnt01
        }
        result.append(FitnessStatus(
            code=container_assessments[0]["code"],
            isCheck=True,
            resultDetails="Контейнеры найдены в модели",
            assessmentDescription=container_assessments[0]["description"],
            assessmentObjects=[assessment_obj_cnt01]
        ))
        logger.info("CNT.01 пройден: Контейнеры найдены")
    else:
        result.append(FitnessStatus(
            code=container_assessments[0]["code"],
            isCheck=False,
            resultDetails='Система не содержит контейнеров',
            assessmentDescription=container_assessments[0]["description"],
            assessmentObjects=[]
        ))
        logger.warning("CNT.01 не пройден: Система не содержит контейнеров")

    # Оценка наличия контейнерных диаграмм (CNT.02)
    logger.info('Проверка CNT.02: Наличие в хотя бы одной диаграммы контейнеров')
    if has_view:
        # Создаем AssessmentObjects как словарь
        assessment_obj_cnt02: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_cnt02
        }
        msg_res = '<br>'.join([list(d.values())[0] for d in found_objects_cnt02])
        result.append(FitnessStatus(
            code=container_assessments[1]["code"],
            isCheck=True,
            resultDetails=msg_res,
            assessmentDescription=container_assessments[1]["description"],
            assessmentObjects=[assessment_obj_cnt02]
        ))
        logger.info("CNT.02 пройден: Контейнерная диаграмма найдена")
    else:
        result.append(FitnessStatus(
            code=container_assessments[1]["code"],
            isCheck=False,
            resultDetails='Не найдено контейнерной диаграммы',
            assessmentDescription=container_assessments[1]["description"],
            assessmentObjects=[]
        ))
        logger.warning("CNT.02 не пройден: Контейнерная диаграмма не найдена")
    
    # Оценка технологий в связях (CNT.03)
    logger.info('Проверка CNT.03: Все вызовы между контейнерами имеют технологию')
    if len(relationships_wo_tech) == 0:
        # Создаем AssessmentObjects как словарь
        
        result.append(FitnessStatus(
            code=container_assessments[2]["code"],
            isCheck=True,
            resultDetails="Все связи имеют технологии",
            assessmentDescription=container_assessments[2]["description"],
            assessmentObjects=[]
        ))
        logger.info("CNT.03 пройден: Все связи имеют технологии")
    else:

        msg_res = '<ol>'
        for m in relationships_wo_tech:
            msg_res += f"<li>{relationships[m].get('description', '')}</li>"
        msg_res += '</ol>'
        # Создаем AssessmentObjects для связей без технологий

        assessment_obj_cnt03: AssessmentObjects = {
            "isCheck": False,
            "details": found_objects_cnt03
        }
        result.append(FitnessStatus(
            code=container_assessments[2]["code"],
            isCheck=False,
            resultDetails='Связи без технологий: ' + msg_res,
            assessmentDescription=container_assessments[2]["description"],
            assessmentObjects=[assessment_obj_cnt03]
        ))
        logger.warning(f"CNT.03 не пройден: Найдено {len(relationships_wo_tech)} связей без технологий")

    logger.info(f"Найдено {len(found_objects_git01)} из {total_containers_git_count} контейнеров")

    # Оценка наличия git репозиториев (GIT.01)
    logger.info('Проверка GIT.01: Наличие в модели git репозитория')
    if total_containers_git_count == 0:
        # Нет контейнеров для проверки git
        result.append(FitnessStatus(
            code=container_assessments[4]["code"],
            isCheck=True,
            resultDetails='Нет контейнеров, требующих проверки git репозитория',
            assessmentDescription=container_assessments[4]["description"],
            assessmentObjects=[]
        ))
        logger.info("GIT.01 пропущен: Нет контейнеров для проверки git")
    elif found_containers_with_git_count == total_containers_git_count:
        
        assessment_obj_git01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_git01
        }
        
        msg = f"Контейнеры с репозиторием {total_containers_git_count}:<br><table>"
        i = 1
        for c in [cnt for cnt in found_objects_git01 if 'url' in cnt]:            
            msg += f"<tr><th>{i}</th><td>{c.get('name','')} </td><td> <a href='{c.get('url','')}' target='_'>{c.get('url','')}</a></td></tr>"
            i += 1
        msg += f"</table>"

        result.append(FitnessStatus(
            code=container_assessments[4]["code"],
            isCheck=True,
            resultDetails=msg,
            assessmentDescription=container_assessments[4]["description"],
            assessmentObjects=[assessment_obj_git01]
        ))
        logger.info("GIT.01 пройден: Все контейнеры имеют git репозиторий")
    else:
        # Создаем AssessmentObjects как словарь
        
        assessment_obj_git01: AssessmentObjects = {
            "isCheck": True,
            "details": found_objects_git01
        }

        assessment_obj_git01_bad: AssessmentObjects = {
            "isCheck": False,
            "details": not_found_objects_git01
        }
        
        msg = f"Контейнеры с репозиторием {found_containers_with_git_count}:<br><table>"
        i = 1
        for c in found_objects_git01:            
            msg += f"<tr><th>{i}</th><td>{c.get('name','')} </td><td> <a href='{c.get('url','')}' target='_'>{c.get('url','')}</a></td></tr>"
            i += 1
        msg += f"</table> <hr> Контейнеры без репозитория {total_containers_git_count-found_containers_with_git_count}:<ol>"
        for c in not_found_objects_git01:            
            msg += f"<li>{c.get('name','')}</li>"
        msg += "</ol>"

        result.append(FitnessStatus(
            code=container_assessments[4]["code"],
            isCheck=False,
            resultDetails=f'Не у всех контейнеров есть git репозиторий: <hr> {msg}',
            assessmentDescription=container_assessments[4]["description"],
            assessmentObjects=[assessment_obj_git01,assessment_obj_git01_bad]
        ))
        logger.warning(f"GIT.01 не пройден: Найдено {found_containers_with_git_count} контейнеров с git репозиторием из {total_containers_git_count}")


    logger.info(f"Проверка контейнерной модели завершена. Результатов: {len(result)}")
    return result