from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FailureClass(StrEnum):
    TOOL_FAILURE = "TOOL_FAILURE"
    CODE_FAILURE = "CODE_FAILURE"
    RESOURCE_FAILURE = "RESOURCE_FAILURE"
    DATA_FAILURE = "DATA_FAILURE"
    SCIENTIFIC_FAILURE = "SCIENTIFIC_FAILURE"
    EVIDENCE_FAILURE = "EVIDENCE_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"


class RepairAction(StrEnum):
    RETRY = "RETRY"
    REPLAN = "REPLAN"
    DOWNGRADE_OR_REJECT = "DOWNGRADE_OR_REJECT"
    WAIT_FOR_AUTHORIZATION = "WAIT_FOR_AUTHORIZATION"
    STOP = "STOP"


class RepairRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    failure_class: FailureClass
    message: str = Field(min_length=1)
    retry_count: int = Field(ge=0)
    max_retries: int = Field(ge=0)


class RepairResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: RepairAction
    retry_allowed: bool
    reason: str
    suggested_changes: list[str] = Field(default_factory=list)
    preserve_failure: bool = False


class RepairEngine:
    async def decide(self, request: RepairRequest) -> RepairResult:
        if request.failure_class == FailureClass.SCIENTIFIC_FAILURE:
            return RepairResult(
                action=RepairAction.DOWNGRADE_OR_REJECT,
                retry_allowed=False,
                reason="Scientific failure must remain visible and cannot be optimized away.",
                suggested_changes=["Downgrade or reject the hypothesis and preserve the finding."],
                preserve_failure=True,
            )
        if request.failure_class == FailureClass.AUTHORIZATION_FAILURE:
            return RepairResult(
                action=RepairAction.WAIT_FOR_AUTHORIZATION,
                retry_allowed=False,
                reason="Authorization failure requires an explicit policy decision.",
                suggested_changes=["Request approval or revise the tool operation."],
            )
        if request.retry_count >= request.max_retries:
            return RepairResult(
                action=RepairAction.STOP,
                retry_allowed=False,
                reason="Retry limit has been exhausted.",
                preserve_failure=True,
            )
        if request.failure_class == FailureClass.RESOURCE_FAILURE:
            return RepairResult(
                action=RepairAction.RETRY,
                retry_allowed=True,
                reason="Retry with reduced resource demand.",
                suggested_changes=["Reduce batch size or execution parallelism."],
            )
        if request.failure_class in {FailureClass.DATA_FAILURE, FailureClass.EVIDENCE_FAILURE}:
            return RepairResult(
                action=RepairAction.REPLAN,
                retry_allowed=False,
                reason="The inputs require correction before continuing.",
                suggested_changes=["Replan with validated data and evidence inputs."],
            )
        return RepairResult(
            action=RepairAction.RETRY,
            retry_allowed=True,
            reason="Retry the technical operation within the remaining limit.",
            suggested_changes=["Inspect the failure and apply a bounded repair."],
        )
