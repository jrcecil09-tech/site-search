"""Microsoft OneDrive integration via Microsoft Graph API."""

import httpx

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


async def list_files(access_token: str, folder_path: str = "root") -> list[dict]:
    url = f"{GRAPH_BASE_URL}/me/drive/{folder_path}/children"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


async def upload_file(access_token: str, folder_path: str, name: str, data: bytes) -> dict:
    url = f"{GRAPH_BASE_URL}/me/drive/{folder_path}:/{name}:/content"
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream",
            },
            content=data,
        )
        resp.raise_for_status()
        return resp.json()
