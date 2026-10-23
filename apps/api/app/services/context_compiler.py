from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.research.models import ResearchState


class AgentCapability(StrEnum):
    LITERATURE = "LITERATURE"
    CODING = "CODING"
    CRITIC = "CRITIC"
    GENERAL = "GENERAL"


class ContextSourceType(StrEnum):
    RESEARCH_STATE = "RESEARCH_STATE"
    TASK = "TASK"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT = "EXPERIMENT"
    ARTIFACT = "ARTIFACT"
    PAPER = "PAPER"


class ContextSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: ContextSourceType
    source_id: str


class CompiledContextItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    content: str
    source: ContextSource
    estimated_tokens: int


class CompiledContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    capability: AgentCapability
    task_objective: str
    items: list[CompiledContextItem] = Field(default_factory=list)
    estimated_tokens: int
    token_budget: int
    truncated: bool


class ContextCompiler:
    def compile(
        self,
        state: ResearchState,
        capability: AgentCapability,
        task_objective: str,
        token_budget: int,
    ) -> CompiledContext:
        candidates = _candidate_items(state, capability, task_objective)
        selected: list[CompiledContextItem] = []
        used_tokens = 0
        truncated = False
        for item in candidates:
            if used_tokens + item.estimated_tokens <= token_budget:
                selected.append(item)
                used_tokens += item.estimated_tokens
                continue
            remaining = token_budget - used_tokens
            if remaining > 0:
                shortened = _truncate_item(item, remaining)
                selected.append(shortened)
                used_tokens += shortened.estimated_tokens
            truncated = True
            break
        return CompiledContext(
            capability=capability,
            task_objective=task_objective,
            items=selected,
            estimated_tokens=used_tokens,
            token_budget=token_budget,
            truncated=truncated,
        )


def _candidate_items(
    state: ResearchState,
    capability: AgentCapability,
    task_objective: str,
) -> list[CompiledContextItem]:
    common = [
        _item(
            "research_goal",
            state.goal,
            ContextSourceType.RESEARCH_STATE,
            str(state.research_run_id),
        ),
        _item("task_objective", task_objective, ContextSourceType.TASK, str(state.research_run_id)),
    ]
    if capability == AgentCapability.LITERATURE:
        return common + [
            _id_list_item(
                "open_questions",
                state.open_question_ids,
                ContextSourceType.RESEARCH_STATE,
                state.research_run_id,
            ),
            _id_list_item(
                "known_papers",
                state.evidence_ids,
                ContextSourceType.PAPER,
                state.project_id,
            ),
            _id_list_item(
                "constraint_references",
                state.constraint_ids,
                ContextSourceType.RESEARCH_STATE,
                state.research_run_id,
            ),
        ]
    if capability == AgentCapability.CODING:
        return common + [
            _id_list_item(
                "experiment_specification",
                state.experiment_ids,
                ContextSourceType.EXPERIMENT,
                state.project_id,
            ),
            _id_list_item(
                "artifact_references",
                state.artifact_ids,
                ContextSourceType.ARTIFACT,
                state.project_id,
            ),
        ]
    if capability == AgentCapability.CRITIC:
        return common + [
            _id_list_item(
                "claim_references",
                state.claim_ids,
                ContextSourceType.CLAIM,
                state.project_id,
            ),
            _id_list_item(
                "evidence_references",
                state.evidence_ids,
                ContextSourceType.EVIDENCE,
                state.project_id,
            ),
            _id_list_item(
                "experiment_references",
                state.experiment_ids,
                ContextSourceType.EXPERIMENT,
                state.project_id,
            ),
            _id_list_item(
                "hypothesis_references",
                state.hypothesis_ids,
                ContextSourceType.HYPOTHESIS,
                state.project_id,
            ),
        ]
    return common


def _id_list_item(
    label: str,
    ids: list[UUID],
    source_type: ContextSourceType,
    fallback_source_id: UUID,
) -> CompiledContextItem:
    content = "\n".join(str(item_id) for item_id in ids) if ids else "No references available."
    source_id = str(ids[0]) if ids else str(fallback_source_id)
    return _item(label, content, source_type, source_id)


def _item(
    label: str,
    content: str,
    source_type: ContextSourceType,
    source_id: str,
) -> CompiledContextItem:
    return CompiledContextItem(
        label=label,
        content=content,
        source=ContextSource(source_type=source_type, source_id=source_id),
        estimated_tokens=_estimate_tokens(content),
    )


def _truncate_item(item: CompiledContextItem, token_budget: int) -> CompiledContextItem:
    words = item.content.split()
    content = " ".join(words[:token_budget])
    return item.model_copy(
        update={
            "content": content,
            "estimated_tokens": _estimate_tokens(content),
        }
    )


def _estimate_tokens(content: str) -> int:
    return max(1, len(content.split()))
