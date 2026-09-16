# Chat API Contract

## `POST /api/chat`

Ask a Purdue Northwest policy question.

### Request

Content type: `application/json`

| Field | Type | Required | Description |
|---|---|---:|---|
| `question` | string | Yes | Student's natural-language question |
| `student_type` | string | No | `undergraduate`, `graduate`, or `unknown` |

Example:

```json
{
  "question": "What is the deadline to drop a class?",
  "student_type": "undergraduate"
}
```

### Response

Status: `200 OK`

Content type: `application/json`

| Field | Type | Required | Description |
|---|---|---:|---|
| `answer` | string | Yes | Response shown to the student |
| `response_type` | string | Yes | `direct_answer`, `clarification_needed`, or `safe_referral` |
| `citations` | array | Yes | Supporting approved source citations |
| `referral` | object | No | Referral details when the answer requires escalation |
| `clarification_prompt` | string | No | Follow-up question when required context is missing |

Citation object:

| Field | Type | Required | Description |
|---|---|---:|---|
| `source_id` | UUID | Yes | Approved source identifier |
| `source_url` | string | Yes | Accessible source location |
| `citation_text` | string | Yes | Supporting excerpt |

Referral object:

| Field | Type | Required | Description |
|---|---|---:|---|
| `office_name` | string | Yes | Responsible Purdue Northwest office |
| `referral_reason` | string | Yes | Reason for the referral |
| `contact_url` | string | No | Verified contact or directory URL |

## `GET /api/sources`

List approved sources available to the chatbot.

### Response

Status: `200 OK`

Content type: `application/json`

Each source object contains:

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Approved source identifier |
| `title` | string | Yes | Official document or webpage title |
| `source_url` | string | No | Canonical source location |
| `review_status` | string | Yes | `approved`, `pending_review`, `rejected`, or `superseded` |

## Behavioral requirements

- A `direct_answer` must include at least one citation to an active approved source.
- A `clarification_needed` response must include `clarification_prompt`.
- A `safe_referral` response must include referral instructions and a verified office or official source when available.
- The API must not return unsupported university policy as a direct answer.
