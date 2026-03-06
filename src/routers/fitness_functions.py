# Copyright (c) 2024 PJSC VimpelCom
import os
import json
import requests
import tempfile
import base64
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from json.decoder import JSONDecodeError
from pydantic import BaseModel
from typing import Dict

from structurizr_utils.models.model_documents import get_document
from structurizr_utils.models.models_product import Product, get_product,FitnessFunctionClient
from structurizr_utils.functions.objects import safe_execution
from structurizr_utils.functions.adr import check_adr
from structurizr_utils.functions.api import check_api
from structurizr_utils.functions.capability import check_capability
from structurizr_utils.functions.context import check_context
from structurizr_utils.functions.container import check_container
from structurizr_utils.functions.technology import check_technology
from structurizr_utils.functions.sequences import check_sequences
from structurizr_utils.functions.deployment import check_deployment
from structurizr_utils.functions.patterns import check_patterns
from structurizr_utils.utils.utils import get_workspace_cmdb
from structurizr import url_onpremises_base
from . import log_endpoint_call, log_key_milestone, log_error_with_details, log_function_entry, log_function_exit

router = APIRouter()

# Модели для ошибок
class ErrorDetail(BaseModel):
    detail: str

class SuccessResponse(BaseModel):
    details: str
    workspace_id: str = None
    dashboard: str = None


def publish_json_workspace(cmdb: str, workspace_id : int, structurizrApiKey : str, structurizrApiSecret: str,  product_json : dict) -> bool:
    log_function_entry("publish_json_workspace", cmdb=cmdb, workspace_id=workspace_id)
    
    log_key_milestone(f"Publishing JSON workspace for {cmdb}")

    try:
        filename = tempfile.gettempdir() +f'/workspace_{cmdb}.json'
        
        log_key_milestone(f"Writing workspace JSON to {filename}")
        
        with open(filename,'w') as f:
            f.write(json.dumps(product_json,ensure_ascii=False))

        command  = "/usr/local/structurizr-cli/structurizr.sh "
        command += "push -url "+url_onpremises_base+" "
        command += "-id "+ str(workspace_id) + " "
        command += "-key "+structurizrApiKey+" "
        command += "-secret "+structurizrApiSecret+" "
        command += "-workspace "+filename
        command += " -merge false"
        
        log_key_milestone(f"Executing CLI command for workspace {workspace_id}")
        
        result = False
        if os.system(command) == 0:
            result = True
            log_key_milestone(f"CLI command successful for workspace {workspace_id}")

        if os.path.exists(filename):
            os.remove(filename)
            log_key_milestone(f"Temporary file {filename} removed")
        
        log_function_exit("publish_json_workspace", result=result)
        return result
        
    except Exception as e:
        log_error_with_details(e, "publish_json_workspace", {"cmdb": cmdb, "workspace_id": workspace_id})
        log_function_exit("publish_json_workspace", result=False)
        return False
    
