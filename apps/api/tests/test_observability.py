from uuid import uuid4

import pytest

from packages.observability.researchos_observability.events import (
    EventType,
    ObservabilityEvent,
    ObservabilityStore,
)


@pytest.mark.asyncio
async def test_observability_records_correlated_research_trace() -> None:
    store = ObservabilityStore()
    trace_id = uuid4()
    run_id = uuid4()
    task_id = uuid4()

    await store.record(
        ObservabilityEvent(
            event_type=EventType.RESEARCH_RUN_STARTED,
            trace_id=trace_id,
            research_run_id=run_id,
            latency_ms=0,
        )
    )
    await store.record(
        ObservabilityEvent(
            event_type=EventType.TOOL_COMPLETED,
            trace_id=trace_id,
            research_run_id=run_id,
            task_id=task_id,
            tool_name="document.search",
            latency_ms=120.5,
            tokens=80,
            cost=0.12,
            retry_count=1,
        )
    )

    trace = await store.trace(trace_id)

    assert [event.event_type for event in trace] == [
        EventType.RESEARCH_RUN_STARTED,
        EventType.TOOL_COMPLETED,
    ]
    assert trace[1].tool_name == "document.search"
    assert trace[1].retry_count == 1
    assert trace[0].sequence == 1
    assert trace[1].sequence == 2


@pytest.mark.asyncio
async def test_observability_rejects_missing_correlation_and_unknown_trace() -> None:
    store = ObservabilityStore()
    with pytest.raises(ValueError, match="trace"):
        await store.record(
            ObservabilityEvent(event_type=EventType.TASK_STARTED, trace_id=None)
        )
    with pytest.raises(KeyError, match="trace"):
        await store.trace(uuid4())
