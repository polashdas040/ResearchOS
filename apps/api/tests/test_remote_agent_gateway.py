from dataclasses import dataclass

import pytest

from packages.agents.researchos_agents.remote_gateway import (
    RemoteAgentGateway,
    RemoteAgentRequest,
    RemoteAgentResult,
)


@dataclass
class FakeRemoteTransport:
    result: RemoteAgentResult
    request: RemoteAgentRequest | None = None
    cancelled_task_id: str | None = None

    async def execute(self, request: RemoteAgentRequest) -> RemoteAgentResult:
        self.request = request
        return self.result

    async def cancel(self, task_id: str, auth_token: str) -> RemoteAgentResult:
        self.cancelled_task_id = task_id
        return RemoteAgentResult(status="CANCELLED", summary=f"Cancelled {task_id}")


@pytest.mark.asyncio
async def test_remote_gateway_tags_untrusted_results_and_preserves_agent_card() -> None:
    transport = FakeRemoteTransport(
        RemoteAgentResult(
            status="SUCCEEDED",
            summary="Remote literature search completed.",
            artifact_ids=["remote-artifact-1"],
        )
    )
    gateway = RemoteAgentGateway(
        transport,
        agent_id="literature-specialist",
        endpoint="https://remote.example/agent",
        auth_token="token",
    )

    card = await gateway.agent_card()
    result = await gateway.execute(RemoteAgentRequest(task="Find related papers"))

    assert card.agent_id == "literature-specialist"
    assert card.endpoint == "https://remote.example/agent"
    assert result.untrusted is True
    assert result.agent_id == "literature-specialist"
    assert transport.request is not None
    assert transport.request.auth_token == "token"


@pytest.mark.asyncio
async def test_remote_gateway_returns_timeout_as_structured_failure() -> None:
    transport = FakeRemoteTransport(
        RemoteAgentResult(status="TIMED_OUT", summary="Remote agent timed out")
    )
    gateway = RemoteAgentGateway(
        transport,
        agent_id="specialist",
        endpoint="https://remote.example/agent",
        auth_token="token",
    )

    result = await gateway.execute(RemoteAgentRequest(task="Long task", timeout_seconds=1))

    assert result.status == "TIMED_OUT"
    assert result.untrusted is True


@pytest.mark.asyncio
async def test_remote_gateway_cancels_with_auth_and_untrusted_result() -> None:
    transport = FakeRemoteTransport(
        RemoteAgentResult(status="RUNNING", summary="Remote task started")
    )
    gateway = RemoteAgentGateway(
        transport,
        agent_id="specialist",
        endpoint="https://remote.example/agent",
        auth_token="token",
    )

    result = await gateway.cancel("remote-task-1")

    assert transport.cancelled_task_id == "remote-task-1"
    assert result.status == "CANCELLED"
    assert result.agent_id == "specialist"
    assert result.untrusted is True