# Метода публикации архитектуры в Structurizr
@router.post(
    "/api/v1/workspace/{docId}",
    response_model=SuccessResponse,
    responses={
        201: {
            "description": "Workspace успешно опубликован в Structurizr",
            "content": {
                "application/json": {
                    "example": {"details": "Ok", "workspace_id": "123"}
                }
            }
        },
        400: {
            "description": "Некорректная структура JSON или отсутствует CMDB код",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't find CMDB code in workspace.json"}
                }
            }
        },
        404: {
            "description": "Документ не найден или продукт не найден в BeeAtlas",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE not found in BeeAtlas"}
                }
            }
        },
        503: {
            "description": "Ошибка сервиса документов",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Error calling document service"}
                }
            }
        }
    }
)
@log_endpoint_call
def upload_workspace_structurizr(docId: int):
    log_key_milestone(f"Starting workspace upload process for document {docId}")
    
    # load document
    log_key_milestone("Loading document from service")
    try:
        data = get_document(document_id=docId)
        log_key_milestone("Document loaded successfully")
    except HTTPException as e:
        log_key_milestone(f"HTTP error loading document: {e.status_code}", level="error")
        raise e
    except JSONDecodeError as e:
        log_key_milestone(f"JSON decode error: {e}", level="error")
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as ex:
        log_error_with_details(ex, "document_loading", {"docId": docId})
        raise HTTPException(status_code=503, detail=f"Error calling document service {ex}")

    # get cmdb_code from document
    log_key_milestone("Extracting CMDB code from document")
    try:
        cmdb = get_workspace_cmdb(data)
        if cmdb is None or cmdb=="":
            log_key_milestone("CMDB code not found in workspace.json", level="error")
            raise HTTPException(status_code=400, detail=f"Can't find CMDB code in workspace.json")
        log_key_milestone(f"CMDB code extracted: {cmdb}")
    except Exception as ex:
        log_error_with_details(ex, "cmdb_extraction", {"docId": docId, "data": str(data)[:200]})
        raise HTTPException(status_code=400, detail=f"Wrong json structure {ex}")

    log_key_milestone(f"Loading product {cmdb} from BeeAtlas")
    product_beeatlas = get_product(cmdb)
    if product_beeatlas is None:
        log_key_milestone(f"Product with code {cmdb} not found in BeeAtlas", level="error")
        raise HTTPException(status_code=404, detail=f"Product with code {cmdb} not found in BeeAtlas")
    
    if product_beeatlas.structurizrApiUrl is None:
        log_key_milestone(f"Product {cmdb} does not have structurizrApiUrl", level="error")
        raise HTTPException(status_code=404, detail=f"Product with code {cmdb} not have structurizrApiUrl")
    
    try:
        id = product_beeatlas.structurizrApiUrl.split('/')[-1]
        log_key_milestone(f"Extracted workspace ID: {id}")

        log_key_milestone("Publishing JSON workspace to Structurizr")
        if not publish_json_workspace(cmdb= product_beeatlas.alias,
                               workspace_id=id, 
                               structurizrApiKey = product_beeatlas.structurizrApiKey,
                               structurizrApiSecret = product_beeatlas.structurizrApiSecret,
                               product_json=data):
            return JSONResponse(status_code=409, content={"details": f"Error publish to Structurizr OnPremises {url_onpremises_base}","workspace_id":id})
        
        log_key_milestone("Workspace published successfully")
        return JSONResponse(status_code=201, content={"details": "Ok","workspace_id":id})
        
    except Exception as e:
        log_error_with_details(e, "workspace_validation", {"docId": docId, "cmdb": cmdb, "workspace_id": id})
        raise HTTPException(status_code=400, detail=f"Error validating workspace")

