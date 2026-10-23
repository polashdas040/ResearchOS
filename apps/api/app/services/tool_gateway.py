from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol, TypeVar, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apps.api.app.domain.organizations.models import OrganizationRole
from apps.api.app.services.authorization import AuthorizationService, Principal

ArgumentsT = TypeVar("ArgumentsT", bound=BaseModel)


class ToolGatewayError(Exception):
    """Raised when a tool call is denied or cannot be normalized."""


class ToolApprovalRequired(ToolGatewayError):
    def __init__(self, approval_id: UUID) -> None:
        super().__init__(f"Tool execution requires approval: {approval_id}")
        self.approval_id = approval_id


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONSUMED = "CONSUMED"


class ToolRisk(StrEnum):
    READ_ONLY = "R0_READ_ONLY"
    LOCAL_COMPUTE = "R1_LOCAL_COMPUTE"
    EXPENSIVE_COMPUTE = "R2_EXPENSIVE_COMPUTE"
    EXTERNAL_WRITE = "R3_EXTERNAL_WRITE"
    DESTRUCTIVE = "R4_DESTRUCTIVE"
    FINANCIAL = "R5_FINANCIAL"


class ToolContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    principal: Principal
    organization_id: UUID
    project_id: UUID
    research_run_id: UUID | None = None
    task_id: UUID | None = None
    sandboxed: bool = False
    available_budget: float | None = Field(default=None, ge=0)


class ToolResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str = Field(min_length=1)
    content: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class Tool(Protocol[ArgumentsT]):
    name: str
    risk_level: ToolRisk
    arguments_model: type[ArgumentsT]

    async def execute(
        self,
        context: ToolContext,
        arguments: ArgumentsT,
    ) -> ToolResult | dict[str, Any]:
        """Execute a policy-approved tool call."""


class ToolAuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    tool_name: str
    organization_id: UUID
    project_id: UUID
    user_id: UUID
    research_run_id: UUID | None
    task_id: UUID | None
    risk_level: ToolRisk
    status: str
    approval_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolApproval(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    tool_name: str
    arguments: dict[str, Any]
    organization_id: UUID
    project_id: UUID
    user_id: UUID
    research_run_id: UUID | None
    task_id: UUID | None
    risk_level: ToolRisk
    status: ApprovalStatus = ApprovalStatus.PENDING
    explicit: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None


class InMemoryToolApprovalStore:
    def __init__(self) -> None:
        self.approvals: dict[UUID, ToolApproval] = {}

    async def create(self, approval: ToolApproval) -> ToolApproval:
        self.approvals[approval.id] = approval
        return approval

    async def get(self, approval_id: UUID) -> ToolApproval:
        try:
            return self.approvals[approval_id]
        except KeyError as exc:
            raise ToolGatewayError("Tool approval not found") from exc

    async def save(self, approval: ToolApproval) -> ToolApproval:
        self.approvals[approval.id] = approval
        return approval

    async def find_pending(
        self,
        organization_id: UUID,
        project_id: UUID,
        user_id: UUID,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolApproval | None:
        for approval in self.approvals.values():
            if (
                approval.status == ApprovalStatus.PENDING
                and approval.organization_id == organization_id
                and approval.project_id == project_id
                and approval.user_id == user_id
                and approval.tool_name == tool_name
                and approval.arguments == arguments
            ):
                return approval
        return None


class InMemoryToolAuditSink:
    def __init__(self) -> None:
        self.events: list[ToolAuditEvent] = []

    async def record(self, event: ToolAuditEvent) -> None:
        self.events.append(event)


class ToolPolicy:
    def __init__(self, authorization_service: AuthorizationService) -> None:
        self._authorization_service = authorization_service

    async def authorize(
        self,
        context: ToolContext,
        tool: Tool[Any],
        approval: ToolApproval | None = None,
    ) -> None:
        allowed_org = await self._authorization_service.can_access_organization(
            context.principal,
            context.organization_id,
        )
        if not allowed_org:
            raise ToolGatewayError("Tool context is outside the principal organization")
        if tool.risk_level == ToolRisk.READ_ONLY:
            return
        if tool.risk_level == ToolRisk.LOCAL_COMPUTE:
            self._require_researcher_access(context)
            if not context.sandboxed:
                raise ToolGatewayError("Local compute tools require a sandboxed context")
            return
        if tool.risk_level == ToolRisk.EXPENSIVE_COMPUTE:
            self._require_researcher_access(context)
            estimated_cost = _estimated_cost(tool)
            if context.available_budget is None or context.available_budget < estimated_cost:
                raise ToolGatewayError("Tool execution exceeds the available budget")
            return
        if approval is None:
            raise ToolGatewayError(f"Tool risk level requires approval: {tool.risk_level}")
        if approval.status != ApprovalStatus.APPROVED:
            if approval.status == ApprovalStatus.REJECTED:
                raise ToolGatewayError("Tool approval was rejected")
            if approval.status == ApprovalStatus.CONSUMED:
                raise ToolGatewayError("Tool approval was already consumed")
            raise ToolGatewayError(f"Tool approval is not approved: {approval.status}")
        if tool.risk_level in {ToolRisk.DESTRUCTIVE, ToolRisk.FINANCIAL} and not approval.explicit:
            raise ToolGatewayError("Tool execution requires explicit approval")

    async def authorize_approval_request(self, context: ToolContext) -> None:
        allowed_org = await self._authorization_service.can_access_organization(
            context.principal,
            context.organization_id,
        )
        if not allowed_org:
            raise ToolGatewayError("Tool context is outside the principal organization")
        self._require_researcher_access(context)

    @staticmethod
    def _require_researcher_access(context: ToolContext) -> None:
        if not _has_researcher_access(context.principal):
            raise ToolGatewayError("Tool execution requires researcher access")


class ToolGateway:
    def __init__(
        self,
        tools: list[Tool[Any]],
        policy: ToolPolicy,
        audit_sink: InMemoryToolAuditSink,
        approval_store: InMemoryToolApprovalStore | None = None,
    ) -> None:
        self._tools = _index_tools(tools)
        self._policy = policy
        self._audit_sink = audit_sink
        self._approval_store = approval_store or InMemoryToolApprovalStore()

    def describe_tools(self) -> list[tuple[str, ToolRisk, dict[str, Any]]]:
        return [
            (tool.name, tool.risk_level, tool.arguments_model.model_json_schema())
            for tool in self._tools.values()
        ]

    async def request_approval(
        self,
        context: ToolContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolApproval:
        tool = self._get_tool(tool_name)
        typed_arguments = _validate_arguments(tool, arguments)
        if tool.risk_level not in {
            ToolRisk.EXTERNAL_WRITE,
            ToolRisk.DESTRUCTIVE,
            ToolRisk.FINANCIAL,
        }:
            raise ToolGatewayError("This tool does not require approval")
        await self._policy.authorize_approval_request(context)
        existing = await self._approval_store.find_pending(
            organization_id=context.organization_id,
            project_id=context.project_id,
            user_id=context.principal.user_id,
            tool_name=tool.name,
            arguments=typed_arguments.model_dump(mode="json"),
        )
        if existing is not None:
            return existing
        approval = ToolApproval(
            tool_name=tool.name,
            arguments=typed_arguments.model_dump(mode="json"),
            organization_id=context.organization_id,
            project_id=context.project_id,
            user_id=context.principal.user_id,
            research_run_id=context.research_run_id,
            task_id=context.task_id,
            risk_level=tool.risk_level,
        )
        created = await self._approval_store.create(approval)
        await self._audit_sink.record(
            self._approval_audit_event(context, created, "APPROVAL_REQUESTED")
        )
        return created

    async def approve(
        self,
        context: ToolContext,
        approval_id: UUID,
        *,
        explicit: bool = False,
    ) -> ToolApproval:
        approval = await self._get_matching_approval(context, approval_id)
        if approval.status not in {ApprovalStatus.PENDING, ApprovalStatus.APPROVED}:
            raise ToolGatewayError(f"Tool approval is not pending: {approval.status}")
        updated = approval.model_copy(
            update={
                "status": ApprovalStatus.APPROVED,
                "explicit": approval.explicit or explicit,
                "decided_at": datetime.now(UTC),
            }
        )
        await self._audit_sink.record(
            self._approval_audit_event(context, updated, "APPROVAL_APPROVED")
        )
        return await self._approval_store.save(updated)

    async def resume(self, context: ToolContext, approval_id: UUID) -> ToolResult:
        approval = await self._get_matching_approval(context, approval_id)
        return await self.execute(
            context,
            approval.tool_name,
            approval.arguments,
            approval_id=approval.id,
        )

    async def reject(self, context: ToolContext, approval_id: UUID) -> ToolApproval:
        approval = await self._get_matching_approval(context, approval_id)
        if approval.status != ApprovalStatus.PENDING:
            raise ToolGatewayError(f"Tool approval is not pending: {approval.status}")
        updated = approval.model_copy(
            update={"status": ApprovalStatus.REJECTED, "decided_at": datetime.now(UTC)}
        )
        await self._audit_sink.record(
            self._approval_audit_event(context, updated, "APPROVAL_REJECTED")
        )
        return await self._approval_store.save(updated)

    async def execute(
        self,
        context: ToolContext,
        tool_name: str,
        arguments: dict[str, Any],
        approval_id: UUID | None = None,
    ) -> ToolResult:
        tool = self._get_tool(tool_name)
        typed_arguments = _validate_arguments(tool, arguments)
        approval: ToolApproval | None = None
        if tool.risk_level in {
            ToolRisk.EXTERNAL_WRITE,
            ToolRisk.DESTRUCTIVE,
            ToolRisk.FINANCIAL,
        }:
            if approval_id is None:
                approval = await self.request_approval(context, tool_name, arguments)
                await self._audit_sink.record(
                    self._approval_audit_event(context, approval, "WAITING_APPROVAL")
                )
                raise ToolApprovalRequired(approval.id)
            approval = await self._get_matching_approval(context, approval_id)
            if approval.arguments != typed_arguments.model_dump(mode="json"):
                raise ToolGatewayError("Tool approval arguments do not match context")
        await self._policy.authorize(context, tool, approval)
        if approval is not None:
            approval = await self._approval_store.save(
                approval.model_copy(update={"status": ApprovalStatus.CONSUMED})
            )
        result = _normalize_result(await tool.execute(context, typed_arguments))
        await self._audit_sink.record(
            ToolAuditEvent(
                tool_name=tool.name,
                organization_id=context.organization_id,
                project_id=context.project_id,
                user_id=context.principal.user_id,
                research_run_id=context.research_run_id,
                task_id=context.task_id,
                risk_level=tool.risk_level,
                status=result.status,
                approval_id=approval.id if approval is not None else None,
            )
        )
        return result

    def _get_tool(self, tool_name: str) -> Tool[Any]:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolGatewayError(f"Unknown tool: {tool_name}")
        return tool

    async def _get_matching_approval(
        self,
        context: ToolContext,
        approval_id: UUID,
    ) -> ToolApproval:
        approval = await self._approval_store.get(approval_id)
        if (
            approval.organization_id != context.organization_id
            or approval.project_id != context.project_id
            or approval.user_id != context.principal.user_id
            or approval.research_run_id != context.research_run_id
            or approval.task_id != context.task_id
        ):
            raise ToolGatewayError("Tool approval context does not match")
        return approval

    def _approval_audit_event(
        self,
        context: ToolContext,
        approval: ToolApproval,
        status: str,
    ) -> ToolAuditEvent:
        return ToolAuditEvent(
            tool_name=approval.tool_name,
            organization_id=context.organization_id,
            project_id=context.project_id,
            user_id=context.principal.user_id,
            research_run_id=context.research_run_id,
            task_id=context.task_id,
            risk_level=approval.risk_level,
            status=status,
            approval_id=approval.id,
        )


def _index_tools(tools: list[Tool[Any]]) -> dict[str, Tool[Any]]:
    indexed: dict[str, Tool[Any]] = {}
    for tool in tools:
        if tool.name in indexed:
            raise ToolGatewayError(f"Duplicate tool name: {tool.name}")
        indexed[tool.name] = tool
    return indexed


def _validate_arguments[T: BaseModel](tool: Tool[T], arguments: dict[str, Any]) -> T:
    try:
        return tool.arguments_model.model_validate(arguments)
    except ValidationError as exc:
        raise ToolGatewayError(f"Invalid arguments for tool {tool.name}") from exc


def _normalize_result(result: ToolResult | dict[str, Any]) -> ToolResult:
    if isinstance(result, ToolResult):
        return result
    return ToolResult(status="SUCCEEDED", content=result)


def _estimated_cost(tool: Tool[Any]) -> float:
    declared_cost = getattr(tool, "estimated_cost", 0.0)
    if not isinstance(declared_cost, int | float) or declared_cost < 0:
        raise ToolGatewayError("Tool estimated cost must be a non-negative number")
    return float(declared_cost)


def _has_researcher_access(principal: Principal) -> bool:
    allowed_roles = {
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
        OrganizationRole.RESEARCHER,
    }
    return any(role in allowed_roles for role in principal.roles)
