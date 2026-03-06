import requests
import os
import logging
from fastapi import HTTPException

RULE_COMPILER_URL = os.getenv(key='RULE_COMPILER_URL')

# Метод GET /api/v1/elements?cmdb={id} 
def get_cypher_query(cmdb :str, rule:str) -> str:
    url = f"{RULE_COMPILER_URL}/api/v1/elements?cmdb={cmdb}"
    headers = {'Content-Type': 'text/plain'} 
    logging.info(f"# Send request to compiler service {url}")
    response = requests.post(url, headers=headers , data = rule, verify= False)
    if response.status_code == 200:
        logging.info(f"# Result from compiler service {response.status_code}")
        return response.content.decode("utf-8")
    else:
        logging.error(f"# Error from compiler service {response.status_code} {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"{response.text}")