# Метода публикации архитектуры в ФДМ
@router.post(
    "/api/v1/workspace/{docId}/fdm",
    response_model=SuccessResponse,
    responses={
        201: {
            "description": "Проверки выполнены успешно",
            "content": {
                "application/json": {
                    "example": {"details": "Ok"}
                }
            }
        },
        400: {
            "description": "Ошибка валидации workspace",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't find CMDB code in workspace.json"}
                }
            }
        },
        404: {
            "description": "Документ или продукт не найден",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE not found in BeeAtlas"}
                }
            }
        },
        503: {
            "description": "Ошибка сервиса документов",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Error calling document service"}
                }
            }
        }
    }
)
@log_endpoint_call
def upload_workspace_fdm(docId: int):
    # load document
    data = None
    try:
        log_key_milestone(f"Loading document id {docId}")
        data = get_document(document_id=docId)
        
    except HTTPException as e:
        raise e
    except JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as ex:
        log_error_with_details(ex, "document_loading", {"docId": docId})
        raise HTTPException(status_code=503, detail=f"Error calling document service {ex}")

    # get cmdb_code from document
    log_key_milestone("Extracting CMDB code from document")
    try:
        cmdb = get_workspace_cmdb(data)
        if cmdb is None or cmdb=="":
            raise HTTPException(status_code=400, detail=f"Can't find CMDB code in workspace.json")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Wrong json structure {ex}")

    log_key_milestone(f"Loading product {cmdb}")
    product_beeatlas = get_product(cmdb)
    if product_beeatlas is None:
        raise HTTPException(status_code=404, detail=f"Product with code {cmdb} not found in BeeAtlas")
    
    if product_beeatlas.structurizrApiUrl is None:
        raise HTTPException(status_code=404, detail=f"Product with code {cmdb} not have structurizrApiUrl")

    log_key_milestone(f"Starting fitness check for {cmdb}")
    result = list()
    url_sparx = os.getenv("URL_SPARX",None)
    product_id = product_beeatlas.id

    if url_sparx:
        url_sparx = url_sparx.rstrip("/")

    try:
        share_url = product_beeatlas.structurizrApiUrl
        result.extend(safe_execution(check_context,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_capability,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_technology,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_sequences,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_deployment,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_container,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_adr,cmdb,data,url_sparx,share_url, True,product_id))
        result.extend(safe_execution(check_api,cmdb,data,url_sparx,share_url, True,False,product_id))
        result.extend(safe_execution(check_patterns, cmdb, data, url_sparx, share_url, True,product_id))
    except Exception as e:
        log_error_with_details(e, "fitness_check_execution", {"cmdb": cmdb, "docId": docId})
        raise HTTPException(status_code=400, detail=f"Error validating workspace")

    return JSONResponse(status_code=201, content={"details": "Ok"})

