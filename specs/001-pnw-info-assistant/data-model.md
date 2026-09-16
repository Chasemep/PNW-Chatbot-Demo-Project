# Data Model: PNW Student Information & Advising Assistant

**Feature**: `001-pnw-info-assistant`
**Date**: 2026-09-16
**Status**: Complete

## 1. Relational & Vector Schema Overview

The database uses **PostgreSQL 16** with the **`pgvector`** extension. The schema serves two critical complementary roles:
1. **Semantic & Full-Text Search**: Ingested policy documents, regulations, handbooks, and PDF chunks with dense vector embeddings (`vector(1536)` / `vector(768)`) and GIN-indexed full-text vectors (`tsvector`).
2. **Deterministic Relational Knowledge**: Academic terms, multi-subterm refund schedules, course prerequisite dependency graphs, administrative office contact directories, and anonymous feedback logs.

```
 +------------------------+         +--------------------------+
 |       documents        | 1 --- * |     document_chunks      |
 | (title, url, campus)   |         | (text, embedding, tsv)   |
 +------------------------+         +--------------------------+
 
 +------------------------+         +--------------------------+
 |        courses         | 1 --- * |   course_prerequisites   |
 | (code, title, campus)  |         | (min_grade, coreq, AND/OR) |
 +------------------------+         +--------------------------+
 
 +------------------------+         +--------------------------+
 |   academic_terms       |         | administrative_contacts  |
 | (dates, drop cutoffs)  |         | (offices, phones, emails)|
 +------------------------+         +--------------------------+
 
 +------------------------+         +--------------------------+
 |       query_logs       | 1 --- * |    response_feedback     |
 | (redacted_query, pii)  |         | (sentiment, issue report)|
 +------------------------+         +--------------------------+
```

---

## 2. Entity Definitions

### 2.1 `documents`
Represents an authoritative PNW university policy, handbook, catalog section, or regulatory publication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Unique document identifier |
| `title` | `VARCHAR(255)` | NOT NULL | Title of the policy or guide (e.g., "Parking Regulations") |
| `source_url` | `TEXT` | NOT NULL, UNIQUE | Canonical live URL on official PNW domain (`pnw.edu`) |
| `doc_type` | `VARCHAR(50)` | NOT NULL | `html_page`, `pdf_handbook`, `academic_catalog`, `schedule_table` |
| `campus_scope` | `VARCHAR(30)` | NOT NULL, DEFAULT `'ALL'` | `'HAMMOND'`, `'WESTVILLE'`, or `'ALL'` |
| `department_owner` | `VARCHAR(100)` | NOT NULL | Responsible department (e.g., "Dean of Students", "Registrar") |
| `version_or_term` | `VARCHAR(50)` | NULL | Effective academic year or publication term |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | Initial ingestion timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | Last synchronization timestamp |

---

### 2.2 `document_chunks`
Represents a chunked semantic section of a university document equipped for hybrid dense-vector and lexical retrieval.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Unique chunk ID |
| `document_id` | `UUID` | NOT NULL, REFERENCES `documents(id)` ON DELETE CASCADE | Parent document reference |
| `chunk_index` | `INTEGER` | NOT NULL | Sequential chunk order in parent document |
| `section_heading` | `VARCHAR(255)` | NULL | Immediate section/header (e.g., "Student Citation Appeals") |
| `content` | `TEXT` | NOT NULL | Raw text content of the chunk |
| `embedding` | `vector(1536)` | NOT NULL | Dense vector embedding for semantic cosine distance search |
| `tsv` | `tsvector` | Generated (`to_tsvector('english', content)`) | GIN indexed for exact keyword and code matching |
| `metadata` | `JSONB` | NOT NULL, DEFAULT `'{}'::jsonb` | Extracted table columns, step numbering, or tags |

**Indexes**:
- `CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`
- `CREATE INDEX idx_chunks_tsv ON document_chunks USING gin(tsv);`
- `CREATE INDEX idx_chunks_doc_id ON document_chunks(document_id);`

---

### 2.3 `academic_terms`
Stores official semester dates, deadline thresholds, and drop/refund cutoff points for Fall, Spring, and Summer sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `term_code` | `VARCHAR(20)` | Primary Key (e.g., `'FALL_2026'`) | Deterministic term identifier |
| `name` | `VARCHAR(50)` | NOT NULL | Display name (e.g., "Fall 2026 Full Term") |
| `session_type` | `VARCHAR(30)` | NOT NULL, DEFAULT `'16_WEEK'` | `'16_WEEK'`, `'1ST_8_WEEK'`, `'2ND_8_WEEK'`, `'SUMMER'` |
| `start_date` | `DATE` | NOT NULL | First day of classes |
| `end_date` | `DATE` | NOT NULL | Last day of final exams |
| `add_deadline` | `DATE` | NOT NULL | Last day to add courses without instructor permission |
| `drop_100_refund_deadline`| `DATE` | NOT NULL | Last day for 100% tuition refund (drop cutoff) |
| `drop_50_refund_deadline` | `DATE` | NULL | Last day for 50% tuition refund |
| `withdraw_deadline` | `DATE` | NOT NULL | Last day to withdraw with a 'W' grade |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Current administrative active term flag |

