from app.models.base import ResponseType
from app.schemas.chat import ChatResponse, ReferralResponse


def test_safe_referral_contract_requires_referral_details():
    response = ChatResponse(
        answer="I cannot verify that individualized decision.",
        response_type=ResponseType.SAFE_REFERRAL,
        referral=ReferralResponse(
            office_name="Registrar",
            referral_reason="Contact the Registrar for a case-specific decision.",
        ),
    )

    assert response.citations == []
    assert response.referral.office_name == "Registrar"


def test_direct_answer_contract_rejects_missing_citations():
    try:
        ChatResponse(
            answer="Unsupported policy answer.",
            response_type=ResponseType.DIRECT_ANSWER,
        )
    except ValueError as error:
        assert "citation" in str(error).lower()
    else:
        raise AssertionError("direct answers must require citations")