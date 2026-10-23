from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class RemoteAgentCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    agent_id: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)


class RemoteAgentRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    task: str = Field(min_length=1)
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    auth_token: str | None = None


class RemoteAgentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str = Field(min_length=1)
    summary: str = ""
    artifact_ids: list[str] = Field(default_factory=list)
    agent_id: str = ""
    untrusted: bool = True


class RemoteAgentTransport(Protocol):
    async def execute(self, request: RemoteAgentRequest) -> RemoteAgentResult: ...

    async def cancel(self, task_id: str, auth_token: str) -> RemoteAgentResult: ...


class RemoteAgentGateway:
    def __init__(
        self,
        transport: RemoteAgentTransport,
        agent_id: str,
        endpoint: str,
        auth_token: str,
    ) -> None:
        if not auth_token:
            raise ValueError("remote agent authentication is required")
        self._transport = transport
        self._card = RemoteAgentCard(agent_id=agent_id, endpoint=endpoint)
        self._auth_token = auth_token

    async def agent_card(self) -> RemoteAgentCard:
        return self._card

    async def execute(self, request: RemoteAgentRequest) -> RemoteAgentResult:
        authenticated = request.model_copy(update={"auth_token": self._auth_token})
        result = await self._transport.execute(authenticated)
        return result.model_copy(
            update={"agent_id": self._card.agent_id, "untrusted": True}
        )

    async def cancel(self, task_id: str) -> RemoteAgentResult:
        if not task_id.strip():
            raise ValueError("remote task id cannot be empty")
        result = await self._transport.cancel(task_id, self._auth_token)
        return result.model_copy(
            update={"agent_id": self._card.agent_id, "untrusted": True}
        )
