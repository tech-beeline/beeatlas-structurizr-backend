from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import requests


# Общие модели
class Error(BaseModel):
    code: int
    debug: str
    description: str
    error: str

class GlossaryRegion(BaseModel):
    id: str
    name: str

class GlossaryImage(BaseModel):
    id: str
    name: str

# Модели для IP-адресов
class Address(BaseModel):
    address: str
    auto_delete: bool
    condition: str
    id: str
    metadata: Dict[str, str]
    name: str
    project_id: str
    purpose: str
    region: GlossaryRegion
    status: str
    tags: List[str]
    type: str
    version: str

class AddressCreate(BaseModel):
    metadata: Dict[str, str]
    name: str
    region: str
    tags: List[str]

class AddressUpdate(BaseModel):
    auto_delete: bool
    name: str
    tags: List[str]

class AddressAttach(BaseModel):
    server_id: str

# Модели для аффинити-групп
class AffinityGroup(BaseModel):
    condition: str
    id: str
    metadata: Dict[str, str]
    name: str
    policy: str
    project_id: str
    region: GlossaryRegion
    tags: List[str]

class AffinityGroupCreate(BaseModel):
    metadata: Dict[str, str]
    name: str
    policy: str
    region: str
    tags: List[str]

class AffinityGroupUpdate(BaseModel):
    name: str
    tags: List[str]

# Модели для тарифных планов (Flavors)
class Flavor(BaseModel):
    group: str
    group_priority: int
    id: str
    name: str
    ram: int
    regions: List[str]
    slug: str
    vcpu: int

# Модели для образов (Images)
class Image(BaseModel):
    application: Optional[str] = None
    application_version: Optional[str] = None
    distribution: str
    id: str
    min_disk: int
    name: str
    projects: Optional[List] = None
    regions: List[str]
    slug: str
    version: str

class ImagePatchBody(BaseModel):
    projects: List[str]

# Модели для квот
class Quota(BaseModel):
    instance: int
    ram: int
    vcpu: int
    volume_size: Dict[str, int]

class QuotaStatisticsUsed(BaseModel):
    quota: int
    used: int

class QuotaStatistics(BaseModel):
    instance: QuotaStatisticsUsed
    ram: QuotaStatisticsUsed
    vcpu: QuotaStatisticsUsed
    volume_size: Dict[str, QuotaStatisticsUsed]

class QuotaUpdate(BaseModel):
    instance: int
    ram: int
    vcpu: int
    volume_size: Dict[str, int]

# Модели для регионов
class Region(BaseModel):
    features: List[str]
    hypervisor: str
    id: str
    limits: Dict[str, Any]
    location: str
    name: str
    priority: int
    slug: str
    volumes_type: List[str]
    zone: str

# Модели для серверов
class Server(BaseModel):
    addresses: List[Address]
    affinity_group: AffinityGroup
    condition: str
    created_at: str
    created_by: str
    flavor: Flavor
    fqdn: str
    id: str
    image: Image
    name: str
    project: str
    region: Region
    status: str
    tags: List[str]
    user_data: str
    volumes: List['Volume']

class ServerCreate(BaseModel):
    address: Optional[str]
    affinity_group: Optional[str]
    flavor: str
    image: str
    metadata: Dict[str, str]
    name: str
    region: str
    tags: List[str]
    user_data: Optional[str]
    volume_size: int
    volume_type: str
    volumes_attached: Optional[List[Dict[str, Any]]]

class ServerResize(BaseModel):
    flavor_id: str

# Модели для дисков (Volumes)
class Volume(BaseModel):
    attached_to: str
    attachment: Dict[str, str]
    condition: str
    created_at: str
    created_by: str
    device: str
    id: str
    is_boot: bool
    name: str
    project_id: str
    region_id: str
    size: int
    tags: List[str]
    type: str

class VolumeCreate(BaseModel):
    attach_to_server: Optional[str]
    name: str
    region: str
    size: int
    tags: List[str]
    type: str

class VolumeUpdate(BaseModel):
    name: str
    tags: List[str]

class VolumeAttach(BaseModel):
    server_id: str

class VolumeDetach(BaseModel):
    server_id: str

class VolumeExtendSize(BaseModel):
    size: int

# Обновляем ссылки на модели
Server.model_rebuild()


class VegaVPSClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_flavors(self, project: str, vcpu: Optional[int] = None, ram: Optional[int] = None,
                    order: Optional[str] = None) -> List[Flavor]:
        url = f"{self.base_url}/api/v1/projects/{project}/vps/flavors"
        params = {
            "vcpu": vcpu,
            "ram": ram,
            "order": order
        }
        response = requests.get(url, headers=self.headers, params=params, verify=False)
        response.raise_for_status()
        return [Flavor(**flavor) for flavor in response.json()]

    def get_images(self, project: str) -> List[Image]:
        url = f"{self.base_url}/api/v1/projects/{project}/vps/images"

        response = requests.get(url, headers=self.headers, verify=False)
        response.raise_for_status()
        return [Image(**image) for image in response.json()]
    
    def get_regions(self, project: str, perimeter: Optional[str] = None, zone: Optional[str] = None) -> List[Region]:
        url = f"{self.base_url}/api/v1/projects/{project}/vps/regions"
        params = {
            "perimeter": perimeter,
            "zone": zone
        }
        response = requests.get(url, headers=self.headers, params=params, verify=False)
        response.raise_for_status()
        return [Region(**region) for region in response.json()]