**Validation Rules**:
- `start_date < drop_100_refund_deadline`
- `drop_100_refund_deadline <= withdraw_deadline`
- `withdraw_deadline < end_date`

---

### 2.4 `courses`
Authoritative course catalog registry for Hammond and Westville offerings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Unique course record |
| `course_code` | `VARCHAR(20)` | NOT NULL, UNIQUE (e.g., `'CS 30200'`) | Subject and number identifier |
| `title` | `VARCHAR(150)` | NOT NULL | Official course title |
| `credits` | `INTEGER` | NOT NULL | Credit hours |
| `campus_scope` | `VARCHAR(30)` | NOT NULL, DEFAULT `'ALL'` | `'HAMMOND'`, `'WESTVILLE'`, or `'ALL'` |
| `college` | `VARCHAR(100)` | NOT NULL | Offering college (e.g., "College of Engineering & Sciences") |
| `description` | `TEXT` | NOT NULL | Catalog course description |

---

### 2.5 `course_prerequisites`
Directed dependency table modeling progressive prerequisite chains, minimum grade cutoffs, and AND/OR logical groupings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Record ID |
| `target_course_id` | `UUID` | NOT NULL, REFERENCES `courses(id)` ON DELETE CASCADE | The course to be taken |
| `prereq_course_id` | `UUID` | NOT NULL, REFERENCES `courses(id)` ON DELETE RESTRICT | The required prerequisite course |
| `min_grade` | `VARCHAR(5)` | NOT NULL, DEFAULT `'C'` | Minimum required grade (e.g., `'C'`, `'C-'`, `'D'`) |
| `is_corequisite` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Whether course may be taken concurrently |
| `group_id` | `INTEGER` | NOT NULL, DEFAULT 1 | Group identifier for grouping OR conditions |
| `logic_operator` | `VARCHAR(5)` | NOT NULL, DEFAULT `'AND'` | `'AND'` (cross-group) or `'OR'` (within group) |

**Validation Rules**:
- A course cannot be its own prerequisite (`target_course_id != prereq_course_id`).
- Cycles are prevented through database validation triggers on insert/update.

---

### 2.6 `administrative_contacts`
Official departmental routing directory for Constitution Principle II (Fail Safely).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Department record ID |
| `office_name` | `VARCHAR(100)` | NOT NULL, UNIQUE | Official office title (e.g., "Office of the Registrar") |
| `category` | `VARCHAR(50)` | NOT NULL | Category: `academic_advising`, `registration`, `bursar`, `dean_of_students`, `financial_aid`, `parking`, `graduate_school` |
| `contact_email` | `VARCHAR(100)` | NOT NULL | Verified official university email |
| `phone_number` | `VARCHAR(30)` | NOT NULL | Official campus phone number |
| `campus` | `VARCHAR(30)` | NOT NULL, DEFAULT `'ALL'` | `'HAMMOND'`, `'WESTVILLE'`, or `'ALL'` |
| `building_room` | `VARCHAR(100)` | NOT NULL | Physical campus location (e.g., "Lawshe Hall, Room 130") |
| `website_url` | `TEXT` | NOT NULL | Official department website |
| `office_hours` | `VARCHAR(100)` | NULL | Typical walk-in and phone hours |

---

### 2.7 `query_logs`
Logs single-turn interactions with in-flight PII sanitization. Never stores unmasked student IDs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Query trace ID |
| `sanitized_query`| `TEXT` | NOT NULL | User query with PII scrubbed to `[REDACTED_PUID]` |
| `pii_detected` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Whether PII was detected and sanitized |
| `outcome` | `VARCHAR(30)` | NOT NULL | `'GROUNDED_ANSWER'`, `'FAIL_SAFE_ROUTED'`, `'OUT_OF_SCOPE'` |
| `applied_term` | `VARCHAR(20)` | NULL | Academic term applied during deadline lookup |
| `top_similarity` | `FLOAT` | NULL | Cosine similarity score of primary retrieved chunk |
| `response_time_ms`| `INTEGER`| NOT NULL | Total processing latency in milliseconds |
| `created_at` | `TIMESTAMPTZ`| NOT NULL, DEFAULT `NOW()` | Timestamp |

---

### 2.8 `response_feedback`
Anonymous inline user feedback for auditing policy accuracy and link integrity (FR-012, SC-007).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | Primary Key, default `gen_random_uuid()` | Feedback ID |
| `query_id` | `UUID` | NOT NULL, REFERENCES `query_logs(id)` ON DELETE CASCADE | Associated query trace |
| `sentiment` | `VARCHAR(10)` | NOT NULL | `'HELPFUL'` or `'UNHELPFUL'` |
| `issue_category` | `VARCHAR(30)` | NULL | `'OUTDATED_INFO'`, `'BROKEN_LINK'`, `'INCORRECT_RULE'`, `'OTHER'` |
| `comment` | `TEXT` | NULL | Optional user feedback comment (max 500 chars) |
| `created_at` | `TIMESTAMPTZ`| NOT NULL, DEFAULT `NOW()` | Timestamp |
