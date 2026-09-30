# Knowledge-Base Preparation Command Contract

## Command

`uv run python scripts/prepare_knowledge_base.py`

Run the command from the `backend/` `uv` project. The command is an authorized batch operation for loading an approved source
manifest into a new PostgreSQL + pgvector knowledge-base release. It is not a
student-facing source-management UI.

## Inputs

Required:

- `--manifest PATH`: JSON manifest of approved sources.
- `--release-label STRING`: Human-readable label for the preparation run.

Optional:

- `--source-root PATH`: Root for local files referenced by the manifest.
- `--dry-run`: Parse and validate without calling Gemini embeddings, writing vectors, or activating.
- `--activate`: Publish after all required gates pass. Without this flag the
  release remains `validated` for review.

Each manifest source must provide:

```json
{
  "source_key": "registration-calendar-2026",
  "title": "Registration Calendar",
  "location": "https://example.purdue.edu/registration/calendar",
  "source_type": "html",
  "issuing_office": "Registrar",
  "review_status": "approved",
  "effective_date": "2026-01-01",
  "reviewed_at": "2026-09-01"
}
```

## Processing contract

The command must:

1. Snapshot the manifest into a new isolated release.
2. Fetch/read and hash every source.
3. Parse supported formats into ordered structural blocks.
4. Preserve headings, paragraphs, tables, lists, sidebars, callouts, and
   source locations in normalized chunks.
5. Exclude failed, inaccessible, unapproved, superseded, or incomplete sources
   from authoritative retrieval and create review records.
6. Generate vectors through the Google Gemini API free tier using the release's pinned embedding model and dimension.
7. Validate metadata, parse results, chunk content, vector dimensions, and
   representative retrieval/citation behavior.
8. Activate the release atomically only when all required gates pass.

## Output contract

Successful validation returns a report containing:

- release ID and status
- source counts by parsed, excluded, and failed status
- chunk count and embedding model/dimension
- embedding provider (`google-gemini`) and provider diagnostics, excluding credentials
- validation checks and warnings
- active release ID before and after the run

Activation failure is non-success even if individual files parsed. The command
must leave the previously active release unchanged and return a non-zero exit
status with actionable diagnostics.

Embedding-provider failure or free-tier quota exhaustion is also non-success;
the command must not write partial vectors or activate the candidate release.
