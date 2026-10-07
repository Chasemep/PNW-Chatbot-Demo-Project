# User-Requirements

Purdue Northwest policy chatbot with a React web interface, FastAPI service,
and a versioned PostgreSQL + pgvector knowledge base.

## Run Locally with Docker

Requirements: Docker Compose and a root `.env` file. Create the local file from
the template, then configure its Gemini values:

```bash
cp .env.example .env
```

Start the full stack from the repository root:

```bash
docker compose --file docker/docker-compose.yml up --build
```

- Frontend: `http://localhost:3000`
- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

Keep the Compose command running while using the app; stop with Ctrl+C. The
database credentials in the checked-in Compose file are local-development
defaults only. Do not expose the database port or deploy those credentials.

## Prepare the Knowledge Base

The approved manifest and source files are in `backend/documents/`. First run a
non-mutating dry run to confirm that all local files parse:

```bash
docker compose --file docker/docker-compose.yml run --rm backend \
	uv run python scripts/prepare_knowledge_base.py \
	--manifest documents/approved-sources.json \
	--source-root documents/sources \
	--release-label local-dry-run \
	--dry-run
```

To write a new release and make it active, add `--activate` and use a distinct
release label. This calls the configured embedding provider and changes the
active database release only after required validation passes. See
[docs/knowledge-base-preparation.md](docs/knowledge-base-preparation.md) for
manifest semantics and database verification commands.

## Development Checks

Backend checks use the `uv` project rooted in `backend/`:

```bash
cd backend
uv sync
uv run pytest
```

Frontend checks use the package in `frontend/`:

```bash
cd frontend
npm install
npm test
npm run build
npm run lint
```

Docker end-to-end smoke testing is opt-in. Start the stack, then from `backend/`
run `CHATBOT_E2E_URL=http://localhost:3000 uv run pytest
tests/integration/test_quickstart_flow.py`. The smoke test sends a chat request
and writes an audit record to the configured database.