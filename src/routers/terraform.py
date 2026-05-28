# Copyright (c) 2024 PJSC VimpelCom
import os
import subprocess
import json
import requests
import tempfile
import logging

from pydantic import BaseModel
from typing import Annotated, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request, Header
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from json.decoder import JSONDecodeError

from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

from structurizr_utils.models.models_product import Product, get_product
from structurizr_utils.models.model_documents import get_document
from structurizr_utils.models.model_terraform import Resources,Vm,Redis,PostgreSQL,KafkaCluster,MongoDB,GeneralResource
from structurizr_utils.models.model_vega_vps import VegaVPSClient
from structurizr_utils.utils.utils import get_workspace_cmdb
from . import log_endpoint_call, log_key_milestone, log_error_with_details, log_function_entry, log_function_exit

router = APIRouter()

def error(msg : str):
    log_key_milestone(f"Error: {msg}", level="error")

class Error (BaseModel):
    error_msg : str

class ErrorDetail(BaseModel):
    detail: str

def get_resource_model(environment : str, workspace : dict, error_list : list) -> Resources:
    log_function_entry("get_resource_model", environment=environment)
    
    log_key_milestone("Validating workspace structure")
    
    if not 'model' in workspace:
        log_key_milestone("Workspace missing 'model' section", level="error")
        raise HTTPException(status_code=400, detail=f"В workspace нет model")

        
    model = workspace['model']
    
    if not 'deploymentNodes' in model:
        log_key_milestone("Workspace missing 'deploymentNodes' section", level="error")
        raise HTTPException(status_code=400, detail=f"Должен быть только один проект для Development Environment")
    
    log_key_milestone("Workspace structure validated successfully")
    
    containers = dict()

    for s in model.get('softwareSystems',dict()):
        for c in s.get('containers',dict()):
            containers[c.get('id','0')] = c
    
    def walk_tree(environment : str,
                  res : Resources,
                  deployment_node : dict,
                  region : str,
                  vega_project : str,
                  containers : dict, 
                  error_list : list):
        
        if deployment_node['environment'].lower().strip() == environment:
            instances = int(deployment_node.get('instances','1'))
            if 'properties' in deployment_node:
                if 'region' in deployment_node['properties']:
                    region = deployment_node['properties'].get('region','')
                if 'vega_project' in deployment_node['properties']:
                    vega_project = deployment_node['properties'].get('vega_project','')

                type = deployment_node['properties'].get('type','').lower().strip()

                if type == "vm":
                    log_key_milestone(f"Processing VM resource: {deployment_node['name']}")
                    error_msg = Vm().check_errors(
                        properties = deployment_node['properties'], 
                        name = deployment_node["name"], 
                        instances = instances, 
                        region = region,
                        project = vega_project)
                    if error_msg is not None:
                        error_list.append(Error(error_msg=error_msg))
                        log_key_milestone(f"VM validation failed: {error_msg}", level="error")
                    else:
                        res.resources.append(Vm().parse(
                            properties = deployment_node['properties'], 
                            name = deployment_node["name"], 
                            instances = instances, 
                            region = region,
                            project = vega_project))
                        log_key_milestone(f"VM resource added successfully: {deployment_node['name']}")
                elif type == "postgresql":
                    log_key_milestone(f"Processing PostgreSQL resource: {deployment_node['name']}")
                    error_msg = PostgreSQL().check_errors(
                        properties = deployment_node['properties'], 
                        name = deployment_node["name"], 
                        instances = instances, 
                        region = region,
                        project = vega_project)
                    if error_msg is not None:
                        error_list.append(Error(error_msg=error_msg))
                        log_key_milestone(f"PostgreSQL validation failed: {error_msg}", level="error")
                    else:
                        res.resources.append(PostgreSQL().parse(
                            properties = deployment_node['properties'], 
                            name = deployment_node["name"], 
                            instances = instances, 
                            region = region,
                            project = vega_project))
                        log_key_milestone(f"PostgreSQL resource added successfully: {deployment_node['name']}")
                elif type == "mongodb":
                    log_key_milestone(f"Processing MongoDB resource: {deployment_node['name']}")
                    error_msg = MongoDB().check_errors(
                        properties = deployment_node['properties'], 
                        name = deployment_node["name"], 
                        instances = instances, 
                        region = region,
                        project = vega_project)
                    if error_msg is not None:
                        error_list.append(Error(error_msg=error_msg))
                        log_key_milestone(f"MongoDB validation failed: {error_msg}", level="error")
                    else:
                        res.resources.append(MongoDB().parse(
                            properties = deployment_node['properties'], 
                            name = deployment_node["name"], 
                            instances = instances, 
                            region = region,
                            project = vega_project))
                        log_key_milestone(f"MongoDB resource added successfully: {deployment_node['name']}")
                elif type == "redis":
                    log_key_milestone(f"Processing Redis resource: {deployment_node['name']}")
                    error_msg = Redis().check_errors(
                        properties = deployment_node['properties'], 
                        name = deployment_node["name"], 
                        instances = instances, 
                        region = region,
                        project = vega_project)
                    if error_msg is not None:
                        error_list.append(Error(error_msg=error_msg))
                        log_key_milestone(f"Redis validation failed: {error_msg}", level="error")
                    else:
                        res.resources.append(Redis().parse(
                            properties = deployment_node['properties'], 
                            name = deployment_node["name"], 
                            instances = instances, 
                            region = region,
                            project = vega_project))
                        log_key_milestone(f"Redis resource added successfully: {deployment_node['name']}")
                elif type == "kafka":
                    if "containerInstances" in deployment_node:
                        topic_names = list()

                        for ci in deployment_node["containerInstances"]:
                            containerId = ci.get("containerId","0")
                            if containerId in containers:
                                topic_names.append(containers.get(containerId,dict()).get('name',None))

                        if len(topic_names)>0 :
                            log_key_milestone(f"Processing Kafka cluster resource: {deployment_node['name']}")
                            error_msg = KafkaCluster().check_errors(
                                properties = deployment_node['properties'], 
                                name = deployment_node["name"], 
                                instances = instances, 
                                region = region,
                                project = vega_project)
                            if error_msg is not None:
                                error_list.append(Error(error_msg=error_msg))
                                log_key_milestone(f"Kafka cluster validation failed: {error_msg}", level="error")
                            else:    
                                res.resources.append(KafkaCluster().parse(
                                    properties = deployment_node['properties'], 
                                    name = deployment_node["name"], 
                                    instances = instances, 
                                    region = region,
                                    project = vega_project,
                                    topic_names = topic_names))
                                log_key_milestone(f"Kafka cluster resource added successfully: {deployment_node['name']}")
                        else:
                            error_list.append(Error(error_msg=f"No topics for kafka cluster"))
                            log_key_milestone(f"Kafka cluster validation failed: No topics for kafka cluster", level="error")
                    else:
                        error_list.append(Error(error_msg=f"No container instances in kafka cluster"))
                        log_key_milestone(f"Kafka cluster validation failed: No container instances in kafka cluster", level="error")
                else:
                    log_key_milestone(f"Processing GeneralResource resource: {deployment_node['name']}")
                    error_msg = GeneralResource().check_errors(
                        properties = deployment_node['properties'], 
                        name = deployment_node["name"], 
                        instances = instances, 
                        region = region,
                        project = vega_project)
                    if error_msg is not None:
                        error_list.append(Error(error_msg=error_msg))
                        log_key_milestone(f"GeneralResource validation failed: {error_msg}", level="error")
                    else:
                        res.resources.append(GeneralResource().parse(
                            properties = deployment_node['properties'], 
                            name = deployment_node["name"], 
                            instances = instances, 
                            region = region,
                            project = vega_project))
                        log_key_milestone(f"GeneralResource resource added successfully: {deployment_node['name']}")

                
            if 'children' in deployment_node:
                for c in deployment_node['children']:
                    walk_tree(environment = environment,
                            res = res,
                            deployment_node = c,
                            region = region,
                            vega_project = vega_project,
                            containers=containers,
                            error_list=error_list)

    res            = Resources()
    region         = None
    vega_project   = None

    for node in model["deploymentNodes"]:
        walk_tree(environment=environment.lower().strip(),
                res=res,
                deployment_node=node,
                region=region,
                vega_project=vega_project,
                containers = containers,
                error_list=error_list)
        
    log_function_exit("get_resource_model")
    return res


