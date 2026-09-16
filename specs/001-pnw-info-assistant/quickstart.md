# Quickstart & Validation Guide: PNW Student Information & Advising Assistant

**Feature**: `001-pnw-info-assistant`
**Date**: 2026-09-16
**Status**: Ready for Validation

This guide provides runnable instructions to deploy the containerized assistant locally and validate all acceptance scenarios defined in [spec.md](./spec.md).

---

## 1. Prerequisites & Environment Setup

- **Docker & Docker Compose**: Docker Engine 24+ and Docker Compose v2.
- **Git**: Working copy of the repository.
- **Ports**: Port `8000` (FastAPI backend), `3000` (React frontend), and `5432` (PostgreSQL with pgvector).

### Environment Configuration
Copy the example environment template:
```bash
cp .env.example .env
```
Key environment variables:
```ini
POSTGRES_DB=pnw_assistant
POSTGRES_USER=pnw_user
POSTGRES_PASSWORD=pnw_secure_pass
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://pnw_user:pnw_secure_pass@db:5432/pnw_assistant

# Model / Embedding Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_PROVIDER=local_or_api
FASTAPI_PORT=8000
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 2. Launching with Docker Compose

Build and start all three containers (`db`, `backend`, `frontend`):

```bash
docker compose up --build -d
```

Check container status and health:
```bash
docker compose ps
```
Verify logs during migration & seed ingestion:
```bash
docker compose logs -f backend
```

Once running:
- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **API Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 3. End-to-End Validation Scenarios

### Validation Scenario 1: Policy Procedure & Grounded Citation (User Story 1 / FR-001, FR-002)
- **Action**: Open [http://localhost:3000](http://localhost:3000) and query: `"How do I pay my parking ticket?"`
- **Expected Outcome**:
  - Response displays step-by-step payment instructions (online portal, in-person cashier, mail).
  - Verified citation card displays: `PNW Parking Regulations & Citations` with active link `https://www.pnw.edu/police/parking/`.
  - No broken link or ungrounded statement.

### Validation Scenario 2: Dynamic Calendar Term Resolution (FR-003)
- **Action**: Submit query: `"When is the deadline to drop a class for a 100% refund?"` (without specifying a semester).
- **Expected Outcome**:
  - Assistant displays the active or upcoming term name (e.g. `Fall 2026 Full Term` or `Spring 2027`).
  - Dates match official academic calendar table.
  - Applied academic term badge appears above the response.

### Validation Scenario 3: Progressive Prerequisite Hierarchy (User Story 2 / FR-005)
- **Action**: Submit query: `"What are all the prerequisites for CS 30200?"`
- **Expected Outcome**:
  - Visual prerequisite tree appears showing foundational prerequisites (`CS 12400`, `CS 27500`, `MA 16300` / `MA 16500`).
  - Required minimum letter grades are explicitly labeled (e.g., `Grade of C or higher`).
  - Branching `OR` options are visibly differentiated.

### Validation Scenario 4: Fail-Safe Advisor Escalation (User Story 3 / FR-006, Principle II)
- **Action**: Submit ungrounded query: `"Why is there a registration hold on my personal student account?"`
- **Expected Outcome**:
  - Assistant acknowledges it does not have access to individual student records.
  - Displays official Advisor Routing Card:
    - **Office**: Office of the Registrar / Academic Advising Center
    - **Email**: `registrar@pnw.edu`
    - **Phone**: `(219) 989-2344`
    - **Location**: Lawshe Hall, Room 130 (Hammond) / Schwarz Hall, Room 120 (Westville).

### Validation Scenario 5: In-Flight PII Redaction (FR-007)
- **Action**: Submit query: `"My PUID is 003194821. How do I file a grade appeal?"`
- **Expected Outcome**:
  - Query processed successfully, answering the grade appeal steps.
  - PII Alert Banner is visible: *"Notice: Student ID number was detected and redacted."*
  - Database `query_logs` record verifies stored query is: `"My PUID is [REDACTED_PUID]. How do I file a grade appeal?"`

### Validation Scenario 6: Anonymous Feedback Submission (FR-012, SC-007)
- **Action**: Click "Thumbs Up" or "Report Issue" beneath any answer and submit.
- **Expected Outcome**:
  - Instant confirmation toast: *"Thank you for your feedback."*
  - Record inserted into `response_feedback` linked to `query_id`.

---

## 4. Automated Test Suite Execution

Run automated unit, integration, and contract tests inside the backend container:

```bash
docker compose exec backend pytest -v
```

Run frontend component tests inside the frontend container:
```bash
docker compose exec frontend npm test
```

To stop all services:
```bash
docker compose down -v
```
