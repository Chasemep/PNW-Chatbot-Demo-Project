# Research & Technical Decisions: PNW Student Information & Advising Assistant

**Feature**: `001-pnw-info-assistant`
**Date**: 2026-09-16
**Status**: Completed

## 1. Architecture & Tech Stack Selection

### Context & Requirements
The PNW Student Information & Advising Assistant requires an unauthenticated, accessible, single-turn stateless web interface backed by grounded university policy information, structured prerequisite trees, calendar deadline tables, and human advisor fail-safe routing.
The user mandated: **FastAPI**, **React**, **PostgreSQL with pgvector**, and **Docker** for deployment.

### Decision 1: Full-Stack Web Application Layout
- **Decision**: Decouple the system into `backend/` (FastAPI + Python 3.11) and `frontend/` (React + TypeScript + Vite), orchestrated via `docker-compose.yml`.
- **Rationale**:
  - FastAPI provides native async execution, automatic OpenAPI schema generation, fast Pydantic v2 serialization, and seamless integration with Python ML/NLP libraries.
  - React with TypeScript delivers a responsive, accessible single-turn interface with interactive prerequisite hierarchy rendering and inline feedback widgets.
  - Clear separation of concerns enables independent containerization and parallel testing.
- **Alternatives Considered**:
  - *Full-stack Next.js/Node*: Rejected because Python has richer ecosystem support for vector embeddings, document chunking, and tabular policy parsing.
  - *Single Monolithic FastAPI with Jinja2 templates*: Rejected because rendering dynamic prerequisite graphs and smooth interactive feedback widgets is significantly cleaner in React.

---

## 2. Storage & Vector Retrieval Strategy

### Decision 2: PostgreSQL with pgvector & Hybrid Retrieval
- **Decision**: Use PostgreSQL 16 with the `pgvector` extension (`pgvector/pgvector:pg16` Docker image) combining dense vector embeddings with PostgreSQL Full-Text Search (tsvector + GIN indexes).
- **Rationale**:
  - **Grounded Retrieval (Constitution Principle I)**: Policy documents and handbook sections are chunked into semantic units with metadata (source URL, title, document section, campus scope).
  - **Exact Code Matching**: Catalog queries like "CS 30200" or "MA 16300" require exact keyword lookup; vector search alone can experience semantic drift on alphanumeric course codes. Combining full-text search with vector cosine similarity (hybrid search) ensures 100% precision on course identifiers.
  - **Relational Integrity**: Academic terms, tabular refund schedules, and course prerequisite graphs are stored in relational tables with foreign keys, ensuring deterministic queries for dates and prerequisite chains.
  - **Operational Simplicity**: Avoids maintaining a separate vector database (e.g. Pinecone, Chroma, Qdrant) alongside a relational database. Everything resides in a single transactional PostgreSQL instance.
- **Alternatives Considered**:
  - *Standalone Vector DB (Chroma/Qdrant/Milvus)*: Adds multi-container operational overhead without relational querying capabilities needed for prerequisite graphs and calendar schedules.
  - *Pure Full-Text Search (PostgreSQL without pgvector)*: Fails to understand natural language phrasing students use (e.g., "How do I dispute an unfair grade?" vs. "Academic Regulations: Grade Appeal Procedure").

---

## 3. Groundedness Verification & Fail-Safe Routing (Constitution Principles I & II)

### Decision 3: Two-Tier Groundedness Gate & Fallback Handler
- **Decision**:
  1. In-flight PII redaction and out-of-scope detection gate.
  2. Cosine distance threshold gate (< 0.35 cosine distance / > 0.65 similarity).
  3. Strict generation prompt containing ONLY retrieved official chunks, requiring source URL attribution for every claim.
  4. Automatic Fallback Handler: If similarity is below threshold, official text is ambiguous/conflicting, or query is outside PNW policy bounds, the system automatically returns an official routing card citing the relevant department contact (Dean of Students, Registrar, Bursar, Advising) without guessing.
- **Rationale**:
  - Enforces Constitution Principle I (Grounded Answers) by verifying that generated responses can only be constructed from verified, retrieved chunks.
  - Enforces Constitution Principle II (Fail Safely) by deterministically returning official office contacts whenever confidence is insufficient or personal account info is requested.
- **Alternatives Considered**:
  - *Unconstrained LLM generation with post-hoc fact checking*: High risk of hallucination; violates Principle I and II.

---

## 4. In-Flight PII Redaction & FERPA Safeguard

### Decision 4: Deterministic Regex + Pattern Scrubbing Middleware
- **Decision**: Implement an in-flight redaction middleware before vector search or persistence:
  - Detects 9-digit Purdue University IDs (PUID: `\b\d{9}\b` or `\b\d{10}\b`), Social Security numbers (`\b\d{3}-\d{2}-\d{4}\b`), and phone numbers/emails.
  - Masks detected PII with `[REDACTED_PUID]` / `[REDACTED_CONTACT]`.
  - Sets `pii_detected=True` flag in response payload to trigger a student-facing advisory note: *"Reminder: Please do not submit student ID numbers or confidential personal details."*
- **Rationale**:
  - Directly satisfies clarified requirement FR-007.
  - Ensures no confidential student records or identifiers enter database query logs or external LLM contexts.

---

## 5. Academic Term Dynamic Resolution

### Decision 5: Calendar-Based Date Range Resolution
- **Decision**: Store structured academic calendar ranges in `academic_terms` table (`term_code`, `name`, `start_date`, `end_date`, `add_drop_deadline`, `refund_100_deadline`, `withdraw_deadline`).
  - If a query specifies a term (e.g., "Spring 2027"), match directly.
  - If no term is specified, evaluate `CURRENT_DATE`:
    - If `CURRENT_DATE <= add_drop_deadline`, select current active term.
    - If `CURRENT_DATE > add_drop_deadline` or in intersession break, automatically resolve to the upcoming semester and clearly annotate: *"Showing upcoming term: Spring 2027 (current Fall drop deadlines have passed)"*.
- **Rationale**:
  - Solves clarified requirement FR-003 and prevents delivering stale refund/drop deadlines.

---

## 6. Prerequisite Hierarchy Modeling & Rendering

### Decision 6: Relational Prerequisite Graph & Progressive Tree Rendering
- **Decision**:
  - Store courses in `courses` and dependencies in `course_prerequisites` (`course_id`, `prerequisite_course_id`, `min_grade`, `is_corequisite`, `group_id`, `logic_operator`: 'AND' | 'OR').
  - Recursively query full dependency chains up to 5 levels deep.
  - The API returns a structured recursive JSON node tree.
  - React renders an expandable visual hierarchy showing:
    - Foundational → Intermediate → Target course.
    - Explicit tags for `Min Grade: C or higher`, `Corequisite (concurrent permitted)`, and `OR` branch selectors.
- **Rationale**:
  - Solves clarified requirement FR-005 and addresses student interview pain points where hidden grade cutoffs delayed graduation.

---

## 7. Containerization & Deployment Setup

### Decision 7: Docker Compose with 3 Services
- **Decision**:
  - `db`: `pgvector/pgvector:pg16` with volume persistence and healthcheck.
  - `backend`: Multi-stage Python 3.11 Dockerfile running Uvicorn with auto-reload in dev, non-root user in production. Includes database migration & seed scripts for initial PNW corpus.
  - `frontend`: Multi-stage Node 20 Dockerfile (Vite build served via lightweight Nginx in production, or Vite dev server).
  - Network: Isolated internal bridge network `pnw-assistant-net`.
- **Rationale**:
  - Fully containerized reproducible setup; one-command launch via `docker compose up --build`.