def generate_terraform_content(client: VegaVPSClient, environment : str, token : str, workspace : dict, error_list : list) -> str:
    log_function_entry("generate_terraform_content", environment=environment)
    env = Environment(loader=FileSystemLoader('/opt/structurizr_backend/templates/terraform'))
    main_template = env.get_template('main.jinja')
    
    # load resources
    res = get_resource_model( environment = environment,workspace   = workspace, error_list = error_list)

    projects        = set()
    project_regions = dict()
    project_flavors = dict()
    project_images  = dict()

    main_project = None

    # load resources
    
    resources = []
    for item in res.resources:
        if item.project and item.resource_type:
            projects.add(item.project)
            resources.append(item)

    res.resources = resources

    log_key_milestone(f"Resource model generated with {len(resources)} resources")

    log_key_milestone(f"Projects found: {projects}")
    if len(projects) > 1:
        error_list.append(Error(error_msg=f"Должен быть только один проект для Development Environment, сейчас {len(projects)}"))
        log_key_milestone(f"Terraform generation failed: Multiple projects found for environment {environment}", level="error")
        log_function_exit("generate_terraform_content")
        return None
    if len(projects) == 0:
        error_list.append(Error(error_msg=f"Не найден ни один Development Environment с именем {environment}"))
        log_key_milestone(f"Terraform generation failed: No development environment found with name {environment}", level="error")
        log_function_exit("generate_terraform_content")
        return None

    
    main_project = next(iter(projects))
    log_key_milestone(f"Main project: {main_project}")

    for project in projects:
        try:
            project_flavors[project] = client.get_flavors(project)
        except Exception as e:
            error_list.append(Error(error_msg=f"Unable to load Vega flavors with provided token from { client.base_url} for {project}: {e}"))
            log_key_milestone(f"Unable to load Vega flavors for project {project}: {e}", level="error")
            log_function_exit("generate_terraform_content")
            return None
        
        try:
            project_images[project]  = client.get_images(project)
        except Exception as e:
            error_list.append(Error(error_msg=f"Unable to load Vega images with provided token from { client.base_url} for {project}: {e}"))
            log_key_milestone(f"Unable to load Vega images for project {project}: {e}", level="error")
            log_function_exit("generate_terraform_content")
            return None

        
        try:
            project_regions[project] = client.get_regions(project)
        except Exception as e:
            error_list.append(Error(error_msg=f"Unable to load Vega regions with provided token from { client.base_url} for {project}: {e}"))
            log_key_milestone(f"Unable to load Vega regions for project {project}: {e}", level="error")
            log_function_exit("generate_terraform_content")
            return None


    for item in res.resources:
        if item.project is not None and len(item.project)>0:
            if hasattr(item, 'region') and hasattr(item, 'region_id'):
                region_slugs = [region for region in project_regions[project] if region.name == item.region]
                if len(region_slugs) == 1:
                    log_key_milestone(f"Found region {region_slugs[0].slug} for {item.name}")
                    item.region_id = region_slugs[0].id
                else:
                    error_list.append(Error(error_msg=f"Недопустимое имя региона {item.region} для {item.name}"))
                    log_key_milestone(f"Invalid region name {item.region} for resource {item.name}", level="error")
                    

            if hasattr(item, 'image') and hasattr(item, 'image_id'):
                image_slugs = [image for image in project_images[project] if image.slug == item.image]
                if len(image_slugs) == 1:
                    log_key_milestone(f"Found image {image_slugs[0].slug} for {item.name}")
                    item.image_id = image_slugs[0].id
                else:
                    error_list.append(Error(error_msg=f"Недопустимое имя image {item.image} для {item.name}"))
                    log_key_milestone(f"Invalid image name {item.image} for resource {item.name}", level="error")


            if hasattr(item, 'flavor') and hasattr(item, 'flavor_id'):
                flavor_slugs = [flavor for flavor in project_flavors[project] if flavor.slug == item.flavor]
                if len(flavor_slugs) == 1:
                    log_key_milestone(f"Found flavor {flavor_slugs[0].slug} for {item.name}")
                    item.flavor_id = flavor_slugs[0].id
                else:
                    error_list.append(Error(error_msg=f"Недопустимое имя flavor {item.flavor} для {item.name}"))
                    log_key_milestone(f"Invalid flavor name {item.flavor} for resource {item.name}", level="error")
        # else:
        #     error_list.append(Error(error_msg=f"Нет проекта для элемента развретывния {item.name}"))

    if len(error_list)>0:
        log_function_exit("generate_terraform_content")
        return None

    content = main_template.render(token = token, resources = res, project = main_project)
    log_function_exit("generate_terraform_content")
    return content

