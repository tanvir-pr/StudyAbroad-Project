# StudyPath EU (backend)

FastAPI backend for the StudyPath EU AI study-abroad platform.

## Quick start

```bash
# from repo root
docker compose up -d
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python scripts/seed_catalog.py
uv run uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Catalog list filters for programs: `country`, `degree`, `max_tuition`, `language`, `ielts`, `deadline_before`, `q`. Compare: `GET /api/v1/programs/compare?ids=...&ids=...`
