# Quickstart: Purdue Policy Chatbot and RAG Knowledge-Base Preparation

## Prerequisites

- Docker and Docker Compose installed
- `uv` installed and available on `PATH`
- Git available
- Access to approved Purdue Northwest source documents
- A Google Gemini API key configured as a backend environment variable for answer generation and embeddings
- A pinned Gemini embedding model and dimension configured for the backend
- An approved-source manifest containing canonical source identity, owner, source type, effective/review dates, and supersession status

## Local setup

```bash
cd backend
uv sync
cd ..
docker compose --file docker/docker-compose.yml up --build
```

The backend is a `uv` project. Install dependencies with `uv sync` and run
backend commands with `uv run`; do not use `pip install`, a separate
`requirements.txt`, or an unmanaged virtual environment.

## Expected results

- Backend API available at `http://localhost:8000/docs`
- Frontend available at `http://localhost:3000`
- PostgreSQL service available on port `5432`
- pgvector extension enabled in the database
- Backend can reach the configured Google Gemini API endpoint for both embeddings and answer generation

## Prepare and publish a knowledge-base release

Run the batch preparation command from the backend container using an approved
manifest and a directory containing local source fixtures or configured source
URLs:

```bash
docker compose --file docker/docker-compose.yml run --rm backend \
  uv run python scripts/prepare_knowledge_base.py \
  --manifest /data/approved-sources.json \
  --release-label local-validation
```

The command must:

1. Create a new `preparing` release without changing the current active release.
2. Parse HTML, PDF, and DOC/DOCX sources while retaining structural paths and source locations.
3. Record parse failures or incomplete sources as review records and exclude them from authoritative chunks.
4. Normalize and deterministically chunk valid content, generate vectors through the Google Gemini free tier with the pinned embedding configuration, and validate dimensions.
5. Run metadata, parse-completeness, duplicate/empty-chunk, vector, and retrieval smoke-test gates.
6. Atomically activate the new release only when required gates pass; otherwise retain the prior active release.

Inspect the release report and database records for the release ID before using
it in chat. A failed run is expected to leave the prior active release
unchanged.

## Validation scenarios

1. Launch the stack and confirm all services are healthy.
2. Submit a common policy question such as: "What is the deadline to add or drop a class?"
3. Verify the answer is sourced from an approved document and includes a citation.
4. Submit an unsupported or low-confidence question and confirm the response refuses to answer and directs the student to the appropriate office.
5. Check that the database records the relevant answer and citation metadata for review.
6. Temporarily remove or invalidate the Gemini API configuration and verify that preparation fails without activating a partial release, while chat returns a safe referral instead of inventing a policy answer.
7. Prepare a release containing representative HTML, PDF, and DOCX fixtures with headings, tables, lists, and callouts; verify the structural locations and source hashes are preserved.
8. Include an HTML table larger than the chunk bound; verify preparation splits it between complete rows, repeats the required heading/column context on continuation chunks, and flags any individually oversized row instead of truncating it.
9. Include one malformed or inaccessible source; verify it creates a review record, is excluded from the active release, and is reported rather than silently ignored.
10. Re-run preparation with unchanged inputs; verify deterministic source/chunk identities and no duplicate active content.
11. Replace one source with a changed version; verify only the new release becomes active and the prior release remains auditable but is not retrieved for current answers.

## Troubleshooting

- If the backend cannot start, verify the database container is healthy and the pgvector extension is installed.
- If Python dependencies are missing, run `cd backend && uv sync`; inspect `backend/uv.lock` for lockfile or interpreter issues.
- If source ingestion fails, inspect parsing logs and ensure the source file format is supported.
- If the UI is blank, verify the frontend service started successfully and that the backend is reachable.
- If Gemini embedding or answer requests fail, verify the backend API key, free-tier quota, network access, and configured model name; preparation must fail safely and chat must return a safe referral.
