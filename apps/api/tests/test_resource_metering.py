from uuid import uuid4

import pytest

from packages.billing.researchos_billing.metering import (
    ResourceMeter,
    ResourceUsage,
)


@pytest.mark.asyncio
async def test_meter_records_usage_and_maps_resources_to_credits() -> None:
    meter = ResourceMeter(
        rates={
            "llm_tokens": 0.01,
            "pdf_pages": 0.5,
            "cpu_seconds": 0.2,
        }
    )
    run_id = uuid4()
    task_id = uuid4()

    record = await meter.record(
        ResourceUsage(
            research_run_id=run_id,
            task_id=task_id,
            resources={"llm_tokens": 100, "pdf_pages": 2, "cpu_seconds": 5},
        )
    )

    assert record.credits == 3.0
    assert record.resources["llm_tokens"] == 100
    assert (await meter.task_total(task_id)) == 3.0
    assert (await meter.run_total(run_id)) == 3.0


@pytest.mark.asyncio
async def test_meter_preserves_task_level_records_and_supports_zero_rate_resources() -> None:
    meter = ResourceMeter(rates={"searches": 0.25})
    task_id = uuid4()
    run_id = uuid4()
    await meter.record(
        ResourceUsage(
            research_run_id=run_id,
            task_id=task_id,
            resources={"searches": 4, "storage_bytes": 1024},
        )
    )

    records = await meter.records_for_task(task_id)
    assert len(records) == 1
    assert records[0].credits == 1.0
    assert records[0].resources["storage_bytes"] == 1024


@pytest.mark.asyncio
async def test_meter_allows_provider_rate_updates_for_future_usage() -> None:
    meter = ResourceMeter(rates={"vision_images": 2.0})
    run_id = uuid4()
    task_id = uuid4()

    first = await meter.record(
        ResourceUsage(
            research_run_id=run_id,
            task_id=task_id,
            resources={"vision_images": 1},
        )
    )
    meter.configure_rate("vision_images", 3.5)
    second = await meter.record(
        ResourceUsage(
            research_run_id=run_id,
            task_id=task_id,
            resources={"vision_images": 1},
        )
    )

    assert first.credits == 2.0
    assert second.credits == 3.5
    assert await meter.run_total(run_id) == 5.5
