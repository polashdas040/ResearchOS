from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.agents.researchos_agents.hypothesis import Hypothesis


class HypothesisLineageError(ValueError):
    """Raised when an immutable hypothesis lineage operation is invalid."""


class LineageRelation(StrEnum):
    MUTATED_FROM = "MUTATED_FROM"
    COMBINED_FROM = "COMBINED_FROM"
    SPECIALIZED_FROM = "SPECIALIZED_FROM"
    REJECTED_FROM = "REJECTED_FROM"


class HypothesisVersion(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis: Hypothesis
    version: int = Field(ge=1)
    parent_ids: list[UUID] = Field(default_factory=list)
    relation: LineageRelation | None = None
    reason: str = Field(min_length=1)
    critic_feedback: list[str] = Field(default_factory=list)
    new_evidence_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HypothesisLineageStore:
    def __init__(self) -> None:
        self._versions: dict[UUID, HypothesisVersion] = {}

    async def create_root(self, hypothesis: Hypothesis) -> HypothesisVersion:
        if hypothesis.id in self._versions:
            raise HypothesisLineageError("Hypothesis version already exists")
        version = HypothesisVersion(
            hypothesis=hypothesis,
            version=1,
            reason="Root hypothesis",
        )
        self._versions[hypothesis.id] = version
        return version

    async def evolve(
        self,
        hypothesis: Hypothesis,
        parent_ids: list[UUID],
        relation: LineageRelation,
        reason: str,
        critic_feedback: list[str],
        new_evidence_ids: list[UUID],
    ) -> HypothesisVersion:
        if hypothesis.id in self._versions:
            raise HypothesisLineageError("Hypothesis version already exists")
        if not parent_ids:
            raise HypothesisLineageError("Evolved hypothesis requires a parent")
        if len(set(parent_ids)) != len(parent_ids):
            raise HypothesisLineageError("Evolved hypothesis requires distinct parents")
        if relation == LineageRelation.COMBINED_FROM and len(parent_ids) < 2:
            raise HypothesisLineageError("Combined hypothesis requires two parents")
        unknown_parent = next(
            (parent_id for parent_id in parent_ids if parent_id not in self._versions),
            None,
        )
        if unknown_parent is not None:
            raise HypothesisLineageError(f"Hypothesis has unknown parent: {unknown_parent}")
        version = HypothesisVersion(
            hypothesis=hypothesis,
            version=1,
            parent_ids=list(parent_ids),
            relation=relation,
            reason=reason,
            critic_feedback=list(critic_feedback),
            new_evidence_ids=list(new_evidence_ids),
        )
        self._versions[hypothesis.id] = version
        return version

    async def get(self, hypothesis_id: UUID) -> HypothesisVersion | None:
        return self._versions.get(hypothesis_id)

    async def ancestors(self, hypothesis_id: UUID) -> list[HypothesisVersion]:
        if hypothesis_id not in self._versions:
            raise HypothesisLineageError("Hypothesis version not found")
        result: list[HypothesisVersion] = []
        pending = list(self._versions[hypothesis_id].parent_ids)
        visited: set[UUID] = set()
        while pending:
            parent_id = pending.pop(0)
            if parent_id in visited:
                continue
            visited.add(parent_id)
            parent = self._versions[parent_id]
            result.append(parent)
            pending.extend(parent.parent_ids)
        return result
