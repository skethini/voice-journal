# Render deploy checklist

## Recommended: Docker

| Setting | Value |
|---------|--------|
| **Root Directory** | *(empty)* |
| **Runtime** | Docker |
| **Dockerfile Path** | `Dockerfile.cloud` |
| **Start Command** | *(empty)* |
| **Health Check Path** | `/health` |

Push to GitHub before deploy — Render builds from the remote repo, not your laptop.

## Environment variables

Copy from `.env.example.cloud`. Required: `LLM_API_KEY`, `LLM_MODEL`, `PASSCODE_HASH`, `SESSION_SECRET`, `PUBLIC_URL`.

## Fallback: Python runtime (not recommended)

| Setting | Value |
|---------|--------|
| **Build Command** | `./scripts/render-build.sh` |
| **Start Command** | `./scripts/render-start.sh` |

Requires Node in the build environment (Render provides it).

## Files Render needs in GitHub

- `Dockerfile.cloud`
- `requirements-cloud.txt` (repo root)
- `requirements.txt` (repo root)
- `server/app/` …
- `client/` …
