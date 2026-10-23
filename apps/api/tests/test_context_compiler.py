from uuid import uuid4

from apps.api.app.domain.research.models import ResearchState
from apps.api.app.services.context_compiler import (
    AgentCapability,
    ContextCompiler,
    ContextSourceType,
)


def test_literature_context_focuses_on_goal_questions_and_papers() -> None:
    state = research_state()
    compiler = ContextCompiler()

    context = compiler.compile(
        state=state,
        capability=AgentCapability.LITERATURE,
        task_objective="Find closest prior work.",
        token_budget=120,
    )

    labels = [item.label for item in context.items]
    assert context.capability == AgentCapability.LITERATURE
    assert "research_goal" in labels
    assert "open_questions" in labels
    assert "known_papers" in labels
    assert "experiment_specification" not in labels


def test_coding_context_focuses_on_experiment_and_artifacts() -> None:
    state = research_state()
    compiler = ContextCompiler()

    context = compiler.compile(
        state=state,
        capability=AgentCapability.CODING,
        task_objective="Implement experiment runner script.",
        token_budget=120,
    )

    labels = [item.label for item in context.items]
    assert context.capability == AgentCapability.CODING
    assert "experiment_specification" in labels
    assert "artifact_references" in labels
    assert "known_papers" not in labels


def test_critic_context_focuses_on_claims_results_and_evidence() -> None:
    state = research_state()
    compiler = ContextCompiler()

    context = compiler.compile(
        state=state,
        capability=AgentCapability.CRITIC,
        task_objective="Attack the strongest hypothesis.",
        token_budget=120,
    )

    labels = [item.label for item in context.items]
    assert context.capability == AgentCapability.CRITIC
    assert "claim_references" in labels
    assert "evidence_references" in labels
    assert "experiment_references" in labels
    assert "known_papers" not in labels


def test_context_compiler_enforces_token_budget() -> None:
    compiler = ContextCompiler()
    state = research_state(goal=" ".join(["longgoal"] * 80))

    context = compiler.compile(
        state=state,
        capability=AgentCapability.LITERATURE,
        task_objective=" ".join(["task"] * 80),
        token_budget=25,
    )

    assert context.estimated_tokens <= 25
    assert context.truncated is True


def test_context_items_record_source_provenance() -> None:
    compiler = ContextCompiler()

    context = compiler.compile(
        state=research_state(),
        capability=AgentCapability.CRITIC,
        task_objective="Review support.",
        token_budget=120,
    )

    assert context.items
    assert all(item.source.source_type in set(ContextSourceType) for item in context.items)
    assert all(item.source.source_id for item in context.items)


def research_state(goal: str = "Find evidence-backed ADNI research gaps.") -> ResearchState:
    return ResearchState(
        research_run_id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        goal=goal,
        open_question_ids=[uuid4()],
        claim_ids=[uuid4()],
        evidence_ids=[uuid4()],
        hypothesis_ids=[uuid4()],
        experiment_ids=[uuid4()],
        artifact_ids=[uuid4()],
        task_ids=[uuid4()],
        decision_ids=[uuid4()],
    )
