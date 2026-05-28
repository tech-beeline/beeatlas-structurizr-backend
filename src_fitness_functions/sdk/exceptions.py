"""
Исключения для FDM Gateway SDK
"""

from typing import Optional, Dict, Any


class GatewayException(Exception):
    """Базовое исключение для FDM Gateway SDK"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(GatewayException):
    """Ошибка аутентификации (401)"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class AuthorizationError(GatewayException):
    """Ошибка авторизации (403)"""
    
    def __init__(self, message: str = "Access forbidden", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(GatewayException):
    """Ресурс не найден (404)"""
    
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class ValidationError(GatewayException):
    """Ошибка валидации (400)"""
    
    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(message, status_code=400, **kwargs)


class ServerError(GatewayException):
    """Ошибка сервера (500)"""
    
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class TimeoutError(GatewayException):
    """Ошибка таймаута"""
    
    def __init__(self, message: str = "Request timeout", **kwargs):
        super().__init__(message, **kwargs)


class NetworkError(GatewayException):
    """Ошибка сети"""
    
    def __init__(self, message: str = "Network error", **kwargs):
        super().__init__(message, **kwargs)


class APIError(GatewayException):
    """Общая ошибка API"""
    
    def __init__(self, message: str = "API error", **kwargs):
        super().__init__(message, **kwargs)


class HMACValidationError(GatewayException):
    """Ошибка валидации HMAC подписи"""
    
    def __init__(self, message: str = "HMAC validation failed", **kwargs):
        super().__init__(message, **kwargs)
