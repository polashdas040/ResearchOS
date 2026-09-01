from typing import Protocol


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
