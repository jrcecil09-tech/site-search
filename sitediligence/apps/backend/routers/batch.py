"""Batch router — bulk operations and watch-folder processing."""

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

router = APIRouter()


class BatchQueryRequest(BaseModel):
    site_ids: list[str]
    query_types: list[str]
    priority: str = "normal"


class BatchExportRequest(BaseModel):
    site_ids: list[str]
    format: str
    zip_output: bool = True


@router.post("/queries", status_code=status.HTTP_202_ACCEPTED)
async def batch_run_queries(body: BatchQueryRequest):
    # TODO: enqueue batch Celery workflow
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/exports", status_code=status.HTTP_202_ACCEPTED)
async def batch_export(body: BatchExportRequest):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/upload-folder", status_code=status.HTTP_202_ACCEPTED)
async def upload_folder(site_id: str, files: list[UploadFile]):
    # TODO: ingest multiple files, detect format, parse geometries
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/jobs/{job_id}")
async def get_batch_job(job_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
