# Copyright (c) 2024 PJSC VimpelCom
import logging
import time
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, REGISTRY, generate_latest
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from routers import fitness_functions, integraion, terraform, workspace

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