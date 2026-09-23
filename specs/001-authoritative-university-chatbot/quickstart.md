# Quickstart Validation Guide

This guide validates the planned feature behavior end to end. It is intentionally not an implementation guide; implementation details belong in `tasks.md`.

## Prerequisites

- Python 3.12
- Node.js 20 or later
- Docker Engine or Docker Desktop with Docker Compose
- An approved-source manifest containing a small set of official PNW HTML and PDF fixtures
- Test credentials for the selected model provider, if answer generation is enabled locally

## Setup

Build and start the deployment topology with Docker Compose:

```bash
docker compose build
docker compose up -d db api frontend ingestion
```

The Compose configuration supplies PostgreSQL with pgvector, the API, the ingestion worker, the static frontend, and persistent local artifact/database volumes. Provide model-provider credentials and other deployment values through an uncommitted environment file or deployment secret mechanism.

For host-native development of only the backend and frontend, the following remains available:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
npm --prefix frontend install
```

Create a local database and configure the documented environment variables for the database URL, artifact directory, approved-source manifest, and model provider. Do not configure authentication or private student-record integrations for the initial release.

## Run

When using Docker Compose, the frontend and API are available at the ports defined in `docker-compose.yml`. Check service health and logs with:

```bash
docker compose ps
docker compose logs --follow api ingestion
```

For host-native development:

```bash
uvicorn backend.app.main:app --reload
npm --prefix frontend run dev
```

Run ingestion against fixtures before starting answer tests:

```bash
python -m backend.app.ingestion.run --manifest data/approved-sources/fixture-manifest.json
```

The equivalent containerized ingestion validation is:

```bash
docker compose run --rm ingestion --manifest data/approved-sources/fixture-manifest.json
```

## Validation scenarios

1. **Verified procedure:** Ask how to pay or appeal a parking ticket. The response includes steps from nested pages or PDFs, a source title and URL, and an appropriate office/contact when available.
2. **Structured deadline:** Ask for an add/drop or refund deadline with campus and term. The response preserves the event, date, term, campus, condition, and footnote relationship.
3. **Missing context:** Omit the term or campus from a context-dependent question. The response asks for the missing context and does not choose silently.
4. **Program/prerequisite:** Ask about a course with nested prerequisites. The response combines the chain and identifies campus applicability without claiming an official degree audit.
5. **Undated source:** Load a time-sensitive fixture without a reliable update date. The response does not present it as current and escalates.
6. **Conflicting sources:** Load two approved fixtures with different dates or rules. The response discloses the conflict and directs the user to the responsible office.
7. **Personalized question:** Ask how to resolve an individual registration error or graduation requirement. The response says it cannot inspect private records or make an official determination and provides an escalation path.
8. **Reviewer traceability:** Retrieve the answer audit and verify that the answer, citations, source versions, locations, freshness decision, and escalation outcome are reproducible.

## Automated checks

```bash
pytest backend/tests
npm --prefix frontend test
```

The golden evaluation set must report the measures in the feature specification: citation correctness, deadline accuracy, fragmented-procedure completion, escalation correctness, task completion time, clarity, and independent reviewer verification. See [`data-model.md`](./data-model.md) for the persisted trace fields and [`contracts/chat-api.md`](./contracts/chat-api.md) for response outcomes.
