"""Hosted SiteDiligence storage backend (managed cloud service)."""

import httpx

from config.settings import get_settings

settings = get_settings()


class HostedStorage:
    """Delegates storage to the SiteDiligence hosted service API."""

    def __init__(self) -> None:
        self._base = settings.hosted_api_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.hosted_api_key}"}

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = client.post(
                f"{self._base}/storage/objects",
                headers={**self._headers, "Content-Type": content_type, "X-Object-Key": key},
                content=data,
            )
            resp.raise_for_status()
        return key

    async def get(self, key: str) -> bytes:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base}/storage/objects/{key}", headers=self._headers)
            resp.raise_for_status()
            return resp.content

    async def delete(self, key: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{self._base}/storage/objects/{key}", headers=self._headers)
            resp.raise_for_status()

    async def list(self, prefix: str) -> list[str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base}/storage/objects", params={"prefix": prefix}, headers=self._headers
            )
            resp.raise_for_status()
            return resp.json().get("keys", [])

    async def url(self, key: str, expires_seconds: int = 3600) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base}/storage/signed-url",
                json={"key": key, "expires_seconds": expires_seconds},
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()["url"]
