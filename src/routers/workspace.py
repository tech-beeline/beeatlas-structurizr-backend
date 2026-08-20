# Copyright (c) 2024 PJSC VimpelCom
import os
import subprocess
import warnings
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

from structurizr_utils.models.models_workspace import RestProduct,RestWorkspace
from structurizr_utils.models.models_product import Product, ProductPutDto, get_product, patch_product
from structurizr_utils.models.model_documents import upload_workspace_json
from structurizr import load_workspace,post_workspace,get_workspaces,Workspace, get_workspace_cmdb,url_onpremises_base
from . import log_endpoint_call, log_key_milestone, log_error_with_details, log_function_entry, log_function_exit

from routers.utils import DSLWorkspace, convert_dsl2json, decode_base64, ValidationError, ErrorDetail

router = APIRouter()

# Отключение вывода предупреждений из requests
warnings.simplefilter('ignore', InsecureRequestWarning)


def publish_default_workspace(workspace_id : int, architect_name : str, product : Product) -> bool:
    log_function_entry("publish_default_workspace", workspace_id=workspace_id, architect_name=architect_name, product_alias=product.alias)
    
    log_key_milestone(f"Publishing default workspace template for {product.alias}")
    
    try:
        env = Environment(loader=FileSystemLoader('/opt/structurizr_backend/templates'))
        workspace_template = env.get_template('workspace.dsl')
        filename = tempfile.gettempdir() +'/workspace.dsl'
        
        log_key_milestone(f"Template loaded, writing to {filename}")
        
        # Экранируем кавычки в имени продукта
        product.name = product.name.replace('"',' ').replace("'",'')

        with open(filename,'w') as f:
            f.write(str(workspace_template.render( {'product': product, "architect_name" : architect_name})))

        log_key_milestone(f"Executing CLI command for workspace {workspace_id}")
        
        # Use subprocess.run with argument list to avoid shell word-splitting on spaces
        command = [
            "/usr/local/structurizr-cli/structurizr.sh",
            "push",
            "-url", url_onpremises_base,
            "-id", str(workspace_id),
            "-key", product.structurizrApiKey,
            "-secret", product.structurizrApiSecret,
            "-workspace", filename
        ]
        
        proc = subprocess.run(command, capture_output=True, text=True)
        
        if proc.returncode == 0:
            log_function_exit("publish_default_workspace", result=True)
            return True
        else:
            log_key_milestone(f"CLI command failed for workspace {workspace_id} (rc={proc.returncode})", level="error")
            if proc.stdout:
                log_key_milestone(f"CLI stdout: {proc.stdout.strip()}")
            if proc.stderr:
                log_key_milestone(f"CLI stderr: {proc.stderr.strip()}")
            log_function_exit("publish_default_workspace", result=False)
            return False
    except Exception as e:
        log_error_with_details(e, "publish_default_workspace", {"workspace_id": workspace_id, "product_alias": product.alias})
        log_function_exit("publish_default_workspace", result=False)
        return False
    

@router.post(
    "/api/v1/workspace/validate",
    response_model=Dict,
    responses={
        200: {
            "description": "Workspace валиден",
            "content": {
                "application/json": {
                    "example": {"valid": "true"}
                }
            }
        },
        400: {
            "description": "Некорректный base64 или ошибка валидации",
            "model": ValidationError,
            "content": {
                "application/json": {
                    "example": {"valid": "false", "error": "Переданная строка не является base64 закодированной UTF-8 строкой"}
                }
            }
        }
    }
)
@log_endpoint_call
def validate_workspace(dsl_workspace : DSLWorkspace) -> Dict:

    # check if workspace exist
    if dsl_workspace is None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой запрос"})
    
    # check if workspace key exists and not None
    if "workspace" not in dsl_workspace or dsl_workspace["workspace"] is None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой workspace"})

    if len(dsl_workspace["workspace"].strip())==0:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой workspace"})

    # check if workspace base64 encoded
    log_key_milestone("Decoding base64 encoded workspace")
    dsl_workspace_decoded = decode_base64(dsl_workspace["workspace"],"utf-8", False)

    if dsl_workspace_decoded == None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Переданная строка не является base64 закодированной UTF-8 строкой"})

    result = convert_dsl2json(dsl = dsl_workspace_decoded)

    if result.get("errors"):
        raise HTTPException(status_code=400, detail={"valid": "false","error" : result.get("errors")})

    return {"valid": "true"}


