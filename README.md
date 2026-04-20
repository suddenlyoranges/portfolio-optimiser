# Portfolio Optimiser

A full-stack portfolio optimisation web application. The backend is built with FastAPI and the frontend with React + Vite. It supports portfolio construction, mean-variance optimisation, historical backtesting, and beta hedging.

---

## Prerequisites

| Tool                    | Minimum Version |
| ----------------------- | --------------- |
| Python                  | 3.12            |
| Node.js                 | 18              |
| Docker + Docker Compose | 24              |
| Git                     | any             |

Docker is only required for the Docker-based setup. The local development setup uses a standalone Postgres container instead.

---

## Option 1 — Docker Compose (recommended for a quick run)

Runs the database, backend, and frontend together in containers.

```bash
git clone <repo-url>
cd portfolio-optimiser
docker compose up --build
```

| Service            | URL                        |
| ------------------ | -------------------------- |
| Frontend           | http://localhost:3000      |
| Backend API        | http://localhost:8000      |
| API docs (Swagger) | http://localhost:8000/docs |

To stop all services:

```bash
docker compose down
```

To stop and delete the database volume:

```bash
docker compose down -v
```

---

## Option 2 — Local Development (hot reload for both frontend and backend)

This setup runs the database in Docker but the backend and frontend directly on your machine so that code changes are reflected immediately without rebuilding containers.

### Step 1 — Start the database

```bash
docker compose -f docker-compose.dev.yml up db -d
```

This starts a Postgres 16 instance on port `5432` with:

- **User:** `postgres`
- **Password:** `postgres`
- **Database:** `portfolio_optimiser`

A pgAdmin instance is also available at http://localhost:5050 (email: `admin@admin.com`, password: `admin`).

---

### Step 2 — Configure the backend environment

```bash
cd backend
copy .env.example .env
```

Open `.env` and confirm or update the values:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_optimiser
SECRET_KEY=change-me-to-a-random-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GUEST_TOKEN_EXPIRE_HOURS=24
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

### Step 3 — Create a Python virtual environment and install dependencies

From the `backend/` directory:

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

---

### Step 4 — Run database migrations

Still inside `backend/` with the virtual environment active:

**Windows (PowerShell):**

```powershell
$env:PYTHONPATH = "."
alembic upgrade head
```

**macOS / Linux:**

```bash
PYTHONPATH=. alembic upgrade head
```

---

### Step 5 — Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000. Interactive API docs are at http://localhost:8000/docs.

---

### Step 6 — Install frontend dependencies and start the dev server

Open a new terminal, navigate to the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173.

---

## Running Tests

From the project root with the virtual environment active:

```bash
pytest --tb=short -v
```

All tests are located in `backend/tests/`. The test suite covers the optimisation engine, backtest engine, and hedging module (19 tests total). No database connection is required to run the tests.

---

## Environment Variables Reference

| Variable                      | Description                                      | Default |
| ----------------------------- | ------------------------------------------------ | ------- |
| `DATABASE_URL`                | asyncpg connection string                        | —       |
| `SECRET_KEY`                  | JWT signing key — change in production           | —       |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime                            | `30`    |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token lifetime                           | `7`     |
| `GUEST_TOKEN_EXPIRE_HOURS`    | Guest session lifetime                           | `24`    |
| `CORS_ORIGINS`                | Comma-separated list of allowed frontend origins | —       |

---

## Project Structure

```
portfolio-optimiser/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, middleware, router registration
│   │   ├── config.py          # Pydantic settings (reads .env)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # Route handlers (auth, portfolios, assets, ...)
│   │   └── services/          # Business logic (optimisation, backtest, hedging, market data)
│   ├── alembic/               # Database migration scripts
│   ├── tests/                 # Pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/             # React page components
│   │   ├── components/        # Reusable UI components and charts
│   │   └── api/               # Axios API client modules
│   └── package.json
├── docker-compose.yml         # Production Docker Compose
└── docker-compose.dev.yml     # Development Docker Compose (includes pgAdmin, hot reload)
```
