# Copyright (c) 2024 PJSC VimpelCom
import os
import logging
import tempfile
import random
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Annotated, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request, Header
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
# from langchain_openai import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.schema import HumanMessage, SystemMessage

from structurizr_utils.functions.api import ApiLoader
from . import log_endpoint_call, log_key_milestone, log_error_with_details, log_function_entry, log_function_exit

router = APIRouter()

# Загружаем API-ключ из .env
load_dotenv()

# Модели для ошибок
class ErrorDetail(BaseModel):
    detail: str

# def get_sla_from_openai(spec: str) -> str:
#     llm = ChatOpenAI(
#         model="RuadaptQwen", 
#         temperature=0,
#         api_key=os.getenv("OPENAI_API_KEY"),
#         base_url="http://ta-dev.apps.yd-kt05.vimpelcom.ru/api/v1"
#     )
#     template = """
#             Как разработчик REST API сформируй метрики для REST end-point.
#             В качестве отображения результата используй следующий формат, как пример: 
#             "put /pet" rps=100;latency=10;error_rate=0.5
#             "get /pet/findByStatus" rps=10;latency=15;error_rate=0.3
#             "post /pet/{{petId}}" rps=2;latency=200;error_rate=0.1
            
#             Возвращай только список в указанном формате. Не делай пустых строк между строчками.
#             Перечень end-point возьми из OpenAPI спецификации:
#             {query}
#             """
#     prompt_template = PromptTemplate(
#             input_variables=["query"],  # Переменные, которые подставляются в шаблон
#             template=template,
#         )
    
#     formatted_prompt = prompt_template.format(query=spec)
#     response = llm.invoke([HumanMessage(content=formatted_prompt)])
#     return response.content

def create_temp_file(extension: str = None, prefix: str = None) -> str:
    """
    Создает временный файл и возвращает его путь.
    Файл будет автоматически удален при закрытии программы (если не сохранить его).
    """
    log_function_entry("create_temp_file", extension=extension, prefix=prefix)
    
    try:
        suffix = extension if extension else ""
        if prefix:
            filename = tempfile.mkstemp(suffix=suffix, prefix=prefix)[1]
        else:
            filename = tempfile.mkstemp(suffix=suffix)[1]
        
        log_key_milestone(f"Temporary file created: {filename}")
        log_function_exit("create_temp_file", result=filename)
        return filename
    except Exception as e:
        log_error_with_details(e, "create_temp_file", {"extension": extension, "prefix": prefix})
        log_function_exit("create_temp_file", result=None)
        raise

def get_sla_from_parser(spec: str) -> str:
    log_function_entry("get_sla_from_parser")
    
    try:
        log_key_milestone("Creating temporary file for API specification")
        temp_file = create_temp_file(extension=".txt", prefix="log_")
        
        with open(temp_file,"w") as f:
            f.write(spec)
            f.close()

        log_key_milestone("Loading API methods using ApiLoader")
        loader = ApiLoader()
        methods = loader.get_api_methods_rest(temp_file)

        if len(methods) == 0:
            log_key_milestone("No REST methods found, trying WSDL")
            methods = loader.get_api_methods_wsdl(temp_file)

        if len(methods) == 0:
            log_key_milestone("No WSDL methods found, trying Protocol Buffers")
            methods = loader.get_api_methods_proto(temp_file)

        log_key_milestone(f"Found {len(methods)} API methods")
        
        result_list = [f"\"{m.name}\" rps={random.randint(1,30)};latency={random.randint(50,1000)};error_rate={random.uniform(0, 3):.2f}\n" for m in methods]

        if os.path.exists(temp_file):
            os.remove(temp_file)
            log_key_milestone("Temporary file removed")

        result = ""
        for r in result_list:
            result += r

        log_key_milestone("SLA calculation completed successfully")
        log_function_exit("get_sla_from_parser", result=f"Generated SLA for {len(methods)} methods")
        return result
        
    except Exception as e:
        log_error_with_details(e, "get_sla_from_parser", {"spec_length": len(spec) if spec else 0})
        log_function_exit("get_sla_from_parser", result=None)
        raise

@router.post(
    "/api/v1/integration/sla",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "SLA метрики рассчитаны",
            "content": {
                "text/plain": {
                    "example": "\"GET /api/users\" rps=25;latency=150;error_rate=0.1\n\"POST /api/users\" rps=5;latency=300;error_rate=0.2"
                }
            }
        },
        400: {
            "description": "Ошибка парсинга спецификации",
            "model": ErrorDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Error parsing API specification"}
                }
            }
        }
    }
)
@log_endpoint_call
async def calculate_sla(text_content: str = Body(..., media_type="text/plain")):
    log_key_milestone("Starting SLA calculation for API methods")

    try:
        #response = get_sla_from_openai(text_content)
        response = get_sla_from_parser(text_content)

        log_key_milestone("SLA calculation completed successfully")
        return response
        
    except Exception as e:
        log_error_with_details(e, "calculate_sla", {"content_length": len(text_content) if text_content else 0})
        raise


