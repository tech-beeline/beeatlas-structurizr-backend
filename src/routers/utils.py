from typing import Dict, Optional
from typing_extensions import TypedDict
import base64
import binascii
import json
import tempfile
import subprocess
from pydantic import BaseModel
from . import log_endpoint_call, log_key_milestone, log_error_with_details, log_function_entry, log_function_exit

def decode_base64(encoded_string, encoding='utf-8', url_safe=False) -> Optional[str]:
    """
    Safely decode a Base64 string with comprehensive error handling
    
    Args:
        encoded_string (str): The Base64 encoded string
        encoding (str): Character encoding for the decoded string
        url_safe (bool): Whether to use URL-safe decoding
    
    Returns:
        str: Decoded string, or None if decoding fails
    """
    if not encoded_string:
        return None
    
    try:
        # Remove any whitespace or newlines
        encoded_string = encoded_string.strip()
        
        # Add padding if needed
        padding = 4 - (len(encoded_string) % 4)
        if padding != 4:
            encoded_string += '=' * padding
        
        # Choose decoding method
        if url_safe:
            decoded_bytes = base64.urlsafe_b64decode(encoded_string)
        else:
            decoded_bytes = base64.b64decode(encoded_string)
        
        # Convert to string
        return decoded_bytes.decode(encoding)
        
    except (binascii.Error, UnicodeDecodeError, Exception) as e:
        print(f"Base64 decoding error: {e}")
        return None

class ConvertResult(TypedDict):
    errors : Optional[str]
    json : Optional[Dict]

def convert_dsl2json(dsl : str) -> ConvertResult:

    log_function_entry("convert_dsl2json", dsl_length=len(dsl) if dsl else 0)
    
    log_key_milestone(f"Converting DSL to JSON format")
    
    try:
        tempdir = tempfile.gettempdir()
        filename = tempdir + '/workspace.dsl'
        filename_json = tempdir + '/workspace.json'
        
        log_key_milestone(f"Request loaded, writing DSL to {filename}")

        log_key_milestone(f"DSL: {dsl[:100]} ...")
        
        with open(filename,'w') as f:
            f.write(dsl)
        
        log_key_milestone(f"Executing CLI command for JSON ")

        process = subprocess.Popen(["/usr/local/structurizr-cli/structurizr.sh", "export", "-workspace", filename,"-format","json"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          text=True)

        stdout, stderr = process.communicate()
        # logging.info("Output:", stdout)
        # logging.info("Errors:", stderr)
        # logging.info("Return code:", process.returncode)
        
        if process.returncode == 0:
            log_function_exit("convert_dsl2json", result=True)
            with open(filename_json,"r") as f:
                json_string = f.read()
                return {"errors" : None, "json" : json.loads(json_string)}
        else:
            log_function_exit("convert_dsl2json", result=False)
            return { "errors" : f"{stderr}", "json" : None }
    except Exception as e:
        log_function_exit("convert_dsl2json", result=False)
        return { "errors": f"{e}", "json" : None }

class DSLWorkspace(TypedDict):
    workspace : str

# Модели для ошибок
class ValidationError(BaseModel):
    valid: str
    error: str

class ErrorDetail(BaseModel):
    detail: str