import asyncio
import tempfile
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SandboxStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class SandboxLimits(BaseModel):
    model_config = ConfigDict(frozen=True)

    timeout_seconds: float = Field(default=30.0, gt=0.0)
    memory_mb: int = Field(default=512, gt=0)
    cpu_seconds: int = Field(default=30, gt=0)
    pids_limit: int = Field(default=64, gt=0)
    network_enabled: bool = False

    def model_post_init(self, __context: object) -> None:
        if self.network_enabled:
            raise ValueError("Sandbox network access is disabled")


class SandboxRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(min_length=1)
    files: dict[str, str] = Field(default_factory=dict)
    limits: SandboxLimits = Field(default_factory=SandboxLimits)

    @model_validator(mode="after")
    def validate_file_paths(self) -> "SandboxRequest":
        for relative_path in self.files:
            _validate_relative_path(relative_path)
        return self


class RawSandboxResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: SandboxStatus
    stdout: str
    stderr: str
    exit_code: int | None
    created_files: list[str] = Field(default_factory=list)
    runtime_seconds: float = Field(ge=0.0)
    resource_usage: dict[str, float] = Field(default_factory=dict)


class SandboxRunner(Protocol):
    async def run(self, command: list[str], timeout_seconds: float) -> RawSandboxResult: ...


class SubprocessSandboxRunner:
    async def run(self, command: list[str], timeout_seconds: float) -> RawSandboxResult:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.communicate()
            return RawSandboxResult(
                status=SandboxStatus.TIMED_OUT,
                stdout="",
                stderr="Sandbox execution timed out",
                exit_code=None,
                runtime_seconds=timeout_seconds,
            )
        return RawSandboxResult(
            status=SandboxStatus.SUCCEEDED if process.returncode == 0 else SandboxStatus.FAILED,
            stdout=stdout.decode(errors="replace"),
            stderr=stderr.decode(errors="replace"),
            exit_code=process.returncode,
            runtime_seconds=0.0,
        )


class DockerSandbox:
    def __init__(
        self,
        runner: SandboxRunner | None = None,
        image: str = "python:3.12-slim",
    ) -> None:
        self._runner = runner or SubprocessSandboxRunner()
        self._image = image

    async def execute(self, request: SandboxRequest) -> RawSandboxResult:
        with tempfile.TemporaryDirectory(prefix="researchos-sandbox-") as directory:
            workspace = Path(directory)
            input_dir = workspace / "input"
            output_dir = workspace / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            self._write_workspace(input_dir, request)
            command = self._build_command(workspace, request.limits)
            result = await self._runner.run(command, request.limits.timeout_seconds)
            if not result.created_files:
                result = result.model_copy(
                    update={"created_files": self._created_files(output_dir)}
                )
            return result

    @staticmethod
    def _write_workspace(input_dir: Path, request: SandboxRequest) -> None:
        (input_dir / "main.py").write_text(request.code, encoding="utf-8")
        for relative_path, content in request.files.items():
            path = _safe_workspace_path(input_dir, relative_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def _build_command(self, workspace: Path, limits: SandboxLimits) -> list[str]:
        input_dir = workspace / "input"
        output_dir = workspace / "output"
        return [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(limits.pids_limit),
            "--memory",
            f"{limits.memory_mb}m",
            "--cpus",
            str(limits.cpu_seconds),
            "--mount",
            f"type=bind,src={input_dir},dst=/workspace/input,readonly",
            "--mount",
            f"type=bind,src={output_dir},dst=/workspace/output",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--workdir",
            "/workspace",
            self._image,
            "python",
            "/workspace/input/main.py",
        ]

    @staticmethod
    def _created_files(workspace: Path) -> list[str]:
        return sorted(
            str(path.relative_to(workspace)).replace("\\", "/")
            for path in workspace.rglob("*")
            if path.is_file() and path.name != "main.py"
        )


def _safe_workspace_path(workspace: Path, relative_path: str) -> Path:
    candidate = _validate_relative_path(relative_path)
    path = workspace.joinpath(*candidate.parts).resolve()
    if workspace.resolve() not in path.parents:
        raise ValueError("Sandbox file path escapes workspace")
    return path


def _validate_relative_path(relative_path: str) -> PurePosixPath:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("Sandbox file path escapes workspace")
    return candidate
