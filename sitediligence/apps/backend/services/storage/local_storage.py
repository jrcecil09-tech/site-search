"""Local filesystem storage backend."""

import os
from pathlib import Path


class LocalStorage:
    def __init__(self, base_path: str) -> None:
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        dest = self.base / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return str(dest)

    async def get(self, key: str) -> bytes:
        return (self.base / key).read_bytes()

    async def delete(self, key: str) -> None:
        path = self.base / key
        if path.exists():
            path.unlink()

    async def list(self, prefix: str) -> list[str]:
        root = self.base / prefix
        if not root.exists():
            return []
        return [str(p.relative_to(self.base)) for p in root.rglob("*") if p.is_file()]

    async def url(self, key: str, expires_seconds: int = 3600) -> str:
        # For local storage, return a relative path (front-end resolves via /api/v1/storage)
        return f"/api/v1/storage/files/{key}"
