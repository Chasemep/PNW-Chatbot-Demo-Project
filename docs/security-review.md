# Security Review

**Review date:** 2026-10-06  
**Scope:** `frontend/src/`, `backend/app/core/`, `backend/app/api/`, and `docker/`  
**Purpose:** Phase 10 T085 review of credential exposure and unintended sign-in requirements.

## Findings

| Severity | Finding | Evidence | Disposition |
|---|---|---|---|
| High for production | Compose hardcodes PostgreSQL credentials (`purdue` / `purdue`) and publishes ports 5432 and 8000 on all host interfaces. | `docker/docker-compose.yml` | Local-development configuration only. Replace credentials, restrict network bindings, and use deployment secrets before any shared or public deployment. Do not expose PostgreSQL publicly. |
| Medium for production | Public chat and source APIs have no authentication or rate limiting. | `backend/app/main.py`, `backend/app/api/routes/chat.py`, `backend/app/api/routes/sources.py` | No sign-in is an explicit first-release requirement. Add abuse controls, quotas, and operational monitoring at the deployment edge before exposing to untrusted high-volume traffic. |
| Medium for production | Nginx config proxies requests and serves the SPA but defines no Content-Security-Policy or other browser security headers. | `docker/nginx.conf` | Add and verify an environment-appropriate CSP and standard security headers before production deployment. |
| Low / accepted for public app | CORS allows any origin, with credentials disabled. | `backend/app/main.py` | This matches the public standalone application contract; revisit if the API becomes private or authenticated. |

## Controls Verified

- Gemini keys are read by backend settings/providers; the frontend source has no key, token, browser storage, or authorization-header handling.
- `.env` is git-ignored and excluded from the Docker build context by `.dockerignore`; the local `.env` was present and confirmed ignored without reading its values.
- API error handlers return generic client-safe errors and log exception type/path rather than request bodies or exception contents.
- Gemini provider exceptions redact the configured API key before constructing diagnostic messages.
- Active source discovery filters to approved, active, non-superseded sources. There are no public source-management routes.
- Public access does not require sign-in, as required by FR-020 and FR-021.

## Release Decision

The code paths reviewed show no accidental frontend credential exposure or unintended sign-in requirement. This is **not a production security approval**: the default Compose database credential, open port bindings, missing request rate limiting, and missing security headers must be addressed or explicitly accepted by an authorized deployment owner before public production hosting.
