# Research: Purdue Policy Chatbot Architecture

## Decision: Use a FastAPI backend + React frontend + PostgreSQL with pgvector + Docker deployment

**Rationale**:
- FastAPI provides a clear API layer for grounding and retrieval while supporting Pydantic validation and OpenAPI documentation.
- React provides a simple student-facing interface for Q&A and safe-fallback responses without requiring sign-in in the first release.
- PostgreSQL with pgvector is the best fit for approved-source storage, metadata, and semantic retrieval in a single system.
- Docker Compose keeps local development and deployment reproducible and reduces environment drift across backend, frontend, and database services.

**Alternatives considered**:
- Fully serverless stack: rejected because the project requires structured source metadata and a vector database with operational control over freshness and policy provenance.
- Single-app monolith: rejected because the product has a distinct UI and retrieval pipeline, and separation improves testing and maintenance.
- MySQL or NoSQL vector alternatives: rejected because PostgreSQL + pgvector provides the required similarity and metadata capabilities without a separate database system.

## Decision: Parse HTML, DOCX, and PDF content into structured chunks with metadata and provenance

**Rationale**:
- The spec explicitly requires handling HTML, DOC/DOCX, and PDF sources while preserving headings, tables, lists, sidebars, and callouts.
- A preprocessing pipeline that extracts semantic blocks and stores source metadata reduces the risk of losing structure during retrieval.
- Storing chunk-level provenance enables answer citations and supports source freshness checks.

**Alternatives considered**:
- Plain full-document search only: rejected because it would lose section-level understanding and source traceability.
- Direct ingestion without chunking: rejected because policy questions often require precise retrieval of a specific section or table.

## Decision: Separate retrieval and answer generation with an explicit safety layer

**Rationale**:
- The product’s constitutional requirement is that answers must be grounded and safe; retrieval and answer generation should be separate from the user-facing response assembly.
- A dedicated safe-fallback and referral layer ensures unsupported, conflicting, or low-confidence situations return a refusal or direction to a verified office.

**Alternatives considered**:
- End-to-end generation without citation gating: rejected because it risks unsupported statements and violates the fail-safe principle.
- Single-source retrieval with no guardrails: rejected because conflicting or stale sources require explicit handling.

## Decision: Use the Google Gemini API as the first-release language model provider

**Rationale**:
- Gemini provides a practical hosted language-model API with an available free tier for early development and small-scale evaluation.
- Keeping the provider behind the FastAPI backend prevents API credentials from reaching the public React client.
- Gemini is used only to draft responses from retrieved approved content; source retrieval, citation requirements, confidence checks, and safe referrals remain application responsibilities.
- The backend can return a safe referral when the provider is unavailable, rate-limited, or unable to produce a grounded response.

**Alternatives considered**:
- Self-hosted language model: rejected for the first release because it adds infrastructure and operational complexity beyond the current scope.
- Multiple model providers: deferred because provider abstraction and fallback routing are not required for the first release.
- Unrestricted model answering: rejected because it conflicts with the grounded-answer and fail-safe requirements.

## Decision: Use Docker Compose for local deployment and service orchestration

**Rationale**:
- Local development and deployment are easier to standardize with a single compose file.
- Docker also supports the requirement to run PostgreSQL with pgvector and keep the frontend/backend services isolated.

**Alternatives considered**:
- Bare-metal local installs: rejected because of cross-environment inconsistency and slower onboarding.
- Kubernetes-only deployment: rejected for the first release as it adds operational complexity without solving the stated user need.

## Additional implementation assumptions

- Approved source documents are prepared by a human or admin workflow outside the product in this first release.
- Policy content is ingested into a structured corpus that retains document title, source URL, last-reviewed date, and supersession status.
- Source parsing failures are recorded as review records and cannot be used as authoritative answer material.
- Frontend responses will include citations and referral language when the answer is not confidently grounded.
- The Gemini API key is supplied through deployment environment configuration and is never stored in source control or exposed to the frontend.
