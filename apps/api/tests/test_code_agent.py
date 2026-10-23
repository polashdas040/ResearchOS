from dataclasses import dataclass

import pytest

from packages.agents.researchos_agents.code_agent import (
    CodeAgent,
    CodeAgentRequest,
    CodeProposal,
)
from packages.execution.researchos_execution.sandbox import (
    RawSandboxResult,
    SandboxStatus,
)


@dataclass
class FakeCoder:
    proposals: list[CodeProposal]
    requests: list[CodeAgentRequest]
    failures: list[RawSandboxResult | None]

    async def propose(
        self,
        request: CodeAgentRequest,
        previous_failure: RawSandboxResult | None,
    ) -> CodeProposal:
        self.requests.append(request)
        self.failures.append(previous_failure)
        return self.proposals.pop(0)


@dataclass
class FakeSandbox:
    results: list[RawSandboxResult]
    requests: list[object]

    async def execute(self, request: object) -> RawSandboxResult:
        self.requests.append(request)
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_code_agent_generates_tests_and_executes_in_sandbox() -> None:
    coder = FakeCoder(
        proposals=[
            CodeProposal(
                source_files={"solution.py": "def answer(): return 42"},
                test_files={"test_solution.py": "assert answer() == 42"},
                execution_code="from solution import answer\nprint(answer())",
                summary="Implemented the answer function.",
            )
        ],
        requests=[],
        failures=[],
    )
    sandbox = FakeSandbox(
        results=[
            RawSandboxResult(
                status=SandboxStatus.SUCCEEDED,
                stdout="42\n",
                stderr="",
                exit_code=0,
                created_files=[],
                runtime_seconds=0.1,
            )
        ],
        requests=[],
    )

    result = await CodeAgent(coder, sandbox).run(
        CodeAgentRequest(task="Implement answer", repository_files={"README.md": "# Demo"})
    )

    assert result.status == "SUCCEEDED"
    assert result.generated_tests == ["test_solution.py"]
    assert result.source_files["solution.py"]
    assert len(sandbox.requests) == 1


@pytest.mark.asyncio
async def test_code_agent_returns_structured_failure_after_repair_attempts() -> None:
    failure = RawSandboxResult(
        status=SandboxStatus.FAILED,
        stdout="",
        stderr="AssertionError",
        exit_code=1,
        created_files=[],
        runtime_seconds=0.1,
    )
    coder = FakeCoder(
        proposals=[
            CodeProposal(
                source_files={"solution.py": "raise AssertionError"},
                test_files={"test_solution.py": "assert False"},
                execution_code="raise AssertionError",
                summary="First attempt.",
            ),
            CodeProposal(
                source_files={"solution.py": "raise AssertionError"},
                test_files={"test_solution.py": "assert False"},
                execution_code="raise AssertionError",
                summary="Repair attempt.",
            ),
        ],
        requests=[],
        failures=[],
    )
    sandbox = FakeSandbox(results=[failure, failure], requests=[])

    result = await CodeAgent(coder, sandbox).run(
        CodeAgentRequest(task="Implement failing task", max_attempts=2)
    )

    assert result.status == "FAILED"
    assert result.attempts == 2
    assert result.last_failure is not None
    assert result.last_failure.stderr == "AssertionError"
    assert coder.failures == [None, failure]


def test_code_proposal_requires_generated_tests() -> None:
    with pytest.raises(ValueError):
        CodeProposal(
            source_files={"solution.py": "def answer(): return 42"},
            test_files={},
            execution_code="print('not enough')",
            summary="Implementation without tests.",
        )
