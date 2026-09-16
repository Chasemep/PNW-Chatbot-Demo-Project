# API Contracts: FastAPI Backend Service

**Feature**: `001-pnw-info-assistant`
**Date**: 2026-09-16
**Status**: Complete
**Base URL**: `/api/v1`

This document defines the REST API contract for the PNW Student Information & Advising Assistant backend. It enforces Constitution Principle I (*Grounded Answers with citations*) and Constitution Principle II (*Fail Safely with departmental routing*).

---

## 1. Endpoints Overview

| Method | Path | Summary | Authentication |
|--------|------|---------|----------------|
| `POST` | `/api/v1/query` | Submit a single-turn student inquiry | None (Public) |
| `POST` | `/api/v1/feedback` | Submit anonymous feedback on an answer | None (Public) |
| `GET` | `/api/v1/courses/{course_code}/prerequisites` | Retrieve hierarchical prerequisite DAG | None (Public) |
| `GET` | `/api/v1/terms/active` | Get active and upcoming academic calendar terms | None (Public) |
| `GET` | `/api/v1/health` | Service and database health check | None (Public) |

---

## 2. Endpoint Details

### 2.1 `POST /api/v1/query`
Processes a student inquiry statelessly. Applies in-flight PII redaction (FR-007), resolves the academic calendar term (FR-003), runs hybrid retrieval against official PNW documents, and returns a verified grounded response or a fail-safe advisor referral card.

#### Request Headers
- `Content-Type: application/json`

