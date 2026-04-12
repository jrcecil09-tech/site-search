"""Mobile router — sync, offline bundles, and field observations."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class ObservationCreate(BaseModel):
    site_id: str
    category_id: str
    title: str
    description: str = ""
    coordinates: tuple[float, float] | None = None
    severity: str = "info"
    tags: list[str] = []
    custom_fields: dict = {}


class SyncRequest(BaseModel):
    device_id: str
    last_sync_at: str | None = None
    observations: list[ObservationCreate] = []


@router.post("/sync")
async def sync(body: SyncRequest):
    # TODO: upsert observations, return delta since last_sync_at
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/offline-bundle/{site_id}")
async def get_offline_bundle(site_id: str):
    # TODO: return compressed GeoJSON + config for offline use
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/observations", status_code=status.HTTP_201_CREATED)
async def create_observation(body: ObservationCreate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/observations/{site_id}")
async def list_observations(site_id: str):
    return {"observations": []}
