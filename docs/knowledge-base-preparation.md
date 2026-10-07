# Knowledge-Base Preparation

This guide covers preparing an approved source manifest, validating local source files, publishing a knowledge-base release, and checking the active records. The command runs in the backend container and uses the manifest bundled into the backend image.

## Requirements

- Docker Compose is running the PostgreSQL/pgvector service.
- The root `.env` exists and contains server-side Gemini configuration for non-dry-run preparation.
- `backend/documents/approved-sources.json` contains reviewed source metadata.
- Every local `location` in the manifest names a file under `backend/documents/sources/`.
- Every local-file entry has a public absolute HTTP(S) `source_url` for citations.

`location` is the content read by ingestion. `source_url` is the canonical URL shown in citations. For remote HTTP(S) locations, `source_url` can be omitted and the remote location is used as the citation URL.

## Validate Before Writing

From the repository root, first check that paths and parsers work without embeddings or database writes:

```bash
docker compose --file docker/docker-compose.yml run --rm backend \
  uv run python scripts/prepare_knowledge_base.py \
  --manifest documents/approved-sources.json \
  --source-root documents/sources \
  --release-label local-dry-run \
  --dry-run
```

A successful dry run reports `status: dry_run`, `failed: 0`, and a non-zero chunk count. It does not create a database release or call the embedding provider.

## Prepare and Publish

After reviewing the dry-run report and the source URLs, prepare and activate a release:

```bash
docker compose --file docker/docker-compose.yml run --rm backend \
  uv run python scripts/prepare_knowledge_base.py \
  --manifest documents/approved-sources.json \
  --source-root documents/sources \
  --release-label manual-refresh \
  --activate
```

This operation writes a candidate release, creates embeddings, runs the configured validation gates, and activates only after validation succeeds. Without `--activate`, a successful candidate remains `validated` and does not replace the active release. A failed candidate must not replace the prior active release. Do not run a real activation just to check connectivity.

The default Compose database credentials in `docker/docker-compose.yml` are for local development only. Do not expose this configuration or the database port publicly. Back up the database volume before operational refreshes.

## Verify the Active Release

```bash
docker compose --file docker/docker-compose.yml exec -T postgres \
  psql -U purdue -d purdue_policy_chatbot -c \
  "SELECT r.id, r.status, COUNT(DISTINCT s.id) AS sources, COUNT(c.id) AS chunks FROM knowledge_base_releases r LEFT JOIN source_content_segments c ON c.release_id = r.id LEFT JOIN approved_sources s ON s.id = c.source_id WHERE r.status = 'active' GROUP BY r.id, r.status;"
```

Verify canonical citation URLs:

```bash
docker compose --file docker/docker-compose.yml exec -T postgres \
  psql -U purdue -d purdue_policy_chatbot -c \
  "SELECT DISTINCT s.title, s.source_url FROM approved_sources s JOIN source_content_segments c ON c.source_id = s.id JOIN knowledge_base_releases r ON r.id = c.release_id WHERE r.status = 'active' ORDER BY s.title;"
```

The active release should have sources and chunks. `source_url` values should be public URLs, not local filenames.

## Common Problems

- **Local source not found:** Set `--source-root documents/sources`; paths are resolved relative to that root inside the backend container.
- **Missing `.env`:** Copy `.env.example` to `.env`, then enter the real Gemini key directly into that local file. Never paste credentials into source code or commit `.env`.
- **Embedding provider unavailable or quota exhausted:** Preparation returns a failure and does not activate partial vectors. Check provider configuration and quota, then retry when service is available.
- **Validation rejects a release:** Inspect the returned `diagnostics.validation` and `failed_sources`; fix manifest/source issues and dry-run again.
- **Citation still shows a filename:** Confirm the image was rebuilt from current source and the new release was activated; old releases keep their previous source metadata for audit.