# Проверка fitness-функций для документа
@router.post(
    "/api/v1/fitness-function/local/{docId}",
    response_model=SuccessResponse,
    responses={
        201: {
            "description": "Проверки выполнены успешно",
            "content": {
                "application/json": {
                    "example": {
                        "details": "Ok",
                        "dashboard": "https://dashboard-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru/systems/PRODUCT_CODE"
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации workspace",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't find CMDB code in workspace.json"}
                }
            }
        },
        404: {
            "description": "Документ или продукт не найден",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE not found in BeeAtlas"}
                }
            }
        },
        500: {
            "description": "Ошибка сохранения результатов",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Error saving fitness function information into Sparx"}
                }
            }
        },
        503: {
            "description": "Ошибка сервиса документов",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Error calling document service"}
                }
            }
        }
    }
)
@log_endpoint_call
def fitness_check(docId: int,pipelineId : int = 0):

    # load document
    log_key_milestone(f"Loading document {docId} for process {pipelineId}")
    try:
        data = get_document(document_id=docId)
    except HTTPException as e:
        raise e
    except JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as ex:
        log_error_with_details(ex, "document_loading", {"docId": docId, "pipelineId": pipelineId})
        raise HTTPException(status_code=503, detail=f"Error calling document service {ex}")

    # get cmdb_code from document
    log_key_milestone("Extracting CMDB code from document")
    try:
        cmdb = get_workspace_cmdb(data)
        if cmdb is None or cmdb=="":
            raise HTTPException(status_code=400, detail=f"Can't find CMDB code in workspace.json")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Wrong json structure {ex}")

    log_key_milestone(f"Loading product {cmdb}")
    product_beeatlas = get_product(cmdb)
    if product_beeatlas is None:
        raise HTTPException(status_code=404, detail=f"Product with code {cmdb} not found in BeeAtlas")
    
    if product_beeatlas.structurizrApiUrl is None:
        raise HTTPException(status_code=404, detail=f"Product with code {cmdb} not have structurizrApiUrl")

    log_key_milestone(f"Starting fitness check for {cmdb}")
    result = list()
    url_sparx = os.getenv("URL_SPARX",None)
    product_id = product_beeatlas.id

    if url_sparx:
        url_sparx = url_sparx.rstrip("/")

    try:
        share_url = product_beeatlas.structurizrApiUrl
        result.extend(safe_execution(check_context,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_capability,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_technology,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_sequences,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_deployment,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_container,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_adr,cmdb,data,url_sparx,share_url, False,product_id))
        result.extend(safe_execution(check_api,cmdb,data,url_sparx,share_url, False,False,product_id))
        result.extend(safe_execution(check_patterns, cmdb, data, url_sparx, share_url, False,product_id))

    except Exception as e:
        log_error_with_details(e, "fitness_check_execution", {"cmdb": cmdb, "docId": docId, "pipelineId": pipelineId})
        raise HTTPException(status_code=400, detail=f"Error validating workspace")
    

    if result:
        log_key_milestone(f'Dashboard::Отправляем {len(result)} результатов проверок в backend для CMDB: {cmdb}')
        
        try: 
            for f in result:
                gmt_plus_3 = timezone(timedelta(hours=3))
                current_time = datetime.now(gmt_plus_3)
                status = 0
                if not f["isCheck"]:
                    status = 404

                assesment_data = {
                    "system_code": cmdb,
                    "fitness_function_code": f["code"],
                    "assessment_date": current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "assessment_description": f["assessmentDescription"],
                    "status": status,
                    "result_details": f["resultDetails"]
                    }
                # Формирование URL для отправки результатов
                url: str = f"{url_sparx}/api/v4/systems/{cmdb}/assessments"
                headers: Dict[str, str] = {
                    'content-type': 'application/json',
                    'accept': 'application/json'
                }
                json_request: str = json.dumps(assesment_data, ensure_ascii=False)
                response: requests.Response = requests.post(
                    url, 
                    data=json_request.encode('utf-8'), 
                    headers=headers, 
                    verify=False
                )
                
                if response.status_code == 200:
                    log_key_milestone(f'Результат ff {f["code"]} отправлен: {response.status_code} {response.reason}')
                else:
                    log_key_milestone(f'Ошибка при отправке результата в URL: {url}')
                    log_key_milestone(f'Ответ сервера: {response.status_code} {response.reason}')
                    log_key_milestone(f'Текст ответа: {response.text}')
                    log_key_milestone(f'Тело запроса: {json_request}')
                    
        except Exception as ex:
            log_error_with_details(ex, "fitness_check_service_posting", {"cmdb": cmdb})

    # Основной способ отправки через FitnessFunctionClient 
    try:
        ffclient = FitnessFunctionClient()
        res = list()
        log_key_milestone(f"Posting fitness check to new service {cmdb}")
        for f in result:
            new_assessment_objects = []               
            for assessment_object in f["assessmentObjects"]:
                
                for detail in assessment_object["details"]:
                    new_details = assessment_object.copy()
                    new_details["details"] = []
                    for key, value in detail.items():
                        new_details["details"].append({
                            "key": "name",
                            "value": key
                        })
                        new_details["details"].append({
                            "key": "value",
                            "value": value
                        })
                    assessment_object = new_details.copy()
                    new_assessment_objects.append(assessment_object)
            
            res.append({"code": f["code"],
                        "isCheck": f["isCheck"],
                        "assessmentDescription": f["assessmentDescription"],
                        "assessmentObjects": new_assessment_objects,
                        "resultDetails": f["resultDetails"]})

        ffclient.post_fitness_functions(cmdb=cmdb,
                                        source_type="pipeline",
                                        requests=res,
                                        source_id=pipelineId)
        log_key_milestone(f'Результаты отправлены в product backend для CMDB: {cmdb}')
    except Exception as ex:
        log_key_milestone(f'Body: {json.dumps(res, ensure_ascii=False)}')
        log_error_with_details(ex, "fitness_check_service_posting", {"cmdb": cmdb})
        
    return JSONResponse(status_code=201, content={"details": "Ok","dashboard":f"https://dashboard-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru/systems/{cmdb}"})