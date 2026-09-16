# Implementation Plan: PNW Student Information & Advising Assistant

**Branch**: `001-pnw-info-assistant` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-pnw-info-assistant/spec.md`, clarified through user interview notes and 5 resolved specification clarification items. Tech stack specified: **FastAPI**, **React**, **PostgreSQL with pgvector**, and **Docker**.

---

## Summary

The PNW Student Information & Advising Assistant is a containerized, single-turn, stateless web application designed to help Purdue University Northwest students find grounded answers to university policies, registration/refund deadlines, and multi-level course prerequisite chains. 

The system couples a **FastAPI** backend with a **React** (TypeScript + Vite) frontend and a **PostgreSQL 16** database with `pgvector`. Retrieval is powered by hybrid vector cosine similarity and full-text keyword search against ingested PNW policy documents and catalog tables. To uphold project Constitution Principles, the assistant features in-flight PII redaction, strict citation grounding with active official links, automatic calendar term resolution, progressive prerequisite tree visualization, and a deterministic fail-safe routing mechanism directing students to university offices when answers cannot be verified.

---

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5.0+ / Node.js 20+ (Frontend)

**Primary Dependencies**:
- *Backend*: FastAPI, Uvicorn, SQLAlchemy (asyncpg), pgvector, Pydantic v2, Alembic, httpx, sentence-transformers
- *Frontend*: React 18, Vite, TypeScript, Lucide React, Tailwind CSS

**Storage**: PostgreSQL 16 with `pgvector` extension (`pgvector/pgvector:pg16` Docker image); relational tables for documents, chunks, terms, courses, prerequisites, contacts, query traces, and feedback.

**Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (Backend tests); `Vitest`, `React Testing Library` (Frontend tests).

**Target Platform**: Containerized Linux server via Docker & Docker Compose (`docker-compose.yml`).

**Project Type**: Full-stack web application (Decoupled FastAPI backend service + React SPA frontend).

**Performance Goals**:
- P95 query response time < 3.0 seconds (retrieval + grounding + citation formatting).
- Direct prerequisite graph and calendar term lookups < 500ms.
- 100% service uptime for static contact referrals during database cold start.

**Constraints**:
- Single-turn stateless Q&A: No multi-turn session context or chat history retained.
- Constitution Principle I: 100% of policy and deadline statements must cite verified official university URLs.
- Constitution Principle II: When information is ungrounded or ambiguous, the system must fail safely by directing the user to official department contacts.
- In-flight PII Sanitization: Mask 9-digit PUIDs and personal student records before logging or processing (FERPA).
- Public access: No student login or authentication required for v1.

**Scale/Scope**:
- Serving current and prospective PNW students (~9,000 students across Hammond and Westville campuses).
- Ingested knowledge corpus: ~50-100 official PNW policy documents, academic catalog entries, prerequisite chains, and deadline tables.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Spec Requirement | Architecture & Design Verification | Status |
|-----------|------------------|------------------------------------|--------|
| **I. Grounded Answers** | FR-001, FR-002, SC-001 | Hybrid vector + keyword retrieval restricts generation context strictly to ingested official chunks; response payload requires verified citations (`source_url`, `title`, `campus_scope`). | **PASS** |
| **II. Fail Safely** | FR-006, FR-007, SC-002, SC-005 | Two-tier confidence gate (< 0.35 cosine distance threshold); ungrounded or personal account inquiries trigger deterministic `AdvisorRoutingCard` with office name, email, phone, and building/room. | **PASS** |
| **III. Requirements Before Implementation** | All FRs & SCs | Specification clarified across all 5 key decision points (conversational model, term resolution, PII handling, prerequisite depth, inline feedback) in `spec.md`. | **PASS** |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-pnw-info-assistant/
├── plan.md              # Master implementation plan (this file)
├── research.md          # Phase 0: Technical decisions and architectural research
├── data-model.md        # Phase 1: Database entities, relational schema, and vector indexes
├── quickstart.md        # Phase 1: Runnable Docker Compose instructions and validation scenarios
├── contracts/           # Phase 1: Formal API & UI component specifications
│   ├── openapi.yaml     # REST API endpoints (OpenAPI 3.1)
│   └── ui-contracts.md  # React component interfaces and layout hierarchy
└── tasks.md             # Phase 2: Actionable tasks generated by /speckit-tasks
```

### Source Code Layout (repository root)

```text
.
├── docker-compose.yml          # Container orchestration (db, backend, frontend)
├── .env.example                # Sample environment configuration
│
├── backend/                    # FastAPI Backend Service
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── alembic/                # Database migrations
│   │   └── versions/
│   ├── src/
│   │   ├── main.py             # Application entrypoint & middleware
│   │   ├── config.py           # Pydantic BaseSettings
│   │   ├── database.py         # Async SQLAlchemy session factory
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── document.py     # documents & document_chunks (with pgvector)
│   │   │   ├── academic_term.py# academic_terms (dates & drop deadlines)
│   │   │   ├── course.py       # courses & course_prerequisites
│   │   │   ├── contact.py      # administrative_contacts
│   │   │   └── query_log.py    # query_logs & response_feedback
│   │   ├── schemas/            # Pydantic v2 schemas
│   │   │   ├── query.py
│   │   │   ├── feedback.py
│   │   │   ├── course.py
│   │   │   └── contact.py
│   │   ├── services/           # Core business and retrieval logic
│   │   │   ├── pii_redactor.py # In-flight PUID & sensitive data masking
│   │   │   ├── term_resolver.py# Calendar date mapping & upcoming term advance
│   │   │   ├── prerequisite_service.py # Recursive prerequisite DAG builder
│   │   │   ├── vector_search.py# Hybrid pgvector + full-text search engine
│   │   │   └── grounded_generator.py   # Grounded response synthesis & citation binder
│   │   ├── api/                # FastAPI Routers
│   │   │   ├── v1/
│   │   │   │   ├── query.py    # POST /api/v1/query
│   │   │   │   ├── feedback.py # POST /api/v1/feedback
│   │   │   │   ├── courses.py  # GET /api/v1/courses/{code}/prerequisites
│   │   │   │   ├── terms.py    # GET /api/v1/terms/active
│   │   │   │   └── health.py   # GET /api/v1/health
│   │   └── scripts/
│   │       ├── ingest_corpus.py# Ingestion script for PNW PDFs and HTML docs
│   │       └── seed_data.py    # Seed academic calendar, catalog, and office contacts
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       ├── integration/
│       └── contract/
│
└── frontend/                   # React Frontend SPA
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx             # Main layout container
    │   ├── components/
    │   │   ├── Header.tsx      # PNW branding & scope disclaimers
    │   │   ├── InquiryInput.tsx# Single-turn input box with suggested questions
    │   │   ├── AnswerCard.tsx  # Grounded answer container with term/campus badges
    │   │   ├── PrerequisiteTree.tsx # Progressive visual tree for course dependencies
    │   │   ├── CitationList.tsx# Verified official university source links
    │   │   ├── AdvisorRoutingCard.tsx # Fail-safe escalation office contact card
    │   │   ├── InlineFeedbackWidget.tsx # Thumbs up/down + issue reporting modal
    │   │   └── PrivacyAlertBanner.tsx   # PII detection & masking notice
    │   ├── services/
    │   │   └── api.ts          # Axios / fetch client calling FastAPI backend
    │   └── types/
    │       └── index.ts        # TypeScript interfaces matching OpenAPI schema
    └── tests/
        └── components/
```

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | Design uses minimal 3-tier architecture (FastAPI + React + Postgres/pgvector) matching user requirements and constitution. |
