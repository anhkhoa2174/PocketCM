# PocketCM – AI Onboarding Agent

FastAPI microservice that ingests customer data files (CSV, XLSX, PDF, DOCX, JSON), extracts structured customer records, validates them with Pydantic, and syncs them asynchronously to an external endpoint with retries and rate limiting.

## Quick start
- Install deps: `make install`
- Run locally: `make dev` (localhost:8000, docs at `/docs`)
- Run tests: `make test`
- Docker: `docker-compose up --build` (exposes `8000:8000`)

## How it works
- Ingest: `POST /api/v1/upload` accepts file upload with MIME/signature checks and size limits. Rate limited to 5 requests/min/IP via slowapi middleware.
- Extract: Structured files parsed with pandas/JSON; PDF/DOCX use pdfplumber/python-docx to pull text, then LLM (Instructor + OpenAI) when an API key is set, otherwise regex fallback to recover emails/names.
- Validate (Pydantic): `CustomerRecord` enforces:
  - `email` regex validation and normalization to lowercase
  - `subscription_tier` normalization (`Professional`, `Prem`, `Premium`, etc → `Pro`; unknown → `Basic`)
  - `signup_date` parsing across multiple formats, including ordinal suffixes
  - Required fields check via `model_validator`
- Sync: `APIClientService` posts validated records with aiohttp, retries with exponential backoff; falls back to batch if individual posts fail.

## Configuration
- Environment (pydantic-settings, `.env`): `OPENAI_API_KEY`, `DESTINATION_API_URL`, `MAX_FILE_SIZE`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`, `API_HOST`, `API_PORT`.
- Defaults in `src/core/config.py`. Uploads stored under `uploads/` (volume-mounted in Docker).

## Design decisions
- Chose Instructor + OpenAI for structured LLM output when available; regex fallback keeps service functional offline or on extraction failures.
- SlowAPI middleware is attached globally so decorator limits are enforced consistently.
- Security: filename sanitization, MIME + magic number verification, size limits, non-root Docker user.

## Testing
- `pytest` with coverage; unit tests focus on Pydantic validators (email, tier normalization, date parsing) and regex extraction fallback behavior.

## Notes
- Some parts were drafted with AI assistance: docker-compose, Dockerfile, pyproject, Makefile, the MIME/magic-number security checks, the rate-limiting middleware setup, and CORS configuration.
- Unit tests were also drafted with AI assistance.
