from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from collections.abc import Iterable
import logging

class Capability(BaseModel):
    code: str
    isDomain: bool
    name: str
    description: str
    author: str
    status: str
    createdDate: datetime
    modifieddDate: datetime
    parent: Optional[dict] = None
    children: List[dict]
    self: str

class Term(BaseModel):
    id: str
    name: str
    displayName: str
    fullyQualifiedName: str
    synonyms: List[str]
    description: str

class Glossary(BaseModel):
    id: str
    type: str
    name: str
    fullyQualifiedName: str
    description: str
    deleted: bool
    self: str

class SystemLink(BaseModel):
    code: str
    # name: str
    # href: str

class TechnicalCapability(BaseModel):
    code: str
    name: str
    description: str
    author: str
    # createdDate: datetime
    # modifiedDate: datetime
    status: str
    parents: List[dict]
    system: SystemLink
    owner: str
    version: str
    goal_from: str
    goal_to: str

class Method(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    implements: Optional[str] = None
    rps: Optional[float] = None
    latency: Optional[float] = None
    error_rate: Optional[float] = None
    

class Interface(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    protocol: Optional[str] = None
    implements: Optional[str] = None
    specification: Optional[str] = None
    methods: Optional[List[Method]] = None
    self: Optional[str] = None

class Container(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    interfaces: Optional[List[Interface]] = None

class System(BaseModel):
    code: str
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    ea_guid: Optional[str] = None
    FQName: Optional[str] = None
    status: Optional[str] = None
    status: Optional[str] = None
    status: Optional[str] = None
    modifiedDate: Optional[datetime] = None
    containers: Optional[List[Container]] = None
    links: Optional[dict] = None

class SystemPurpose(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    children: Optional[List['SystemPurpose']] = list
    href: Optional[str] = None

    def as_set(self) -> set:
        result = set()
        def walk_purpose(purpose : SystemPurpose, result : set):
            if hasattr(purpose,"code"):
                if purpose.code is not None:
                    if purpose.type is not None:
                        if purpose.type.lower() == "TechnicalCapability".lower():
                            result.add(purpose.code)
            
            if hasattr(purpose,"children"):
                if purpose.children is not None:
                    if isinstance(purpose.children, Iterable):
                        for p in purpose.children:
                            if p is not None:
                                walk_purpose(purpose=p,result=result)

        walk_purpose(purpose=self,result=result)
        return result

class SystemE2EParticipation(BaseModel):
    process: dict
    bi: dict
    message: dict
    system: dict

class SystemAssessmentResult(BaseModel):
    system_code: str
    fitness_function_code: str
    assessment_date: str
    assessment_description: str
    status: int
    result_details: str


class E2EProcess(BaseModel):
    uid: str
    name: str

class E2EProcessMessage(BaseModel):
    uid: str
    name: str

class GrafanaSource(BaseModel):
    name: str
    uid: str

class ObservabilitySource(BaseModel):
    pass

class TechRadarCategory(BaseModel):
    id: int
    name: str

class TechRadarTechnology(BaseModel):
    id: int
    label: str
    createdDate: datetime
    deletedDate: Optional[datetime] = None
    lastModifiedDate: datetime
    link: str
    category: TechRadarCategory
    sector: dict
    ring: dict

