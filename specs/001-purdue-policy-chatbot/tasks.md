---

description: "Phased implementation tasks for the Purdue policy chatbot and RAG knowledge-base workflow"
---

# Tasks: Purdue Policy Chatbot and RAG Knowledge-Base Preparation

**Input**: Design documents from `/specs/001-purdue-policy-chatbot/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Organization**: Work is divided into executable phases. User-story tasks remain labeled `[US1]` through `[US4]` for traceability.

## Phase 1: Project Setup

**Purpose**: Create the application, test, and deployment skeleton.

- [X] T001 Create `backend/`, `frontend/`, `docker/`, and required package entry points in `backend/app/main.py` and `frontend/src/`
- [X] T002 Initialize the Python 3.12 `uv` project in `backend/pyproject.toml`, add runtime dependencies with `uv add`, add development dependencies with `uv add --dev`, and commit the generated `backend/uv.lock` for FastAPI, SQLAlchemy, PostgreSQL/pgvector, parsers, embeddings, and pytest
- [X] T003 [P] Initialize the React/Node.js 20 frontend in `frontend/package.json`
- [X] T004 [P] Configure backend linting, formatting, typing, and pytest scripts in `backend/pyproject.toml` to execute through `uv run`
- [X] T005 [P] Configure frontend TypeScript, linting, formatting, and tests in `frontend/tsconfig.json` and `frontend/vite.config.ts`
- [X] T006 [P] Create service images in `docker/backend.Dockerfile` and `docker/frontend.Dockerfile`, installing and executing the backend through `uv sync` and `uv run`
- [X] T007 Create PostgreSQL/pgvector, backend, and frontend services in `docker/docker-compose.yml`
- [X] T008 [P] Add credential examples and exclusions in `.env.example` and `.gitignore`
- [X] T008A [P] Load the root `.env` into the Docker backend service through `docker/docker-compose.yml` while keeping real credentials excluded from version control

**Checkpoint**: The repository has buildable service skeletons and reproducible local orchestration.

---

## Phase 2: Shared Foundation - Persistence and Configuration

**Purpose**: Establish database models, migrations, configuration, and shared schemas before story implementation.

- [X] T009 Create environment configuration and structured logging in `backend/app/core/config.py` and `backend/app/core/logging.py`
- [X] T010 Create SQLAlchemy sessions and migration scaffolding in `backend/app/db/session.py` and `backend/app/db/migrations/`
- [X] T011 [P] Define shared enums, UUIDs, timestamps, and pgvector types in `backend/app/models/base.py`
- [X] T012 Create source and release models in `backend/app/models/source.py` with `review_status` values `approved`, `pending_review`, `rejected`, or `superseded`; require `superseded_by` for `superseded`; allow only one `active` release
- [X] T013 Create chunk model in `backend/app/models/source_chunk.py` requiring non-empty `content_text`, `release_id`, `structural_path`, `content_kind`, `location_label`, `chunk_hash`, and finite vectors of the configured dimension
- [X] T014 [P] Create question, answer, citation, and referral models in `backend/app/models/answer_log.py`
- [X] T015 [P] Create parsing-review and preparation-validation models in `backend/app/models/review_record.py`
- [X] T016 Generate database migrations for all models, foreign keys, pgvector, indexes, and active-release uniqueness in `backend/app/db/migrations/`
- [X] T017 Create shared schemas in `backend/app/schemas/source.py`, `backend/app/schemas/review.py`, and `backend/app/schemas/chat.py`
- [X] T018 [P] Add model and migration tests in `backend/tests/unit/test_models.py` and `backend/tests/integration/test_database_migrations.py`

**Checkpoint**: Persistence and configuration are ready; no story-specific work should bypass these invariants.

---

## Phase 3: Shared Foundation - Runtime and Retrieval

**Purpose**: Implement the common API boundary and active-release retrieval rules.

- [X] T019 Implement database/configuration dependency wiring in `backend/app/api/deps.py`
- [X] T020 Implement shared error handling in `backend/app/core/errors.py` without exposing secrets or converting failures into successful answers
- [X] T021 Implement active-release retrieval in `backend/app/services/retrieval.py`, filtering to approved, active, non-superseded sources only
- [X] T022 [P] Add retrieval and schema validation tests in `backend/tests/integration/test_active_release_retrieval.py` and `backend/tests/unit/test_schemas.py`
- [X] T023 Register the base FastAPI app and health endpoint in `backend/app/main.py`

**Checkpoint**: The shared runtime can validate requests and retrieve only authoritative content from the active release.

---

## Phase 4: User Story 3A - Acquire and Parse Approved Sources (Priority: P1)

**Goal**: Load approved HTML, PDF, and DOC/DOCX sources into immutable source versions and structure-aware blocks.

**Independent Test**: Parse fixtures containing headings, tables, lists, sidebars, and callouts; verify ordering, locations, hashes, and review records for unreliable inputs.

### Tests

- [X] T024 [P] [US3] Add manifest validation tests in `backend/tests/unit/ingestion/test_manifest.py`
- [X] T025 [P] [US3] Add HTML parser tests in `backend/tests/unit/ingestion/test_html_parser.py`
- [X] T026 [P] [US3] Add PDF parser tests in `backend/tests/unit/ingestion/test_pdf_parser.py`
- [X] T027 [P] [US3] Add DOC/DOCX parser tests in `backend/tests/unit/ingestion/test_docx_parser.py`
- [X] T028 [P] [US3] Add representative source fixtures in `backend/tests/fixtures/ingestion/`

### Implementation

- [X] T029 [P] [US3] Implement approved-source manifest validation in `backend/app/services/ingestion/manifest.py`, requiring canonical identity, title, location, source type, issuing office, review status, effective date, and reviewed timestamp
- [X] T030 [P] [US3] Implement local/remote source loading, SHA-256 hashing, and immutable source versions in `backend/app/services/ingestion/loader.py`
- [X] T031 Implement structural block types and parser dispatch in `backend/app/services/ingestion/parser.py`
- [X] T032 [P] [US3] Implement HTML parsing in `backend/app/services/ingestion/html.py` for headings, paragraphs, tables, lists, sidebars, callouts, order, and locations
- [X] T033 [P] [US3] Implement PDF parsing in `backend/app/services/ingestion/pdf.py` with page metadata and review records for image-only or unreliable extraction
- [X] T034 [P] [US3] Implement DOC/DOCX parsing in `backend/app/services/ingestion/docx.py` with heading hierarchy, tables, lists, sidebars, callouts, and locations

**Checkpoint**: Approved inputs are parsed into traceable blocks; failed or incomplete sources are isolated for review.

---

## Phase 5: User Story 3B - Normalize, Chunk, and Embed (Priority: P1)

**Goal**: Produce deterministic retrieval chunks and compatible embeddings from valid structural blocks.

**Independent Test**: Reprocess unchanged fixtures and verify identical chunk IDs/hashes, preserved context, bounded chunks, and validated vector dimensions.

### Tests

- [X] T035 [P] [US3] Add normalization and chunking tests in `backend/tests/unit/ingestion/test_chunking.py`
- [X] T036 [P] [US3] Add embedding-provider tests in `backend/tests/unit/ingestion/test_embeddings.py`

### Implementation

- [X] T037 [US3] Implement canonical normalization in `backend/app/services/ingestion/normalize.py`, preserving table/list relationships and rejecting empty or unverifiable content
- [X] T038 [US3] Implement deterministic bounded chunking in `backend/app/services/ingestion/chunk.py` with heading context, structural path, content kind, location, ordinal, and stable hash
- [X] T038A [US3] Extend `backend/app/services/ingestion/chunk.py` and `backend/tests/unit/ingestion/test_chunking.py` to split oversized tables between complete rows, preserve heading/column context and continuation metadata, and flag individually oversized rows without truncation
- [X] T039 [US3] Implement pinned embedding generation in `backend/app/services/ingestion/embed.py`, rejecting wrong dimensions, non-finite vectors, provider changes, and partial batches
- [X] T039A [US3] Implement the Google Gemini free-tier embedding adapter in `backend/app/services/ingestion/gemini_embed.py` using server-side credentials, pinned model/dimension configuration, quota failure handling, and provider tests

**Checkpoint**: Valid source blocks become reproducible, traceable chunks with compatible embeddings.

---

## Phase 6: User Story 3C - Validate and Publish the Vector Release (Priority: P1)

**Goal**: Validate the complete corpus and atomically activate only a release that satisfies all authority and retrieval gates.

**Independent Test**: Prepare valid and invalid releases; verify failed content is excluded and reported, successful releases activate transactionally, and failed activation leaves the previous release active.

### Tests

- [X] T040 [P] [US3] Add release-gate tests in `backend/tests/integration/test_knowledge_base_validation.py`
- [X] T041 [P] [US3] Add atomic publish and rollback tests in `backend/tests/integration/test_knowledge_base_publish.py`
- [X] T042 [P] [US3] Add CLI contract tests in `backend/tests/contract/test_knowledge_base_cli.py` using `specs/001-purdue-policy-chatbot/contracts/knowledge-base-preparation-cli.md`

### Implementation

- [X] T043 [US3] Implement metadata, parse-completeness, duplicate/empty-chunk, approval, and vector gates in `backend/app/services/ingestion/validate.py`
- [X] T044 [US3] Implement HNSW pgvector index creation in `backend/app/db/migrations/` and `backend/app/services/ingestion/publish.py`
- [X] T045 [US3] Implement retrieval smoke questions and citation-resolution checks in `backend/app/services/ingestion/validate.py`
- [X] T046 [US3] Implement transactional release activation and prior-release retirement in `backend/app/services/ingestion/publish.py`
- [X] T047 [US3] Implement the preparation command in `backend/scripts/prepare_knowledge_base.py` with `--manifest`, `--release-label`, `--source-root`, `--dry-run`, and `--activate`, consuming the Gemini adapter from T039A for non-dry-run preparation
- [X] T048 [US3] Add preparation metrics and release diagnostics in `backend/app/services/ingestion/`

**Checkpoint**: A validated vector release can be audited, activated, rolled back, and used by retrieval without failed or superseded content.

---

## Phase 7: User Story 1 - Find an Answer to a Common University Question (Priority: P1) 🎯 MVP

**Goal**: Answer supported student policy questions with grounded citations or targeted clarification.

**Independent Test**: Ask representative registration, class-change, academic-standing, grade-appeal, financial-aid, and contact questions against an active release.

### Tests

- [X] T049 [P] [US1] Add `/api/chat` contract tests in `backend/tests/contract/test_chat_api.py`
- [X] T050 [P] [US1] Add supported-question integration tests in `backend/tests/integration/test_supported_policy_questions.py`
- [X] T051 [P] [US1] Add frontend chat-flow tests in `frontend/tests/chat-flow.test.tsx`

### Implementation

- [X] T052 [US1] Implement chat schemas in `backend/app/schemas/chat.py` with non-empty `question` and `student_type` values `undergraduate`, `graduate`, or `unknown`
- [X] T053 [US1] Extend semantic retrieval in `backend/app/services/retrieval.py` with student type, term, campus, program, and policy-category filters
- [X] T054 [US1] Implement citation construction in `backend/app/services/citation.py` using source URL, title, snippet, structural path, and location
- [X] T055 [US1] Implement grounded answer generation in `backend/app/services/answering.py` using only retrieved approved context
- [X] T056 [US1] Implement targeted ambiguity detection and clarification prompts in `backend/app/services/answering.py`
- [X] T057 [US1] Implement `POST /api/chat` in `backend/app/api/routes/chat.py`, persisting questions, answers, and citations
- [X] T058 [US1] Implement `GET /api/sources` in `backend/app/api/routes/sources.py` for active approved sources
- [X] T059 [P] [US1] Build the React chat page and form in `frontend/src/pages/ChatPage.tsx` and `frontend/src/components/QuestionForm.tsx`
- [X] T060 [P] [US1] Build answer, citation, and clarification components in `frontend/src/components/AnswerCard.tsx`, `frontend/src/components/CitationList.tsx`, and `frontend/src/components/ClarificationPrompt.tsx`
- [X] T061 [US1] Connect the frontend API client and application rendering in `frontend/src/services/chatApi.ts` and `frontend/src/app/App.tsx`
- [X] T062 [US1] Register chat/source routes and public CORS in `backend/app/main.py`

**Checkpoint**: The MVP answers supported questions or asks for necessary context, with citations tied to the active vector release.

---

## Phase 8: User Story 2 - Receive a Safe Referral When Information Is Unreliable (Priority: P1)

**Goal**: Refuse unsupported, stale, conflicting, unavailable, or individualized guidance and provide verified escalation paths.

**Independent Test**: Ask unsupported, conflicting, expired, context-insufficient, individualized, and provider-failure questions; verify no unsupported direct answer is returned.

### Tests

- [X] T063 [P] [US2] Add safe-referral contract tests in `backend/tests/contract/test_safe_referral_contract.py`
- [X] T064 [P] [US2] Add unsupported, stale, conflict, and individualized-advice tests in `backend/tests/integration/test_safe_failure.py`
- [X] T065 [P] [US2] Add provider outage tests in `backend/tests/integration/test_provider_failures.py`
- [X] T066 [P] [US2] Add safe-referral UI tests in `frontend/tests/safe-referral.test.tsx`

### Implementation

- [X] T067 [P] [US2] Add safe-referral schema validation in `backend/app/schemas/review.py` and `backend/app/schemas/chat.py`
- [X] T068 [US2] Implement confidence, freshness, conflict, and individualized-advice checks in `backend/app/services/answering.py`
- [X] T069 [US2] Implement verified-office and official-directory referral selection in `backend/app/services/referral.py`
- [X] T070 [US2] Update `backend/app/api/routes/chat.py` to return clarification or safe-referral responses when checks fail
- [X] T071 [US2] Persist referral and grounding audit metadata in `backend/app/models/answer_log.py` and `backend/app/services/answering.py`
- [X] T072 [P] [US2] Add safe-referral UI states in `frontend/src/components/SafeReferralCard.tsx`
- [X] T073 [US2] Add structured grounding and provider-failure audit logs in `backend/app/core/logging.py` and `backend/app/services/answering.py`

**Checkpoint**: Unsupported or unreliable answers cannot bypass safe-failure behavior.

---

## Phase 9: User Story 4 - Identify Relevant Contacts (Priority: P2)

**Goal**: Return current, source-grounded office and contact information for supported processes.

**Independent Test**: Ask who to contact for registration, financial aid, academic standing, grade appeals, and class changes; verify current contact data or an official directory fallback.

- [ ] T074 [P] [US4] Add contact referral tests in `backend/tests/integration/test_contact_referrals.py`
- [ ] T075 [P] [US4] Add unavailable-contact tests in `backend/tests/integration/test_unverified_contacts.py`
- [ ] T076 [P] [US4] Add contact UI tests in `frontend/tests/contact-referral.test.tsx`
- [ ] T077 [US4] Implement contact metadata extraction in `backend/app/services/referral.py`
- [ ] T078 [US4] Implement process-to-office matching in `backend/app/services/referral.py`
- [ ] T079 [US4] Add contact referrals to chat responses in `backend/app/api/routes/chat.py` and `backend/app/services/answering.py`
- [ ] T080 [US4] Render contact and directory fallback details in `frontend/src/components/ContactReferral.tsx`

**Checkpoint**: Contact answers remain grounded in active approved sources and never invent unavailable details.

---

## Phase 10: Integration, Evaluation, and Release

**Purpose**: Validate the complete implementation against the quickstart, success criteria, and constitution.

- [ ] T081 [P] Add Docker end-to-end smoke tests in `backend/tests/integration/test_quickstart_flow.py`
- [ ] T082 [P] Add latency and preparation performance tests in `backend/tests/integration/test_performance.py`, executed with `uv run pytest`
- [ ] T083 [P] Add evaluation datasets and scoring scripts for SC-001 through SC-008 in `backend/tests/evaluation/`
- [ ] T084 [P] Document operator setup and knowledge-base preparation in `README.md` and `docs/knowledge-base-preparation.md`
- [ ] T085 Review `frontend/src/`, `backend/app/core/`, and `docker/` for credential exposure and unintended sign-in requirements
- [ ] T086 Run every scenario in `specs/001-purdue-policy-chatbot/quickstart.md` and record release validation results
- [ ] T087 Perform final traceability and constitution review across `specs/001-purdue-policy-chatbot/` and implemented source paths

---

## Dependencies and Execution Order

1. **Phase 1** has no dependencies.
2. **Phases 2-3** depend on Phase 1 and block all user stories.
3. **Phases 4-6** implement User Story 3 in order: acquire/parse → normalize/embed → validate/publish.
4. **Phase 7** depends on an active vector release and completes the MVP chat flow.
5. **Phase 8** depends on the Phase 7 answer path but can begin its tests in parallel.
6. **Phase 9** depends on the referral interfaces from Phase 8.
7. **Phase 10** depends on all required stories.

### Parallel Opportunities

- Phase 1 tasks T003-T006 and T008 can run in parallel.
- Phase 2 model tasks T011, T014, and T015 can run in parallel before migrations.
- Phase 4 parser tests and implementations for HTML, PDF, and DOCX can run in parallel.
- Phase 7 frontend components can run in parallel with backend citation and answer services.
- Phase 8 safety tests can run in parallel; provider-failure handling is separate from UI work.
- Phase 9 contact tests and contact extraction can run in parallel.

## MVP Strategy

1. Complete Phases 1-3.
2. Complete the minimum vector-release path in Phases 4-6.
3. Complete Phase 7 for grounded chat with citations.
4. Complete Phase 8 before public exposure.
5. Stop and validate the supported and unsafe-question evaluation sets.

All tasks use the required checklist format: checkbox, sequential ID, optional `[P]`, required story label for story phases, and an explicit file path.
