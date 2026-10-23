from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.services.tool_gateway import (
    ToolContext,
    ToolGateway,
    ToolGatewayError,
    ToolResult,
    ToolRisk,
)


class MCPToolDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    risk_level: ToolRisk
    input_schema: dict[str, Any]


class MCPToolCall(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPGateway:
    def __init__(self, gateway: ToolGateway, context: ToolContext) -> None:
        self._gateway = gateway
        self._context = context

    async def list_tools(self) -> list[MCPToolDescriptor]:
        return [
            MCPToolDescriptor(name=name, risk_level=risk, input_schema=schema)
            for name, risk, schema in self._gateway.describe_tools()
        ]

    async def call_tool(self, call: MCPToolCall) -> ToolResult:
        known_tools = {name for name, _, _ in self._gateway.describe_tools()}
        if call.name not in known_tools:
            raise ValueError(f"unknown tool: {call.name}")
        try:
            return await self._gateway.execute(self._context, call.name, call.arguments)
        except ToolGatewayError:
            raise
