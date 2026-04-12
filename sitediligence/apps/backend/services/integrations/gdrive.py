"""Google Drive integration — upload/download site files."""

import httpx

GDRIVE_BASE_URL = "https://www.googleapis.com/drive/v3"
GDRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"


async def list_files(access_token: str, folder_id: str | None = None) -> list[dict]:
    params: dict = {"fields": "files(id,name,mimeType,size,modifiedTime)"}
    if folder_id:
        params["q"] = f"'{folder_id}' in parents"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GDRIVE_BASE_URL}/files",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        resp.raise_for_status()
        return resp.json().get("files", [])


async def upload_file(access_token: str, name: str, data: bytes, mime_type: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GDRIVE_UPLOAD_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": mime_type,
                "X-Upload-Content-Type": mime_type,
            },
            params={"uploadType": "media", "name": name},
            content=data,
        )
        resp.raise_for_status()
        return resp.json()
