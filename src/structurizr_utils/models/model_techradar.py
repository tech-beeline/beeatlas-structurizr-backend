import logging
import os
from enum import Enum
from typing import List, Optional, Dict, Any, Union
import requests
from pydantic import BaseModel, Field
from requests import Response

# Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)


class StatusCode(str, Enum):
    ACCEPTED = "ACCEPTED"
    ALREADY_REPORTED = "ALREADY_REPORTED"
    BAD_GATEWAY = "BAD_GATEWAY"
    BAD_REQUEST = "BAD_REQUEST"
    BANDWIDTH_LIMIT_EXCEEDED = "BANDWIDTH_LIMIT_EXCEEDED"
    CHECKPOINT = "CHECKPOINT"
    CONFLICT = "CONFLICT"
    CONTINUE = "CONTINUE"
    CREATED = "CREATED"
    DESTINATION_LOCKED = "DESTINATION_LOCKED"
    EXPECTATION_FAILED = "EXPECTATION_FAILED"
    FAILED_DEPENDENCY = "FAILED_DEPENDENCY"
    FORBIDDEN = "FORBIDDEN"
    FOUND = "FOUND"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"
    GONE = "GONE"
    HTTP_VERSION_NOT_SUPPORTED = "HTTP_VERSION_NOT_SUPPORTED"
    IM_USED = "IM_USED"
    INSUFFICIENT_SPACE_ON_RESOURCE = "INSUFFICIENT_SPACE_ON_RESOURCE"
    INSUFFICIENT_STORAGE = "INSUFFICIENT_STORAGE"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    I_AM_A_TEAPOT = "I_AM_A_TEAPOT"
    LENGTH_REQUIRED = "LENGTH_REQUIRED"
    LOCKED = "LOCKED"
    LOOP_DETECTED = "LOOP_DETECTED"
    METHOD_FAILURE = "METHOD_FAILURE"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    MOVED_PERMANENTLY = "MOVED_PERMANENTLY"
    MOVED_TEMPORARILY = "MOVED_TEMPORARILY"
    MULTIPLE_CHOICES = "MULTIPLE_CHOICES"
    MULTI_STATUS = "MULTI_STATUS"
    NETWORK_AUTHENTICATION_REQUIRED = "NETWORK_AUTHENTICATION_REQUIRED"
    NON_AUTHORITATIVE_INFORMATION = "NON_AUTHORITATIVE_INFORMATION"
    NOT_ACCEPTABLE = "NOT_ACCEPTABLE"
    NOT_EXTENDED = "NOT_EXTENDED"
    NOT_FOUND = "NOT_FOUND"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_MODIFIED = "NOT_MODIFIED"
    NO_CONTENT = "NO_CONTENT"
    OK = "OK"
    PARTIAL_CONTENT = "PARTIAL_CONTENT"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    PERMANENT_REDIRECT = "PERMANENT_REDIRECT"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    PRECONDITION_REQUIRED = "PRECONDITION_REQUIRED"
    PROCESSING = "PROCESSING"
    PROXY_AUTHENTICATION_REQUIRED = "PROXY_AUTHENTICATION_REQUIRED"
    REQUESTED_RANGE_NOT_SATISFIABLE = "REQUESTED_RANGE_NOT_SATISFIABLE"
    REQUEST_ENTITY_TOO_LARGE = "REQUEST_ENTITY_TOO_LARGE"
    REQUEST_HEADER_FIELDS_TOO_LARGE = "REQUEST_HEADER_FIELDS_TOO_LARGE"
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"
    REQUEST_URI_TOO_LONG = "REQUEST_URI_TOO_LONG"
    RESET_CONTENT = "RESET_CONTENT"
    SEE_OTHER = "SEE_OTHER"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SWITCHING_PROTOCOLS = "SWITCHING_PROTOCOLS"
    TEMPORARY_REDIRECT = "TEMPORARY_REDIRECT"
    TOO_EARLY = "TOO_EARLY"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNAVAILABLE_FOR_LEGAL_REASONS = "UNAVAILABLE_FOR_LEGAL_REASONS"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    UPGRADE_REQUIRED = "UPGRADE_REQUIRED"
    URI_TOO_LONG = "URI_TOO_LONG"
    USE_PROXY = "USE_PROXY"
    VARIANT_ALSO_NEGOTIATES = "VARIANT_ALSO_NEGOTIATES"


