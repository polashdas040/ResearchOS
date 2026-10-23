from dataclasses import dataclass
from pathlib import Path

import pytest

from packages.execution.researchos_execution.sandbox import (
    DockerSandbox,
    RawSandboxResult,
    SandboxLimits,
    SandboxRequest,
    SandboxStatus,
)


@dataclass
class FakeRunner:
    result: RawSandboxResult
    command: list[str] | None = None
    output_file: str | None = None

    async def run(self, command: list[str], timeout_seconds: float) -> RawSandboxResult:
        self.command = command
        if self.output_file:
            output_dir = _mounted_source(command, "/workspace/output")
            path = output_dir / self.output_file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("artifact", encoding="utf-8")
        return self.result


@pytest.mark.asyncio
async def test_docker_sandbox_enforces_isolation_and_resource_limits() -> None:
    runner = FakeRunner(
        RawSandboxResult(
            status=SandboxStatus.SUCCEEDED,
            stdout="42\n",
            stderr="",
            exit_code=0,
            created_files=["result.json"],
            runtime_seconds=0.2,
        )
    )
    sandbox = DockerSandbox(runner=runner, image="python:3.12-slim")

    result = await sandbox.execute(
        SandboxRequest(
            code="print(42)",
            files={"input.txt": "data"},
            limits=SandboxLimits(timeout_seconds=3, memory_mb=256, cpu_seconds=2, pids_limit=32),
        )
    )

    assert result.status == SandboxStatus.SUCCEEDED
    assert result.stdout == "42\n"
    assert result.created_files == ["result.json"]
    assert runner.command is not None
    assert "--network" in runner.command
    assert runner.command[runner.command.index("--network") + 1] == "none"
    assert "--read-only" in runner.command
    assert "--cap-drop" in runner.command
    assert "ALL" in runner.command
    assert "--memory" in runner.command
    assert "256m" in runner.command
    assert "--cpus" in runner.command
    assert "2" in runner.command
    assert "--pids-limit" in runner.command
    assert "32" in runner.command


@pytest.mark.asyncio
async def test_sandbox_returns_timeout_as_structured_failure() -> None:
    runner = FakeRunner(
        RawSandboxResult(
            status=SandboxStatus.TIMED_OUT,
            stdout="partial",
            stderr="timeout",
            exit_code=None,
            created_files=[],
            runtime_seconds=1.0,
        )
    )
    result = await DockerSandbox(runner=runner).execute(
        SandboxRequest(code="while True: pass")
    )

    assert result.status == SandboxStatus.TIMED_OUT
    assert result.exit_code is None
    assert result.stderr == "timeout"


@pytest.mark.asyncio
async def test_sandbox_created_files_excludes_supplied_inputs() -> None:
    runner = FakeRunner(
        RawSandboxResult(
            status=SandboxStatus.SUCCEEDED,
            stdout="done",
            stderr="",
            exit_code=0,
            created_files=[],
            runtime_seconds=0.1,
        ),
        output_file="result.txt",
    )

    result = await DockerSandbox(runner=runner).execute(
        SandboxRequest(
            code="from pathlib import Path\nPath('/workspace/output/result.txt').write_text('ok')",
            files={"input/data.txt": "source"},
        )
    )

    assert result.created_files == ["result.txt"]


def test_sandbox_rejects_file_path_traversal() -> None:
    with pytest.raises(ValueError, match="escapes workspace"):
        SandboxRequest(code="print('x')", files={"../secret.txt": "bad"})


def test_network_is_disabled_by_default() -> None:
    limits = SandboxLimits()

    assert limits.network_enabled is False


def _mounted_source(command: list[str], destination: str) -> Path:
    for index, value in enumerate(command):
        if value == "--mount":
            mount = command[index + 1]
            options = dict(
                option.split("=", maxsplit=1) for option in mount.split(",") if "=" in option
            )
            if options.get("dst") == destination:
                return Path(options["src"])
    raise AssertionError(f"Missing mount for {destination}")
