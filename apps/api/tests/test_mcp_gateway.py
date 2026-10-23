from dataclasses import dataclass
from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

from apps.api.app.services.authorization import AuthorizationService
from apps.api.app.services.tool_gateway import (
    InMemoryToolAuditSink,
    ToolContext,
    ToolGateway,
    ToolPolicy,
    ToolResult,
    ToolRisk,
)
from packages.tools.researchos_tools.mcp import MCPGateway, MCPToolCall, MCPToolDescriptor


class Arguments(BaseModel):
    query: str


@dataclass
class SearchTool:
    name: str = "document.search"
    risk_level: ToolRisk = ToolRisk.READ_ONLY
    arguments_model: type[Arguments] = Arguments

    async def execute(self, context: ToolContext, arguments: Arguments) -> ToolResult:
        return ToolResult(status="SUCCEEDED", content={"query": arguments.query})


def context() -> ToolContext:
    organization_id = uuid4()
    return ToolContext(
        principal=AuthorizationService().build_principal(
            user_id=uuid4(), organization_id=organization_id, roles=[]
        ),
        organization_id=organization_id,
        project_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_mcp_gateway_discovers_typed_tools_and_executes_through_policy_gateway() -> None:
    gateway = ToolGateway(
        tools=[SearchTool()],
        policy=ToolPolicy(AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )
    adapter = MCPGateway(gateway, context())

    tools = await adapter.list_tools()
    result = await adapter.call_tool(
        MCPToolCall(name="document.search", arguments={"query": "MRI"})
    )

    assert tools[0].name == "document.search"
    assert tools[0].risk_level == ToolRisk.READ_ONLY
    assert result.content["query"] == "MRI"


@pytest.mark.asyncio
async def test_mcp_gateway_rejects_unknown_tool() -> None:
    gateway = ToolGateway(
        tools=[SearchTool()],
        policy=ToolPolicy(AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )
    adapter = MCPGateway(gateway, context())

    with pytest.raises(ValueError, match="unknown tool"):
        await adapter.call_tool(MCPToolCall(name="missing.tool", arguments={}))


def test_mcp_tool_descriptor_requires_non_empty_name() -> None:
    with pytest.raises(ValidationError):
        MCPToolDescriptor(name="", risk_level=ToolRisk.READ_ONLY, input_schema={})
