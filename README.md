# TSLA Simulator Platform

An options backtesting platform with a FastAPI backend and React frontend.

## Project Structure

```
tsla-simulator-platform/
├── app/                    # FastAPI application
│   ├── api/v1/             # REST endpoints (backtest, strategy, data, report)
│   ├── core/
│   │   ├── data/           # Parquet data loader
│   │   └── engine/         # Backtest engine (simulator, decision, executor …)
│   ├── models/             # SQLAlchemy ORM models
│   ├── services/           # Business logic layer
│   ├── tasks/              # Celery async tasks
│   ├── config.py           # Settings (loaded from .env)
│   ├── database.py         # SQLAlchemy engine & session
│   ├── celery_app.py       # Celery application
│   └── main.py             # FastAPI entry point
├── frontend/               # React + Vite frontend
├── data/                   # Parquet data files (git-ignored)
├── .env                    # Local environment variables (git-ignored)
├── .env.example            # Environment variable template
├── .venv/                  # Python virtual environment (git-ignored)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Local Development Setup

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11 + |
| Node.js | 18 + |
| Docker & Docker Compose | any recent |
| PostgreSQL | 16 (or via Docker) |
| Redis | 7 (or via Docker) |

### 1 — Clone & configure environment

```bash
git clone <repo-url>
cd tsla-simulator-platform

# Copy the env template and fill in your values
cp .env.example .env
```

Key variables in `.env`:

```dotenv
DATABASE_URL=postgresql://tsla_user:tsla_pass@localhost:5432/tsla_simulator
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
DATA_DIR=./data
SECRET_KEY=<your-random-secret>
```

### 2 — Start infrastructure (PostgreSQL + Redis)

```bash
# Spin up only the DB and Redis containers, keep everything else local
docker-compose up -d db redis
```

### 3 — Python virtual environment

```bash
# Create the virtual environment (only needed once)
python3 -m venv .venv

# Activate it
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4 — Run the FastAPI backend

```bash
# From the project root (with .venv active)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs are available at <http://localhost:8000/docs>

### 5 — Run the Celery worker

Open a second terminal (with `.venv` active):

```bash
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### 6 — Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is served at <http://localhost:5173>

---

## Docker — Full Stack

To run every service in containers:

```bash
docker-compose up -d
```

| Service | URL |
|---------|-----|
| FastAPI backend | <http://localhost:8000> |
| API docs (Swagger) | <http://localhost:8000/docs> |
| Frontend | <http://localhost:5173> |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

View logs:

```bash
docker-compose logs -f backend celery_worker
```

Stop everything:

```bash
docker-compose down
```

---

## Data Files

Place Parquet data files under `data/<symbol>/`:

```
data/
└── tsla/
    ├── underlying_TSLA_with_iv.parquet
    └── options_TSLA.parquet
```

The `data/` directory is git-ignored. Contact the team for sample datasets.

---

## Environment Variables Reference

See [.env.example](.env.example) for the full list of supported variables.
