# Data Model: Purdue Policy Chatbot and RAG Knowledge Base

## Overview

The system stores approved university source content, immutable source versions, preparation releases, structure-aware retrieval chunks, embeddings, user questions, answer events, and review records. PostgreSQL is the primary relational store; pgvector stores chunk embeddings for retrieval. The active release pointer is the only release eligible for current answers.

## Entity Definitions

### ApprovedSource

| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| title | string | Official document or page title |
| source_url | string | Canonical public URL used for citations |
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
- `source_url` must be an absolute HTTP(S) URL for web pages and documents loaded from local paths; remote `location` values may supply it by default.
- `review_status` cannot be `approved` if `is_active = false`.
- `superseded_by` is required when `review_status = superseded`.

### SourceVersion

| Field | Type | Description |
|---|---|---|
| id | UUID | Immutable fetched/imported source version |
| source_id | UUID | Foreign key to ApprovedSource |
| content_hash | string | SHA-256 hash of source bytes or canonical fetched content |
| fetched_at | timestamp | Time content was fetched/imported |
| parser_name | string | Parser and version used |
| parse_status | enum | succeeded, failed, incomplete |
| byte_size | integer | Input size |
| original_location | string | URL or file path used for preparation |

**Validation rules**:
- The same source version content hash is idempotent within a preparation release.
- `parse_status = succeeded` is required before chunks can be embedded.
- A version with failed or incomplete parsing cannot be used for authoritative retrieval.

### KnowledgeBaseRelease

| Field | Type | Description |
|---|---|---|
| id | UUID | Preparation run/release identifier |
| status | enum | preparing, validated, active, rejected, retired |
| embedding_model | string | Pinned embedding model/configuration |
| embedding_dimension | integer | Expected vector dimension |
| started_at | timestamp | Preparation start |
| validated_at | timestamp | Gate completion time |
| activated_at | timestamp | Atomic publish time |
| failure_summary | text | Operator-visible gate failures |

**Validation rules**:
- Only one release may be `active`.
- An active release must have passed all required validation gates.
- A rejected release cannot be used by retrieval.

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
| release_id | UUID | Foreign key to KnowledgeBaseRelease |
| structural_path | string | Heading/list/table/callout path within the source |
| content_kind | enum | heading, paragraph, table, list, sidebar, callout, continuation |
| location_label | string | Human-readable page/section/table location |
| chunk_hash | string | Stable hash of normalized chunk content and context |

**Validation rules**:
- `content_text` cannot be empty.
- `source_id` must reference an active or previously reviewed source.
- `release_id` must reference the release that produced the chunk.
- `embedding` must have the release's configured dimension and finite values.
- `content_kind` and `structural_path` must be retained for citation and review.
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

### PreparationValidation

| Field | Type | Description |
|---|---|---|
| id | UUID | Validation result identifier |
| release_id | UUID | Release being checked |
| check_name | string | Named gate, such as metadata, parse, vector, or retrieval smoke test |
| status | enum | passed, failed, warning |
| measured_value | string | Machine-readable result or count |
| details | text | Diagnostic information |
| created_at | timestamp | Check time |

**Validation rules**:
- A release cannot activate with a failed required check.
- Warnings must be visible in the release report and cannot silently change source authority.

## Relationships

- `ApprovedSource` has many `SourceContentSegment` rows.
- `ApprovedSource` has many `SourceVersion` rows.
- `KnowledgeBaseRelease` has many `SourceContentSegment` and `PreparationValidation` rows.
- `SourceContentSegment` belongs to one `ApprovedSource`.
- `StudentQuestion` has one or many `GroundedAnswer` rows.
- `GroundedAnswer` has one or many `AnswerCitation` rows.
- `GroundedAnswer` may have zero or one `SafeReferral` row.
- `ParsingReviewRecord` belongs to one `ApprovedSource`.
- `SourceContentSegment` belongs to one `KnowledgeBaseRelease`.

## State transitions

- `ApprovedSource`: `approved` -> `superseded` -> `inactive`
- `ParsingReviewRecord`: `pending` -> `reviewed` -> `accepted_with_warning` or `rejected`
- `KnowledgeBaseRelease`: `preparing` -> `validated` -> `active` -> `retired`, or `preparing` -> `rejected`
- `GroundedAnswer`: generated -> delivered -> logged for audit review
