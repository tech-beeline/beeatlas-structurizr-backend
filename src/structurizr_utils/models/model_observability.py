import requests
import base64
"""
Класс для публикации дашбордов наблюдаемости по архитектуре в structurizr.vimpelcom.ru
"""

class ObservabilityClient:
    url : str
    token : str

    def __init__(self, url: str) -> None:
        self.url = url
        self.token = None


    def get_token(self,login : str, password: str) -> str:
        url = f"{self.url}/api/token"
        credentials = f"{login}:{password}".encode("utf-8")
        encoded_credentials = base64.b64encode(credentials).decode("utf-8")
        auth_header = f"Basic {encoded_credentials}"

        headers = {"Content-Type" : "application/json", "Authorization" : auth_header}

        response = requests.post(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            data_dict = response.json()
            self.token = data_dict["token"]
        else:
            print(f"Observability error: {response.status_code} {response.reason}")
            raise Exception(f"{response.status_code} {response.reason}")
            

    def publish_dashboard(self,workspace_id : int) -> None:
        url  = f"{self.url}/api/structurizrmodel"
        body = {"ModelId" : workspace_id }
        headers = {"Content-Type" : "application/json", "Authorization" : f"Bearer {self.token}"}

        result =requests.post(url=url,json=body,verify=False,headers=headers)
        result.raise_for_status()


    
