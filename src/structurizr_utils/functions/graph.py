import logging
import os
import requests
from typing import Dict, Any
from structurizr_utils.models.models_product import get_product, Product
from structurizr_utils.models.model_documents import upload_workspace_json
import uuid
import pika
import time
import datetime
import jwt
import json



def get_token() -> str:
    ambasador_url = os.getenv("AMBASADOR_URL","https://ambassador-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru")
    url = f"{ambasador_url}/rabbit-token"
    logging.info(f"Getting token from {url}")
    response = requests.get(url, verify=False)
    response.raise_for_status()
    logging.info(f"Token: {response.json()['access_token']}")
    return response.json()["access_token"]


def send_rabbit_message_for_graph(cmdb: str, doc_id: int, token: str):
    rabbit_message = json.dumps({ "taskKey" : str(uuid.uuid4()), # generated GUID string
                    "docId" : doc_id,
                    "cmdbCode" : cmdb }, ensure_ascii=False)

    credentials = pika.PlainCredentials('', token)
    rabbit_vhost = os.getenv("RABBIT_VHOST", "dev_host")

    # Устанавливаем соединение с RabbitMQ
    hosts = os.getenv("RABBIT_HOSTS", "eafdmmart-rabbit-dev-1.arch-code.cloud.vimpelcom.ru,eafdmmart-rabbit-dev-2.arch-code.cloud.vimpelcom.ru").split(",")
    connection = None
    for host in hosts:
        try:
            logging.info(f"Connecting to RabbitMQ: {host}")
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=host,
                virtual_host=rabbit_vhost, # dev_host or prod_host
                credentials=credentials
            ))
            break
        except Exception as ex:
            logging.error(f"Error connecting to RabbitMQ: {ex}")
            continue

    # Создаем канал
    if connection:
        channel = connection.channel()
        channel.basic_publish(
            exchange='',
            routing_key='create_global_graph',
            body=rabbit_message,
            properties=pika.BasicProperties(content_type='application/json'))
       # channel.tx_commit()
        channel.close()
        logging.info(f"Rabbit message sent {rabbit_message}")
    else:
        logging.error(f"Error connecting to RabbitMQ")
        raise Exception("Error connecting to RabbitMQ")


cached_token = None

def publish_graph(cmdb: str, data: Dict[str, Any]):

    # get product by cmdb
    logging.info(f"Publish graph for {cmdb}")
    if  product := get_product(cmdb=cmdb):
        logging.info(f"Loaded product for {cmdb}: {product.id} - {product.name}")
        logging.info(f"Product data: {product.structurizrApiKey} , {product.uploadSource}")
        if product.uploadSource is None or product.uploadSource == "script" and product.structurizrApiKey:
            logging.info(f"Uploading document")
            try:
                doc_id = upload_workspace_json(data)
                logging.info(f"Document id {doc_id}")

                global cached_token

                if not cached_token:
                    cached_token = get_token()
                else:
                    logging.info(f"Cached token {cached_token}")
                    token_decoded = jwt.decode(cached_token, options={"verify_signature": False})
                    if datetime.datetime.fromtimestamp(token_decoded['exp'], datetime.timezone.utc) < datetime.datetime.fromtimestamp(time.time(), datetime.timezone.utc):
                        logging.info("Renew rabbit token")
                        cached_token = get_token()

                if cached_token:
                    send_rabbit_message_for_graph(cmdb, doc_id, cached_token)

            except Exception as ex:
                logging.error(f"Error sending rabbit message: {ex}")
        else:
            logging.error(f"Product {cmdb} has no structurizrApiKey or uploadSource is not script")
    else:
        logging.error(f"Cant't find product with cmdb {cmdb} in product service")
 