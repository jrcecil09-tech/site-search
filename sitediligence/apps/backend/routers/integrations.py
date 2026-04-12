"""Integrations router — OAuth and data sync for Procore, Autodesk, Drive, OneDrive."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

SUPPORTED_INTEGRATIONS = ["procore", "autodesk", "gdrive", "onedrive"]


class IntegrationConnect(BaseModel):
    integration: str
    auth_code: str
    redirect_uri: str


@router.get("/")
async def list_integrations():
    return {"integrations": SUPPORTED_INTEGRATIONS}


@router.post("/connect")
async def connect_integration(body: IntegrationConnect):
    if body.integration not in SUPPORTED_INTEGRATIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown integration: {body.integration}",
        )
    # TODO: exchange auth_code for tokens, store encrypted
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{integration}")
async def disconnect_integration(integration: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{integration}/sync")
async def sync_integration(integration: str, site_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
