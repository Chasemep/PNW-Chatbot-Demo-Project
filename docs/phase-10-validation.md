# Phase 10 Validation Record

**Date:** 2026-10-06  
**Scope:** Quickstart scenarios 1–11, local test suites, current Docker stack, Phase 10 evaluation and release review.

## Automated Results

| Check | Result | Evidence |
|---|---|---|
| Docker Compose build/start (Scenario 1) | PASS | `docker compose --file docker/docker-compose.yml up --build -d`; Postgres healthy, backend and frontend up. |
| Live frontend / API / source endpoint (Scenarios 1 and 5) | PASS | `http://localhost:3000/`, `/health`, and `/api/sources` returned HTTP 200. |
| Live Docker proxy smoke (Scenarios 1 and 4) | PASS | `CHATBOT_E2E_URL=http://localhost:3000 uv run pytest tests/integration/test_quickstart_flow.py`: passed through Nginx, API, and DB. This made a normal audited chat request. |
| Live supported answer with citations (Scenarios 2 and 3) | PARTIAL / FAIL | A supported add/drop question returned a 200 and citations, but citations used local filenames (`pnw-refund-withdrawal-Schedule.html`, `Student Handbook.pdf`) instead of public `source_url` values. The active release predates the source-URL ingestion update. |
| Live unsupported/individualized request (Scenario 4) | PASS after rebuild | Initial deployment said it could not provide a reliable answer but used `response_type: direct_answer`; phrase filtering alone still failed for “Can I receive a personal policy exception?”. Added question-level individualized-decision blocking. After rebuilding, that exact request returned `safe_referral`, zero citations, and the verified PNW directory URL. |
| Live clarification for missing student type (Scenarios 2 and 4) | PASS | Unknown student type for academic-standing question returned `clarification_needed`, a targeted prompt, and no citations. |
| Answer/citation audit persistence (Scenario 5) | PASS | After live checks, database reported 59 questions, 59 answers, 140 citation rows, and 34 safe-referral rows. Counts include earlier workspace use, not just this validation run. |
| Gemini outage behavior (Scenario 6) | PARTIAL | Provider failure has unit coverage; no live credential removal was attempted because it would mutate running configuration. Current deployment’s external Gemini behavior was not deliberately disrupted. |
| HTML/PDF/DOCX structural parsing (Scenario 7) | PASS | Existing HTML, PDF, DOC/DOCX fixture tests passed in the 53-passed offline suite; image-only PDF review behavior is covered. |
| Oversized table splitting (Scenario 8) | PASS | Existing deterministic row-boundary, column-context, continuation, and oversized-row rejection tests passed. |
| Inaccessible source diagnostics (Scenario 9) | PASS | New isolated dry-run integration check confirms failure count and actionable source error without database writes. |
| Unchanged-input determinism (Scenario 10) | PASS | New integration check produced matching prepared/failed counts and chunk counts on two dry runs. Stable chunk hash determinism also has unit coverage. |
| Changed-source activation and retired-release retrieval (Scenario 11) | PASS in unit/integration coverage; not run against live data | Atomic publish/rollback and active-release-only retrieval tests cover this behavior without mutating the live release. |
| Container dry-run ingest | PASS | Docker backend prepared all 3 manifest entries, generated 574 chunks, 0 failures; `status: dry_run`, no embeddings or database writes. |
| Performance checks | PASS (local/mocked) | Chat p95 stayed below 5 seconds for 20 local mocked requests; source dry-run stayed below its 15-second guard. These are not measurements of live Gemini/provider latency. |
| Backend regression groups | PASS, with separate host-DB setting required for API tests | Parser/retrieval/publish/provider/evaluation/performance/Quickstart groups: 68 passed, 1 opt-in skip. Safe-failure API: 2 passed with `DATABASE_URL` explicitly set to the local Compose database URL; without it, host `.env` uses `change-me` while the running database has a different password. Contact/safe API group also passed 9 tests through `uv run pytest`. |
| Frontend tests/build/lint | PASS | Full Vitest suite: 5 passed; TypeScript/Vite production build and ESLint succeeded during Phase 9 verification. |

## User Evaluation

SC-004 (find answer/contact within 3 minutes) and SC-005 (understand response type) require participant measurements. No participants or adjudicated usability results were supplied, so these remain **NOT_EVALUATED**. Use `backend/tests/evaluation/dataset.json` to conduct the study, save adjudicated case results in `backend/tests/evaluation/results.json` using `results.template.json` as the initial empty file, then run:

```bash
cd backend
uv run python scripts/score_evaluation.py --results tests/evaluation/results.json
```

The scorer reports each SC-001–SC-008 metric separately and does not infer passes for missing data. Use `--require-all` for a release gate that rejects unevaluated criteria.

## Release Blockers / Follow-up

1. Rebuild and restart the backend after current source changes, then activate a validated release so stored active-source URLs use canonical manifest `source_url` values.
2. Repeat a live individualized/unsupported question and require `safe_referral`, not `direct_answer`.
3. Run a real Gemini/provider-failure scenario in a controlled environment if Scenario 6 must be certified end to end.
4. Gather real usability participants for SC-004 and SC-005.
5. Resolve host-vs-Compose database credentials before running the complete integration suite from the host.
6. Review [security-review.md](security-review.md): default Compose credentials, published database/API ports, missing rate limiting, and missing browser security headers prevent this from being a production security approval.

## Requirements and Constitution Traceability

| Governance requirement | Implementation path | Automated evidence |
|---|---|---|
| Constitution I: Grounded Answers; FR-003/004/013 | Active-release filters in `backend/app/services/retrieval.py`; source-preserving citations in `backend/app/services/citation.py`; citation resolution gate in `backend/app/services/ingestion/validate.py` | `test_active_release_retrieval.py`, `test_knowledge_base_validation.py`, `test_chat_api.py` |
| Constitution II: Fail Safely; FR-007/008/009/010/017 | Ambiguity and refusal handling in `backend/app/services/answering.py`; safe routing in `backend/app/api/routes/chat.py`; verified directory fallback in `backend/app/services/referral.py` | `test_safe_failure.py`, `test_provider_failures.py`, `test_unverified_contacts.py`, `test_answering.py` |
| Constitution III: Requirements Before Implementation | Acceptance criteria in `spec.md`, API/ingestion requirements in `contracts/`, sequential release plan in `tasks.md` | Speckit prerequisite script passed; requirements checklist 17/17 checked |
| FR-020/021: Standalone public frontend, no required sign-in | React entry/page, Nginx SPA and `/api/` proxy, public API CORS | Docker smoke test and public CORS contract test |
| SC-001/002/003/006/007 | Dataset and scorer in `backend/tests/evaluation/`; source, parser, release and citation gates | Adjudicated evaluation pending for empirical rates; deterministic parser/release tests pass |
| SC-004/005 | Usability cases in evaluation dataset | Not evaluated; requires actual participant observations |
| SC-008 | Evaluation latency cases plus local p95 performance test | Mocked/local p95 passes; live Gemini latency not certified |
