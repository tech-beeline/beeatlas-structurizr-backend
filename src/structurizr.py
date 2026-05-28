# Copyright (c) 2024 PJSC VimpelCom
import json
import requests
import hashlib
import hmac
from base64 import b64encode
from datetime import datetime, timedelta
import os
import logging

password                    = os.environ['ONPREMISES_PASSWORD'] 
url_onpremises_workspace    = os.environ['URL_ONPREMISES_WORKSPACE'] 
url_onpremises_base         = os.environ['URL_ONPREMISES_BASE']

class StructurizrException(Exception):
    def __init__(self, message):
        super().__init__(message)

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
    def __init__(self,id,name,description,apiKey,apiSecret,privateUrl,publicUrl) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        self.privateUrl = privateUrl
        self.publicUrl = publicUrl
    
    def print(self) -> None:
        print("id=",self.id)
        print("name=",self.name)
        print("description=",self.description)
        print("apiKey=",self.apiKey)
        print("apiSecret=",self.apiSecret)
        print("privateUrl=",self.privateUrl)
        print("publicUrl=",self.publicUrl)                     

# load workspace from Structurizr OnPremises
def load_workspace(wrk : Workspace):
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

    resp = requests.get(url=apiUrl, headers=headers, verify=False)

    if(resp.status_code==200):
        return resp.json()
    else:
        return dict()


# post new workspace to structurizr OnPremises
def post_workspace():
    headers = {"X-Authorization": password}
    resp = requests.post(url=url_onpremises_workspace, headers=headers, verify=False)
    if(resp.status_code==200):
        return resp.json()
    else:
        logging.error(f'\u001b[31m# result {resp.status_code} {resp.reason}\u001b[37m')
        logging.error(f'\u001b[31m# result {resp.text}\u001b[37m')
        return None

def get_workspaces():
    headers = {"X-Authorization": password}
    resp = requests.get(url=url_onpremises_workspace, headers=headers, verify=False)
    if(resp.status_code==200):
        return resp.json()
    else:
        raise StructurizrException("Не могу подключится к Structurizr OnPremise")
                
def get_workspace_cmdb(data):
    # workspace_cmdb "LCR"
    result = dict()
    systems             = dict()

    cmdb            = ''
    workspace_cmdb  = ''
    diagram_key     = ''
    
    model               = data['model']
    views               = data['views']
    
    model_properties = model.get('properties',dict())
    if 'workspace_cmdb' in model_properties:
        workspace_cmdb = model_properties['workspace_cmdb']

    if 'softwareSystems' in model:
        software_systems    = model['softwareSystems'] # Системы  
        for s in software_systems:
            systems[s['id']] = s

    if 'systemContextViews' in views:
        context_views = views['systemContextViews']
        for v in context_views:
            if 'softwareSystemId' in v:
                softwareSystemId = v['softwareSystemId']
                if softwareSystemId in systems:
                    system = systems[softwareSystemId]
                    if 'properties' in system:
                        properties = system['properties']
                        if 'cmdb' in properties:
                            cmdb = properties['cmdb']
                            if 'key' in v:
                                 diagram_key = '/diagrams#'+v['key']
                                 result[cmdb] = diagram_key

    if workspace_cmdb != '':
        if workspace_cmdb not in result:
            result[workspace_cmdb] = ''
        else:
            diagram_key = result[workspace_cmdb]
            result.clear()
            result[workspace_cmdb] = diagram_key

    return result
