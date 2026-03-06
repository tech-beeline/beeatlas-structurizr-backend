import requests
import hashlib
import hmac
import logging
from base64 import b64encode
from datetime import datetime, timedelta
from typing import Dict, Optional
# ----------------------------
# Structurizr Helper Functions
# ----------------------------

def _number_once() -> str:
    """Return the number of milliseconds since the epoch."""
    return str(
            int((datetime.utcnow() - datetime(1970, 1, 1)) / timedelta(milliseconds=1))
        )


def _hmac_hex(secret: str, digest: str) -> str:
    """Hash the given digest using HMAC+SHA256 and return the hex string."""
    return hmac.new(
        secret.encode("utf-8"), digest.encode("utf-8"), "sha256"
    ).hexdigest()


def _md5(content: str) -> str:
    """Return the MD5 hash of the given string."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def _base64_str(content: str) -> str:
    """Return the base64 encoded string."""
    return b64encode(content.encode("utf-8")).decode("utf-8")

def _message_digest(
    http_verb: str,
    uri_path: str,
    definition_md5: str,
    content_type: str,
    nonce: str,
    ) -> str:
    """Assemble the complete message digest."""
    return f"{http_verb}\n{uri_path}\n{definition_md5}\n{content_type}\n{nonce}\n"

# -------------------
# Classes
# -------------------
class Workspace:
    """Класс для представления workspace в Structurizr.
    
    Attributes:
        id: Уникальный идентификатор workspace
        name: Название workspace
        description: Описание workspace
        apiKey: API ключ для аутентификации
        apiSecret: API секрет для аутентификации
        privateUrl: Приватный URL для API
        publicUrl: Публичный URL для просмотра
    """
    
    def __init__(self, id: int, name: str, description: str, apiKey: str, 
                 apiSecret: str, privateUrl: str, publicUrl: str) -> None:
        """Инициализация объекта Workspace.
        
        Args:
            id: Уникальный идентификатор workspace
            name: Название workspace
            description: Описание workspace
            apiKey: API ключ для аутентификации
            apiSecret: API секрет для аутентификации
            privateUrl: Приватный URL для API
            publicUrl: Публичный URL для просмотра
        """
        self.id = id
        self.name = name
        self.description = description
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        self.privateUrl = privateUrl
        self.publicUrl = publicUrl
    
    def print(self) -> None:
        """Выводит информацию о workspace в лог.
        
        Note:
            Использует logging вместо print для лучшей интеграции с системой логирования.
        """
        logging.info(f"Workspace ID: {self.id}")
        logging.info(f"Workspace Name: {self.name}")
        logging.info(f"Workspace Description: {self.description}")
        logging.info(f"API Key: {self.apiKey}")
        logging.info(f"API Secret: {self.apiSecret}")
        logging.info(f"Private URL: {self.privateUrl}")
        logging.info(f"Public URL: {self.publicUrl}")                     

def load_workspace(wrk: Workspace, url_onpremises_base: str) -> Optional[Dict]:
    apiKey=wrk.apiKey
    apiSecret=wrk.apiSecret
    apiUrl=url_onpremises_base+wrk.privateUrl
    method ='GET'
    content=''
    content_type=''
    url_path = '/api'+wrk.privateUrl 
    definition_md5 = _md5(content)
    nonce = _number_once()
    message_digest = _message_digest(
                method,
                url_path,
                definition_md5,
                content_type,
                nonce)
    
    message_hash = _base64_str(_hmac_hex(apiSecret, message_digest))

    headers = {
                "X-Authorization": f"{apiKey}:{message_hash}",
                "Nonce": nonce
            }

    try:
        resp = requests.get(url=apiUrl, headers=headers, verify=False)
        
        if resp.status_code == 200:
            #logging.info(f"Successfully loaded workspace {wrk.id}")
            return resp.json()
        else:
            logging.error(f"Failed to load workspace {wrk.id}. Status code: {resp.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error while loading workspace {wrk.id}: {e}")
        return None

