from dotenv import load_dotenv
import os
from fastapi import Depends, Security
from fastapi.security.api_key import APIKeyHeader
from handlers.exception_handler import APIKeyException

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

load_dotenv()

API_KEY = os.getenv("API_KEY")


async def get_api_key(
    api_key: str = Security(api_key_header),
):
    if api_key is None:
        raise APIKeyException(
            status=401, message="Authorization header missing")

    token = api_key.replace("Bearer ", "")

    if not token == API_KEY:
        raise APIKeyException(status=403, message="Invalid API Key")

    return True
