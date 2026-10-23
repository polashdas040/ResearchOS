import pytest

from packages.execution.researchos_execution.repair import (
    FailureClass,
    RepairAction,
    RepairEngine,
    RepairRequest,
)


@pytest.mark.asyncio
async def test_resource_failure_retries_with_bounded_resource_change() -> None:
    result = await RepairEngine().decide(
        RepairRequest(
            failure_class=FailureClass.RESOURCE_FAILURE,
            message="CUDA out of memory",
            retry_count=0,
            max_retries=2,
        )
    )

    assert result.action == RepairAction.RETRY
    assert result.retry_allowed is True
    assert "batch" in result.suggested_changes[0].lower()


@pytest.mark.asyncio
async def test_scientific_failure_is_not_optimized_into_a_retry() -> None:
    result = await RepairEngine().decide(
        RepairRequest(
            failure_class=FailureClass.SCIENTIFIC_FAILURE,
            message="Hypothesis contradicted by held-out evidence",
            retry_count=0,
            max_retries=3,
        )
    )

    assert result.action == RepairAction.DOWNGRADE_OR_REJECT
    assert result.retry_allowed is False
    assert result.preserve_failure is True


@pytest.mark.asyncio
async def test_retry_limit_and_authorization_failures_stop_automatically() -> None:
    exhausted = await RepairEngine().decide(
        RepairRequest(
            failure_class=FailureClass.CODE_FAILURE,
            message="AssertionError",
            retry_count=2,
            max_retries=2,
        )
    )
    unauthorized = await RepairEngine().decide(
        RepairRequest(
            failure_class=FailureClass.AUTHORIZATION_FAILURE,
            message="Approval required",
            retry_count=0,
            max_retries=2,
        )
    )

    assert exhausted.action == RepairAction.STOP
    assert exhausted.retry_allowed is False
    assert unauthorized.action == RepairAction.WAIT_FOR_AUTHORIZATION
    assert unauthorized.retry_allowed is False


@pytest.mark.asyncio
async def test_data_and_evidence_failures_replan_without_direct_retry() -> None:
    for failure_class in (FailureClass.DATA_FAILURE, FailureClass.EVIDENCE_FAILURE):
        result = await RepairEngine().decide(
            RepairRequest(
                failure_class=failure_class,
                message="Inputs are not valid for this claim.",
                retry_count=0,
                max_retries=3,
            )
        )

        assert result.action == RepairAction.REPLAN
        assert result.retry_allowed is False
