"""Verified referral selection for safe-failure responses."""

from app.schemas.chat import ReferralResponse


def select_verified_referral(question: str) -> ReferralResponse:
    """Select a conservative official-office fallback without inventing contacts."""

    normalized = question.lower()
    office = "Purdue Northwest official office"
    if "financial aid" in normalized:
        office = "Financial Aid Office"
    elif "grade" in normalized or "academic standing" in normalized:
        office = "Academic Affairs"
    elif "registration" in normalized or "class" in normalized:
        office = "Registrar"
    return ReferralResponse(
        office_name=office,
        referral_reason=(
            "Contact the responsible office for a verified, case-specific decision."
        ),
    )