"""Exports router — generate PDF, CAD, GeoJSON, and GIS package exports."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

EXPORT_FORMATS = ["pdf", "docx", "xlsx", "geojson", "kml", "shapefile", "dxf", "qgis", "arcgis"]


class ExportRequest(BaseModel):
    site_id: str
    format: str
    include_attachments: bool = True
    include_layers: bool = True
    include_observations: bool = True
    crs: int = 4326
    page_size: str = "letter"
    orientation: str = "portrait"


@router.get("/formats")
async def list_export_formats():
    return {"formats": EXPORT_FORMATS}


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_export(body: ExportRequest):
    if body.format not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported format: {body.format}",
        )
    # TODO: enqueue Celery export task, return job_id
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{job_id}/status")
async def get_export_status(job_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{job_id}/download")
async def download_export(job_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