@router.post(
    "/api/v1/workspace/conversion",
    response_model=Dict,
    responses={
        200: {
            "description": "Workspace JSON создан",
            "content": {
                "application/json": {
                    "example": {"valid": "true"}
                }
            }
        },
        400: {
            "description": "Некорректный base64 или ошибка валидации",
            "model": ValidationError,
            "content": {
                "application/json": {
                    "example": {"valid": "false", "error": "Переданная строка не является base64 закодированной UTF-8 строкой"}
                }
            }
        }
    }
)
@log_endpoint_call
def convert_workspace(dsl_workspace : DSLWorkspace) -> Dict:

    # check if workspace exist
    if dsl_workspace is None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой запрос"})
    
    # check if workspace key exists and not None
    if "workspace" not in dsl_workspace or dsl_workspace["workspace"] is None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой workspace"})

    if len(dsl_workspace["workspace"].strip())==0:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой workspace"})

    # check if workspace base64 encoded
    log_key_milestone("Decoding base64 encoded workspace")
    dsl_workspace_decoded = decode_base64(dsl_workspace["workspace"],"utf-8", False)

    if dsl_workspace_decoded == None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Переданная строка не является base64 закодированной UTF-8 строкой"})

    result = convert_dsl2json(dsl = dsl_workspace_decoded)

    if result.get("errors"):
        raise HTTPException(status_code=400, detail={"valid": "false","error" : result.get("errors")})

    return result.get("json")

@router.post(
    "/api/v1/workspace/conversion2doc",
    response_model=Dict,
    responses={
        200: {
            "description": "Workspace JSON создан и отправлен в Document сервис",
            "content": {
                "application/json": {
                    "example": {"doc_id": 9999}
                }
            }
        },
        400: {
            "description": "Некорректный base64 или ошибка валидации",
            "model": ValidationError,
            "content": {
                "application/json": {
                    "example": {"valid": "false", "error": "Переданная строка не является base64 закодированной UTF-8 строкой"}
                }
            }
        }
    }
)
@log_endpoint_call
def convert2doc_workspace(dsl_workspace : DSLWorkspace) -> Dict:

    # check if workspace exist
    if dsl_workspace is None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой запрос"})
    
    # check if workspace key exists and not None
    if "workspace" not in dsl_workspace or dsl_workspace["workspace"] is None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой workspace"})

    if len(dsl_workspace["workspace"].strip())==0:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Передан пустой workspace"})

    # check if workspace base64 encoded
    log_key_milestone("Decoding base64 encoded workspace")
    dsl_workspace_decoded = decode_base64(dsl_workspace["workspace"],"utf-8", False)

    if dsl_workspace_decoded == None:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : "Переданная строка не является base64 закодированной UTF-8 строкой"})

    result = convert_dsl2json(dsl = dsl_workspace_decoded)

    if result.get("errors"):
        raise HTTPException(status_code=400, detail={"valid": "false","error" : result.get("errors")})

    # upload to doc service

    try:
        log_key_milestone(f"Uploading workspace.json to {os.getenv('URL_DOCUMENTS')}")
        doc_id = upload_workspace_json(result.get("json"))
        return {"doc_id" : doc_id }
    except Exception as ex:
        raise HTTPException(status_code=400, detail={"valid": "false","error" : f"{ex}"})


