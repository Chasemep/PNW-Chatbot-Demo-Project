# Tasks: PNW Student Information & Advising Assistant

**Feature**: `001-pnw-info-assistant`
**Input**: `specs/001-pnw-info-assistant/` — spec.md, plan.md, data-model.md, contracts/api-contracts.md, contracts/ui-contracts.md, research.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on in-progress tasks)
- **[Story]**: Which user story this task belongs to ([US1]–[US4])
- File paths follow the project layout defined in plan.md (`backend/`, `frontend/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding, Docker wiring, and foundational configuration.

- [ ] T001 Create repository directory structure per plan.md (`backend/`, `frontend/`, `docker-compose.yml`, `.env.example`)
- [ ] T002 [P] Initialize Python 3.11 backend project with `pyproject.toml` and `requirements.txt` listing FastAPI, Uvicorn, SQLAlchemy (asyncpg), pgvector, Pydantic v2, Alembic, httpx, google-genai, pytest, pytest-asyncio, pytest-cov in `backend/`
- [ ] T003 [P] Initialize React 18 + TypeScript + Vite frontend project with `package.json`, `vite.config.ts`, `tsconfig.json`, and Tailwind CSS + Lucide React dependencies in `frontend/`
- [ ] T004 [P] Write `docker-compose.yml` at repo root with three services: `db` (pgvector/pgvector:pg16 with volume and healthcheck), `backend` (Python 3.11, Uvicorn), `frontend` (Node 20, Vite dev server), on isolated bridge network `pnw-assistant-net`
- [ ] T005 [P] Write `backend/Dockerfile` (multi-stage Python 3.11, non-root user, Uvicorn entrypoint)
- [ ] T006 [P] Write `frontend/Dockerfile` (multi-stage Node 20 + Nginx for production, Vite dev server for development)
- [ ] T007 [P] Write `.env.example` at repo root documenting required variables: `DATABASE_URL`, `GEMINI_API_KEY`, `EMBEDDING_MODEL`, `COSINE_DISTANCE_THRESHOLD` (default `0.35`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that ALL user story phases depend on — database schema, async DB session, Pydantic settings, Alembic migrations, and seed scripts.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T008 Implement `backend/src/config.py` — Pydantic BaseSettings loading `DATABASE_URL`, `GEMINI_API_KEY`, `EMBEDDING_MODEL` (default `text-embedding-004`), `COSINE_DISTANCE_THRESHOLD` (default `0.35`), `FALLBACK_HF_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`)
- [ ] T009 Implement `backend/src/database.py` — async SQLAlchemy engine and `AsyncSession` factory using asyncpg, exported `get_db` dependency for FastAPI route injection
- [ ] T010 [P] Implement `backend/src/models/document.py` — SQLAlchemy ORM models for `documents` (id UUID PK, title VARCHAR(255) NOT NULL, source_url TEXT NOT NULL UNIQUE, doc_type VARCHAR(50) NOT NULL in [html_page, pdf_handbook, academic_catalog, schedule_table], campus_scope VARCHAR(30) NOT NULL DEFAULT 'ALL', department_owner VARCHAR(100) NOT NULL, version_or_term VARCHAR(50) NULL, created_at/updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()) and `document_chunks` (id UUID PK, document_id UUID FK NOT NULL, chunk_index INTEGER NOT NULL, section_heading VARCHAR(255) NULL, content TEXT NOT NULL, embedding vector(1536) NOT NULL, tsv tsvector generated column to_tsvector('english', content), metadata JSONB NOT NULL DEFAULT '{}') per data-model.md §2.1–2.2
- [ ] T011 [P] Implement `backend/src/models/academic_term.py` — ORM model for `academic_terms` (term_code VARCHAR(20) PK, name VARCHAR(50) NOT NULL, session_type VARCHAR(30) NOT NULL DEFAULT '16_WEEK' in [16_WEEK, 1ST_8_WEEK, 2ND_8_WEEK, SUMMER], start_date DATE NOT NULL, end_date DATE NOT NULL, add_deadline DATE NOT NULL, drop_100_refund_deadline DATE NOT NULL, drop_50_refund_deadline DATE NULL, withdraw_deadline DATE NOT NULL, is_active BOOLEAN NOT NULL DEFAULT FALSE) with DB-level CHECK: start_date < drop_100_refund_deadline, drop_100_refund_deadline <= withdraw_deadline, withdraw_deadline < end_date per data-model.md §2.3
- [ ] T012 [P] Implement `backend/src/models/course.py` — ORM models for `courses` (id UUID PK, course_code VARCHAR(20) NOT NULL UNIQUE e.g. 'CS 30200', title VARCHAR(150) NOT NULL, credits INTEGER NOT NULL, campus_scope VARCHAR(30) NOT NULL DEFAULT 'ALL', college VARCHAR(100) NOT NULL, description TEXT NOT NULL) and `course_prerequisites` (id UUID PK, target_course_id UUID FK NOT NULL ON DELETE CASCADE, prereq_course_id UUID FK NOT NULL ON DELETE RESTRICT, min_grade VARCHAR(5) NOT NULL DEFAULT 'C', is_corequisite BOOLEAN NOT NULL DEFAULT FALSE, group_id INTEGER NOT NULL DEFAULT 1, logic_operator VARCHAR(5) NOT NULL DEFAULT 'AND') with DB CHECK target_course_id != prereq_course_id per data-model.md §2.4–2.5
- [ ] T013 [P] Implement `backend/src/models/contact.py` — ORM model for `administrative_contacts` (id UUID PK, office_name VARCHAR(100) NOT NULL UNIQUE, category VARCHAR(50) NOT NULL in [academic_advising, registration, bursar, dean_of_students, financial_aid, parking, graduate_school], contact_email VARCHAR(100) NOT NULL, phone_number VARCHAR(30) NOT NULL, campus VARCHAR(30) NOT NULL DEFAULT 'ALL', building_room VARCHAR(100) NOT NULL, website_url TEXT NOT NULL, office_hours VARCHAR(100) NULL) per data-model.md §2.6
- [ ] T014 [P] Implement `backend/src/models/query_log.py` — ORM models for `query_logs` (id UUID PK, sanitized_query TEXT NOT NULL, pii_detected BOOLEAN NOT NULL DEFAULT FALSE, outcome VARCHAR(30) NOT NULL in [GROUNDED_ANSWER, FAIL_SAFE_ROUTED, OUT_OF_SCOPE], applied_term VARCHAR(20) NULL, top_similarity FLOAT NULL, response_time_ms INTEGER NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()) and `response_feedback` (id UUID PK, query_id UUID FK NOT NULL ON DELETE CASCADE, sentiment VARCHAR(10) NOT NULL in [HELPFUL, UNHELPFUL], issue_category VARCHAR(30) NULL in [OUTDATED_INFO, BROKEN_LINK, INCORRECT_RULE, OTHER], comment TEXT NULL max 500 chars, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()) per data-model.md §2.7–2.8
- [ ] T015 Initialize Alembic in `backend/alembic/` — generate initial migration creating all 7 tables with all indexes: `idx_chunks_embedding` (ivfflat, vector_cosine_ops, lists=100), `idx_chunks_tsv` (GIN), `idx_chunks_doc_id` (btree) per data-model.md §2.2 (depends on T010–T014)
- [ ] T016 [P] Implement `backend/src/models/__init__.py` exporting all ORM models; implement `backend/src/main.py` — FastAPI app entrypoint with lifespan, CORS middleware, and router registration stubs
- [ ] T017 Write `backend/src/scripts/seed_data.py` — seed canonical PNW administrative contacts (Registrar, Dean of Students, Bursar, Financial Aid, Parking, Graduate School, Academic Advising) and sample `academic_terms` records (Fall 2026 Full Term, Spring 2027 Full Term) with correct date ranges per data-model.md §2.3 and §2.6
- [ ] T018 Write `backend/src/scripts/ingest_corpus.py` — ingestion script accepting PNW document URLs/PDF paths, chunks content into ~400-token semantic units with section headings, calls `text-embedding-004` (or HuggingFace fallback) for embeddings, upserts into `documents` + `document_chunks`
- [ ] T019 Implement `backend/src/api/v1/health.py` — `GET /api/v1/health` router returning `{"status":"healthy","database":"connected","pgvector_enabled":true}` per api-contracts.md §2.5; register on `backend/src/main.py`

**Checkpoint**: Database schema deployed, seed data loaded, health endpoint reachable — user story implementation can now begin.

---

## Phase 3: User Story 1 — Verified Policy & Procedure Inquiries with Source Grounding (Priority: P1) 🎯 MVP

**Goal**: Students can submit plain-language questions about PNW policies, deadlines, and procedures and receive step-by-step answers grounded in official documents with cited source links. Active term is automatically resolved. PII in queries is redacted in-flight.

**Independent Test**: Ask "How do I pay my parking ticket?" and "What is the deadline to drop a class for a full refund in Fall?" — system must return structured, step-by-step instructions with at least one verified pnw.edu citation link and the explicitly named academic term applied.

### Implementation for User Story 1

- [ ] T020 [P] [US1] Implement `backend/src/services/pii_redactor.py` — `PIIRedactor` class with `redact(query: str) -> tuple[str, bool]`; detects 9-digit PUIDs (\b\d{9}\b), 10-digit IDs, SSNs (\b\d{3}-\d{2}-\d{4}\b), and phone/email patterns; replaces with [REDACTED_PUID] / [REDACTED_CONTACT]; returns sanitized string and pii_detected boolean per research.md Decision 4 and FR-007
- [ ] T021 [P] [US1] Implement `backend/src/services/term_resolver.py` — `TermResolver` class with `resolve(db: AsyncSession, query_date: date = None) -> AcademicTerm | None`; if query_date <= add_deadline of current active term return it; if in break or past drop deadline advance to upcoming semester; annotate with display label e.g. "Showing upcoming term: Spring 2027 (current Fall drop deadlines have passed)" per FR-003 and research.md Decision 5
- [ ] T022 [P] [US1] Implement `backend/src/services/vector_search.py` — `HybridSearchEngine` class with `search(db: AsyncSession, query_text: str, limit: int = 5) -> list[DocumentChunk]`; executes concurrent dense cosine similarity (vector_cosine_ops) and PostgreSQL full-text (tsvector @@ plainto_tsquery) searches; merges by rank; returns top chunks with top_similarity score per research.md Decision 2
- [ ] T023 [US1] Implement `backend/src/services/grounded_generator.py` — `GroundedGenerator` with `generate(query: str, chunks: list[DocumentChunk], term_label: str | None) -> GeneratorResult`; strict Gemini 1.5 Flash (gemini-1.5-flash) prompt using ONLY retrieved chunks with instruction to cite official source_url for every claim; raises `InsufficientGroundingError` if cosine distance >= 0.35 or zero chunks returned; returns answer, citations, applied_term per research.md Decision 3 (depends on T020, T021, T022)
- [ ] T024 [US1] Implement `backend/src/services/fallback_router.py` — `FallbackRouter` with `route(db: AsyncSession, query: str) -> AdministrativeContact`; keyword-maps query topics to administrative_contacts categories (parking, registrar, dean_of_students, financial_aid, bursar, graduate_school); defaults to Dean of Students; satisfies FR-006 and Constitution Principle II (depends on T013)
- [ ] T025 [P] [US1] Implement `backend/src/schemas/query.py` — Pydantic v2 `QueryRequest` (query: str, min_length=2, max_length=1000) and `QueryResponse` (query_id: UUID, answer: str, outcome: Literal['GROUNDED_ANSWER','FAIL_SAFE_ROUTED','OUT_OF_SCOPE'], applied_term: str | None, citations: list[CitationItem], prerequisite_hierarchy: dict | None, department_contact: DepartmentContactInfo | None, pii_detected: bool, privacy_notice: str | None) per api-contracts.md §2.1
- [ ] T026 [US1] Implement `backend/src/api/v1/query.py` — `POST /api/v1/query` router: (1) validate request, (2) PIIRedactor.redact(), (3) TermResolver.resolve(), (4) HybridSearchEngine.search(), (5) GroundedGenerator.generate() or on InsufficientGroundingError call FallbackRouter.route(), (6) persist query_logs record, (7) return QueryResponse; register on main.py per api-contracts.md §2.1 (depends on T023, T024, T025)
- [ ] T027 [P] [US1] Implement `frontend/src/types/index.ts` — TypeScript interfaces: QueryRequest, QueryResponse, CitationItem, DepartmentContactInfo, PrerequisiteHierarchyData, PrerequisiteCourseNode, FeedbackPayload per ui-contracts.md §2
- [ ] T028 [P] [US1] Implement `frontend/src/services/api.ts` — typed fetch client wrapping POST /api/v1/query and POST /api/v1/feedback; handles network errors and non-2xx status with typed error responses
- [ ] T029 [P] [US1] Implement `frontend/src/components/Header.tsx` — PNW Assistant branding bar with scope disclaimer: "This assistant answers general PNW policy questions only. Do not enter personal IDs."
- [ ] T030 [P] [US1] Implement `frontend/src/components/InquiryInput.tsx` — single-turn query text input with submit button, loading state, suggested prompt chips ("How do I pay a parking ticket?", "What are my add/drop deadlines?", "How do I appeal a grade?", "What are prerequisites for CS 30200?"); props: { onSubmit, isLoading, disabled? } per ui-contracts.md §2.1
- [ ] T031 [P] [US1] Implement `frontend/src/components/CitationList.tsx` — renders verified official university source links with document title, section heading, and campus scope badge (HAMMOND / WESTVILLE / ALL); props: { citations: CitationItem[] } per ui-contracts.md §2.4 and FR-002
- [ ] T032 [P] [US1] Implement `frontend/src/components/PrivacyAlertBanner.tsx` — conditional dismissible banner shown when pii_detected === true, displaying the privacy_notice message from the API response; props: { message, visible } per ui-contracts.md §2.7 and FR-007
- [ ] T033 [US1] Implement `frontend/src/components/AnswerCard.tsx` — renders Markdown-formatted grounded answer body, applied term badge (e.g., "Fall 2026 Full Term"), campus applicability tags; conditionally renders CitationList, AdvisorRoutingCard, PrerequisiteTree, and InlineFeedbackWidget based on outcome; props: full AnswerCardProps per ui-contracts.md §2.2 (depends on T031)
- [ ] T034 [US1] Implement `frontend/src/App.tsx` — main container: manages query state, loading state, API call via api.ts, renders Header, InquiryInput, PrivacyAlertBanner, and AnswerCard; assembles single-turn UI flow (depends on T029, T030, T032, T033)

**Checkpoint**: User Story 1 fully functional — submit a parking ticket or drop-deadline query and receive a verified cited answer or fail-safe referral card.

---

## Phase 4: User Story 2 — Campus-Specific & Program-Specific Academic Navigation (Priority: P2)

**Goal**: Students can query multi-level course prerequisites with AND/OR logic and min grade annotations, and receive campus-specific program availability answers, in a single response.

**Independent Test**: Ask "What are all the prerequisites for CS 30200?" — system must return the complete hierarchical chain including foundational courses, min grade requirements (e.g., "C or better"), corequisites, and OR branches. Ask "Does PNW offer a Computer Science PhD program?" — system must explicitly state availability.

### Implementation for User Story 2

- [ ] T035 [US2] Implement `backend/src/services/prerequisite_service.py` — `PrerequisiteService` with `get_tree(db: AsyncSession, course_code: str, max_depth: int = 5) -> PrerequisiteHierarchyData`; recursively traverses `course_prerequisites` grouped by group_id labeled AND/OR; annotates each node with min_grade, is_corequisite, sub_prerequisites; prevents cycles; returns structured JSON matching api-contracts.md §2.3 response schema (depends on T012)
- [ ] T036 [P] [US2] Implement `backend/src/schemas/course.py` — Pydantic v2 `PrerequisiteCourseNode` (courseCode, title, minGrade, isCorequisite, subPrerequisites) and `PrerequisiteHierarchyResponse` (courseCode, title, credits, campusScope, prerequisiteGroups) per api-contracts.md §2.3
- [ ] T037 [US2] Implement `backend/src/api/v1/courses.py` — `GET /api/v1/courses/{course_code}/prerequisites` router: URL-decode course_code, call PrerequisiteService.get_tree(), return PrerequisiteHierarchyResponse; return 404 if not found; register on main.py per api-contracts.md §2.3 (depends on T035, T036)
- [ ] T038 [US2] Extend `backend/src/api/v1/query.py` — when hybrid search matches a course code pattern, additionally call PrerequisiteService.get_tree() and include result in QueryResponse.prerequisite_hierarchy; use campus_scope from courses table to annotate Hammond/Westville distinctions in composite answers (depends on T026, T035)
- [ ] T039 [P] [US2] Implement `frontend/src/components/PrerequisiteTree.tsx` — interactive progressive visual tree rendering PrerequisiteHierarchyData; shows hierarchy levels from foundational to target course; annotates each node with "Min Grade: {minGrade}", "Corequisite (concurrent OK)" tag when isCorequisite=true, and OR/AND branch dividers; supports onNodeClick to trigger new query for a prerequisite course; props: { data: PrerequisiteHierarchyData, onNodeClick? } per ui-contracts.md §2.3 and FR-005
- [ ] T040 [US2] Integrate PrerequisiteTree into `frontend/src/components/AnswerCard.tsx` — render conditionally when prerequisiteHierarchy is non-null; pass onNodeClick to trigger new App query for the clicked course (depends on T033, T039)

**Checkpoint**: User Stories 1 AND 2 independently functional — grounded policy answers AND full prerequisite tree visualization both work end-to-end.

---

## Phase 5: User Story 3 — Fail-Safe Routing & Human Advisor Escalation (Priority: P3)

**Goal**: When a student asks an ungrounded, personalized, or out-of-scope question, the system clearly states it cannot answer and immediately presents the correct university office with full contact info.

**Independent Test**: Ask "Why is my registration hold active?" and "What is my scheduling PIN?" — system must NOT guess and MUST display a deterministic AdvisorRoutingCard with the Office of the Registrar contact info (office_name, contact_email, phone_number, building_room).

### Implementation for User Story 3

- [ ] T041 [P] [US3] Implement `backend/src/schemas/contact.py` — Pydantic v2 `DepartmentContactInfo` (officeName, contactEmail, phoneNumber, campus, buildingRoom, websiteUrl, officeHours) per ui-contracts.md §2.5 and api-contracts.md §2.1 fail-safe response shape
- [ ] T042 [US3] Extend `backend/src/api/v1/query.py` — add explicit out-of-scope detection gate before hybrid search: if query lacks university-related intent signals after PII redaction, set outcome='OUT_OF_SCOPE', return scope-limiting message, and include Dean of Students contact in department_contact (depends on T026)
- [ ] T043 [US3] Extend `backend/src/services/fallback_router.py` — complete topic keyword mapping for all contact categories (parking, registration, financial_aid, bursar, dean_of_students, graduate_school, academic_advising) with priority ordering; verify query_log records outcome='FAIL_SAFE_ROUTED' for all low-confidence paths; ensure 100% of fail-safe paths return non-null department_contact (depends on T024)
- [ ] T044 [P] [US3] Implement `frontend/src/components/AdvisorRoutingCard.tsx` — styled escalation card displaying office name, email (mailto link), phone, building/room, office hours, and official website link; visually distinct from AnswerCard (e.g., "Contact Your Advisor" header, alert icon); props: { contact: DepartmentContactInfo, reason? } per ui-contracts.md §2.5 and FR-006
- [ ] T045 [US3] Integrate AdvisorRoutingCard into `frontend/src/components/AnswerCard.tsx` — render when outcome === 'FAIL_SAFE_ROUTED' or 'OUT_OF_SCOPE' and department_contact is non-null; hide CitationList in this state (depends on T033, T044)

**Checkpoint**: All three user stories independently functional — grounded policy answers (US1), prerequisite trees (US2), and fail-safe routing (US3) all work end-to-end.

---

## Phase 6: User Story 4 — Graduate Student Milestone & Plan of Study Guidance (Priority: P4)

**Goal**: Graduate students can ask about Plan of Study submission, committee approvals, and graduate admission procedures and receive complete official step-by-step sequences with citation links.

**Independent Test**: Ask "How do I submit my plan of study for the Master's in Computer Science?" — system must return an ordered workflow (course draft → advisor approval → Graduate School portal submission → department sign-off) with citations to official Graduate School policy pages.

### Implementation for User Story 4

- [ ] T046 [US4] Extend `backend/src/scripts/ingest_corpus.py` — add ingestion entries for Graduate School documents: Graduate Admission/Requirements page, Master's Plan of Study form, Graduate School policy portal; ensure campus_scope='ALL' and appropriate doc_type set; re-run ingestion against updated source list (depends on T018)
- [ ] T047 [US4] Extend `backend/src/services/fallback_router.py` and `backend/src/scripts/seed_data.py` — ensure category='graduate_school' contact record exists in administrative_contacts seed and keyword routing maps graduate-related queries (plan of study, committee, thesis, graduate admission, master's) to that contact (depends on T043)
- [ ] T048 [US4] Validate end-to-end: submit "How do I submit my plan of study?" via POST /api/v1/query; verify outcome='GROUNDED_ANSWER', response body contains ordered workflow steps, and citations array includes at least one Graduate School pnw.edu URL; if corpus coverage insufficient, adjust chunking parameters in ingest_corpus.py and re-ingest (depends on T026, T046)

**Checkpoint**: All four user stories functional — graduate Plan of Study queries return grounded, cited workflow answers.

---

## Phase 7: Inline Feedback & Academic Terms API (Cross-Story Features)

**Purpose**: Anonymous feedback collection (FR-012, SC-007) and academic terms endpoint (FR-003) span all user stories.

- [ ] T049 [P] Implement `backend/src/schemas/feedback.py` — Pydantic v2 `FeedbackRequest` (queryId UUID, sentiment Literal['HELPFUL','UNHELPFUL'], issueCategory optional Literal['OUTDATED_INFO','BROKEN_LINK','INCORRECT_RULE','OTHER'], comment optional str max_length=500) and `FeedbackResponse` (status: str, feedbackId: UUID) per api-contracts.md §2.2
- [ ] T050 [P] Implement `backend/src/api/v1/feedback.py` — `POST /api/v1/feedback` router: validate request, verify query_id exists in query_logs, insert response_feedback record, return FeedbackResponse(status="received", feedback_id=...); return 404 if query_id not found; register on main.py per api-contracts.md §2.2 (depends on T049)
- [ ] T051 [P] Implement `backend/src/api/v1/terms.py` — `GET /api/v1/terms/active` router: query academic_terms using TermResolver logic to return active and upcoming term records as structured JSON; register on main.py per api-contracts.md §2.4 (depends on T021)
- [ ] T052 [P] Implement `frontend/src/components/InlineFeedbackWidget.tsx` — thumbs up/down buttons below each AnswerCard; on thumbs-down click reveal modal with optional issue category dropdown (OUTDATED_INFO, BROKEN_LINK, INCORRECT_RULE, OTHER) and optional comment textarea (max 500 chars); on submit call POST /api/v1/feedback; show confirmation on success; props: { queryId, onFeedbackSubmitted? } per ui-contracts.md §2.6 and FR-012
- [ ] T053 [US1] Integrate InlineFeedbackWidget into `frontend/src/components/AnswerCard.tsx` — render for ALL response outcomes (grounded, fail-safe, and out-of-scope); pass queryId from QueryResponse (depends on T033, T052)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, error handling hardening, accessibility, corpus ingestion, and documentation.

- [ ] T054 [P] Add global error handling middleware to `backend/src/main.py` — catch unhandled exceptions, return RFC 7807 {"detail": "..."} format; add request logging middleware recording method, path, and response time; ensure all 400/404/500 error shapes match api-contracts.md §3
- [ ] T055 [P] Add input validation to `backend/src/api/v1/query.py` — reject empty/whitespace-only queries with 400 Bad Request; reject queries exceeding 1000 characters with 400 Bad Request; add course_code URL decoding and 404 handling in `backend/src/api/v1/courses.py`
- [ ] T056 [P] Run `backend/src/scripts/seed_data.py` and `backend/src/scripts/ingest_corpus.py` against all corpus documents from initial corpus review (Parking Regulations, Academic Schedule tables, Academic Catalog prerequisites, Graduate School Admission, Accessibility Policy, Academic Integrity, Student Handbook PDF, Classroom Behavior Policy PDF, Information Services Policy, Dean of Students Policies); verify document_chunks count and embedding coverage
- [ ] T057 [P] Validate `quickstart.md` scenarios end-to-end in Docker Compose stack: (1) parking ticket payment query returns grounded answer; (2) CS 30200 prerequisites query returns full tree; (3) registration hold query returns Registrar routing card; (4) Plan of Study query returns graduate workflow; (5) PUID-containing query triggers PII redaction banner
- [ ] T058 [P] Accessibility and responsive design pass on `frontend/` — verify keyboard navigation, ARIA labels on InquiryInput submit button, AnswerCard, PrerequisiteTree nodes, InlineFeedbackWidget buttons, AdvisorRoutingCard contact links; verify layout usable on mobile screen widths
- [ ] T059 [P] Update `README.md` at repo root with project description, prerequisites (Docker, Gemini API key), one-command launch (`docker compose up --build`), environment variable reference, and link to `specs/001-pnw-info-assistant/quickstart.md` for validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
- **US1 (Phase 3)**: Depends on Phase 2 — MVP delivery target
- **US2 (Phase 4)**: Depends on Phase 2 — can proceed in parallel with US1 after foundational; T038 depends on US1's T026
- **US3 (Phase 5)**: Depends on Phase 2 and US1's query.py router (T026)
- **US4 (Phase 6)**: Depends on US1 pipeline (T026) and ingest script (T018)
- **Feedback & Terms (Phase 7)**: Depends on T014 (query_logs model) and T021 (TermResolver)
- **Polish (Phase 8)**: Depends on all prior phases complete

### User Story Dependencies

- **US1**: Can start immediately after Foundational — no story dependencies
- **US2**: Can start after Foundational — parallel with US1; T038 depends on T026
- **US3**: T042, T043 extend US1's query.py (T026) and fallback_router.py (T024)
- **US4**: Extends corpus ingestion (T018) and fail-safe routing (T043); minimal new code

### Parallel Opportunities

- **Phase 1**: T002–T007 all parallelizable
- **Phase 2**: T010–T014 all parallelizable (separate model files); T015 depends on T010–T014
- **Phase 3**: T020–T022, T027–T032 all parallelizable; T023 depends on T020–T022; T026 depends on T023–T025
- **Phase 4**: T035, T036, T039 parallelizable; T037 depends on T035–T036; T040 depends on T033, T039
- **Phase 7**: T049–T052 all parallelizable; T053 depends on T033, T052

---

## Parallel Example: User Story 1

```bash
# Parallel backend services (different files, no deps):
Task T020: backend/src/services/pii_redactor.py
Task T021: backend/src/services/term_resolver.py
Task T022: backend/src/services/vector_search.py

# Then serially:
Task T023: backend/src/services/grounded_generator.py  (depends on T020–T022)
Task T024: backend/src/services/fallback_router.py     (depends on T013)
Task T025: backend/src/schemas/query.py
Task T026: backend/src/api/v1/query.py                 (depends on T023–T025)

# Parallel frontend (different files, no deps):
Task T027: frontend/src/types/index.ts
Task T028: frontend/src/services/api.ts
Task T029: frontend/src/components/Header.tsx
Task T030: frontend/src/components/InquiryInput.tsx
Task T031: frontend/src/components/CitationList.tsx
Task T032: frontend/src/components/PrivacyAlertBanner.tsx

# Then assemble:
Task T033: frontend/src/components/AnswerCard.tsx       (depends on T031)
Task T034: frontend/src/App.tsx                         (depends on T029–T033)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete **Phase 1**: Setup — Docker stack running
2. Complete **Phase 2**: Foundational — DB schema + seed data + health check green
3. Complete **Phase 3**: User Story 1 — grounded query endpoint + React UI
4. **STOP and VALIDATE**: Run quickstart.md scenario #1 (parking ticket query)
5. Demo to stakeholders if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Grounded policy answers + PII redaction → Test → **MVP Demo**
3. Add US2 → Prerequisite tree visualization → Test → Demo
4. Add US3 → Fail-safe advisor routing → Test → Demo
5. Add US4 → Graduate Plan of Study guidance → Test → Demo
6. Phase 7 + 8 → Feedback widget + polish → Final delivery

### Parallel Team Strategy

With multiple developers after Phase 2 completion:
- **Developer A**: US1 backend (PIIRedactor, TermResolver, HybridSearchEngine, GroundedGenerator)
- **Developer B**: US1 frontend (InquiryInput, AnswerCard, CitationList, App)
- **Developer C**: US2 (PrerequisiteService + courses endpoint + PrerequisiteTree)
- **Developer D**: US3 (AdvisorRoutingCard + out-of-scope gate) + Phase 7 (FeedbackWidget + feedback endpoint)

---

## Notes

- `[P]` tasks operate on distinct files with no in-progress dependencies — safe to run concurrently
- `[Story]` label maps each task to its user story for independent traceability and MVP scoping
- **Constitution Principle I (Grounded Answers)**: Every task involving LLM generation (T023, T026) must enforce citation requirements — the Gemini prompt must refuse to answer without verified official source URLs
- **Constitution Principle II (Fail Safely)**: Every task extending the query pipeline (T026, T042, T043) must guarantee a non-null department_contact when outcome != 'GROUNDED_ANSWER'
- Commit after each task or logical group; validate quickstart.md scenarios after each story checkpoint
- Stop at any checkpoint to demo the current story increment independently
