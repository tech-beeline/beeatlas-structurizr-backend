from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi import HTTPException

class ResourceBase(BaseModel):
    project         : Optional[str] = None
    region          : Optional[str] = None
    instances       : Optional[int] = 0
    name            : Optional[str] = None
    resource_params : Optional[dict] = None

class Vm(ResourceBase):
    resource_type   : Optional[str] = "vm"
    flavor          : Optional[str] = None
    image           : Optional[str] = None
    volume_size     : Optional[str] = None
    volume_type     : Optional[str] = None # nvme
    flavor_id       : Optional[str] = None
    image_id        : Optional[str] = None
    region_id       : Optional[str] = None

    def check_errors(self, properties : dict, name: str, instances: int, region : str, project: str):
        result = ""
        if 'flavor' not in properties:
            if 'flavour' not in properties:
                result += f"VM {name} parameters error - not found flavor\n"

        if 'image' not in properties:
                result += f"VM {name} parameters error - not found image\n"

        if 'volume_size' not in properties:
                result += f"VM {name} parameters error - not found volume_size\n"
        else:
             val = properties.get('volume_size')
             if not val.isdigit():
                  result += f"VM {name} parameters error - volume_size must be a number\n"

        if len(result) == 0:
            result = None
        return result

    def parse(self, properties : dict, name: str, instances: int, region : str, project: str):
        self.project        = project
        self.region         = region
        self.name           = name
        self.instances      = instances
        self.flavor         = properties.get("flavor",None)
        if self.flavor is None: # fix of old bug
            self.flavor         = properties.get("flavour",None)

        self.image          = properties.get("image",None)
        self.volume_size    = properties.get("volume_size",None)
        self.volume_type    = properties.get("volume_type","nvme")

        return self

class GeneralResource(ResourceBase):
    resource_type   : Optional[str] = None



    def check_errors(self, properties : dict, name: str, instances: int, region : str, project: str):
        return None

    def parse(self, properties : dict, name: str, instances: int, region : str, project: str):
        self.project        = project
        self.region         = region
        self.name           = name
        self.instances      = instances
        self.resource_type = properties.get("type",None)
        self.resource_params = dict()
        
        for k in [key for key in properties.keys() if key!="type" and key!="structurizr.dsl.identifier" and key!="region" and key!="vega_project"]:
            self.resource_params[k] = properties[k]

        return self

class PostgreSQL(ResourceBase):
    resource_type       : Optional[str] = "postgresql"
    flavor              : Optional[str] = None
    flavor_id           : Optional[str] = None
    version             : Optional[str] = None # 14
    volume_size         : Optional[str] = None
    backup_strategies   : Optional[str] = None # backup-off
    deployment_configuration : Optional[str] = None # single

    def check_errors(self, properties : dict, name: str, instances: int, region : str, project: str):
        result = ""

        if 'flavor' not in properties:
            if 'flavour' not in properties:
                result += f"PostgreSQL {name} parameters error - not found flavor\n"

        if 'volume_size' not in properties:
                result += f"PostgreSQL {name} parameters error - not found volume_size\n"
        else:
             val = properties.get('volume_size')
             if not val.isdigit():
                  result += f"VM {name} parameters error - volume_size must be a number\n"

        if len(result) == 0:
            result = None

        return result
    
    def parse(self, properties : dict, name: str, instances: int, region : str, project: str):
        self.project        = project
        self.region         = region
        self.name           = name
        self.instances      = instances
        self.flavor         = properties.get("flavor",None)
        if self.flavor is None: # fix of old bug
            self.flavor         = properties.get("flavour",None)
        self.version                    = properties.get("version","14")
        self.volume_size                = properties.get("volume_size",None)
        self.backup_strategies          = properties.get("backup_strategies","backup-off")
        self.deployment_configuration   = properties.get("deployment_configuration","single")
        return self