@router.post(
    "/workspace", 
    response_model=RestWorkspace,
    responses={
        200: {
            "description": "Workspace успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "code": "PRODUCT_CODE",
                        "name": "Product Name",
                        "api_key": "structurizr_api_key",
                        "api_secret": "structurizr_api_secret",
                        "api_url": "https://structurizr.example.com/share/123"
                    }
                }
            }
        },
        400: {
            "description": "Некорректные параметры запроса",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Some of parameters is empty or missing"}
                }
            }
        },
        404: {
            "description": "Продукт не найден в BeeAtlas",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE not found in BeeAtlas"}
                }
            }
        },
        422: {
            "description": "Продукт уже имеет Structurizr workspace",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE already has structurizrApiUrl"}
                }
            }
        },
        409: {
            "description": "Ошибка вызова Structurizr On Premises",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't create new structurizr workspace"}
                }
            }
        },
        500: {
            "description": "Ошибка создания workspace",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't create new structurizr workspace"}
                }
            }
        }
    }
)
@router.post(
    "/api/v1/workspace", 
    response_model=RestWorkspace,
    responses={
        200: {
            "description": "Workspace успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "code": "PRODUCT_CODE",
                        "name": "Product Name",
                        "api_key": "structurizr_api_key",
                        "api_secret": "structurizr_api_secret",
                        "api_url": "https://structurizr.example.com/share/123"
                    }
                }
            }
        },
        400: {
            "description": "Некорректные параметры запроса",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Some of parameters is empty or missing"}
                }
            }
        },
        404: {
            "description": "Продукт не найден в BeeAtlas",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE not found in BeeAtlas"}
                }
            }
        },
        422: {
            "description": "Продукт уже имеет Structurizr workspace",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Product with code PRODUCT_CODE already has structurizrApiUrl"}
                }
            }
        },
        409: {
            "description": "Ошибка вызова Structurizr On Premises",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't create new structurizr workspace"}
                }
            }
        },
        500: {
            "description": "Ошибка создания workspace",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Can't create new structurizr workspace"}
                }
            }
        }
    }
)
@log_endpoint_call
def create_workspace(product: RestProduct):
    log_key_milestone("Starting workspace creation process")
    
    # Валидация параметров
    if product.code is None or product.code == "" or product.architect_name is None or product.architect_name == "":
        log_key_milestone("Validation failed: missing required parameters", level="error")
        raise HTTPException(status_code=400, detail=f"Some of parameters is empty or missing")
    
    log_key_milestone("Checking existing product in BeeAtlas")
    product_beeatlas = get_product(product.code)

    if product_beeatlas is None:
        log_key_milestone(f"Product with code {product.code} not found in BeeAtlas", level="error")
        raise HTTPException(status_code=404, detail=f"Product with code {product.code} not found in BeeAtlas")

    # Проверка существования workspace
    if not product_beeatlas.structurizrApiUrl is None and product_beeatlas.structurizrApiUrl != "":
        log_key_milestone(f"Product {product.code} already has structurizrApiUrl", level="warning")
        raise HTTPException(status_code=422, detail=f"Product with code {product.code} already has structurizrApiUrl")
    
    if not product_beeatlas.structurizrApiKey is None and product_beeatlas.structurizrApiKey != "":
        log_key_milestone(f"Product {product.code} already has structurizrApiKey", level="warning")
        raise HTTPException(status_code=422, detail=f"Product with code {product.code} already has structurizrApiKey")
    
    if not product_beeatlas.structurizrApiSecret is None and product_beeatlas.structurizrApiSecret != "":
        log_key_milestone(f"Product {product.code} already has structurizrApiSecret", level="warning")
        raise HTTPException(status_code=422, detail=f"Product with code {product.code} already has structurizrApiSecret")

    log_key_milestone("Creating new Structurizr workspace")
    created_workspace = post_workspace()

    if created_workspace is None:
        log_key_milestone("Failed to create new Structurizr workspace", level="error")
        raise HTTPException(status_code=500, detail="Can't create new structurizr workspace")

    log_key_milestone(f"Workspace created with ID: {created_workspace['id']}")
    
    # Обновление продукта
    product_beeatlas.structurizrApiKey = created_workspace["apiKey"]
    product_beeatlas.structurizrApiSecret= created_workspace["apiSecret"]
    product_beeatlas.structurizrApiUrl= f"{url_onpremises_base[0:url_onpremises_base.find('/api')]}/share/{created_workspace['id']}"
    product_beeatlas.structurizrWorkspaceName= product_beeatlas.name

    log_key_milestone("Publishing default workspace template")
    if  not publish_default_workspace(int(created_workspace['id']),product.architect_name,product_beeatlas):
        log_key_milestone("Failed to publish default workspace template", level="error")
        raise HTTPException(status_code=409, detail=f"Can't publish default workspace to structurizr (cli) {url_onpremises_base}")

    log_key_milestone("Updating product in BeeAtlas")
    product_put = ProductPutDto(
        description = product_beeatlas.description,
        gitUrl = product_beeatlas.gitUrl,
        name = product_beeatlas.name,
        structurizrWorkspaceName = product_beeatlas.name,
        structurizrApiKey =  product_beeatlas.structurizrApiKey,
        structurizrApiSecret = product_beeatlas.structurizrApiSecret,
        structurizrApiUrl = product_beeatlas.structurizrApiUrl)
    patch_product(cmdb= product_beeatlas.alias, product = product_put)

    result = RestWorkspace(id=int(created_workspace["id"]),
                           code=product_beeatlas.alias,
                           name=product_beeatlas.name,
                           api_key=product_beeatlas.structurizrApiKey,
                           api_secret=product_beeatlas.structurizrApiSecret,
                           api_url=product_beeatlas.structurizrApiUrl)

    return result