class TerrafromRequest(BaseModel):
    token : str
    environment : str

# document 254
# token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwcm9qZWN0X2lkIjoiZTE2NzM4MzgtODRlYy00Y2Q0LWE1ZjgtNWQ0MjBhYjYwNDU5IiwidG9rZW5faWQiOiIwOThlZDczMS04YWY1LTRkZDUtOGFhNy04YjJmZTgyZDA4NWUiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiIiLCJpc3MiOiJ2ZWdhIiwic3ViIjoiZTE2NzM4MzgtODRlYy00Y2Q0LWE1ZjgtNWQ0MjBhYjYwNDU5IiwiZXhwIjoyNTMzNzA3NjQ4MDAsIm5iZiI6MTc0MTg2OTIzNSwiaWF0IjoxNzQxODY5MjM1fQ.Ve_JFHQSa2W-z3Z0CWE6nAUzDl2SbSo9UI3lFjaTRGk

@router.get(
    "/api/v1/workspace/{docId}/terraform",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "Terraform конфигурация сгенерирована",
            "content": {
                "text/plain": {
                    "example": "# Generated Terraform configuration\nresource \"vega_vps_instance\" \"gateway\" {\n  name = \"gateway\"\n  flavor = \"cpu2ram2\"\n  image = \"ubuntu-22-04\"\n  region = \"region1\"\n  project = \"project_name\"\n  instances = 1\n}"
                }
            }
        },
        400: {
            "description": "Ошибка валидации или генерации",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "В workspace нет model"}
                }
            }
        },
        404: {
            "description": "Документ не найден",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Document not found"}
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
def get_terraform(docId: int, request: Annotated[TerrafromRequest,Query()]):

    URL_VEGA = os.getenv("URL_VEGA","https://vega.vimpelcom.ru")

    try:
        data = get_document(document_id=docId)
    except HTTPException as e:
        log_error_with_details(e, "document_retrieval", {"docId": docId, "status_code": e.status_code, "detail": e.detail})
        raise e
    except JSONDecodeError as e:
        log_error_with_details(e, "json_decode_error", {"docId": docId})
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as ex:
        log_error_with_details(ex, "document_retrieval", {"docId": docId})
        raise HTTPException(status_code=503, detail=f"Error calling document service {ex}")
        
    client = VegaVPSClient(base_url=URL_VEGA,
                           api_key=request.token)
    
    error_list     = list()
    result_content = generate_terraform_content(client = client,
                                                environment = request.environment,
                                                token = request.token,
                                                workspace = data,
                                                error_list = error_list)

    if len(error_list) == 0:
        log_function_exit("get_terraform")
        return result_content
    else:
        # Преобразуем список моделей в список словарей
        errors_dict = [error.model_dump() for error in error_list]

        # Конвертируем в JSON-строку
        json_string = json.dumps(errors_dict, ensure_ascii=False, indent=4)
        log_error_with_details(Exception("Terraform generation failed"), "terraform_generation", {"docId": docId, "error_count": len(error_list), "errors": errors_dict})
        raise HTTPException(status_code=400, detail=json_string)
    

@router.post(
    "/api/v1/workspace/terraform/generate",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "Terraform конфигурация сгенерирована",
            "content": {
                "text/plain": {
                    "example": "# Generated Terraform configuration\nresource \"vega_vps_instance\" \"gateway\" {\n  name = \"gateway\"\n  flavor = \"cpu2ram2\"\n  image = \"ubuntu-22-04\"\n  region = \"region1\"\n  project = \"project_name\"\n  instances = 1\n}"
                }
            }
        },
        400: {
            "description": "Ошибка парсинга JSON или валидации",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid JSON format"}
                }
            }
        },
        503: {
            "description": "Ошибка генерации",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Error parsing json"}
                }
            }
        }
    }
)
@log_endpoint_call
async def get_terraform_by_json(environment : str = Query(..., description="Deployment Environment"), 
                          token : str = Header(..., alias="X-Token"),# Query(..., description="Vega token"), 
                          text_content: str = Body(..., media_type="text/plain")):
    URL_VEGA = os.getenv("URL_VEGA","https://vega.vimpelcom.ru")
    log_key_milestone("Starting get_terraform_by_json")
    try:
        log_key_milestone("Loading document from JSON content")
        data = json.loads(text_content)
    except HTTPException as e:
        log_error_with_details(e, "json_parsing", {"status_code": e.status_code, "detail": e.detail})
        raise e
    except JSONDecodeError as e:
        log_error_with_details(e, "json_decode_error", {})
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as ex:
        log_error_with_details(ex, "json_parsing", {})
        raise HTTPException(status_code=503, detail=f"Error parsing json {ex}")
    
    client = VegaVPSClient(base_url=URL_VEGA,
                           api_key=token)
    
    log_key_milestone("Generating Terraform content")
    error_list     = list()
    result_content = generate_terraform_content(client = client,
                                                environment = environment,
                                                token = token,
                                                workspace = data,
                                                error_list = error_list)

    if len(error_list) == 0:
        log_function_exit("get_terraform_by_json")
        return result_content
    else:
        # Преобразуем список моделей в список словарей
        errors_dict = [error.model_dump() for error in error_list]

        # Конвертируем в JSON-строку
        json_string = json.dumps(errors_dict, ensure_ascii=False, indent=4)
        log_error_with_details(Exception("Terraform generation failed"), "terraform_generation", {"error_count": len(error_list), "errors": errors_dict})
        raise HTTPException(status_code=400, detail=json_string)

