"""Shared Azure Container Apps session authentication and execution helpers."""
import os
import json
import logging
import time
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Module-level credential and token cache (shared across all ACA tools)
_aca_credential = None
_aca_token = None
_aca_token_expiry = None


def get_pool_endpoint() -> str | None:
    """Return the ACA pool management endpoint, or None if not configured."""
    return os.getenv('ACA_POOL_MANAGEMENT_ENDPOINT')


def get_aca_auth_header() -> tuple[str, int]:
    """
    Authenticate to Azure and return (auth_header, auth_time_ms).
    Uses module-level cached credential and token.
    Raises ImportError if azure-identity is not available.
    """
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

    global _aca_credential, _aca_token, _aca_token_expiry

    start_time = time.time()

    needs_new_token = (
        _aca_token is None
        or _aca_token_expiry is None
        or datetime.now() >= _aca_token_expiry
    )

    if needs_new_token:
        if _aca_credential is None:
            managed_identity_client_id = os.getenv('AZURE_CLIENT_ID')
            container_app_name = os.getenv('CONTAINER_APP_NAME')

            if managed_identity_client_id:
                logger.info(f"🔐 Using ManagedIdentityCredential with client_id (Container App: {container_app_name})")
                _aca_credential = ManagedIdentityCredential(client_id=managed_identity_client_id)
            elif container_app_name or os.getenv('WEBSITE_INSTANCE_ID'):
                logger.info(f"🔐 Using ManagedIdentityCredential with system-assigned identity (Container App: {container_app_name})")
                _aca_credential = ManagedIdentityCredential()
            else:
                logger.info("🔐 Using DefaultAzureCredential (running locally)")
                _aca_credential = DefaultAzureCredential()

        token_response = _aca_credential.get_token("https://dynamicsessions.io/.default")
        _aca_token = token_response.token
        _aca_token_expiry = datetime.now() + timedelta(
            seconds=token_response.expires_on - time.time() - 300
        )

        auth_time = int((time.time() - start_time) * 1000)
        logger.info(f"🔑 New token obtained for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
        print(f"🔑 New token obtained for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
    else:
        auth_time = int((time.time() - start_time) * 1000)
        logger.info(f"♻️ Using cached token for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
        print(f"♻️ Using cached token for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")

    return f"Bearer {_aca_token}", auth_time


def execute_in_sandbox(
    code: str,
    session_id: str,
    pool_management_endpoint: str,
    auth_header: str,
    timeout: int = 30
) -> dict:
    """
    Execute Python code in an ACA dynamic session.

    Returns:
        dict with keys: stdout, stderr, result, raw (full response)
    """
    execute_url = (
        f"{pool_management_endpoint}/code/execute"
        f"?api-version=2024-02-02-preview&identifier={session_id}"
    )

    payload = {
        "properties": {
            "codeInputType": "inline",
            "executionType": "synchronous",
            "code": code,
        }
    }

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json; charset=utf-8",
    }

    json_payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')

    response = requests.post(
        execute_url,
        data=json_payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()

    response.encoding = 'utf-8'
    result_data = response.json()

    props = result_data.get('properties', {})
    return {
        "stdout": props.get('stdout', ''),
        "stderr": props.get('stderr', ''),
        "result": props.get('result', ''),
        "raw": result_data,
    }


def download_file_from_sandbox(
    filename: str,
    session_id: str,
    pool_management_endpoint: str,
    auth_header: str,
    timeout: int = 30
) -> bytes:
    """
    Download a file from the ACA sandbox /mnt/data/ directory.

    Returns:
        Raw bytes of the file content.
    """
    download_url = (
        f"{pool_management_endpoint}/files/content/{filename}"
        f"?api-version=2024-02-02-preview&identifier={session_id}"
    )

    headers = {"Authorization": auth_header}

    response = requests.get(download_url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.content
