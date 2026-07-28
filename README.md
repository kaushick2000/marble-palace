# Marble Palace — Visitor / Lead Tracking Backend

FastAPI + PostgreSQL backend for a showroom visitor sign-in tablet and an admin dashboard for reviewing/exporting visits.

## Stack

- FastAPI (async)
- PostgreSQL + SQLAlchemy 2.0 (async, via asyncpg)
- Alembic migrations
- Pydantic v2 schemas/validation
- Opaque, DB-backed session tokens for admin auth (bcrypt-hashed passwords via passlib)

## Project layout

```
app/
  main.py                  # app factory, CORS, exception handlers, /health
  core/                    # config.py, security.py, exception_handlers.py
  db/                      # session.py, base.py
  models/                  # visitor.py, admin_user.py
  schemas/                 # visitor.py, auth.py
  api/
    deps.py                # session-token auth dependency
    routes/                # public.py, auth.py, admin.py
  services/                # excel_export.py
alembic/                   # migrations
seed_admin.py               # create the first admin user
```

## Local setup

1. Copy the env file and adjust as needed:
   ```bash
   cp .env.example .env
   ```
2. Start Postgres + the app (hot-reload enabled):
   ```bash
   docker compose up --build
   ```
3. Run migrations (from your host, with a venv pointed at the same DB, or exec into the container):
   ```bash
   docker compose exec app alembic upgrade head
   ```
4. Create the first admin user:
   ```bash
   docker compose exec app python seed_admin.py --username admin --password "change-me"
   ```
5. API is now up at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

### Running without Docker

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
# point DATABASE_URL in .env at a local Postgres instance (not "db")
alembic upgrade head
python seed_admin.py --username admin --password "change-me"
uvicorn app.main:app --reload
```

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy URL, e.g. `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `SESSION_TOKEN_EXPIRE_MINUTES` | Admin session token lifetime in minutes (default `480`) |
| `JWT_SECRET_KEY` | Reserved for future JWT-based auth; unused by the current session-token auth |
| `JWT_ALGORITHM` | Reserved, same as above (default `HS256`) |
| `JWT_EXPIRE_MINUTES` | Reserved, same as above (default `60`) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `ADMIN_SETUP_SECRET` | Shared secret intended for gating admin bootstrap flows |

## API reference

### Public — visitor sign-in (no auth)

**`POST /api/visitor-entries`**

```bash
curl -X POST http://localhost:8000/api/visitor-entries \
  -H "Content-Type: application/json" \
  -d '{
    "how_heard": "google",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone_number": "555-123-4567",
    "email": "jane@example.com",
    "reason_for_visit": "new_project_estimate"
  }'
```

### Auth

**`POST /api/auth/login`**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "change-me"}'
```

Returns `{"token": "...", "expires_at": "..."}` and also sets an httponly `session_token` cookie. Use the token as a bearer header on admin routes:

```bash
curl http://localhost:8000/api/admin/visitor-entries \
  -H "Authorization: Bearer <token>"
```

**`POST /api/auth/logout`**

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <token>"
```

### Admin (session-token protected)

**`GET /api/admin/visitor-entries`** — pagination, filtering, sorting

```bash
curl "http://localhost:8000/api/admin/visitor-entries?limit=20&offset=0&date_from=2026-01-01T00:00:00&date_to=2026-12-31T23:59:59&reason_for_visit=new_project_estimate&how_heard=google&sort=created_at_desc" \
  -H "Authorization: Bearer <token>"
```

**`GET /api/admin/visitor-entries/{id}`**

```bash
curl http://localhost:8000/api/admin/visitor-entries/<uuid> \
  -H "Authorization: Bearer <token>"
```

**`GET /api/admin/visitor-entries/export`** — same filters as list, returns an `.xlsx` file

```bash
curl "http://localhost:8000/api/admin/visitor-entries/export?reason_for_visit=new_project_estimate" \
  -H "Authorization: Bearer <token>" \
  -o visitor-entries.xlsx
```

### Health

```bash
curl http://localhost:8000/health
```

## Coolify deployment

- **Build pack:** Dockerfile (uses the multi-stage `Dockerfile` at the repo root; `docker-compose.yml` is for local dev only and is not used in production).
- **Required environment variables** (set directly in Coolify — no `.env` file is read at runtime):
  - `DATABASE_URL` — point at Coolify's managed Postgres or your own instance; must NOT rely on `localhost`/`db` hostnames
  - `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` — reserved for future use, set to non-default values regardless
  - `SESSION_TOKEN_EXPIRE_MINUTES`
  - `CORS_ORIGINS` — comma-separated list of your production frontend origin(s)
  - `ADMIN_SETUP_SECRET`
- **Migrations:** run `alembic upgrade head` as a pre-deploy/release command in Coolify, or manually once via `docker exec` into the running container on first deploy. This app does not run migrations automatically on startup.
- **Health check:** point Coolify's health check at `GET /health` (checks DB connectivity, returns 200 with `{"status": "ok"}` when healthy).
- **Seeding the first admin:** run `python seed_admin.py --username <user> --password <pass>` once via `docker exec` (or `ADMIN_USERNAME`/`ADMIN_PASSWORD` env vars) after the first successful migration.
