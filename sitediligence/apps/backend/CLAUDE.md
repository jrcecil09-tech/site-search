# SiteDiligence Backend — Architecture Guide

This document is the primary reference for AI assistants and developers working
on the FastAPI backend. Read it before modifying any module.

---

## Overview

The backend is a **FastAPI** application (Python 3.11+) structured as a
layered service architecture:

```
main.py               ← App factory, CORS, router registration
routers/              ← HTTP boundary: request parsing, response shaping
services/
  queries/            ← One module per federal/GIS data source
  storage/            ← Storage backends (local, S3, Azure, GCS, hosted)
  exporters/          ← Output generators (PDF, DXF, GeoJSON, QGIS, etc.)
  integrations/       ← OAuth + sync for Procore, Autodesk, Drive, OneDrive
models/               ← SQLAlchemy ORM table definitions
utils/                ← Pure functions: geometry, CRS, file parsing, validation
config/               ← Settings (pydantic-settings) + JSON data stubs
cli/                  ← Typer CLI tools for batch ops and dev utilities
tests/                ← pytest test suite
```

---

## Environment Variables

All configuration is loaded via `config/settings.py` using `pydantic-settings`.
Variables are read from `.env` (create from `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `SECRET_KEY` | `change-me` | JWT signing secret — **must change in prod** |
| `DATABASE_URL` | `sqlite:///./sitediligence.db` | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery broker |
| `STORAGE_BACKEND` | `local` | `local` / `s3` / `azure` / `gcs` / `hosted` |
| `STORAGE_LOCAL_PATH` | `./data/storage` | Root path for local file storage |
| `S3_BUCKET` | — | S3 bucket name (or R2/MinIO bucket) |
| `S3_ENDPOINT_URL` | — | Custom endpoint for S3-compatible stores |
| `STRIPE_SECRET_KEY` | — | Stripe secret key for billing |
| `PROCORE_CLIENT_ID` | — | Procore OAuth2 client ID |
| `AUTODESK_CLIENT_ID` | — | Autodesk Platform Services client ID |
| `GOOGLE_CLIENT_ID` | — | Google OAuth2 client ID (for Drive) |
| `DROPBOX_APP_KEY` | — | Dropbox app key |

---

## Running the Server

```bash
# Activate the virtual environment
source .venv/bin/activate

# Start development server (auto-reload)
uvicorn main:app --reload --port 8000

# Or via pnpm from the repo root
pnpm dev:backend
```

API is available at:
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/redoc` — ReDoc
- `http://localhost:8000/health` — Health check
- `http://localhost:8000/openapi.json` — OpenAPI schema

---

## Database Schema

Tables are defined in `models/`:

| Table | Key Columns | Notes |
|---|---|---|
| `projects` | `id`, `team_id`, `name`, `status` | Top-level container |
| `sites` | `id`, `project_id`, `coordinates`, `bbox` | Spatial entity |
| `users` | `id`, `email`, `hashed_password` | bcrypt hashed |
| `teams` | `id`, `slug` | Multi-user workspace |
| `team_members` | `team_id`, `user_id`, `role` | Roles: owner/admin/editor/viewer |
| `observations` | `id`, `site_id`, `category_id`, `severity` | Field observations |
| `observation_attachments` | `id`, `observation_id`, `storage_key` | Photos, docs |
| `storage_objects` | `id`, `site_id`, `key`, `storage_backend` | File metadata |

Run migrations with Alembic:
```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

---

## How to Add a New Query Module

Each query module lives in `services/queries/` and must expose one async function:

```python
# services/queries/my_new_source.py

async def query(ctx) -> dict:
    """
    ctx.bbox        — (minLon, minLat, maxLon, maxLat)
    ctx.site_id     — string UUID
    ctx.buffer_meters — float, default 1609 (1 mile)
    """
    # Call external API, return dict with GeoJSON features
    return {
        "source": "My Data Source",
        "features": [],   # GeoJSON Feature dicts
    }
```

Then register the module in **two places**:

1. **`services/queries/query_runner.py`** — add to `QUERY_MODULES` dict:
   ```python
   from services.queries import my_new_source
   QUERY_MODULES["my_new_source"] = my_new_source
   ```

2. **`routers/queries.py`** — add the string key to `AVAILABLE_QUERIES`:
   ```python
   AVAILABLE_QUERIES = [..., "my_new_source"]
   ```

That's it. The query runner will automatically execute it in parallel with
other queries and return results in the same response envelope.

---

## How to Add a New Storage Backend

1. Create `services/storage/my_backend.py` implementing these async methods:
   - `put(key, data, content_type) -> str`
   - `get(key) -> bytes`
   - `delete(key) -> None`
   - `list(prefix) -> list[str]`
   - `url(key, expires_seconds) -> str`

2. Add a new `Literal` value to `StorageBackend` in `config/settings.py`

3. Add the import branch in `services/storage/storage_manager.py`
   inside `_init_backend()`

---

## How to Add a New Exporter

1. Create `services/exporters/my_format.py` with a top-level function:
   ```python
   def export_my_format(site: dict, layers: list[dict]) -> bytes:
       ...
   ```

2. Add `"my_format"` to `EXPORT_FORMATS` in `routers/exports.py`

3. Wire the format string → function call in the Celery export task
   (once the task is implemented in `routers/exports.py`)

---

## Running Tests

```bash
source .venv/bin/activate
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests use FastAPI's `TestClient` (synchronous) for HTTP endpoint tests
and plain pytest for utility unit tests.

---

## CLI Tools

| Command | Purpose |
|---|---|
| `python -m cli.batch_processor run sites.csv` | Batch query from file |
| `python -m cli.endpoint_validator validate` | Check federal API uptime |
| `python -m cli.watch_folder watch ./drop --site-id <id>` | Auto-ingest folder |

---

## Code Style

- **Python 3.11+** — use `X | Y` union types, `match`, `tomllib`, etc.
- **No global state** — use FastAPI `Depends()` for DB sessions, settings, storage
- **Async by default** — all router handlers and service calls are `async def`
- **Pydantic v2** — use `model_validator`, `field_validator`, not v1 validators
- **No print()** — use Python `logging` module throughout

---

## Adding a New Router

1. Create `routers/my_feature.py` with `router = APIRouter()`
2. Import and register in `main.py`:
   ```python
   from routers import my_feature
   app.include_router(my_feature.router, prefix="/api/v1/my-feature", tags=["my-feature"])
   ```
3. Add to `routers/__init__.py` exports
