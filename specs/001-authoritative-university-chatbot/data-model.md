# Data Model: Authoritative University Information Chatbot

## ApprovedSource

Represents an approved university source and its current ingestion state.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Stable internal identity |
| `canonical_url` | URL | Required; must match an approved PNW host/path |
| `source_type` | enum | `html`, `pdf`, `catalog`, `schedule`, `handbook`, `form`, `communication` |
| `title` | string | Required for citation |
| `issuing_office` | string nullable | Required when published by a known office |
| `campus_scope` | set | `hammond`, `westville`, `both`, or other verified scope |
| `audience_scope` | set | Prospective student, current student, faculty, staff, or verified broader scope |
| `publication_date` | date nullable | Parsed from source when available |
| `update_date` | date nullable | Required for current time-sensitive use |
| `date_confidence` | enum | `reliable`, `uncertain`, `missing` |
| `status` | enum | `current`, `future`, `archived`, `superseded`, `unavailable`, `freshness-unverified`, `conflicted` |
| `last_checked_at` | timestamp | Required after ingestion attempt |
| `content_hash` | string | Detects source changes |
| `parent_source_id` | UUID nullable | Links discovered child pages/documents to their source |

## SourceVersion

Immutable snapshot of fetched source content.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Stable snapshot identity |
| `source_id` | UUID | References `ApprovedSource` |
| `retrieved_at` | timestamp | Required |
| `artifact_uri` | URI | Points to immutable HTML/PDF artifact |
| `http_status` | integer | Records fetch result |
| `content_hash` | string | Required |
| `parser_version` | string | Required for reproducibility |
| `availability` | enum | `available`, `partial`, `unavailable` |

## ContentBlock

Citation-ready normalized content from a source version.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Stable block identity |
| `source_version_id` | UUID | Required |
| `block_type` | enum | `heading`, `paragraph`, `list`, `table`, `link`, `form_reference` |
| `content` | structured JSON | Retains rows, columns, footnotes, links, or text |
| `section_path` | string | Heading path for citations |
| `page_number` | integer nullable | Required for PDF location when available |
| `dom_anchor` | string nullable | HTML location when available |
| `embedding` | vector nullable | Used for semantic retrieval |
| `search_text` | text | Used for keyword search |

## AcademicScheduleEntry

Structured schedule data extracted from a table.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Stable identity |
| `content_block_id` | UUID | Traceability to source table |
| `term` | string | Required |
| `event` | string | Required |
| `date_or_range` | date/range | Required for a usable deadline |
| `campus_scope` | set | Preserves campus applicability |
| `audience_scope` | set | Preserves audience applicability |
| `refund_percentage` | decimal nullable | Preserves schedule consequence |
| `footnotes` | text nullable | Preserves qualifications |

## ProgramCourseRecord

Catalog-derived program or course information.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Stable identity |
| `catalog_source_id` | UUID | Required |
| `record_type` | enum | `program`, `course` |
| `code` | string nullable | Course/program code when available |
| `name` | string | Required |
| `campus_scope` | set | Required when catalog identifies campus |
| `semester_availability` | set nullable | Must not be inferred when absent |
| `prerequisite_expression` | structured JSON nullable | Preserves AND/OR relationships |
| `prerequisite_depth` | integer nullable | Supports multi-level chains |

## UserContext

Context supplied or requested during a conversation.

| Field | Type | Rules |
|---|---|---|
| `role` | enum nullable | Prospective student, current student, faculty, staff |
| `campus` | enum nullable | Hammond, Westville, both, unknown |
| `term` | string nullable | Required for term-sensitive answers |
| `program` | string nullable | Required where program changes applicability |
| `course` | string nullable | Required for course-specific questions |
| `student_status` | string nullable | Used only when relevant and supplied |

## AnswerAudit

Reviewer-traceable record of an answer decision.

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Stable identity |
| `question` | text | Minimize retention of unnecessary personal data |
| `context` | JSON | Captured `UserContext` and missing-context prompts |
| `retrieved_block_ids` | list | Every factual claim must map to retrieved blocks |
| `source_version_ids` | list | Preserves exact source versions |
| `answer` | text | Final conversational response |
| `citations` | JSON | Source title, office, URL, date, and location |
| `uncertainties` | JSON | Conflicts, freshness, or evidence limitations |
| `escalation` | JSON nullable | Responsible office and verified contact link |
| `outcome` | enum | `answered`, `clarification-required`, `escalated`, `i-dont-know` |
| `validator_status` | enum | `passed`, `rejected`, `needs-review` |
| `created_at` | timestamp | Required |

## Relationships and state rules

- One `ApprovedSource` has many immutable `SourceVersion` records.
- One `SourceVersion` has many `ContentBlock` records.
- `AcademicScheduleEntry` and `ProgramCourseRecord` point back to the exact `ContentBlock` supporting them.
- Discovered child sources reference their parent through `parent_source_id`.
- A source cannot be used as current for a time-sensitive answer when `update_date` is missing or `date_confidence` is not `reliable`.
- A source with conflicting approved evidence becomes `conflicted` until a reviewer resolves it; the chatbot escalates instead of choosing silently.
- An `AnswerAudit` is retained only as long as needed for review and evaluation, with no authentication or private-record data required.
