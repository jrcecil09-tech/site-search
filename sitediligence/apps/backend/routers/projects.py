"""Projects router — CRUD for projects and sites."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = []


class SiteCreate(BaseModel):
    name: str
    description: str = ""
    coordinates: tuple[float, float] | None = None
    address: dict | None = None


@router.get("/")
async def list_projects():
    # TODO: query DB, filter by team/user
    return {"projects": []}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate):
    # TODO: persist to DB
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{project_id}")
async def get_project(project_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.patch("/{project_id}")
async def update_project(project_id: UUID, body: ProjectCreate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# ── Sites ─────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/sites")
async def list_sites(project_id: UUID):
    return {"sites": []}


@router.post("/{project_id}/sites", status_code=status.HTTP_201_CREATED)
async def create_site(project_id: UUID, body: SiteCreate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{project_id}/sites/{site_id}")
async def get_site(project_id: UUID, site_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
