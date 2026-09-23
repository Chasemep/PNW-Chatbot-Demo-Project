---

description: "Executable task list for the Authoritative University Information Chatbot"
---

# Tasks: Authoritative University Information Chatbot

**Input**: Design documents from `/specs/001-authoritative-university-chatbot/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/chat-api.md`, and `quickstart.md`

**Tests**: Included because the specification defines mandatory acceptance scenarios and measurable success criteria.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create the planned backend, frontend, data, scripts, and test directory structure in `backend/`, `frontend/`, `data/`, `scripts/`, and `backend/tests/`.
- [X] T002 Initialize the Python 3.12 backend package and dependency manifests in `backend/pyproject.toml` and `backend/requirements.txt` with FastAPI, Pydantic, SQLAlchemy, PostgreSQL/pgvector, httpx, BeautifulSoup/Trafilatura, Playwright, PyMuPDF, and pytest.
- [X] T003 [P] Initialize the React/Vite TypeScript frontend in `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, and `frontend/src/`.
- [X] T004 [P] Add host and Docker Compose environment templates in `.env.example`, `backend/.env.example`, and `frontend/.env.example` without credentials or private-record integrations.
- [X] T005 [P] Add backend/frontend formatting, linting, and test configuration in `backend/pyproject.toml`, `frontend/package.json`, and `frontend/eslint.config.js`.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T006 Configure SQLAlchemy, PostgreSQL, migrations, pgvector, and full-text search in `backend/app/persistence/database.py`, `backend/alembic.ini`, and `backend/alembic/`.
- [ ] T007 [P] Create the approved-source, source-version, content-block, schedule-entry, program/course, user-context, and answer-audit models in `backend/app/models/`, preserving the exact fields, enums, relationships, and required/nullable rules in `data-model.md`.
- [ ] T008 [P] Create typed chat, citation, limitation, escalation, health, reviewer, and ingestion-manifest schemas in `backend/app/api/schemas.py`.
- [ ] T009 [P] Implement approved PNW host/path allowlist and applicability validation in `backend/app/ingestion/source_policy.py`.
- [ ] T010 [P] Implement freshness rules requiring a reliable update date for current time-sensitive answers in `backend/app/answering/freshness.py`.
- [ ] T011 [P] Implement question classification, missing-context detection, private-record detection, and escalation decision types in `backend/app/answering/safety.py`.
- [ ] T012 Configure FastAPI application construction, versioned routing, structured errors, request logging, and readiness checks in `backend/app/main.py`, `backend/app/api/router.py`, and `backend/app/api/health.py`.
- [ ] T013 Create migrations and indexes for source URLs/hashes, citations, full-text search, and pgvector in `backend/alembic/versions/`.
- [ ] T014 [P] Add HTML/PDF, undated, conflicting, schedule, catalog, and private-record fixtures in `backend/tests/fixtures/`.
- [ ] T015 [P] Verify Python, Node/Vite, environment, build, artifact, coverage, and Docker build-context ignores in `.gitignore` and `.dockerignore`.

---

## Phase 3: User Story 1 - Get a Verified Answer to a University Question (Priority: P1) 🎯 MVP

**Goal**: Answer supported questions from current approved PNW evidence with citations, required context, and general-information limitations.

**Independent Test**: Ask a supported question through the API or browser client and verify a conversational answer, approved source title/office/link, clarification of missing context, and no official-determination guarantee.

- [ ] T016 [P] [US1] Add `POST /api/v1/chat` contract tests for validation, public no-auth behavior, typed outcomes, citations, limitations, and rejected private-record fields in `backend/tests/contract/test_chat_api.py`.
- [ ] T017 [P] [US1] Add integration tests for supported answers, missing campus/term clarification, and general-information limitations in `backend/tests/integration/test_verified_answer.py`.
- [ ] T018 [P] [US1] Implement source/version/content-block citation queries in `backend/app/retrieval/source_repository.py`.
- [ ] T019 [US1] Implement approved, applicable hybrid keyword/vector retrieval in `backend/app/retrieval/hybrid_search.py`.
- [ ] T020 [US1] Implement typed answer generation with the general-information limitation in `backend/app/answering/generator.py`.
- [ ] T021 [US1] Implement claim-to-evidence and citation completeness validation in `backend/app/answering/validator.py`.
- [ ] T022 [US1] Implement chat orchestration for context checks, retrieval, generation, validation, and answered/clarification outcomes in `backend/app/answering/chat_service.py`.
- [ ] T023 [US1] Expose `POST /api/v1/chat` without authentication or private-record inputs in `backend/app/api/chat.py`.
- [ ] T024 [US1] Implement the public chat page, message composer, citations, limitations, and clarification prompts in `frontend/src/features/chat/ChatPage.tsx`, `frontend/src/features/chat/ChatMessage.tsx`, and `frontend/src/services/chatApi.ts`.
- [ ] T025 [US1] Persist answer decisions, retrieved blocks, source versions, citations, limitations, outcomes, and validator status in `backend/app/persistence/answer_audit_repository.py`.

---

## Phase 4: User Story 2 - Find Multi-Page Policies and Procedures (Priority: P1)

**Goal**: Combine approved child pages, PDFs, handbooks, forms, and referenced links into complete procedural answers.

**Independent Test**: Ingest nested HTML/PDF fixtures and verify procedural steps, eligibility, forms/portals, source locations, and escalation when the source chain is incomplete.

- [ ] T026 [P] [US2] Add parser tests for excluding navigation/sharing/decorative content while retaining headings, lists, tables, and forms in `backend/tests/unit/test_content_parsers.py`.
- [ ] T027 [P] [US2] Add nested HTML/PDF procedure and incomplete-evidence integration tests in `backend/tests/integration/test_fragmented_procedure.py`.
- [ ] T028 [P] [US2] Implement approved manifest parsing, child traversal, parent-child links, fetch-attempt recording, and immutable artifact storage in `backend/app/ingestion/crawler.py` and `backend/app/ingestion/artifacts.py`.
- [ ] T029 [P] [US2] Implement normalized HTML extraction with section paths, links, lists, and tables in `backend/app/ingestion/html_parser.py`.
- [ ] T030 [P] [US2] Implement PDF/handbook extraction with page numbers, sections, tables, forms, and partial/unavailable statuses in `backend/app/ingestion/pdf_parser.py`.
- [ ] T031 [US2] Aggregate procedure evidence across parent and child content blocks in `backend/app/retrieval/procedure_search.py`.
- [ ] T032 [US2] Extend chat orchestration for linked references and incomplete-procedure escalation in `backend/app/answering/chat_service.py`.
- [ ] T033 [US2] Add the ingestion command and approved fixture manifest in `backend/app/ingestion/run.py` and `data/approved-sources/fixture-manifest.json`.

---

## Phase 5: User Story 3 - Get Accurate Dates and Deadline Details (Priority: P1)

**Goal**: Return term-specific, campus-aware deadlines while preserving table relationships, refund conditions, footnotes, and freshness limitations.

**Independent Test**: Ask for a deadline with campus and term and verify event/date semantics and update context; missing, stale, conflicting, archived, or undated evidence must not be presented as current.

- [ ] T034 [P] [US3] Add schedule parser tests for term, event, date/range, campus, audience, refund, and footnote fields in `backend/tests/unit/test_schedule_parser.py`.
- [ ] T035 [P] [US3] Add deadline integration tests for correct-term retrieval, missing-term clarification, archived/superseded status, conflicts, and undated escalation in `backend/tests/integration/test_deadline_answers.py`.
- [ ] T036 [P] [US3] Parse structured schedule tables into `AcademicScheduleEntry` while preserving row/column and footnote relationships in `backend/app/ingestion/schedule_parser.py`.
- [ ] T037 [P] [US3] Revalidate sources at ingestion, update-date change, and freshness-window expiry in `backend/app/ingestion/freshness_job.py`.
- [ ] T038 [US3] Retrieve schedule entries by term, campus, audience, and exact source status in `backend/app/retrieval/schedule_search.py`.
- [ ] T039 [US3] Detect and persist conflicts between materially different approved dates or rules in `backend/app/answering/conflicts.py`.
- [ ] T040 [US3] Extend chat orchestration to disclose and escalate stale, archived, superseded, conflicting, or undated deadlines in `backend/app/answering/chat_service.py`.

---

## Phase 6: User Story 5 - Escalate Questions the Chatbot Cannot Reliably Answer (Priority: P1)

**Goal**: Handle unsupported, ambiguous, conflicting, stale, and personalized questions honestly without guessing or claiming private-record access.

**Independent Test**: Ask a personalized or unsupported question and verify an explicit limitation or “I don't know,” no fabricated facts, and a verified responsible office/channel when available.

- [ ] T041 [P] [US5] Add safety unit tests for unsupported, personalized, private-record, missing-context, stale, conflicting, and unverifiable questions in `backend/tests/unit/test_answer_safety.py`.
- [ ] T042 [P] [US5] Add escalation integration tests for `escalated` and `i-dont-know` outcomes and verified contact links in `backend/tests/integration/test_escalation.py`.
- [ ] T043 [P] [US5] Implement verified escalation destination lookup from approved source contacts in `backend/app/answering/escalation.py`.
- [ ] T044 [US5] Extend answer validation to reject unsupported claims, guarantees, invented contacts, and private-record determinations in `backend/app/answering/validator.py`.
- [ ] T045 [US5] Route unsupported, personalized, conflicting, stale, and missing-evidence questions to escalation or `i-dont-know` in `backend/app/answering/chat_service.py`.
- [ ] T046 [US5] Assemble reviewer traceability responses from audits, blocks, source versions, validator status, uncertainty, and escalation in `backend/app/api/reviewer.py`.
- [ ] T047 [US5] Expose `GET /api/v1/reviewer/answers/{answer_id}` behind local/internal authorization in `backend/app/api/reviewer.py`.

---

## Phase 7: User Story 4 - Understand Programs, Courses, and Prerequisites (Priority: P2)

**Goal**: Summarize catalog programs/courses with campus applicability, availability, prerequisite chains, and non-degree-audit limitations.

**Independent Test**: Ask about a program/course with nested prerequisites and campus differences; verify the chain, applicability, missing-campus clarification, and advisor escalation when unverifiable.

- [ ] T048 [P] [US4] Add catalog parser tests for program/course records, campus tags, availability, and nested AND/OR prerequisites in `backend/tests/unit/test_catalog_parser.py`.
- [ ] T049 [P] [US4] Add integration tests for summaries, campus clarification, prerequisite chains, and degree-audit limitations in `backend/tests/integration/test_program_course_answers.py`.
- [ ] T050 [P] [US4] Extract catalog data into `ProgramCourseRecord`, preserving absent availability as unknown and source-block traceability in `backend/app/ingestion/catalog_parser.py`.
- [ ] T051 [US4] Traverse prerequisite expressions and retrieve bounded prerequisite chains in `backend/app/retrieval/catalog_search.py`.
- [ ] T052 [US4] Require campus context when program/course applicability differs between Hammond and Westville in `backend/app/answering/chat_service.py`.
- [ ] T053 [US4] Format program/course answers as informational guidance rather than official degree audits in `backend/app/answering/program_answers.py`.

---

## Phase 8: Polish and Cross-Cutting Validation

- [ ] T054 [P] Add golden evaluation cases and scoring for citation correctness, deadline accuracy, procedure completion, escalation correctness, and reviewer traceability in `backend/tests/evaluation/golden_cases.json` and `backend/tests/evaluation/test_golden_set.py`.
- [ ] T055 [P] Add frontend tests for citations, limitations, clarifications, escalation states, and public no-auth access in `frontend/tests/chat.test.tsx`.
- [ ] T056 [P] Add operational logging and metrics for fetch failures, freshness failures, validation rejection, escalation, and p95 timing in `backend/app/observability/metrics.py`.
- [ ] T057 [P] Add Docker deployment definitions for backend/frontend images and Compose services for API, ingestion, frontend, PostgreSQL/pgvector, and immutable artifacts in `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, and `.dockerignore`.
- [ ] T058 Run all scenarios from `specs/001-authoritative-university-chatbot/quickstart.md` and record results in `backend/tests/evaluation/quickstart_validation.md`.
- [ ] T059 Verify source applicability, freshness, citation locations, validator status, and audit persistence for FR-001 through FR-019 in `backend/tests/integration/test_traceability_requirements.py`.
- [ ] T060 Verify p95 response goals and visible ingestion failures under pilot fixtures in `backend/tests/performance/test_response_targets.py` and `backend/tests/integration/test_ingestion_failures.py`.

