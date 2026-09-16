# Data Model: Purdue Policy Chatbot

## Overview

The system stores approved university source content, chunk-level retrieval units, user questions, answer events, and review records for source-quality monitoring. PostgreSQL is the primary relational store; pgvector stores chunk embeddings for retrieval.

## Entity Definitions

### ApprovedSource

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| title | string | Official document or page title |
| source_url | string | Canonical URL or document path |
| source_type | enum | html, pdf, docx, webpage |
| issuing_office | string | Responsible university office or department |
| publication_date | date | Publish or effective date as available |
| reviewed_at | timestamp | Last review date |
| review_status | enum | approved, pending_review, rejected, superseded |
| superseded_by | UUID | Optional reference to newer source |
| is_active | boolean | Whether the source is currently usable for answers |
| created_at | timestamp | Record creation time |
| updated_at | timestamp | Last metadata update |

**Validation rules**:
- `source_url` must be present for web pages and documents loaded from a known URL.
- `review_status` cannot be `approved` if `is_active = false`.
- `superseded_by` is required when `review_status = superseded`.

### SourceContentSegment

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | Foreign key to ApprovedSource |
| chunk_index | integer | Stable ordering of segments within a document |
| content_text | text | Extracted plain text for retrieval |
| source_snippet | text | Original text snippet for citation confidence |
| page_number | integer | Page number where available |
| embedding | vector | pgvector embedding for semantic retrieval |
| created_at | timestamp | Segment creation time |

**Validation rules**:
- `content_text` cannot be empty.
- `source_id` must reference an active or previously reviewed source.
- If a document is marked superseded or rejected, its chunks must not be used for current answer generation without explicit review.

### StudentQuestion

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| raw_text | text | Student’s natural-language question |
| student_type | enum | undergraduate, graduate, unknown |
| asked_at | timestamp | Question timestamp |

**Validation rules**:
- `raw_text` must be non-empty.

### GroundedAnswer

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| question_id | UUID | Foreign key to StudentQuestion |
| answer_text | text | Final response delivered to the student |
| confidence_score | float | Confidence value from retrieval and validation logic |
| response_type | enum | direct_answer, clarification_needed, safe_referral |
| created_at | timestamp | Answer creation time |

**Validation rules**:
- `answer_text` must be non-empty.
- `response_type = direct_answer` requires at least one supporting source citation.
- `response_type = safe_referral` must include referral instructions or relevant office information.

### AnswerCitation

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| answer_id | UUID | Foreign key to GroundedAnswer |
| source_id | UUID | Referenced approved source |
| chunk_id | UUID | Referenced chunk or section |
| source_url | string | Canonical URL for the cited source |
| citation_text | text | Human-readable excerpt used in the answer |
| created_at | timestamp | Citation creation time |

**Validation rules**:
- Every direct answer must have at least one citation.
- Source URL and chunk must correspond to an approved source that remains active.

### SafeReferral

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| answer_id | UUID | Foreign key to GroundedAnswer |
| office_name | string | Office or department recommended |
| referral_reason | text | Why the student should contact that office |
| contact_url | string | Verified source or directory page |
| created_at | timestamp | Referral creation time |

**Validation rules**:
- Required when the system cannot provide a reliable answer.
- Contact information must be sourced from approved material or a verified university directory.

### ParsingReviewRecord

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | Referenced source |
| issue_type | enum | parse_failure, inaccessible_source, conflicting_metadata, invalid_format, missing_structure |
| issue_details | text | Summary of the problem |
| review_status | enum | pending, reviewed, rejected, accepted_with_warning |
| created_at | timestamp | Review record creation time |
| resolved_at | timestamp | Resolution timestamp if reviewed |

**Validation rules**:
- A source in `pending_review` or `rejected` may not be used for authoritative answer generation.
- Conflicting or unverified material must be flagged and excluded until reviewed.

## Relationships

- `ApprovedSource` has many `SourceContentSegment` rows.
- `SourceContentSegment` belongs to one `ApprovedSource`.
- `StudentQuestion` has one or many `GroundedAnswer` rows.
- `GroundedAnswer` has one or many `AnswerCitation` rows.
- `GroundedAnswer` may have zero or one `SafeReferral` row.
- `ParsingReviewRecord` belongs to one `ApprovedSource`.

## State transitions

- `ApprovedSource`: `approved` -> `superseded` -> `inactive`
- `ParsingReviewRecord`: `pending` -> `reviewed` -> `accepted_with_warning` or `rejected`
- `GroundedAnswer`: generated -> delivered -> logged for audit review
