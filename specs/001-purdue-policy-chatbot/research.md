# Research: Purdue Policy Chatbot and Vector-Database Preparation

## Decision: Use `uv` as the required Python package manager

**Rationale**:
- `uv` provides project initialization, dependency resolution, lockfile generation, virtual-environment management, and command execution in one workflow.
- `backend/pyproject.toml` and `backend/uv.lock` make backend dependencies reproducible across local development, CI, and Docker.
- `uv sync` installs the locked environment and `uv run` ensures commands use that environment without requiring shell activation.

**Alternatives considered**:
- `pip` with `requirements.txt`: rejected because it does not provide the required project-level lock and environment workflow by itself.
- Poetry: rejected because the project requirement explicitly mandates `uv`.
- System Python or manually activated virtual environments: rejected because they are less reproducible and can bypass the locked dependency set.

**Required conventions**:
- Run `uv init --python 3.12` once in `backend/` when creating the project.
- Add runtime dependencies with `uv add` and development dependencies with `uv add --dev`.
- Commit `backend/pyproject.toml` and `backend/uv.lock`.
- Use `uv sync` to install and `uv run ...` to execute backend commands.
- Do not add `requirements.txt` or document `pip install` for the backend.

## Decision: Use a manifest-driven, versioned batch preparation workflow

**Rationale**:
- A manifest makes approval, ownership, canonical identity, effective dates, and supersession explicit instead of inferring authority from fetched content.
- Each run writes to a new isolated knowledge-base release. Retrieval continues using the prior active release until the new release passes all gates.
- An atomic active-release pointer prevents mixed-version answers during refresh and supports rollback/audit.

**Alternatives considered**:
- Mutating the active chunks in place: rejected because partial refreshes could mix old and new policy content.
- Relying on crawler discovery alone: rejected because discovered pages are not necessarily approved university sources.
- Rebuilding and replacing the database: rejected because it is harder to audit and creates unnecessary downtime.

## Decision: Parse into ordered structural blocks before chunking

**Rationale**:
- HTML, PDF, and DOC/DOCX sources need headings, tables, lists, sidebars, and callouts preserved as meaningful context.
- A block intermediate representation allows format-specific parsers to share normalization, validation, chunking, and provenance logic.
- Each block carries source location such as URL/section, page, table, or list position for citations and review.

**Alternatives considered**:
- Extracting plain text first: rejected because table relationships and visually separated callouts can be lost.
- One parser for every format: rejected because PDF, DOCX, and HTML expose different layout and metadata APIs.
- Treating each page as a chunk: rejected because page boundaries do not reliably match policy meaning.

## Decision: Use deterministic bounded chunks with contextual prefixes and stable IDs

**Rationale**:
- Chunks should be small enough for retrieval but large enough to retain the governing heading and nearby qualifiers.
- A stable ID derived from source version, structural path, and chunk ordinal makes refreshes idempotent and citations reproducible.
- Chunking must never split table rows or list items in a way that changes their meaning; oversized blocks may be split only at safe boundaries with continuation metadata.

**Alternatives considered**:
- Fixed character windows without structure: rejected because they can separate rules from their headings or table labels.
- Whole-document embeddings: rejected because retrieval becomes imprecise and citations become too broad.
- Fully dynamic chunking at query time: rejected because it makes validation and reproducibility harder.

## Decision: Pin embedding configuration and validate dimensions before indexing

**Rationale**:
- The embedding model name, provider, version/configuration, and vector dimension are part of the knowledge-base release metadata.
- Every vector is checked for the configured dimension and finite numeric values before insertion.
- A model/configuration change creates a new release and index rather than mixing incompatible vectors.

**Alternatives considered**:
- Automatically changing models during a run: rejected because it produces a non-reproducible corpus.
- Storing vectors without model metadata: rejected because later retrieval quality and compatibility cannot be explained.

## Decision: Keep failed or unreviewed source content out of authoritative retrieval

**Rationale**:
- Parser failures, inaccessible sources, conflicting metadata, and incomplete extraction are recorded as review records.
- A release can only be activated when every included source is approved and every excluded source is explicitly reported; the prior release remains active if gates fail.
- This directly enforces grounded answers and safe failure.

**Alternatives considered**:
- Indexing with a warning flag: rejected because retrieval could still present unverified policy as current.
- Silently dropping failures: rejected because operators and reviewers would not know the source set was incomplete.

## Decision: Use pgvector HNSW indexing after release validation

**Rationale**:
- PostgreSQL keeps source metadata, release state, citations, and vectors in one transactional system.
- HNSW provides practical approximate nearest-neighbor retrieval for a first-release corpus and can be filtered by active release and approved status.
- Building or refreshing the index after bulk loading avoids repeatedly maintaining it during ingestion.

**Alternatives considered**:
- Exact full-table distance scans: acceptable only for tiny fixtures; rejected for the expected corpus size.
- A separate vector database: deferred because it adds operational and consistency complexity without a first-release need.

## Decision: Validate with parser fixtures, corpus gates, and retrieval smoke questions

**Rationale**:
- Fixture documents prove that structural elements survive parsing for each supported format.
- Release gates prove metadata, chunk, vector, and approval invariants before activation.
- Representative questions verify that expected concepts retrieve the right source sections and that citations resolve.

**Alternatives considered**:
- Relying only on end-to-end chat tests: rejected because parser and indexing failures would be difficult to isolate.
- Manual inspection only: rejected because refreshes must be repeatable and measurable.

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
