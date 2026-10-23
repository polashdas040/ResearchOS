from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkflowName(StrEnum):
    IDEA_DISCOVERY = "IDEA_DISCOVERY"
    PAPER_DEEP_DIVE = "PAPER_DEEP_DIVE"
    REPRODUCTION = "REPRODUCTION"
    RESEARCH_DEBUGGING = "RESEARCH_DEBUGGING"
    REVIEWER_SIMULATION = "REVIEWER_SIMULATION"


_ALLOWED_STAGES = {
    "dataset_profile",
    "literature",
    "evidence_map",
    "gap_discovery",
    "hypotheses",
    "novelty",
    "feasibility",
    "critic",
    "tournament",
    "parse_document",
    "methods",
    "figures",
    "tables",
    "claims",
    "critique",
    "repository",
    "environment",
    "implementation",
    "run",
    "comparison",
    "code",
    "logs",
    "dataset",
    "metrics",
    "root_cause_analysis",
    "experiments",
    "ml_reviewer",
    "scientific_reviewer",
    "statistics_reviewer",
    "reproducibility_reviewer",
    "meta_review",
}


class ResearchWorkflow(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: WorkflowName
    stages: list[str] = Field(min_length=1)

    @field_validator("stages")
    @classmethod
    def validate_stages(cls, stages: list[str]) -> list[str]:
        unknown = set(stages) - _ALLOWED_STAGES
        if unknown:
            raise ValueError(f"unknown workflow stage: {sorted(unknown)[0]}")
        if len(stages) != len(set(stages)):
            raise ValueError("workflow stages must be unique")
        return stages

    def next_stage(self, completed_stage: str | None) -> str | None:
        if completed_stage is None:
            return self.stages[0]
        if completed_stage not in self.stages:
            raise ValueError(f"stage is not part of workflow: {completed_stage}")
        index = self.stages.index(completed_stage)
        next_index = index + 1
        if next_index >= len(self.stages):
            return None
        return self.stages[next_index]


class ResearchWorkflowRegistry:
    _WORKFLOWS = {
        WorkflowName.IDEA_DISCOVERY: [
            "dataset_profile", "literature", "evidence_map", "gap_discovery",
            "hypotheses", "novelty", "feasibility", "critic", "tournament",
        ],
        WorkflowName.PAPER_DEEP_DIVE: [
            "parse_document", "methods", "figures", "tables", "claims", "critique",
        ],
        WorkflowName.REPRODUCTION: [
            "literature", "repository", "environment", "implementation", "run", "comparison",
        ],
        WorkflowName.RESEARCH_DEBUGGING: [
            "code", "logs", "dataset", "metrics", "root_cause_analysis", "experiments",
        ],
        WorkflowName.REVIEWER_SIMULATION: [
            "parse_document", "ml_reviewer", "scientific_reviewer", "statistics_reviewer",
            "reproducibility_reviewer", "meta_review",
        ],
    }

    def get(self, name: WorkflowName) -> ResearchWorkflow:
        try:
            stages = self._WORKFLOWS[name]
        except KeyError as exc:
            raise KeyError(f"workflow not found: {name}") from exc
        return ResearchWorkflow(name=name, stages=list(stages))

    def list_names(self) -> list[WorkflowName]:
        return list(self._WORKFLOWS)
