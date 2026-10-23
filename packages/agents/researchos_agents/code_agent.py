from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from packages.execution.researchos_execution.sandbox import (
    RawSandboxResult,
    SandboxRequest,
    SandboxStatus,
)


class CodeAgentStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CodeAgentRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    task: str = Field(min_length=1)
    repository_files: dict[str, str] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=5)


class CodeProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_files: dict[str, str] = Field(default_factory=dict)
    test_files: dict[str, str] = Field(min_length=1)
    execution_code: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class CodeAgentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: CodeAgentStatus
    attempts: int = Field(ge=1)
    source_files: dict[str, str] = Field(default_factory=dict)
    generated_tests: list[str] = Field(default_factory=list)
    summary: str = ""
    last_failure: RawSandboxResult | None = None


class CodeModel(Protocol):
    async def propose(
        self,
        request: CodeAgentRequest,
        previous_failure: RawSandboxResult | None,
    ) -> CodeProposal: ...


class CodeSandbox(Protocol):
    async def execute(self, request: SandboxRequest) -> RawSandboxResult: ...


class CodeAgent:
    def __init__(self, coder: CodeModel, sandbox: CodeSandbox) -> None:
        self._coder = coder
        self._sandbox = sandbox

    async def run(self, request: CodeAgentRequest) -> CodeAgentResult:
        previous_failure: RawSandboxResult | None = None
        last_proposal: CodeProposal | None = None
        for attempt in range(1, request.max_attempts + 1):
            proposal = await self._coder.propose(request, previous_failure)
            last_proposal = proposal
            files = {
                **request.repository_files,
                **proposal.source_files,
                **proposal.test_files,
            }
            execution = await self._sandbox.execute(
                SandboxRequest(code=proposal.execution_code, files=files)
            )
            if execution.status == SandboxStatus.SUCCEEDED:
                return CodeAgentResult(
                    status=CodeAgentStatus.SUCCEEDED,
                    attempts=attempt,
                    source_files=proposal.source_files,
                    generated_tests=sorted(proposal.test_files),
                    summary=proposal.summary,
                )
            previous_failure = execution
        assert last_proposal is not None
        assert previous_failure is not None
        return CodeAgentResult(
            status=CodeAgentStatus.FAILED,
            attempts=request.max_attempts,
            source_files=last_proposal.source_files,
            generated_tests=sorted(last_proposal.test_files),
            summary=last_proposal.summary,
            last_failure=previous_failure,
        )