---

## Dependencies and Execution Order

- Setup (Phase 1) precedes Foundational (Phase 2), which blocks all stories.
- US1, US2, US3, US5, and US4 may proceed in parallel after Phase 2 when shared-file conflicts are avoided.
- Within each story, tests precede implementation; models/persistence precede retrieval; retrieval and safety precede endpoints.
- Phase 8 depends on the stories selected for delivery.

## Parallel Execution Examples

- T003-T005 can run in parallel after T001-T002.
- T007-T011 and T014-T015 can run in parallel after the layout exists.
- US1 tests T016-T017 can run in parallel; T018, T020, and T024 can begin independently after foundation.
- US2 parser tests T026-T027 and ingestion modules T028-T030 can run in parallel.
- US3 tests T034-T035 and parsing/revalidation T036-T037 can run in parallel.
- US5 tests T041-T042 and escalation lookup T043 can run in parallel.
- US4 tests T048-T049 and catalog extraction T050 can run in parallel.

## Implementation Strategy

### MVP

1. Complete Phase 1 and Phase 2.
2. Complete US1 and validate source-backed answers, citations, context clarification, and limitations.
3. Add US2, US3, and US5 before pilot deployment because procedures, deadlines, and escalation are P1 safety capabilities.

### Incremental Delivery

Deliver US1, then US2, US3, US5, and US4 independently, followed by Docker Compose deployment and cross-cutting evaluation.

### Traceability

The task set maps the data model entities, chat/reviewer/ingestion contracts, Docker deployment design, FR-001 through FR-019, and SC-001 through SC-007 to implementation and validation paths.
