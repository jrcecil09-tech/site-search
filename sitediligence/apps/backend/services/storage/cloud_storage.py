"""Cloud storage backends: S3, Azure Blob, Google Cloud Storage."""

from config.settings import get_settings

settings = get_settings()


class S3Storage:
    """Amazon S3 / S3-compatible (Cloudflare R2, MinIO) storage."""

    def __init__(self) -> None:
        import boto3
        kwargs: dict = {
            "aws_access_key_id": settings.s3_access_key_id,
            "aws_secret_access_key": settings.s3_secret_access_key,
            "region_name": settings.s3_region,
        }
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.s3_bucket

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        return key

    async def get(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    async def list(self, prefix: str) -> list[str]:
        resp = self._client.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
        return [obj["Key"] for obj in resp.get("Contents", [])]

    async def url(self, key: str, expires_seconds: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )


class AzureStorage:
    """Azure Blob Storage backend."""

    def __init__(self) -> None:
        from azure.storage.blob import BlobServiceClient  # type: ignore
        self._client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self._container = settings.azure_storage_container

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        blob = self._client.get_blob_client(container=self._container, blob=key)
        blob.upload_blob(data, overwrite=True, content_settings={"content_type": content_type})
        return key

    async def get(self, key: str) -> bytes:
        blob = self._client.get_blob_client(container=self._container, blob=key)
        return blob.download_blob().readall()

    async def delete(self, key: str) -> None:
        self._client.get_blob_client(container=self._container, blob=key).delete_blob()

    async def list(self, prefix: str) -> list[str]:
        container = self._client.get_container_client(self._container)
        return [b.name for b in container.list_blobs(name_starts_with=prefix)]

    async def url(self, key: str, expires_seconds: int = 3600) -> str:
        # TODO: generate SAS URL
        return f"https://{self._container}.blob.core.windows.net/{key}"


class GCSStorage:
    """Google Cloud Storage backend."""

    def __init__(self) -> None:
        from google.cloud import storage as gcs  # type: ignore
        self._client = gcs.Client()
        self._bucket = self._client.bucket(settings.gcs_bucket)

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        blob = self._bucket.blob(key)
        blob.upload_from_string(data, content_type=content_type)
        return key

    async def get(self, key: str) -> bytes:
        return self._bucket.blob(key).download_as_bytes()

    async def delete(self, key: str) -> None:
        self._bucket.blob(key).delete()

    async def list(self, prefix: str) -> list[str]:
        return [b.name for b in self._client.list_blobs(self._bucket, prefix=prefix)]

    async def url(self, key: str, expires_seconds: int = 3600) -> str:
        import datetime
        blob = self._bucket.blob(key)
        return blob.generate_signed_url(expiration=datetime.timedelta(seconds=expires_seconds))
