import requests
import json
import os
import pycamunda.processdef
import pycamunda.processinst
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fastapi import HTTPException

BPM_URL = os.getenv(key='BPM_URL')
CAMUNDA_URL = os.getenv(key='CAMUNDA_URL')
CAMUNDA_USER = os.getenv(key='CAMUNDA_USER')
CAMUNDA_PASSWORD = os.getenv(key='CAMUNDA_PASSWORD')
PROCESS_KEY = os.getenv(key='PROCESS_KEY')


def get_bpm_process_status(business_key: str) -> dict:
    url = f"{BPM_URL}/camunda-process/api/v1/status/business-key/{business_key}/now"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        # Возвращаем содержимое файла (bytes)
        return json.loads(response.content)
    else:
        raise HTTPException(status_code=response.status_code,
                            detail=f"{response.text}")


def start_camunda_process(business_key: str, cmdb: str, doc_id: int) -> int:
    session = requests.Session()
    session.verify = False  # Отключаем проверку SSL
    requests.packages.urllib3.disable_warnings()  # Отключаем предупреждения о SSL

    # Настраиваем политику повторных попыток
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Тип: pycamunda.processdef.StartInstance
    start_instance = pycamunda.processdef.StartInstance(
        url=CAMUNDA_URL, key=PROCESS_KEY, business_key=business_key)
    start_instance.add_variable(name='cmdb', value=cmdb)
    start_instance.add_variable(name='docId', value=doc_id)
    start_instance.session = session

    start_instance.auth = requests.auth.HTTPBasicAuth(
        username=CAMUNDA_USER, password=CAMUNDA_PASSWORD)

    process_instance = start_instance()

    return process_instance.id_
