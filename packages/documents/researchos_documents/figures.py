import hashlib
import re
from typing import Protocol

from apps.api.app.domain.figures.models import FigureDescription, ScientificFigure
from packages.documents.researchos_documents.schema import DocumentElement, DocumentElementType


class FigureExtractionError(Exception):
    """Raised when a figure element cannot be extracted."""


class FigureVisionModel(Protocol):
    async def describe(self, figure: ScientificFigure) -> FigureDescription: ...


class FigureExtractor:
    def extract(
        self,
        element: DocumentElement,
        image_bytes: bytes,
        image_content_type: str,
    ) -> ScientificFigure:
        if element.element_type != DocumentElementType.FIGURE or element.id is None:
            raise FigureExtractionError("Figure extraction requires a persisted figure element")
        if image_content_type not in {"image/png", "image/jpeg"}:
            raise FigureExtractionError("Unsupported figure image type")
        return ScientificFigure(
            document_element_id=element.id,
            page=element.page,
            section=element.section,
            caption=element.caption,
            image_sha256=hashlib.sha256(image_bytes).hexdigest(),
            image_content_type=image_content_type,
        )


class DeterministicFigureVisionModel:
    async def describe(self, figure: ScientificFigure) -> FigureDescription:
        caption = (figure.caption or "").lower()
        figure_type = _figure_type(caption)
        labels = _labels(caption)
        return FigureDescription(
            figure_type=figure_type,
            labels=labels,
            components=labels,
            relationships=_relationships(caption),
            axes=["x", "y"] if figure_type == "chart" else [],
            trends=["trend"] if figure_type == "chart" or "trend" in caption else [],
            architecture_nodes=labels if figure_type == "architecture" else [],
            medical_anatomy=_medical_terms(caption),
            confidence=0.7,
            source_page=figure.page,
        )


class FigureIntelligenceService:
    def __init__(self, vision_model: FigureVisionModel) -> None:
        self._vision_model = vision_model

    async def describe(self, figure: ScientificFigure) -> FigureDescription:
        return await self._vision_model.describe(figure)


def _figure_type(caption: str) -> str:
    if "workflow" in caption or "pipeline" in caption:
        return "workflow"
    if "architecture" in caption or "encoder" in caption:
        return "architecture"
    if "roc" in caption or "trend" in caption or "axis" in caption:
        return "chart"
    return "scientific_figure"


def _labels(caption: str) -> list[str]:
    known = [
        "preprocessing",
        "classifier",
        "encoder",
        "attention",
        "roc",
        "model",
    ]
    words = set(re.findall(r"[a-z0-9]+", caption))
    return [label for label in known if label in words]


def _relationships(caption: str) -> list[str]:
    if "showing" in caption:
        return ["caption describes displayed components"]
    return []


def _medical_terms(caption: str) -> list[str]:
    terms = ["mri", "brain", "tumor", "anatomy"]
    return [term for term in terms if term in caption]
