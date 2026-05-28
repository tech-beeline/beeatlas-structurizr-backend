from typing import List,Union
from pydantic import BaseModel
import json
import os


class ArchitecturePattern(BaseModel):
    code            : str
    name            : str
    description     : str
    validation_rule : Union[str, List[str]]


class ArchitecturePatterns(BaseModel):
    items : List[ArchitecturePattern]

def load_patterns_from_json(file_path: str):
    if not os.path.isfile(file_path):
        raise Exception(f"File not found {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return ArchitecturePatterns(**data)
    return None
        
        