class Redis(ResourceBase):
    resource_type       : Optional[str] = "redis"
    flavor              : Optional[str] = None
    flavor_id           : Optional[str] = None
    version             : Optional[str] = None # 7-0-12
    volume_size         : Optional[str] = None
    volume_type         : Optional[str] = "nvme"

    def check_errors(self, properties : dict, name: str, instances: int, region : str, project: str):
        result = ""
        
        if 'flavor' not in properties:
            if 'flavour' not in properties:
                result += f"Redis {name} parameters error - not found flavor\n"

        if 'volume_size' not in properties:
                result += f"Redis {name} parameters error - not found volume_size\n"
        else:
             val = properties.get('volume_size')
             if not val.isdigit():
                  result += f"VM {name} parameters error - volume_size must be a number\n"

        if len(result) == 0:
            result = None

        return result
    
    def parse(self, properties : dict, name: str, instances: int, region : str, project: str):
        self.project        = project
        self.region         = region
        self.name           = name
        self.instances      = instances
        self.flavor         = properties.get("flavor",None)
        if self.flavor is None: # fix of old bug
            self.flavor         = properties.get("flavour",None)
        self.version        = properties.get("version","7-0-12")
        self.volume_size    = properties.get("volume_size",None)
        return self

class MongoDB(ResourceBase):
    resource_type   : Optional[str] = "mongodb"
    flavor              : Optional[str] = None
    flavor_id           : Optional[str] = None
    volume_size         : Optional[str] = None
    volume_type         : Optional[str] = "nvme"
    backup_strategies   : Optional[str] = None
    deployment_configuration : Optional[str] = None
    
    def check_errors(self, properties : dict, name: str, instances: int, region : str, project: str):
        result = ""
        
        if 'flavor' not in properties:
            if 'flavour' not in properties:
                result += f"MongoDB {name} parameters error - not found flavor\n"

        if 'volume_size' not in properties:
                result += f"MongoDB {name} parameters error - not found volume_size\n"
        else:
             val = properties.get('volume_size')
             if not val.isdigit():
                  result += f"VM {name} parameters error - volume_size must be a number\n"

        if len(result) == 0:
            result = None
        return result
        
    def parse(self, properties : dict, name: str, instances: int, region : str, project: str):
        self.project        = project
        self.region         = region
        self.name           = name
        self.instances      = instances
        self.flavor         = properties.get("flavor",None)
        if self.flavor is None: # fix of old bug
            self.flavor         = properties.get("flavour",None)
        self.volume_size    = properties.get("volume_size",None)
        self.volume_type    = properties.get("volume_type","nvme")
        self.backup_strategies          = properties.get("backup_strategies","backup-off")
        self.deployment_configuration   = properties.get("deployment_configuration","single")
        return self

class KafkaCluster(ResourceBase):
    resource_type       : Optional[str] = "kafka"
    flavor              : Optional[str] = None
    size                : Optional[str] = "3"
    volume_size         : Optional[str] = None
    topic_names         : Optional[list] = list()
    num_partitions      : Optional[str] = "1"
    replication_factor  : Optional[str] = "2"
    log_retention_hours : Optional[str] = "168"
    log_retention_bytes : Optional[str] = "3276800000"

    def check_errors(self, properties : dict, name: str, instances: int, region : str, project: str):
        result = ""
        
        if 'flavor' not in properties:
            if 'flavour' not in properties:
                result += f"Kafka {name} parameters error - not found flavor\n"

        if 'volume_size' not in properties:
                result += f"Kafka {name} parameters error - not found volume_size\n"
        else:
             val = properties.get('volume_size')
             if not val.isdigit():
                  result += f"VM {name} parameters error - volume_size must be a number\n"

        if len(result) == 0:
            result = None
        return result
    
    def parse(self, properties : dict, name: str, instances: int, region : str, project: str, topic_names: list):
        self.project        = project
        self.region         = region
        self.name           = name
        self.instances      = instances
        self.flavor         = properties.get("flavor",None)
        if self.flavor is None: # fix of old bug
            self.flavor         = properties.get("flavour",None)
        self.volume_size    = properties.get("volume_size",None)
        self.topic_names         = topic_names
        self.size                = properties.get("size","3")
        self.num_partitions      = properties.get("num_partitions","1")
        self.replication_factor  = properties.get("replication_factor","2")
        self.log_retention_hours = properties.get("log_retention_hours","168")
        self.log_retention_bytes = properties.get("log_retention_bytes","3276800000")

        return self

    
class Resources(BaseModel):
    resources   : Optional[List] = list()




