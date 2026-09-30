"""Approved source discovery API route."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DatabaseSession
from app.models.base import ReviewStatus
from app.models.source import ApprovedSource
from app.schemas.source import SourceRead

router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/sources", response_model=list[SourceRead])
def list_active_sources(database: DatabaseSession) -> list[ApprovedSource]:
    """Return only sources currently authoritative for chatbot answers."""

    statement = (
        select(ApprovedSource)
        .where(
            ApprovedSource.review_status == ReviewStatus.APPROVED,
            ApprovedSource.is_active.is_(True),
            ApprovedSource.superseded_by.is_(None),
        )
        .order_by(ApprovedSource.title, ApprovedSource.id)
    )
    return list(database.scalars(statement))