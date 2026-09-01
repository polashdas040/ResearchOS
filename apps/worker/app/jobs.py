from collections.abc import Awaitable, Callable

from apps.api.app.repositories.jobs import JobRepository

JobHandler = Callable[[dict[str, object]], Awaitable[dict[str, object]]]


class JobRunner:
    def __init__(self, repository: JobRepository, handlers: dict[str, JobHandler]) -> None:
        self._repository = repository
        self._handlers = handlers

    async def run_once(self) -> bool:
        job = await self._repository.claim_next_job()
        if job is None:
            return False
        handler = self._handlers.get(job.job_type.value)
        if handler is None:
            await self._repository.mark_failed(job.id, f"No handler for {job.job_type.value}")
            return True
        try:
            result = await handler(job.payload)
        except Exception as exc:
            await self._repository.mark_failed(job.id, str(exc))
            return True
        await self._repository.mark_succeeded(job.id, result)
        return True
