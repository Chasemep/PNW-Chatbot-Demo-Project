"""Extract source-grounded office details and safe directory referrals."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.models.source_chunk import SourceContentSegment
from app.schemas.chat import ReferralResponse

OFFICIAL_DIRECTORY_URL = "https://www.pnw.edu/academic-and-administrative-offices/"

_OFFICE_PATTERN = re.compile(
    r"\bcontact\s+(?:the\s+)?(?P<office>[A-Za-z][A-Za-z0-9&'’-]*(?:\s+"
    r"[A-Za-z][A-Za-z0-9&'’-]*){0,5})(?=\s+(?:for|at|via)\b|[.,;:]|$)",
    re.IGNORECASE,
)
_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_PATTERN = re.compile(r"(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]\d{4}")

_CONTACT_PROCESSES = (
    ("financial aid", ("financial aid",)),
    ("academic standing", ("academic standing",)),
    ("grade appeal", ("grade appeal", "appeal a grade", "appeal my grade")),
    (
        "class registration changes",
        ("add or drop", "adding or dropping", "class add", "class drop"),
    ),
    ("registration", ("registration", "register for classes")),
)


@dataclass(frozen=True, slots=True)
class ContactMetadata:
    """Contact details explicitly extracted from one approved source segment."""

    office_name: str
    contact_url: str | None
    contact_email: str | None
    contact_phone: str | None


def extract_contact_metadata(content: str) -> ContactMetadata | None:
    """Extract explicit office and contact details without inferring missing data."""

    office_match = _OFFICE_PATTERN.search(content)
    if office_match is None:
        return None

    contact_url = next(
        (
            candidate.rstrip(".,;:!?) ]")
            for candidate in _URL_PATTERN.findall(content)
            if _is_official_url(candidate.rstrip(".,;:!?) ]"))
        ),
        None,
    )
    contact_email = next(
        (
            candidate
            for candidate in _EMAIL_PATTERN.findall(content)
            if _is_official_domain(candidate.rsplit("@", maxsplit=1)[1])
        ),
        None,
    )
    phone_match = _PHONE_PATTERN.search(content)
    contact_phone = phone_match.group(0) if phone_match else None
    return ContactMetadata(
        office_name=office_match.group("office").strip(),
        contact_url=contact_url,
        contact_email=contact_email,
        contact_phone=contact_phone,
    )


def build_contact_referral(
    question: str,
    chunks: list[SourceContentSegment],
) -> ReferralResponse | None:
    """Match an explicitly sourced contact to the process asked about."""

    process = _question_process(question)
    if process is None:
        return None
    process_name, phrases = process
    for chunk in chunks:
        normalized_content = chunk.content_text.casefold()
        if not any(phrase in normalized_content for phrase in phrases):
            continue
        contact = extract_contact_metadata(chunk.content_text)
        if contact is None:
            continue
        return ReferralResponse(
            office_name=contact.office_name,
            referral_reason=(
                f"Contact {contact.office_name} for {process_name} assistance, "
                "as identified in the approved source."
            ),
            contact_url=contact.contact_url,
            contact_email=contact.contact_email,
            contact_phone=contact.contact_phone,
        )
    return None


def select_verified_referral(_question: str) -> ReferralResponse:
    """Direct students to PNW's directory when no contact is source-verified."""

    return ReferralResponse(
        office_name="Purdue Northwest official directory",
        referral_reason=(
            "I cannot verify current contact details from approved sources. "
            "Use the official directory to locate the appropriate office."
        ),
        contact_url=OFFICIAL_DIRECTORY_URL,
    )


def _question_process(question: str) -> tuple[str, tuple[str, ...]] | None:
    normalized_question = question.casefold()
    for process_name, phrases in _CONTACT_PROCESSES:
        if any(phrase in normalized_question for phrase in phrases):
            return process_name, phrases
    if "class" in normalized_question and any(
        marker in normalized_question for marker in ("add", "drop", "change")
    ):
        return _CONTACT_PROCESSES[3]
    return None


def _is_official_url(value: str) -> bool:
    hostname = urlparse(value).hostname
    return bool(hostname and _is_official_domain(hostname))


def _is_official_domain(hostname: str) -> bool:
    normalized_hostname = hostname.lower().rstrip(".")
    return any(
        normalized_hostname == domain or normalized_hostname.endswith(f".{domain}")
        for domain in ("pnw.edu", "purdue.edu")
    )