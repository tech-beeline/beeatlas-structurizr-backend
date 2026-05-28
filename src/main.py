# Copyright (c) 2024 PJSC VimpelCom
import logging
import os
import sys
import time
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Добавляем корень репозитория в sys.path, чтобы был виден пакет
# src_fitness_functions, который лежит рядом с пакетом src/.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, REGISTRY, generate_latest
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from routers import fitness_functions, integraion, terraform, workspace
from src_fitness_functions.api import health as ff_health_router
from src_fitness_functions.api import (
    ff_adr_01 as ff_adr_01_router,
    ff_api_01 as ff_api_01_router,
    ff_api_02 as ff_api_02_router,
    ff_api_03 as ff_api_03_router,
    ff_cnt_01 as ff_cnt_01_router,
    ff_cnt_02 as ff_cnt_02_router,
    ff_cnt_03 as ff_cnt_03_router,
    ff_cpb_01 as ff_cpb_01_router,
    ff_cpb_02 as ff_cpb_02_router,
    ff_cpb_03 as ff_cpb_03_router,
    ff_cpb_04 as ff_cpb_04_router,
    ff_cpb_05 as ff_cpb_05_router,
    ff_ctx_01 as ff_ctx_01_router,
    ff_ctx_02 as ff_ctx_02_router,
    ff_ctx_03 as ff_ctx_03_router,
    ff_dep_01 as ff_dep_01_router,
    ff_dep_02 as ff_dep_02_router,
    ff_dep_03 as ff_dep_03_router,
    ff_dep_04 as ff_dep_04_router,
    ff_ea_0001 as ff_ea_0001_router,
    ff_git_01 as ff_git_01_router,
    ff_sq_01 as ff_sq_01_router,
    ff_sq_02 as ff_sq_02_router,
    ff_tech_01 as ff_tech_01_router,
    ff_tech_02 as ff_tech_02_router,
    ff_tech_03 as ff_tech_03_router,
    ff_tech_04 as ff_tech_04_router,
    ff_tech_05 as ff_tech_05_router,
    ff_tech_06 as ff_tech_06_router,
)

# Отключение вывода предупреждений из requests
warnings.simplefilter('ignore', InsecureRequestWarning)

# Метрики Prometheus для мониторинга HTTP запросов
REQUEST_COUNT: Counter = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "path", "status_code"]
)

REQUEST_LATENCY: Histogram = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency distribution",
    ["method", "path"]
) 


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    
    Args:
        app: Экземпляр FastAPI приложения
        
    Yields:
        None: Приложение готово к работе
    """
    # Инициализация при необходимости
    yield

# Создание экземпляра FastAPI приложения
app: FastAPI = FastAPI(
    title="Structurizr Backend API",
    description="API для управления шагами архитектурного конвейера",
    lifespan=lifespan
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next) -> Response:
    """
    Middleware для сбора метрик Prometheus.
    
    Args:
        request: Входящий HTTP запрос
        call_next: Следующий обработчик в цепочке
        
    Returns:
        Response: HTTP ответ
    """
    start_time: float = time.time()
    method: str = request.method
    path: str = request.url.path
    
    # Пропускаем логирование для /actuator/prometheus
    if path == "/actuator/prometheus":
        return await call_next(request)
    
    status_code: int = 500
    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        raise e
    finally:
        latency: float = time.time() - start_time
        # Обновляем метрики Prometheus
        REQUEST_COUNT.labels(method, path, str(status_code)).inc()
        REQUEST_LATENCY.labels(method, path).observe(latency)
    
    return response

@app.get("/actuator/prometheus")
async def metrics_endpoint() -> Response:
    """
    Endpoint для получения метрик Prometheus.
    
    Returns:
        Response: Метрики в формате Prometheus
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

# Подключение роутеров для различных модулей API
app.include_router(workspace.router)
app.include_router(fitness_functions.router)
app.include_router(terraform.router)
app.include_router(integraion.router)

