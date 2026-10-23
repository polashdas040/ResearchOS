import asyncio
from io import BytesIO
from typing import Protocol
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error


class ObjectStorage(Protocol):
    async def put_object(self, key: str, content: bytes, content_type: str) -> None: ...

    async def get_object(self, key: str) -> bytes | None: ...

    async def delete_object(self, key: str) -> None: ...


class InMemoryObjectStorage:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    async def put_object(self, key: str, content: bytes, content_type: str) -> None:
        self._objects[key] = content

    async def get_object(self, key: str) -> bytes | None:
        return self._objects.get(key)

    async def delete_object(self, key: str) -> None:
        self._objects.pop(key, None)

    @property
    def objects(self) -> dict[str, bytes]:
        return self._objects.copy()


class MinioObjectStorage:
    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        parsed = urlparse(endpoint)
        self._bucket = bucket
        self._client = Minio(
            parsed.netloc or parsed.path,
            access_key=access_key,
            secret_key=secret_key,
            secure=parsed.scheme == "https",
        )
        self._bucket_ready = False
        self._bucket_lock = asyncio.Lock()

    async def put_object(self, key: str, content: bytes, content_type: str) -> None:
        await self._ensure_bucket()
        await asyncio.to_thread(
            self._client.put_object,
            self._bucket,
            key,
            BytesIO(content),
            len(content),
            content_type=content_type,
        )

    async def get_object(self, key: str) -> bytes | None:
        await self._ensure_bucket()
        try:
            response = await asyncio.to_thread(self._client.get_object, self._bucket, key)
            try:
                return await asyncio.to_thread(response.read)
            finally:
                response.close()
                response.release_conn()
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                return None
            raise

    async def delete_object(self, key: str) -> None:
        await self._ensure_bucket()
        await asyncio.to_thread(self._client.remove_object, self._bucket, key)

    async def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        async with self._bucket_lock:
            if self._bucket_ready:
                return
            exists = await asyncio.to_thread(self._client.bucket_exists, self._bucket)
            if not exists:
                await asyncio.to_thread(self._client.make_bucket, self._bucket)
            self._bucket_ready = True
