import os

from fastapi import Depends, FastAPI, Header, HTTPException

from google.cloud import secretmanager


def access_secret_version(project_id, secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != access_secret_version("aurite-dev", "API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
