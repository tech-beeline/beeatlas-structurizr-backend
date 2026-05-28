# Copyright (c) 2024 PJSC VimpelCom
import logging
import functools
import traceback
from typing import Any, Callable, Dict
from fastapi import Request, HTTPException
import time

# Настройка логгера для роутеров
router_logger = logging.getLogger("router")

def log_endpoint_call(func: Callable) -> Callable:
    """
    Декоратор для логирования вызова эндпоинта
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint_name = f"{func.__module__}.{func.__name__}"
        
        # Логируем начало вызова
        router_logger.info(f"🚀 Endpoint called: {endpoint_name}")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            router_logger.info(f"✅ Endpoint completed: {endpoint_name} (execution time: {execution_time:.3f}s)")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            router_logger.error(f"❌ Endpoint failed: {endpoint_name} (execution time: {execution_time:.3f}s)")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint_name = f"{func.__module__}.{func.__name__}"
        
        # Логируем начало вызова
        router_logger.info(f"🚀 Endpoint called: {endpoint_name}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            router_logger.info(f"✅ Endpoint completed: {endpoint_name} (execution time: {execution_time:.3f}s)")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            router_logger.error(f"❌ Endpoint failed: {endpoint_name} (execution time: {execution_time:.3f}s)")
            raise
    
    # Возвращаем асинхронную или синхронную обертку в зависимости от типа функции
    if func.__code__.co_flags & 0x80:  # CO_COROUTINE flag
        return async_wrapper
    else:
        return sync_wrapper

def log_key_milestone(message: str, level: str = "info") -> None:
    """
    Логирование ключевых отметок в функциях
    """
    milestone_msg = f"📍 MILESTONE: {message}"
    if level.lower() == "debug":
        router_logger.debug(milestone_msg)
    elif level.lower() == "warning":
        router_logger.warning(milestone_msg)
    elif level.lower() == "error":
        router_logger.error(milestone_msg)
    else:
        router_logger.info(milestone_msg)

def log_error_with_details(error: Exception, context: str = "", additional_info: Dict[str, Any] = None) -> None:
    """
    Расширенное логирование ошибок с контекстом
    """
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "traceback": traceback.format_exc(),
        "additional_info": additional_info or {}
    }
    
    router_logger.error(f"💥 ERROR DETAILS: {error_details}")

def log_function_entry(func_name: str, **kwargs) -> None:
    """
    Логирование входа в функцию с параметрами
    """
    params_str = ", ".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
    router_logger.debug(f"🔍 Entering function: {func_name}({params_str})")

def log_function_exit(func_name: str, result: Any = None) -> None:
    """
    Логирование выхода из функции с результатом
    """
    if result is not None:
        router_logger.debug(f"🔍 Exiting function: {func_name} -> {result}")
    else:
        router_logger.debug(f"🔍 Exiting function: {func_name}")

def log_http_request(request: Request, method: str, path: str) -> None:
    """
    Логирование HTTP запроса
    """
    router_logger.info(f"🌐 HTTP Request: {method} {path}")

def log_http_response(status_code: int, path: str) -> None:
    """
    Логирование HTTP ответа
    """
    if 200 <= status_code < 300:
        router_logger.info(f"✅ HTTP Response: {status_code} {path}")
    elif 400 <= status_code < 500:
        router_logger.warning(f"⚠️ HTTP Response: {status_code} {path}")
    else:
        router_logger.error(f"❌ HTTP Response: {status_code} {path}")
