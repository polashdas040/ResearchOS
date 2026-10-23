from typing import Any
from uuid import uuid4

import pytest
from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.organizations.models import OrganizationRole
from apps.api.app.services.authorization import AuthorizationService
from apps.api.app.services.tool_gateway import (
    ApprovalStatus,
    InMemoryToolApprovalStore,
    InMemoryToolAuditSink,
    Tool,
    ToolApprovalRequired,
    ToolContext,
    ToolGateway,
    ToolGatewayError,
    ToolPolicy,
    ToolResult,
    ToolRisk,
)


class SearchArguments(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str = Field(min_length=1)


class SearchTool:
    name = "document.search"
    risk_level = ToolRisk.READ_ONLY
    arguments_model = SearchArguments

    async def execute(self, context: ToolContext, arguments: SearchArguments) -> ToolResult:
        return ToolResult(
            status="SUCCEEDED",
            content={"matches": [arguments.query], "project_id": str(context.project_id)},
        )


class BrokenTool:
    name = "broken.tool"
    risk_level = ToolRisk.READ_ONLY
    arguments_model = SearchArguments

    async def execute(self, context: ToolContext, arguments: SearchArguments) -> dict[str, Any]:
        return {"raw": arguments.query, "project_id": str(context.project_id)}


class ExternalWriteTool(SearchTool):
    name = "external.write"
    risk_level = ToolRisk.EXTERNAL_WRITE


class FinancialTool(SearchTool):
    name = "billing.charge"
    risk_level = ToolRisk.FINANCIAL


class ExpensiveComputeTool(SearchTool):
    name = "experiment.run"
    risk_level = ToolRisk.EXPENSIVE_COMPUTE
    estimated_cost = 25.0


class DestructiveTool(SearchTool):
    name = "project.delete"
    risk_level = ToolRisk.DESTRUCTIVE


def _context(role: OrganizationRole = OrganizationRole.RESEARCHER) -> ToolContext:
    organization_id = uuid4()
    return ToolContext(
        principal=AuthorizationService().build_principal(
            user_id=uuid4(),
            organization_id=organization_id,
            roles=[role],
        ),
        organization_id=organization_id,
        project_id=uuid4(),
        research_run_id=uuid4(),
        task_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_gateway_validates_arguments_and_returns_normalized_result() -> None:
    audit_sink = InMemoryToolAuditSink()
    gateway = ToolGateway(
        tools=[SearchTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=audit_sink,
    )

    result = await gateway.execute(
        _context(),
        "document.search",
        {"query": "amyloid PET"},
    )

    assert result.status == "SUCCEEDED"
    assert result.content["matches"] == ["amyloid PET"]
    assert len(audit_sink.events) == 1
    assert audit_sink.events[0].tool_name == "document.search"
    assert audit_sink.events[0].status == "SUCCEEDED"


@pytest.mark.asyncio
async def test_gateway_rejects_invalid_tool_arguments() -> None:
    gateway = ToolGateway(
        tools=[SearchTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )

    with pytest.raises(ToolGatewayError):
        await gateway.execute(_context(), "document.search", {"query": ""})


@pytest.mark.asyncio
async def test_gateway_blocks_unknown_tool() -> None:
    gateway = ToolGateway(
        tools=[SearchTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )

    with pytest.raises(ToolGatewayError):
        await gateway.execute(_context(), "missing.tool", {"query": "x"})


@pytest.mark.asyncio
async def test_gateway_authorizes_organization_before_execution() -> None:
    context = _context()
    other_organization_context = context.model_copy(update={"organization_id": uuid4()})
    gateway = ToolGateway(
        tools=[SearchTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )

    with pytest.raises(ToolGatewayError):
        await gateway.execute(other_organization_context, "document.search", {"query": "x"})


@pytest.mark.asyncio
async def test_gateway_blocks_viewer_from_local_compute_tool() -> None:
    class ComputeTool(SearchTool):
        name = "python.execute"
        risk_level = ToolRisk.LOCAL_COMPUTE

    gateway = ToolGateway(
        tools=[ComputeTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )

    with pytest.raises(ToolGatewayError):
        await gateway.execute(_context(OrganizationRole.VIEWER), "python.execute", {"query": "x"})


@pytest.mark.asyncio
async def test_local_compute_requires_a_sandboxed_context() -> None:
    class ComputeTool(SearchTool):
        name = "python.execute"
        risk_level = ToolRisk.LOCAL_COMPUTE

    gateway = ToolGateway(
        tools=[ComputeTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )
    context = _context()

    with pytest.raises(ToolGatewayError, match="sandbox"):
        await gateway.execute(context, "python.execute", {"query": "x"})

    result = await gateway.execute(
        context.model_copy(update={"sandboxed": True}),
        "python.execute",
        {"query": "x"},
    )

    assert result.status == "SUCCEEDED"


@pytest.mark.asyncio
async def test_expensive_compute_requires_sufficient_budget() -> None:
    gateway = ToolGateway(
        tools=[ExpensiveComputeTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )
    context = _context().model_copy(update={"available_budget": 25.0})

    result = await gateway.execute(context, "experiment.run", {"query": "x"})
    assert result.status == "SUCCEEDED"

    with pytest.raises(ToolGatewayError, match="budget"):
        await gateway.execute(
            context.model_copy(update={"available_budget": 24.0}),
            "experiment.run",
            {"query": "x"},
        )


@pytest.mark.asyncio
async def test_high_risk_tool_requires_approval_and_executes_after_approval() -> None:
    context = _context()
    approvals = InMemoryToolApprovalStore()
    audit_sink = InMemoryToolAuditSink()
    gateway = ToolGateway(
        tools=[ExternalWriteTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=audit_sink,
        approval_store=approvals,
    )

    approval = await gateway.request_approval(context, "external.write", {"query": "publish"})

    assert approval.status == ApprovalStatus.PENDING
    with pytest.raises(ToolApprovalRequired) as error:
        await gateway.execute(context, "external.write", {"query": "publish"})
    assert error.value.approval_id == approval.id
    assert [event.status for event in audit_sink.events] == [
        "APPROVAL_REQUESTED",
        "WAITING_APPROVAL",
    ]

    approved = await gateway.approve(context, approval.id)
    assert approved.status == ApprovalStatus.APPROVED
    result = await gateway.resume(context, approval.id)

    assert result.status == "SUCCEEDED"
    assert (await approvals.get(approval.id)).status == ApprovalStatus.CONSUMED


@pytest.mark.asyncio
async def test_financial_tool_requires_explicit_approval_and_audits_decision() -> None:
    context = _context()
    audit_sink = InMemoryToolAuditSink()
    gateway = ToolGateway(
        tools=[FinancialTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=audit_sink,
        approval_store=InMemoryToolApprovalStore(),
    )

    approval = await gateway.request_approval(context, "billing.charge", {"query": "100"})
    await gateway.reject(context, approval.id)

    with pytest.raises(ToolGatewayError, match="rejected"):
        await gateway.execute(
            context,
            "billing.charge",
            {"query": "100"},
            approval_id=approval.id,
        )

    assert audit_sink.events[-1].status == "APPROVAL_REJECTED"


@pytest.mark.asyncio
async def test_destructive_tool_requires_explicit_approval() -> None:
    context = _context()
    gateway = ToolGateway(
        tools=[DestructiveTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
        approval_store=InMemoryToolApprovalStore(),
    )
    approval = await gateway.request_approval(context, "project.delete", {"query": "confirm"})

    await gateway.approve(context, approval.id)
    with pytest.raises(ToolGatewayError, match="explicit"):
        await gateway.execute(
            context,
            "project.delete",
            {"query": "confirm"},
            approval_id=approval.id,
        )

    await gateway.approve(context, approval.id, explicit=True)
    result = await gateway.execute(
        context,
        "project.delete",
        {"query": "confirm"},
        approval_id=approval.id,
    )
    assert result.status == "SUCCEEDED"


@pytest.mark.asyncio
async def test_approval_cannot_be_replayed_or_used_for_another_context() -> None:
    context = _context()
    gateway = ToolGateway(
        tools=[ExternalWriteTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
        approval_store=InMemoryToolApprovalStore(),
    )
    approval = await gateway.request_approval(context, "external.write", {"query": "publish"})
    await gateway.approve(context, approval.id)

    result = await gateway.execute(
        context,
        "external.write",
        {"query": "publish"},
        approval_id=approval.id,
    )
    assert result.status == "SUCCEEDED"

    with pytest.raises(ToolGatewayError, match="consumed"):
        await gateway.execute(
            context,
            "external.write",
            {"query": "publish"},
            approval_id=approval.id,
        )

    other_context = context.model_copy(update={"project_id": uuid4()})
    with pytest.raises(ToolGatewayError, match="context"):
        await gateway.execute(
            other_context,
            "external.write",
            {"query": "publish"},
            approval_id=approval.id,
        )


@pytest.mark.asyncio
async def test_gateway_wraps_non_tool_result_as_normalized_result() -> None:
    gateway = ToolGateway(
        tools=[BrokenTool()],
        policy=ToolPolicy(authorization_service=AuthorizationService()),
        audit_sink=InMemoryToolAuditSink(),
    )

    result = await gateway.execute(_context(), "broken.tool", {"query": "x"})

    assert result.status == "SUCCEEDED"
    assert result.content["raw"] == "x"


def test_duplicate_tool_names_are_rejected() -> None:
    with pytest.raises(ToolGatewayError):
        ToolGateway(
            tools=[SearchTool(), SearchTool()],
            policy=ToolPolicy(authorization_service=AuthorizationService()),
            audit_sink=InMemoryToolAuditSink(),
        )


def test_tool_protocol_accepts_compatible_tools() -> None:
    tool: Tool[SearchArguments] = SearchTool()

    assert tool.name == "document.search"
