# Authentication Backend

## Prerequisites

- Python 3.12+ and Git
- PostgreSQL and `psql` (or pgAdmin)

## Setup (Windows PowerShell)

```powershell
git clone <repository-url> user-auth
cd user-auth
py -m venv userauth-venv
.\userauth-venv\Scripts\Activate.ps1
pip install -r requirements.txt
psql -U postgres -c "CREATE DATABASE userauth;"
cd userauth-be
Copy-Item .env.example .env
```

Fill every variable in `.env` using the comments in `.env.example`. Set `ASYNC_DATABASE_URL` to your PostgreSQL user, password, host, port and database. Use two different random JWT secrets; generate each with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Use `0,0,15,0` and `7,0,0,0` for access and refresh lifetimes, respectively. Add `http://127.0.0.1:8000` to `CORS_ALLOWED_ORIGINS` to use direct Swagger requests.

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. The database user must have access to `userauth`. Never commit `.env`.

## Run tests

From `userauth-be`, with the virtual environment active:

```bash
pytest .
```

Tests use `.env.test` and an isolated in-memory database. The PostgreSQL integration test is skipped unless a separate test database is configured.

## Promote an admin

Register the user first, then run from `userauth-be`:

```powershell
python -m scripts.promote_admin user@example.com
```

Replace the email with the registered user's email.

## Folders

- `app/modules/user/` — user models, schemas, repository, service and routes.
- `app/config/` — settings, database sessions and logging.
- `app/security/` — password hashing, JWT, cookies and authorization.
- `app/middleware/` — origin checks and error responses.
- `app/utils/` — shared models, schemas, repositories and constants.
- `alembic/` — database migrations.
- `tests/user/` — router integration tests; `scripts/` — administrative commands.

## Add or update a feature

1. Create a module under `app/modules/`; define SQLAlchemy models and import them in `alembic/env.py` for migration discovery.
2. Create and review the migration, then apply it:

   ```powershell
   alembic revision --autogenerate -m "describe change"
   alembic upgrade head
   ```

3. Add request/response schemas, database queries in a repository, and business rules in a service. The request session owns commit and rollback.
4. Add routes, attach the shared authorization dependency where required, and register the router in `app/main.py`.
5. Add router tests in `tests/<module>/`; run `python -m pytest`. Tests use `.env.test` and an isolated in-memory database.
