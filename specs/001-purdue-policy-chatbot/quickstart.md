# Quickstart: Purdue Policy Chatbot

## Prerequisites

- Docker and Docker Compose installed
- Git available
- Access to approved Purdue Northwest source documents
- A Google Gemini API key configured as a backend environment variable

## Local setup

```bash
docker compose --file docker/docker-compose.yml up --build
```

## Expected results

- Backend API available at `http://localhost:8000/docs`
- Frontend available at `http://localhost:3000`
- PostgreSQL service available on port `5432`
- pgvector extension enabled in the database
- Backend can reach the configured Google Gemini API endpoint

## Validation scenarios

1. Launch the stack and confirm all services are healthy.
2. Submit a common policy question such as: "What is the deadline to add or drop a class?"
3. Verify the answer is sourced from an approved document and includes a citation.
4. Submit an unsupported or low-confidence question and confirm the response refuses to answer and directs the student to the appropriate office.
5. Check that the database records the relevant answer and citation metadata for review.
6. Temporarily remove or invalidate the Gemini API configuration and verify that the chatbot returns a safe referral instead of inventing a policy answer.

## Troubleshooting

- If the backend cannot start, verify the database container is healthy and the pgvector extension is installed.
- If source ingestion fails, inspect parsing logs and ensure the source file format is supported.
- If the UI is blank, verify the frontend service started successfully and that the backend is reachable.
- If Gemini requests fail, verify the backend API key, quota, network access, and configured model name; the expected failure behavior is a safe referral.
