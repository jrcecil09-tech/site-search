"""Storage router — file upload, download, and storage config management."""

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

router = APIRouter()


class StorageConfigUpdate(BaseModel):
    backend: str
    config: dict


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(site_id: str, file: UploadFile):
    # TODO: route to StorageManager based on configured backend
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/files/{site_id}")
async def list_files(site_id: str):
    return {"files": []}


@router.get("/files/{site_id}/{file_key:path}")
async def get_file(site_id: str, file_key: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/files/{site_id}/{file_key:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(site_id: str, file_key: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/config")
async def get_storage_config():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/config")
async def update_storage_config(body: StorageConfigUpdate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