#### Request Body Schema
```json
{
  "query": "How do I pay my parking ticket?"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | **Yes** | Student question (min: 2, max: 1000 characters). Campus and academic term parameters are omitted; the backend automatically handles campus distinctions (returning composite answers when rules differ) and dynamically resolves the active term. |

#### Response: Grounded Answer (`200 OK`)
Returned when retrieved document chunks meet or exceed the groundedness confidence threshold (cosine distance < 0.35).

```json
{
  "query_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "answer": "To pay a parking citation at PNW, follow these steps:\n\n1. **Online**: Visit the official PNW Parking Portal and enter your citation number or vehicle license plate.\n2. **In Person**: Payments can be made at the Bursar's Office on either campus (Lawshe Hall 130 in Hammond, or Schwarz Hall 120 in Westville).\n3. **Appeals**: If you wish to contest the ticket, appeals must be filed through the parking portal within 14 calendar days of citation issuance.",
  "outcome": "GROUNDED_ANSWER",
  "applied_term": "Fall 2026 Full Term",
  "citations": [
    {
      "title": "PNW Parking Regulations & Citations",
      "source_url": "https://www.pnw.edu/police/parking/",
      "section_heading": "Citation Payment and Appeals Process",
      "campus_scope": "ALL"
    }
  ],
  "prerequisite_hierarchy": null,
  "department_contact": null,
  "pii_detected": false,
  "privacy_notice": null
}
```

#### Response: Fail-Safe Advisor Referral (`200 OK`)
Returned when confidence is insufficient, information is ambiguous, or the inquiry requests personalized student records (e.g. registration PIN, financial hold) per Constitution Principle II.

```json
{
  "query_id": "8d1b2291-8512-4aef-bb6e-c19e52a912d4",
  "answer": "I do not have sufficient verified university policy information to answer this question reliably. For personalized assistance with your student records or academic standing, please contact the designated office below:",
  "outcome": "FAIL_SAFE_ROUTED",
  "applied_term": null,
  "citations": [],
  "prerequisite_hierarchy": null,
  "department_contact": {
    "office_name": "Office of the Registrar",
    "contact_email": "registrar@pnw.edu",
    "phone_number": "(219) 989-2344",
    "campus": "ALL",
    "building_room": "Lawshe Hall, Room 130 (Hammond) / Schwarz Hall, Room 120 (Westville)",
    "website_url": "https://www.pnw.edu/registrar/",
    "office_hours": "Mon-Fri 8:00 AM - 4:30 PM"
  },
  "pii_detected": true,
  "privacy_notice": "Notice: A student ID number was detected and redacted. Please do not submit confidential student identifiers."
}
```

---

### 2.2 `POST /api/v1/feedback`
Captures anonymous student ratings and issue reports to audit policy accuracy and link health (FR-012, SC-007).

#### Request Body Schema
```json
{
  "query_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "sentiment": "UNHELPFUL",
  "issue_category": "BROKEN_LINK",
  "comment": "The parking regulations link returns a 404 error."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query_id` | `UUID` | **Yes** | Identifier from original query response. |
| `sentiment` | `string` | **Yes** | `"HELPFUL"` or `"UNHELPFUL"`. |
| `issue_category` | `string` | No | `"OUTDATED_INFO"`, `"BROKEN_LINK"`, `"INCORRECT_RULE"`, or `"OTHER"`. |
| `comment` | `string` | No | Optional description (max 500 characters). |

#### Response (`201 Created`)
```json
{
  "status": "received",
  "feedback_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

---

### 2.3 `GET /api/v1/courses/{course_code}/prerequisites`
Retrieves a complete recursive prerequisite dependency tree for a given course, including minimum grade cutoffs and AND/OR logic branches (FR-005).

#### Path Parameters
- `course_code` (`string`, required): Official course code (e.g. `CS 30200` or `MA 16300`).

#### Response (`200 OK`)
```json
{
  "course_code": "CS 30200",
  "title": "Data Structures",
  "credits": 3,
  "campus_scope": "ALL",
  "prerequisite_groups": [
    {
      "group_id": 1,
      "logic_operator": "AND",
      "options": [
        {
          "course_code": "CS 27500",
          "title": "Computer Architecture",
          "min_grade": "C",
          "is_corequisite": false,
          "sub_prerequisites": [
            {
              "course_code": "CS 12400",
              "title": "Introduction to Programming",
              "min_grade": "C",
              "is_corequisite": false,
              "sub_prerequisites": []
            }
          ]
        }
      ]
    },
    {
      "group_id": 2,
      "logic_operator": "OR",
      "options": [
        {
          "course_code": "MA 16300",
          "title": "Integrated Calculus Analysis Geometry I",
          "min_grade": "C",
          "is_corequisite": false,
          "sub_prerequisites": []
        },
        {
          "course_code": "MA 16500",
          "title": "Analytic Geometry and Calculus I",
          "min_grade": "C",
          "is_corequisite": false,
          "sub_prerequisites": []
        }
      ]
    }
  ]
}
```

---

### 2.4 `GET /api/v1/terms/active`
Returns the active academic semester and upcoming term dates with deadline cutoffs (FR-003).

#### Response (`200 OK`)
```json
{
  "active_term": {
    "term_code": "FALL_2026",
    "name": "Fall 2026 Full Term",
    "start_date": "2026-08-24",
    "end_date": "2026-12-12",
    "drop_100_refund_deadline": "2026-09-07",
    "withdraw_deadline": "2026-10-26"
  },
  "upcoming_term": {
    "term_code": "SPRING_2027",
    "name": "Spring 2027 Full Term",
    "start_date": "2027-01-11",
    "end_date": "2027-05-08",
    "drop_100_refund_deadline": "2027-01-25",
    "withdraw_deadline": "2027-03-22"
  }
}
```

---

### 2.5 `GET /api/v1/health`
Health check endpoint for Docker and monitoring.

#### Response (`200 OK`)
```json
{
  "status": "healthy",
  "database": "connected",
  "pgvector_enabled": true
}
```

---

## 3. Error Responses

All error responses adhere to standard FastAPI/RFC 7807 error format:

```json
{
  "detail": "Invalid query: Query string must not be empty or whitespace only."
}
```

| HTTP Status | Meaning | Scenario |
|-------------|---------|----------|
| `400 Bad Request` | Malformed input | Empty query string, query exceeding 1000 characters |
| `404 Not Found` | Entity not found | Course code not in catalog, feedback on non-existent `query_id` |
| `500 Internal Error`| Server failure | Database unreachable, embedding engine error |
