# finpyme-backend

FastAPI backend for FinPyme — AI-powered financial dashboard for Colombian SMEs.

## Stack

| Layer | Tech |
|---|---|
| API | FastAPI 0.110+ |
| ORM | SQLAlchemy 2.0 async |
| DB | PostgreSQL + asyncpg |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| AI | Anthropic Claude API |
| Tests | pytest-asyncio + httpx |

## Quick start

```bash
# 1. Create virtualenv
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY

# 4. Create DB and run migrations
createdb finpyme
alembic revision --autogenerate -m "init"
alembic upgrade head

# 5. Run dev server
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Email + password → JWT |
| GET | `/auth/me` | Current user info |
| GET | `/empresas/me` | Current tenant data |
| GET | `/periodos/` | List all periods |
| GET | `/periodos/{periodo}` | Single period detail |
| POST | `/periodos/` | Create / update period |
| POST | `/analisis/generar` | Generate AI analysis |
| GET | `/analisis/{periodo}` | Latest analysis for period |

## Architecture

Multi-tenant: every request carries a JWT that encodes `empresa_id`.
`TenantMiddleware` extracts it and sets `request.state.empresa_id`.
All DB queries filter by `empresa_id` — tenants are fully isolated.

## Running tests

```bash
createdb finpyme_test
pytest
```
