"""StorageManager — routes operations to the configured backend."""

from __future__ import annotations

from config.settings import get_settings

settings = get_settings()


class StorageManager:
    """Unified interface over local/S3/Azure/GCS/hosted backends."""

    def __init__(self) -> None:
        self._backend = self._init_backend()

    def _init_backend(self):
        backend = settings.storage_backend
        if backend == "local":
            from services.storage.local_storage import LocalStorage
            return LocalStorage(settings.storage_local_path)
        if backend == "s3":
            from services.storage.cloud_storage import S3Storage
            return S3Storage()
        if backend == "azure":
            from services.storage.cloud_storage import AzureStorage
            return AzureStorage()
        if backend == "gcs":
            from services.storage.cloud_storage import GCSStorage
            return GCSStorage()
        if backend == "hosted":
            from services.storage.hosted_storage import HostedStorage
            return HostedStorage()
        raise ValueError(f"Unknown storage backend: {backend}")

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        return await self._backend.put(key, data, content_type)

    async def get(self, key: str) -> bytes:
        return await self._backend.get(key)

    async def delete(self, key: str) -> None:
        return await self._backend.delete(key)

    async def list(self, prefix: str) -> list[str]:
        return await self._backend.list(prefix)

    async def url(self, key: str, expires_seconds: int = 3600) -> str:
        return await self._backend.url(key, expires_seconds)


_manager: StorageManager | None = None


def get_storage_manager() -> StorageManager:
    global _manager
    if _manager is None:
        _manager = StorageManager()
    return _manager
