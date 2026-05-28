from pydantic import BaseModel

# Определяем модель данных для входящего запроса
class RestProduct(BaseModel):
    code: str
    architect_name: str

# Определяем модель данных для входящего запроса
class RestWorkspace(BaseModel):
    id : int
    code: str
    name: str
    api_key: str
    api_secret: str
    api_url: str