# Research: Authoritative University Information Chatbot

## Decision: Use a Python FastAPI backend with a minimal React/Vite client

**Rationale:** Python has mature tooling for HTML, PDF, table, retrieval, and evaluation workflows. FastAPI and Pydantic provide explicit typed boundaries for chat, ingestion, and reviewer operations. React/Vite is sufficient for a public chat interface while keeping answer safety in the backend.

**Alternatives considered:** A single server-rendered application would reduce deployment pieces but would couple UI and safety logic. A fully managed chatbot platform would accelerate a demo but would make source traceability, freshness enforcement, and deterministic escalation harder to review.

## Decision: Use PostgreSQL with full-text search and pgvector

**Rationale:** One database can store approved-source metadata, normalized citation blocks, structured schedule/catalog fields, keyword indexes, embeddings, conflicts, and answer audits. Hybrid search is important because exact dates and course codes need keyword matching while natural-language questions benefit from semantic retrieval.

**Alternatives considered:** SQLite plus a local vector index is acceptable for a disposable prototype but is weaker for concurrent public access and reviewer queries. A dedicated vector database is deferred until pilot scale demonstrates the need.

## Decision: Preserve structured content blocks instead of flattening documents into plain text

**Rationale:** HTML tables, PDF tables, footnotes, headings, links, and page locations carry meaning needed for deadlines, refund percentages, prerequisites, and procedures. Each block will retain source version and location metadata for citations and review.

**Alternatives considered:** Generic token splitting is simpler but can scramble rows, columns, and prerequisite relationships. Document-framework defaults may accelerate experiments but cannot replace source-specific validation for high-risk schedules.

## Decision: Crawl only an explicit approved PNW allowlist and retain parent-child relationships

**Rationale:** An allowlist prevents unrelated or unofficial content from entering the answer corpus. Parent-child links let ingestion follow nested procedures, forms, and PDFs while preserving how the content was discovered.

**Alternatives considered:** Open-web search would improve breadth but violates approved-source governance and makes applicability difficult to review.

## Decision: Treat freshness and answer safety as deterministic application rules

**Rationale:** Time-sensitive sources require reliable update dates and revalidation at ingestion, update-date change, or configured freshness expiry. Missing dates, conflicts, missing context, and private-record questions must produce clarification or escalation instead of relying on model judgment.

**Alternatives considered:** Prompt-only instructions are insufficient because they do not reliably prevent stale citations or unsupported claims.

## Decision: Use a typed answer contract with citations, limitations, and escalation

**Rationale:** A structured internal response makes it possible to validate that every factual claim maps to retrieved approved evidence and that unsupported or personalized questions are handled safely. “I don't know” is a valid response outcome.

**Alternatives considered:** Free-form model text is easier to prototype but cannot provide reliable reviewer traceability or enforce citation completeness.

## Decision: Validate with parser fixtures, API integration tests, and a golden evaluation set

**Rationale:** The highest risks are extraction regressions, stale or conflicting sources, citation drift, and incorrect escalation. Fixtures and a versioned evaluation set directly cover those risks and map to SC-001 through SC-007.

**Alternatives considered:** Manual spot checks alone do not detect regressions across source layouts or prompt changes.
