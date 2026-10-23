from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from packages.rag.researchos_rag.evidence_packs import EvidencePack, EvidenceSource


class AcademicSection(StrEnum):
    ABSTRACT = "ABSTRACT"
    INTRODUCTION = "INTRODUCTION"
    METHODS = "METHODS"
    RESULTS = "RESULTS"
    DISCUSSION = "DISCUSSION"


class WritingClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    statement: str = Field(min_length=1)
    citation_ids: list[str] = Field(min_length=1)


class WritingRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: AcademicSection
    instruction: str = Field(min_length=1)
    evidence_pack: EvidencePack


class AcademicDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: AcademicSection
    content: str = Field(min_length=1)
    claims: list[WritingClaim] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    sources: list[EvidenceSource] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OutlineSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: AcademicSection
    objective: str = Field(min_length=1)
    required_evidence: list[str] = Field(min_length=1)


class AcademicOutline(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1)
    sections: list[OutlineSection] = Field(min_length=1)


class AcademicWritingAssistant:
    def draft_section(self, request: WritingRequest) -> AcademicDraft:
        if not request.evidence_pack.items:
            raise ValueError("academic writing requires evidence-backed citations")

        item = request.evidence_pack.items[0]
        citation_id = "E1"
        content = (
            f"{_section_prefix(request.section)} {item.content} "
            f"[{citation_id}]"
        )
        claim = WritingClaim(statement=item.content, citation_ids=[citation_id])
        return AcademicDraft(
            section=request.section,
            content=content,
            claims=[claim],
            citation_ids=[citation_id],
            sources=[item.source],
        )

    def build_outline(self, title: str) -> AcademicOutline:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("outline title cannot be empty")
        return AcademicOutline(
            title=normalized_title,
            sections=[
                OutlineSection(
                    section=AcademicSection.ABSTRACT,
                    objective="Summarize the research question, method, result, and contribution.",
                    required_evidence=["validated claims", "primary result evidence"],
                ),
                OutlineSection(
                    section=AcademicSection.INTRODUCTION,
                    objective="Introduce the problem, gap, and evidence-backed motivation.",
                    required_evidence=["background citations", "gap analysis evidence"],
                ),
                OutlineSection(
                    section=AcademicSection.METHODS,
                    objective=(
                        "Describe reproducible data, model, experiment, "
                        "and analysis methods."
                    ),
                    required_evidence=["experiment specification", "dataset profile"],
                ),
                OutlineSection(
                    section=AcademicSection.RESULTS,
                    objective="Report verified metrics and observations without overclaiming.",
                    required_evidence=["experiment run metrics", "statistical review"],
                ),
                OutlineSection(
                    section=AcademicSection.DISCUSSION,
                    objective="Interpret findings, limitations, threats, and future work.",
                    required_evidence=["critic findings", "verification report"],
                ),
            ],
        )


def _section_prefix(section: AcademicSection) -> str:
    prefixes = {
        AcademicSection.ABSTRACT: "In summary,",
        AcademicSection.INTRODUCTION: "Prior evidence indicates that",
        AcademicSection.METHODS: "The study protocol records that",
        AcademicSection.RESULTS: "The verified result is that",
        AcademicSection.DISCUSSION: "This finding suggests that",
    }
    return prefixes[section]
