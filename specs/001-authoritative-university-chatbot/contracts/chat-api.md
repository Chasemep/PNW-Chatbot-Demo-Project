# Chat API Contract

The public client communicates with the backend over JSON HTTPS. The initial release requires no authentication and must not expose private student data.

## `POST /api/v1/chat`

### Request

```json
{
  "message": "When is the fall add/drop deadline?",
  "context": {
    "campus": "Hammond",
    "term": "Fall 2026",
    "role": "current_student"
  },
  "conversation_id": "optional-client-id"
}
```

Rules:

- `message` is required and must be non-empty.
- `context` is optional and contains only general context needed for applicability.
- The server must not accept or request credentials, portal tokens, student IDs, grades, balances, or other private-record data.
- The server must normalize and validate context values before retrieval.

### Response

```json
{
  "outcome": "answered",
  "answer": "The Fall 2026 add/drop deadline is ...",
  "citations": [
    {
      "title": "Academic Schedule",
      "issuing_office": "Registrar",
      "url": "https://...",
      "update_date": "2026-08-01",
      "location": "Fall 2026 table, Add/Drop row"
    }
  ],
  "missing_context": [],
  "limitations": [
    "This is general information, not an official individual determination."
  ],
  "escalation": null,
  "conversation_id": "server-id"
}
```

`outcome` is one of:

- `answered`: evidence is sufficient and current.
- `clarification-required`: required campus, term, program, or status is missing.
- `escalated`: evidence is missing, conflicting, stale, personalized, or requires an official determination.
- `i-dont-know`: the chatbot cannot provide a reliable answer.

The server must reject or transform any generated answer whose factual claims do not map to returned citations. Current time-sensitive answers require a reliable source update date.

## `GET /api/v1/health`

Returns service and database readiness without exposing source content or user data.

## `GET /api/v1/reviewer/answers/{answer_id}`

Reviewer-only operational endpoint for a locally authorized reviewer or internal deployment. It returns the `AnswerAudit`, retrieved block IDs, source versions, validation result, and escalation decision. It is not linked from the public client and must not be used to retrieve private student records.

## Ingestion job contract

The ingestion worker accepts an approved-source manifest:

```json
{
  "seeds": [
    {
      "url": "https://www.pnw.edu/...",
      "source_type": "schedule",
      "allowed_children": true
    }
  ]
}
```

The worker records every fetch attempt, discovered child source, parser version, content hash, update-date confidence, and freshness status. Failed or undated time-sensitive sources remain visible as unavailable or freshness-unverified; they are never silently treated as current.
