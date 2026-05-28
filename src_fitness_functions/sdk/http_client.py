"""
HTTP клиент для FDM Gateway SDK
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src_fitness_functions.sdk.auth import AuthBase
from src_fitness_functions.sdk.exceptions import (
    GatewayException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ServerError,
    TimeoutError,
    NetworkError,
)


class HTTPClient:
    """HTTP клиент для работы с FDM Gateway"""
    
    def __init__(
        self, 
        base_url: str, 
        auth: Optional[AuthBase] = None,
        timeout: int = 30,
        retries: int = 3,
        logging_enabled: bool = False,
        verify_ssl: bool = False
    ):
        """
        Инициализация HTTP клиента
        
        Args:
            base_url: Базовый URL Gateway
            auth: Объект аутентификации
            timeout: Таймаут запросов в секундах
            retries: Количество повторных попыток
            logging_enabled: Включить логирование запросов
            verify_ssl: Проверять SSL сертификаты (по умолчанию False для тестового окружения)
        """
        self.base_url = base_url.rstrip('/')
        self.auth = auth
        self.timeout = timeout
        self.logging_enabled = logging_enabled
        self.verify_ssl = verify_ssl
        
        # Настройка сессии
        self.session = requests.Session()
        
        # Настройка проверки SSL сертификатов
        self.session.verify = verify_ssl
        
        # Отключение предупреждений о небезопасных запросах (только если SSL отключен)
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Настройка retry стратегии
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Настройка логирования

        self.logger = logging.getLogger()
        # self.logger.addHandler(logging.StreamHandler())
        # self.logger.setLevel(logging.DEBUG)

    
    def _log_request(self, method: str, url: str, headers: Dict[str, str], data: Optional[str] = None):
        """Логирование запроса"""
        if self.logger and self.logging_enabled:
            self.logger.info(f"🚀 {method} {url}")
            self.logger.debug(f"📤 Request headers: {dict(headers)}")
            if data:
                self.logger.debug(f"📤 Request body: {data[:500]}{'...' if len(data) > 500 else ''}")
            else:
                self.logger.debug("📤 Request body: (empty)")
    
    def _log_response(self, response: requests.Response):
        """Логирование ответа"""
        if self.logger and self.logging_enabled:
            # Определяем эмодзи для статуса
            status_emoji = "✅" if response.ok else "❌"
            if response.status_code == 404 and response.text.strip() == "Not implemented":
                status_emoji = "⚠️"
            
            self.logger.info(f"{status_emoji} Response: {response.status_code} {response.reason}")
            self.logger.debug(f"📥 Response headers: {dict(response.headers)}")
            
            if response.text:
                # Обрезаем длинные ответы
                response_text = response.text[:1000]
                if len(response.text) > 1000:
                    response_text += "..."
                self.logger.debug(f"📥 Response body: {response_text}")
            else:
                self.logger.debug("📥 Response body: (empty)")
    
    def _handle_response(self, response: requests.Response) -> Union[Dict[str, Any], str]:
        """Обработка ответа сервера"""
        self._log_response(response)
        
        # Проверка статуса ответа
        if response.status_code == 401:
            # Проверяем, не является ли это валидационным ответом
            try:
                response_data = response.json()
                if 'detail' in response_data and 'valid' in response_data['detail']:
                    # Это валидационный ответ, а не ошибка аутентификации
                    if self.logger:
                        self.logger.info("📝 Validation Response: Получен валидационный ответ")
                    return response_data
            except (ValueError, KeyError):
                pass
            
            if self.logger:
                self.logger.warning("🔐 Authentication Error: Неверные учетные данные")
            raise AuthenticationError("Authentication failed")
        elif response.status_code == 403:
            if self.logger:
                self.logger.warning("🚫 Authorization Error: Доступ запрещен")
            try:
                error_data = response.json()
                message = error_data.get('message', 'Authorization error')
                if self.logger:
                        self.logger.info(f"📝 Authorization Response: {error_data}")
            except (ValueError, KeyError):
                pass
            raise AuthorizationError("Access forbidden")
        elif response.status_code == 404:
            # Проверяем, не является ли это ответом "Not implemented" от тестового Gateway
            if self.logger:
                self.logger.warning("🔍 Not Found: Ресурс не найден")
            raise NotFoundError("Resource not found")
        elif response.status_code == 400:
            if self.logger:
                self.logger.warning("📝 Validation Error: Ошибка валидации данных")
            try:
                error_data = response.json()
                message = error_data.get('message', 'Validation error')
                if self.logger:
                        self.logger.info(f"📝 Validation Response: {error_data}")
            except (ValueError, KeyError):
                message = 'Validation error'
            raise ValidationError(message)
        elif response.status_code >= 500:
            if self.logger:
                self.logger.error("🔥 Server Error: Внутренняя ошибка сервера")
            raise ServerError("Internal server error")
        elif not response.ok:
            if self.logger:
                self.logger.error(f"❌ HTTP Error: {response.status_code} - {response.text[:100]}")
            raise GatewayException(f"HTTP {response.status_code}: {response.text}")
        
        # Парсинг ответа
        content_type = response.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            try:
                result = response.json()
                if self.logger and self.logging_enabled:
                    self.logger.info("📋 JSON Response: Успешно распарсен JSON ответ")
                return result
            except ValueError:
                if self.logger:
                    self.logger.warning("⚠️  JSON Parse Error: Не удалось распарсить JSON, возвращаем текст")
                return response.text
        else:
            if self.logger:
                self.logger.info("📄 Text Response: Получен текстовый ответ")
            return response.text
    
    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Выполнить HTTP запрос
        
        Args:
            method: HTTP метод
            path: Путь к ресурсу
            params: Параметры запроса
            data: Тело запроса
            headers: Дополнительные заголовки
            
        Returns:
            Ответ сервера
        """
        # Построение URL
        url = urljoin(self.base_url, path.lstrip('/'))
        
        # Подготовка данных
        json_data = None
        body = ""
        content_type = "application/json"
        
        if data is not None:
            if isinstance(data, dict):
                json_data = data
                body = json.dumps(data, ensure_ascii=False)
            else:
                body = str(data)
                content_type = "text/plain"
        
        # Получение заголовков аутентификации
        auth_headers = {}
        if self.auth:
            if path.find('?') >= 0 :
                path = path[0:path.find('?')]
            auth_headers = self.auth.get_headers(method, path, body, content_type)
        
        # Объединение заголовков
        request_headers = {**auth_headers, **(headers or {})}
        
        # Логирование запроса
        self._log_request(method, url, request_headers, body)
        
        try:
            if self.logger and self.logging_enabled:
                self.logger.info(f"⏳ Выполнение запроса...")

            # Выполнение запроса
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=body, # if not json_data else None,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # Логирование завершения запроса
            if self.logger and self.logging_enabled:
                self.logger.info(f"⏱️  Запрос выполнен за {response.elapsed.total_seconds():.2f}s")
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            if self.logger and self.logging_enabled:
                self.logger.error("⏰ Timeout: Запрос превысил время ожидания")
            raise TimeoutError("Request timeout")
        except requests.exceptions.ConnectionError:
            if self.logger and self.logging_enabled:
                self.logger.error("🌐 Connection Error: Ошибка подключения к серверу")
            raise NetworkError("Network connection error")
        except requests.exceptions.RequestException as e:
            if self.logger and self.logging_enabled:
                self.logger.error(f"💥 Request Exception: {str(e)}")
            raise GatewayException(f"Request failed: {str(e)}")
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Union[Dict[str, Any], str]:
        """GET запрос"""
        return self.request("GET", path, params=params, **kwargs)
    
    def post(self, path: str, data: Optional[Union[Dict[str, Any], str]] = None, **kwargs) -> Union[Dict[str, Any], str]:
        """POST запрос"""
        return self.request("POST", path, data=data, **kwargs)
    
    def put(self, path: str, data: Optional[Union[Dict[str, Any], str]] = None, **kwargs) -> Union[Dict[str, Any], str]:
        """PUT запрос"""
        return self.request("PUT", path, data=data, **kwargs)
    
    def patch(self, path: str, data: Optional[Union[Dict[str, Any], str]] = None, **kwargs) -> Union[Dict[str, Any], str]:
        """PATCH запрос"""
        return self.request("PATCH", path, data=data, **kwargs)
    
    def delete(self, path: str, **kwargs) -> Union[Dict[str, Any], str]:
        """DELETE запрос"""
        return self.request("DELETE", path, **kwargs)
    
    def close(self):
        """Закрыть сессию"""
        self.session.close()
