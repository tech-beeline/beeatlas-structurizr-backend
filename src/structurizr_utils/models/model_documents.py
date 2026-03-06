import requests
import os
import json
import logging
from requests_toolbelt.multipart.encoder import MultipartEncoder
from fastapi import HTTPException

URL_DOCUMENTS = os.getenv("URL_DOCUMENTS","https://document-service-dev-eafdmmart.apps.yd-m6-kt22.vimpelcom.ru")


# Метод GET /api/v1/documents/{id} (getDocument)
def get_document(document_id, user_id=None, user_roles=None) -> dict:
    url = f"{URL_DOCUMENTS}/api/v1/documents/{document_id}"
    headers = {}
    if user_id:
        headers["user-id"] = str(user_id)
    if user_roles:
        headers["user-roles"] = user_roles
    response = requests.get(url, headers=headers , verify= False)
    if response.status_code == 200:
        return json.loads(response.content)  # Возвращаем содержимое файла (bytes)
    else:
        raise HTTPException(status_code=response.status_code, detail=f"{response.text}")
        

# Метод POST /api/v1/documents/{path_name}/{doc_type} 
def upload_file(path_name, doc_type, file_path, is_public=True, user_id=None):
    url = f"{URL_DOCUMENTS}/api/v1/documents/{path_name}/{doc_type}"
    headers = {}
    if user_id:
        headers["user-id"] = str(user_id)

    params = {}
    if is_public is not None:
        params["isPublic"] = str(is_public).lower()

    # Создаем MultipartEncoder для ручного управления формой
    with open(file_path, "rb") as file:
        
        multipart_data = MultipartEncoder(
            fields={
                "file": (file_path, file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")  # Указываем имя файла и MIME-тип
            }
        )

        # Добавляем заголовок Content-Disposition
        headers["Content-Type"] = multipart_data.content_type  # Устанавливаем Content-Type с границей
        headers["Content-Disposition"] = f'attachment; filename="{file_path}"'  # Добавляем Content-Disposition

        # Отправляем запрос
        logging.info(f"# POST {url}")
        response = requests.post(url, headers=headers, params=params, data=multipart_data, verify=False)

        if response.status_code == 200 or response.status_code == 201:
            return int(response.json().get("docId"))  # Возвращаем JSON ответа (DocIdDTO)
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")


    raise Exception("File not found")

def upload_workspace_json(json_dict: dict, is_public=True, user_id=None) -> int:

    path_name = "workspace"
    doc_type  = "json"
    file_path = "workspace.json"
    doc_json  = json.dumps(json_dict, ensure_ascii=False)

    url = f"{URL_DOCUMENTS}/api/v1/documents/{path_name}/{doc_type}"
    headers = {}
    params = {}
    params["isPublic"] = "true"

    # Используем MultipartEncoder для правильного формирования multipart/form-data
    multipart_data = MultipartEncoder(
        fields={
            "file": (file_path, doc_json, "application/json")
        }
    )

    # Устанавливаем правильный Content-Type с boundary
    headers["Content-Type"] = multipart_data.content_type
    headers["Content-Disposition"] = f'attachment; filename="{file_path}"'  # Добавляем Content-Disposition

    response = requests.post(url, headers=headers, params=params, data=multipart_data, verify=False)

    if response.status_code == 200 or response.status_code == 201:
        return int(response.json().get("docId"))  # Возвращаем JSON ответа (DocIdDTO)
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")