# Роутеры из пакета src_fitness_functions
app.include_router(ff_health_router.router)  # GET /health — liveness FF API
app.include_router(ff_adr_01_router.router)  # ADR.01 — наличие хотя бы одного ADR
app.include_router(ff_api_01_router.router)  # API.01 — у приложения есть опубликованные API
app.include_router(ff_api_02_router.router)  # API.02 — для некоторых методов определён SLA
app.include_router(ff_api_03_router.router)  # API.03 — для всех TC есть спецификация
app.include_router(ff_cnt_01_router.router)  # CNT.01 — в модели есть контейнеры системы
app.include_router(ff_cnt_02_router.router)  # CNT.02 — есть хотя бы одна диаграмма контейнеров
app.include_router(ff_cnt_03_router.router)  # CNT.03 — все вызовы между контейнерами с технологией
app.include_router(ff_cpb_01_router.router)  # CPB.01 — определены технические возможности продукта
app.include_router(ff_cpb_02_router.router)  # CPB.02 — для внешних интеграций определены TC
app.include_router(ff_cpb_03_router.router)  # CPB.03 — есть capability в Structurizr
app.include_router(ff_cpb_04_router.router)  # CPB.04 — позиционирование TC
app.include_router(ff_cpb_05_router.router)  # CPB.05 — качество описания TC
app.include_router(ff_ctx_01_router.router)  # CTX.01 — создана диаграмма контекста
app.include_router(ff_ctx_02_router.router)  # CTX.02 — связи на контексте подписаны
app.include_router(ff_ctx_03_router.router)  # CTX.03 — связи на контексте с технологией взаимодействия
app.include_router(ff_dep_01_router.router)  # DEP.01 — есть хотя бы один Deployment Environment
app.include_router(ff_dep_02_router.router)  # DEP.02 — есть хотя бы одна deployment-диаграмма
app.include_router(ff_dep_03_router.router)  # DEP.03 — DeploymentEnvironment ссылается на CMDB
app.include_router(ff_dep_04_router.router)  # DEP.04 — макросегментация Protected/DMZ и зоны
app.include_router(ff_ea_0001_router.router)  # EA.0001 — внешние сервисы в архитектуре (EA)
app.include_router(ff_git_01_router.router)  # GIT.01 — в модели указан git-репозиторий
app.include_router(ff_sq_01_router.router)  # SQ.01 — для TC указаны sequence-диаграммы
app.include_router(ff_sq_02_router.router)  # SQ.02 — вызовы содержат HTTP-запросы
app.include_router(ff_tech_01_router.router)  # TECH.01 — технологии продукта в техрадаре
app.include_router(ff_tech_02_router.router)  # TECH.02 — нет технологий в статусе HOLD
app.include_router(ff_tech_03_router.router)  # TECH.03 — у всех контейнеров заданы технологии
app.include_router(ff_tech_04_router.router)  # TECH.04 — нет протоколов в статусе hold
app.include_router(ff_tech_05_router.router)  # TECH.05 — протоколы взаимодействий из техрадара
app.include_router(ff_tech_06_router.router)  # TECH.06 — технологии из мониторинга/Git в архитектуре



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Обработчик исключений валидации запросов.
    
    Args:
        request: Входящий HTTP запрос
        exc: Исключение валидации
        
    Returns:
        JSONResponse: Ответ с ошибкой валидации
    """
    print(exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Some of parameters is empty or missing"},
    )

def custom_openapi() -> dict:
    """
    Генерация кастомной OpenAPI схемы для документации API.
    
    Returns:
        dict: OpenAPI схема в формате JSON
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema: dict = get_openapi(
        title="Structurizr Backend API",
        version="1.0.0",
        description="API для управления шагами архитектурного конвейера",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Настройка логгера для роутеров
    router_logger: logging.Logger = logging.getLogger("router")
    router_logger.setLevel(logging.INFO)
    
    # Создаем фильтр для исключения /actuator/prometheus из логов
    class ExcludePrometheusFilter(logging.Filter):
        """Фильтр для исключения запросов к /actuator/prometheus из логов."""
        
        def filter(self, record: logging.LogRecord) -> bool:
            """
            Фильтрует записи логов, исключая запросы к метрикам.
            
            Args:
                record: Запись лога
                
            Returns:
                bool: True если запись должна быть записана, False иначе
            """
            return "/actuator/prometheus" not in record.getMessage()
    
    # Применяем фильтр к логгеру доступа Uvicorn
    logging.getLogger("uvicorn.access").addFilter(ExcludePrometheusFilter())
    
    # Запуск сервера
    uvicorn.run(app, host="0.0.0.0", port=8080)