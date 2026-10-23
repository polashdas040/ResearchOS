import pytest

from packages.agents.researchos_agents.workflows import (
    ResearchWorkflow,
    ResearchWorkflowRegistry,
    WorkflowName,
)


def test_registry_exposes_ordered_research_workflows() -> None:
    registry = ResearchWorkflowRegistry()

    workflow = registry.get(WorkflowName.IDEA_DISCOVERY)

    assert workflow.name == WorkflowName.IDEA_DISCOVERY
    assert workflow.stages == [
        "dataset_profile",
        "literature",
        "evidence_map",
        "gap_discovery",
        "hypotheses",
        "novelty",
        "feasibility",
        "critic",
        "tournament",
    ]


def test_registry_contains_all_documented_workflows() -> None:
    registry = ResearchWorkflowRegistry()

    assert set(registry.list_names()) == set(WorkflowName)
    assert all(registry.get(name).stages for name in WorkflowName)


def test_workflow_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="stage"):
        ResearchWorkflow(name=WorkflowName.REPRODUCTION, stages=["unknown"])


def test_workflow_returns_next_stage_without_executing_it() -> None:
    workflow = ResearchWorkflowRegistry().get(WorkflowName.PAPER_DEEP_DIVE)

    assert workflow.next_stage(None) == "parse_document"
    assert workflow.next_stage("parse_document") == "methods"
    assert workflow.next_stage("critique") is None

    with pytest.raises(ValueError, match="not part"):
        workflow.next_stage("dataset_profile")
