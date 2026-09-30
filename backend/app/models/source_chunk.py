"""Structure-aware source chunk model used for retrieval."""

from collections.abc import Iterable
from math import isfinite
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.models.base import ContentKind, ModelBase, embedding_vector_type


class SourceContentSegment(ModelBase):
    """A bounded, traceable chunk of approved source content."""

    __tablename__ = "source_content_segments"
    __table_args__ = (
        CheckConstraint(
            "length(trim(content_text)) > 0",
            name="ck_source_content_segments_content_text_nonempty",
        ),
        CheckConstraint(
            "length(trim(structural_path)) > 0",
            name="ck_source_content_segments_structural_path_nonempty",
        ),
        CheckConstraint(
            "length(trim(location_label)) > 0",
            name="ck_source_content_segments_location_label_nonempty",
        ),
        CheckConstraint(
            "length(trim(chunk_hash)) > 0",
            name="ck_source_content_segments_chunk_hash_nonempty",
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name="ck_source_content_segments_chunk_index_nonnegative",
        ),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("approved_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    release_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_base_releases.id", ondelete="RESTRICT"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(
        embedding_vector_type,
        nullable=False,
    )
    structural_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_kind: Mapped[ContentKind] = mapped_column(
        Enum(
            ContentKind,
            name="content_kind",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    location_label: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    @validates("embedding")
    def validate_embedding(self, _key: str, value: Any) -> list[float]:
        """Reject vectors with the wrong dimension or non-finite values."""

        if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
            raise ValueError("embedding must be a finite numeric vector")

        vector = [float(component) for component in value]
        expected_dimension = embedding_vector_type.dim
        if len(vector) != expected_dimension:
            raise ValueError(
                f"embedding must contain {expected_dimension} dimensions"
            )
        if not all(isfinite(component) for component in vector):
            raise ValueError("embedding must contain only finite values")
        return vector