class ResponseEntity(BaseModel):
    body: Optional[Dict[str, Any]] = None
    statusCode: Optional[StatusCode] = None
    statusCodeValue: Optional[int] = None


class Category(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class RingDTO(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    order: Optional[int] = None


class HistoryDTO(BaseModel):
    createdDate: Optional[str] = Field(None, example="yyyy-MM-dd")
    ring: Optional[RingDTO] = None
    version: Optional[int] = None


class TechCategoryAdvancedDTO(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class HistoryTechDTO(BaseModel):
    category: Optional[List[TechCategoryAdvancedDTO]] = None
    createdDate: Optional[str] = Field(None, example="yyyy-MM-dd")
    currentVersion: Optional[int] = None
    deletedDate: Optional[str] = Field(None, example="yyyy-MM-dd")
    description: Optional[str] = None
    history: Optional[List[HistoryDTO]] = None
    id: Optional[int] = None
    label: Optional[str] = None
    lastModifiedDate: Optional[str] = Field(None, example="yyyy-MM-dd")
    link: Optional[str] = None
    ring: Optional[RingDTO] = None
    sector: Optional[RingDTO] = None


class PatchCategoryDTO(BaseModel):
    name: Optional[str] = None


class TechnologyDTO(BaseModel):
    id: Optional[int] = None
    label: Optional[str] = None
    ring: Optional[RingDTO] = None
    sector: Optional[RingDTO] = None


class PatternDTO(BaseModel):
    code: Optional[str] = None
    createDate: Optional[str] = Field(None, example="yyyy-MM-dd HH:mm:ss.SSS")
    deleteDate: Optional[str] = Field(None, example="yyyy-MM-dd HH:mm:ss.SSS")
    id: Optional[int] = None
    isAntiPattern: Optional[bool] = None
    name: Optional[str] = None
    rule: Optional[str] = None
    technologies: Optional[List[TechnologyDTO]] = None
    updateDate: Optional[str] = Field(None, example="yyyy-MM-dd HH:mm:ss.SSS")


class PostCategoryDTO(BaseModel):
    name: Optional[str] = None


class PostPatternDTO(BaseModel):
    isAntiPattern: Optional[bool] = None
    name: Optional[str] = None
    relationsTech: Optional[List[int]] = None
    rule: Optional[str] = None


class PostProductTechDTO(BaseModel):
    cmdb_code: Optional[str] = None
    proj_lang: Optional[str] = None


class TechCategoryDTO(BaseModel):
    id: Optional[int] = None


class PostTechDTO(BaseModel):
    categories: Optional[List[TechCategoryDTO]] = None
    descr: Optional[str] = None
    label: Optional[str] = None
    link: Optional[str] = None
    review: Optional[bool] = None
    ring_id: Optional[int] = None
    sector_id: Optional[int] = None


class PostTechVersionDTO(BaseModel):
    statusId: Optional[int] = None
    versionEnd: Optional[str] = None
    versionStart: Optional[str] = None


class ProcessDTO(BaseModel):
    process: Optional[str] = None
    tech_name: Optional[str] = None


class ProductTechDTO(BaseModel):
    id: Optional[int] = None
    label: Optional[str] = None


class ProductDTO(BaseModel):
    alias: Optional[str] = None
    product_id: Optional[int] = None
    tech: Optional[List[ProductTechDTO]] = None


class PutTechCategoryDTO(BaseModel):
    joinCategoryName: Optional[str] = None
    joinedCategoriesId: Optional[List[int]] = None


class Ring(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    order: Optional[int] = None


class Sector(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    order: Optional[int] = None


class TechVersionDTO(BaseModel):
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    id: Optional[int] = None
    lastModifiedDate: Optional[str] = None
    ring: Optional[RingDTO] = None
    versionEnd: Optional[str] = None
    versionStart: Optional[str] = None


class TechAdvancedDTO(BaseModel):
    category: Optional[List[TechCategoryAdvancedDTO]] = None
    createdDate: Optional[str] = None
    deletedDate: Optional[str] = None
    description: Optional[str] = None
    id: Optional[int] = None
    label: Optional[str] = None
    lastModifiedDate: Optional[str] = None
    link: Optional[str] = None
    review: Optional[bool] = None
    ring: Optional[RingDTO] = None
    sector: Optional[RingDTO] = None
    versions: Optional[List[TechVersionDTO]] = None


class TechDTO(BaseModel):
    categories: Optional[List[TechCategoryDTO]] = None
    descr: Optional[str] = None
    id: Optional[int] = None
    label: Optional[str] = None
    link: Optional[str] = None
    review: Optional[bool] = None
    ring_id: Optional[int] = None
    sector_id: Optional[int] = None


class TechExportDTO(BaseModel):
    docId: Optional[int] = None


class TechSubscribeDTO(BaseModel):
    description: Optional[str] = None
    id: Optional[int] = None
    label: Optional[str] = None


class TechradarClient:
    def __init__(self, url: Optional[str] = None, token: Optional[str] = None, 
                 base_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Инициализация клиента Techradar
        
        Args:
            url: URL сервиса (новый вариант, совместим с GraphService)
            token: Bearer токен (новый вариант)
            base_url: URL сервиса (старый вариант для обратной совместимости)
            auth_token: Bearer токен (старый вариант для обратной совместимости)
        """
        # Поддержка обоих вариантов параметров
        # Если URL не передан, пытаемся взять из переменной окружения
        self.base_url = (url or base_url or os.getenv("URL_TECHRADAR") or "").rstrip('/')
        self.auth_token = token or auth_token or os.getenv("TOKEN_TECHRADAR") or ""
        self.session = requests.Session()
        if self.auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        user_roles: Optional[str] = None
    ) -> Response:
        url = f"{self.base_url}{endpoint}"
        request_headers = self.session.headers.copy()
        
        if user_roles:
            request_headers['user-roles'] = user_roles
        if headers:
            request_headers.update(headers)
            
        logging.info(f"Making {method} request to {url}")
        logging.debug(f"Params: {params}, JSON: {json}, Headers: {request_headers}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                verify=False,
                headers=request_headers
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            raise

    # Category Controller Methods
    def get_all_categories(self, user_roles: str) -> List[Category]:
        endpoint = "/api/v1/category"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [Category(**item) for item in response.json()]

    def add_category(self, category: PostCategoryDTO, user_roles: str) -> Category:
        endpoint = "/api/v1/category"
        response = self._request("POST", endpoint, json=category.dict(), user_roles=user_roles)
        return Category(**response.json())


    def put_category(self, category: PutTechCategoryDTO, user_roles: str) -> ResponseEntity:
        endpoint = "/api/v1/category/join"
        response = self._request("PUT", endpoint, json=category.dict(), user_roles=user_roles)
        return ResponseEntity(**response.json())

    def get_tech_by_categories(self, id_category: List[int], user_roles: str) -> List[TechAdvancedDTO]:
        endpoint = "/api/v1/category/tech"
        params = {"id_category": id_category}
        response = self._request("GET", endpoint, params=params, user_roles=user_roles)
        return [TechAdvancedDTO(**item) for item in response.json()]

    def delete_category(self, id: str, user_roles: str) -> ResponseEntity:
        endpoint = f"/api/v1/category/{id}"
        response = self._request("DELETE", endpoint, user_roles=user_roles)
        return ResponseEntity(**response.json())

    def patch_category(self, id: str, category: PatchCategoryDTO, user_roles: str) -> ResponseEntity:
        endpoint = f"/api/v1/category/{id}"
        response = self._request("PATCH", endpoint, json=category.dict(), user_roles=user_roles)
        return ResponseEntity(**response.json())

    # Pattern Controller Methods
    def create_pattern(self, pattern: PostPatternDTO, user_roles: str) -> ResponseEntity:
        endpoint = "/api/v1/pattern"
        response = self._request("POST", endpoint, json=pattern.dict(), user_roles=user_roles)
        return ResponseEntity(**response.json())

    def get_pattern_by_id(self, id: int, user_roles: str) -> PatternDTO:
        endpoint = f"/api/v1/pattern/{id}"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return PatternDTO(**response.json())

    def delete_pattern(self, id: int, user_roles: str) -> ResponseEntity:
        endpoint = f"/api/v1/pattern/{id}"
        response = self._request("DELETE", endpoint, user_roles=user_roles)
        return ResponseEntity(**response.json())

    def get_all_patterns(self, user_roles: Optional[str] = None) -> List[PatternDTO]:
        endpoint = "/api/v1/patterns"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [PatternDTO(**item) for item in response.json()]

    def get_patterns_auto_check(self, user_roles: str) -> List[PatternDTO]:
        endpoint = "/api/v1/patterns/auto-check"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [PatternDTO(**item) for item in response.json()]

    def get_technology_patterns(self, tech_id: int, user_roles: str) -> List[PatternDTO]:
        endpoint = f"/api/v1/patterns/tech/{tech_id}"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [PatternDTO(**item) for item in response.json()]

    # Process Controller Methods
    def get_all_processes(self, user_roles: str) -> List[ProcessDTO]:
        endpoint = "/api/v1/processes"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [ProcessDTO(**item) for item in response.json()]

    # Ring Controller Methods
    def get_all_rings(self, user_roles: str) -> List[Ring]:
        endpoint = "/api/v1/rings"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [Ring(**item) for item in response.json()]

    # Sector Controller Methods
    def get_all_sectors(self, user_roles: str) -> List[Sector]:
        endpoint = "/api/v1/sectors"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [Sector(**item) for item in response.json()]

    # Tech Controller Methods
    def get_all_tech(
        self, 
        user_roles: str, 
        actual_tech: Optional[bool] = None
    ) -> List[TechAdvancedDTO]:
        endpoint = "/api/v1/tech"
        params = {}
        if actual_tech is not None:
            params["actualTech"] = actual_tech
        response = self._request("GET", endpoint, params=params, user_roles=user_roles)
        return [TechAdvancedDTO(**item) for item in response.json()]

    def add_tech(self, techs: List[PostTechDTO], user_roles: str) -> ResponseEntity:
        endpoint = "/api/v1/tech"
        techs_dict = [tech.dict() for tech in techs]
        response = self._request("POST", endpoint, json=techs_dict, user_roles=user_roles)
        return ResponseEntity(**response.json())

    def patch_tech_version_export(self, doc_id: int, user_roles: str) -> TechExportDTO:
        endpoint = f"/api/v1/tech/export/{doc_id}"
        response = self._request("POST", endpoint, user_roles=user_roles)
        return TechExportDTO(**response.json())

    def create_product_relations(
        self, 
        tech: PostProductTechDTO, 
        user_roles: str
    ) -> ResponseEntity:
        endpoint = "/api/v1/tech/product-relation"
        response = self._request("POST", endpoint, json=tech.dict(), user_roles=user_roles)
        return ResponseEntity(**response.json())

    def get_product_tech(self, user_roles: str) -> List[ProductDTO]:
        endpoint = "/api/v1/tech/product-tech"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [ProductDTO(**item) for item in response.json()]

    def get_subscribed_tech(self, user_roles: str) -> List[TechSubscribeDTO]:
        endpoint = "/api/v1/tech/subscribed"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return [TechSubscribeDTO(**item) for item in response.json()]

    def get_tech_by_id(self, id: int, user_roles: str) -> HistoryTechDTO:
        endpoint = f"/api/v1/tech/{id}"
        response = self._request("GET", endpoint, user_roles=user_roles)
        return HistoryTechDTO(**response.json())

    def delete_tech(self, id: int, user_roles: str) -> ResponseEntity:
        endpoint = f"/api/v1/tech/{id}"
        response = self._request("DELETE", endpoint, user_roles=user_roles)
        return ResponseEntity(**response.json())

    def patch_tech(self, id: int, tech: TechDTO, user_roles: str) -> ResponseEntity:
        endpoint = f"/api/v1/tech/{id}"
        response = self._request("PATCH", endpoint, json=tech.dict(), user_roles=user_roles)
        return ResponseEntity(**response.json())

    def create_tech_version(
        self, 
        tech_id: int, 
        versions: List[PostTechVersionDTO], 
        user_roles: str
    ) -> ResponseEntity:
        endpoint = f"/api/v1/tech/{tech_id}/version"
        versions_dict = [version.dict() for version in versions]
        response = self._request("POST", endpoint, json=versions_dict, user_roles=user_roles)
        return ResponseEntity(**response.json())

    def patch_tech_version(
        self, 
        tech_id: int, 
        id_version: int, 
        version: PostTechVersionDTO, 
        user_roles: str
    ) -> ResponseEntity:
        endpoint = f"/api/v1/tech/{tech_id}/version/{id_version}"
        response = self._request("PATCH", endpoint, json=version.dict(), user_roles=user_roles)
        return ResponseEntity(**response.json())

    def delete_tech_version(
        self, 
        tech_id: int, 
        version_id: int, 
        user_roles: str
    ) -> ResponseEntity:
        endpoint = f"/api/v1/tech/{tech_id}/version/{version_id}"
        response = self._request("DELETE", endpoint, user_roles=user_roles)
        return ResponseEntity(**response.json())
