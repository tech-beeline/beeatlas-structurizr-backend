"""
Модуль аутентификации для FDM Gateway SDK
"""

import hashlib
import hmac
import base64
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class AuthBase(ABC):
    """Базовый класс для аутентификации"""
    
    @abstractmethod
    def get_headers(self, method: str, path: str, body: str = "", content_type: str = "application/json") -> Dict[str, str]:
        """Получить заголовки для аутентификации"""
        pass


class JWTAuth(AuthBase):
    """JWT Bearer Token аутентификация"""
    
    def __init__(self, token: str):
        """
        Инициализация JWT аутентификации
        
        Args:
            token: JWT токен
        """
        self.token = token
    
    def get_headers(self, method: str, path: str, body: str = "", content_type: str = "application/json") -> Dict[str, str]:
        """Получить заголовки для JWT аутентификации"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type
        }


class HMACAuth(AuthBase):
    """HMAC-SHA256 аутентификация для сервисных вызовов"""
    
    def __init__(self, api_key: str, api_secret: str, service_auth: bool = False):
        """
        Инициализация HMAC аутентификации
        
        Args:
            api_key: API ключ
            api_secret: API секрет
            service_auth: True для сервисной аутентификации, False для продуктовой
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.service_auth = service_auth
    
    def _md5(self, data: str) -> str:
        """Вычислить MD5 хеш"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def _build_message(self, method: str, path: str, body: str, content_type: str, nonce: str) -> str:
        """
        Построить сообщение для HMAC подписи
        body приводится к массиву байтов и переводится в MD5 строку 
        
        Формула: method + "\n" + path + "\n" + md5(body) + "\n" + content-type + "\n" + nonce + "\n"
        """
        md5_body = self._md5(body)
        return f"{method}\n{path}\n{md5_body}\n{content_type}\n{nonce}\n"
    
    def _hmac_sha256(self, message: str, secret: str) -> str:
        """Вычислить HMAC-SHA256 подпись"""
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def get_headers(self, method: str, path: str, body: str = "", content_type: str = "application/json") -> Dict[str, str]:
        """Получить заголовки для HMAC аутентификации"""
        # Генерируем уникальный nonce для предотвращения replay атак
        nonce = "Q5FHK3Sj1FinGDQ7zouJC5X9Ypp9oj2ePK-J4YQ56Z4" #secrets.token_urlsafe(32)
        
        # Строим сообщение для подписи
        message = self._build_message(method, path, body, content_type, nonce)
        # Вычисляем HMAC-SHA256 подпись
        signature = self._hmac_sha256(message, self.api_secret)

        # Формируем X-Authorization заголовок
        x_auth = f"{self.api_key}:{signature}"
        
        return {
            "X-Authorization": x_auth,
            "Nonce": nonce,
            "Content-Type": content_type
        }


class NoAuth(AuthBase):
    """Отсутствие аутентификации (для публичных эндпоинтов)"""
    
    def get_headers(self, method: str, path: str, body: str = "", content_type: str = "application/json") -> Dict[str, str]:
        """Получить заголовки без аутентификации"""
        return {
            "Content-Type": content_type
        }
