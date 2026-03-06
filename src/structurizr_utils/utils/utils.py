import os
import json
import subprocess
import os.path
import logging
from datetime import datetime
from typing import Dict, Optional

def get_workspace_cmdb(data: Dict) -> Optional[str]:
    """Извлекает CMDB код из данных workspace.
    
    Args:
        data: Словарь с данными workspace
        
    Returns:
        Optional[str]: CMDB код если найден, None в противном случае
    """
    model               = data['model']
    model_properties = model.get('properties',dict())

    for key in model_properties:
        if key.lower() == 'workspace_cmdb':
            workspace_cmdb = model_properties[key]
            return workspace_cmdb
    
    return None

class StructurizrError(Exception):
    """Исключение для ошибок в выполнении программы Structurizr.
    
    Attributes:
        message: Сообщение об ошибке
    """
    pass

def load_workspace(json_file_path: str) -> Dict:
    """Загружает данные workspace из JSON файла.
    
    Args:
        json_file_path: Путь к JSON файлу с данными workspace
        
    Returns:
        Dict: Данные workspace в формате словаря
        
    Raises:
        StructurizrError: При ошибке чтения файла
    """
    logging.info('\u001b[32m# Loading data from structurizr ...\u001b[37m')
    try:
        with open(json_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise StructurizrError(f"\u001b[31mError: The file '{json_file_path}' was not found.\u001b[37m")
    except Exception as e:
        raise StructurizrError(f"\u001b[31mAn error occurred: {e}\u001b[37m")
    
def convert_to_json(dsl_file_path: str, json_file_path: str) -> str:
    """Конвертирует DSL файл в JSON формат с помощью Structurizr CLI.
    
    Args:
        dsl_file_path: Путь к DSL файлу
        json_file_path: Путь к JSON файлу (используется для проверки)
        
    Returns:
        str: Путь к сгенерированному JSON файлу
        
    Raises:
        StructurizrError: При ошибке конвертации или отсутствии файлов
    """
    if not os.path.isfile(dsl_file_path):
        if os.path.isfile(json_file_path):
            logging.info("\u001b[32m# No DSL found - using JSON ...\u001b[37m")
            return json_file_path
        else:
            raise StructurizrError(f"{dsl_file_path} file not found in root directory of repository")

    need_convert = True
    # if not os.path.isfile(json_file_path):
    #     need_convert = True
    # else:
    #     mtime_dsl = os.path.getmtime(dsl_file_path)
    #     mtime_json = os.path.getmtime(json_file_path)
    #     # Преобразуем в datetime
    #     dt_dsl  = datetime.fromtimestamp(mtime_dsl)
    #     dt_json = datetime.fromtimestamp(mtime_json)

    #     if dt_dsl > dt_json:
    #         logging.info("\u001b[32m# DSL file more recent then JSON\u001b[37m")
    #         need_convert = True
    #     else:
    #          logging.info("\u001b[32m# JSON file is more recent then DSL, skipping conversion \u001b[37m")

    if need_convert:
        logging.info("Converting DSL to JSON...")
        command = ["/usr/local/structurizr-cli/structurizr.sh", "export", "-workspace", 
                  dsl_file_path, "-format", "json", "-output", "/tmp"]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info("Command executed successfully")
            logging.info(f"Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logging.error("Command failed")
            logging.error(f"Error: {e.stderr}")
            raise StructurizrError(f"Unable to convert {dsl_file_path} to json: {e}")
        except FileNotFoundError:
            logging.error("Structurizr CLI not found at /usr/local/structurizr-cli/structurizr.sh")
            raise StructurizrError("Structurizr CLI not found. Please install Structurizr CLI.")
    
    return "/tmp/workspace.json" 