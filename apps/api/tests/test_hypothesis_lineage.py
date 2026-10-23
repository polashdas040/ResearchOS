from uuid import uuid4

import pytest

from packages.agents.researchos_agents.hypothesis import Hypothesis
from packages.agents.researchos_agents.hypothesis_lineage import (
    HypothesisLineageError,
    HypothesisLineageStore,
    LineageRelation,
)


def hypothesis(statement: str) -> Hypothesis:
    return Hypothesis(
        statement=statement,
        rationale="A grounded rationale.",
        required_data=["benchmark"],
        supporting_gap_ids=[uuid4()],
        falsification_test="The hypothesis fails to beat the baseline.",
        generation_strategy="test_strategy",
    )


@pytest.mark.asyncio
async def test_lineage_traverses_mutation_and_preserves_parent_version() -> None:
    store = HypothesisLineageStore()
    root = hypothesis("A longer follow-up improves prediction.")
    root_version = await store.create_root(root)
    child = hypothesis("A longer follow-up improves calibrated prediction.")

    child_version = await store.evolve(
        child,
        parent_ids=[root.id],
        relation=LineageRelation.MUTATED_FROM,
        reason="Added calibration to address critic feedback.",
        critic_feedback=["Specify calibration procedure."],
        new_evidence_ids=[uuid4()],
    )

    ancestors = await store.ancestors(child.id)

    assert child_version.version == 1
    assert child_version.parent_ids == [root.id]
    assert child_version.reason.startswith("Added calibration")
    assert ancestors == [root_version]
    assert (await store.get(root.id)) == root_version
    assert root_version.hypothesis.statement == "A longer follow-up improves prediction."


@pytest.mark.asyncio
async def test_lineage_records_combination_and_rejection_metadata() -> None:
    store = HypothesisLineageStore()
    first = await store.create_root(hypothesis("A temporal feature improves prediction."))
    second = await store.create_root(hypothesis("A multimodal feature improves prediction."))
    combined = await store.evolve(
        hypothesis("Temporal and multimodal features improve prediction."),
        parent_ids=[first.hypothesis.id, second.hypothesis.id],
        relation=LineageRelation.COMBINED_FROM,
        reason="Combined complementary mechanisms.",
        critic_feedback=[],
        new_evidence_ids=[],
    )
    rejected = await store.evolve(
        hypothesis("A rejected direction."),
        parent_ids=[combined.hypothesis.id],
        relation=LineageRelation.REJECTED_FROM,
        reason="Failed feasibility review.",
        critic_feedback=["Required data are unavailable."],
        new_evidence_ids=[],
    )

    ancestors = await store.ancestors(rejected.hypothesis.id)

    assert combined.relation == LineageRelation.COMBINED_FROM
    assert rejected.relation == LineageRelation.REJECTED_FROM
    assert [item.hypothesis.id for item in ancestors] == [
        combined.hypothesis.id,
        first.hypothesis.id,
        second.hypothesis.id,
    ]


@pytest.mark.asyncio
async def test_lineage_rejects_unknown_parents_and_single_parent_combination() -> None:
    store = HypothesisLineageStore()
    child = hypothesis("A child hypothesis.")

    with pytest.raises(HypothesisLineageError, match="unknown parent"):
        await store.evolve(
            child,
            parent_ids=[uuid4()],
            relation=LineageRelation.SPECIALIZED_FROM,
            reason="Narrowed scope.",
            critic_feedback=[],
            new_evidence_ids=[],
        )

    root = await store.create_root(hypothesis("A root hypothesis."))
    with pytest.raises(HypothesisLineageError, match="two parents"):
        await store.evolve(
            child,
            parent_ids=[root.hypothesis.id],
            relation=LineageRelation.COMBINED_FROM,
            reason="Invalid combination.",
            critic_feedback=[],
            new_evidence_ids=[],
        )


@pytest.mark.asyncio
async def test_lineage_rejects_duplicate_parent_ids() -> None:
    store = HypothesisLineageStore()
    root = await store.create_root(hypothesis("A root hypothesis."))

    with pytest.raises(HypothesisLineageError, match="distinct"):
        await store.evolve(
            hypothesis("A falsely combined hypothesis."),
            parent_ids=[root.hypothesis.id, root.hypothesis.id],
            relation=LineageRelation.COMBINED_FROM,
            reason="Invalid repeated parent.",
            critic_feedback=[],
            new_evidence_ids=[],
        )
