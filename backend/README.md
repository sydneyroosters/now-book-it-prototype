# NBI No-Show Prediction Engine

NBI (Next Booking Intelligence) is a production-quality AI backend that predicts restaurant no-show risk for upcoming bookings. It uses a Claude claude-opus-4-6 agent with a tool-call loop to gather guest history, live weather data, historical slot statistics, and vector-similar past cases — then outputs a structured risk score and actionable staff recommendations.

---

## What NBI Does

- Ingests restaurant bookings and guest profiles stored in SQLite
- For each upcoming booking, runs a Claude agent that calls multiple tools to gather signals
- Returns a risk score (0-100), risk level (low / medium / high / critical), top reasons, and a specific recommended action
- Stores predictions in a log table for future accuracy tracking
- Exposes a REST API consumed by the NBI frontend dashboard

---

## Prerequisites

- Python 3.11 or higher
- An Anthropic API key (Claude claude-opus-4-6 access required)

---

## Setup

```bash
# 1. Clone the repo and navigate to the backend
cd NBI/backend

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your Anthropic API key:
#   ANTHROPIC_API_KEY=sk-ant-...
```

---

## Running the Server

```bash
# Option A — direct (with auto-reload for development)
python main.py

# Option B — uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On first start the server will:
1. Create `nbi.db` (SQLite) and initialise all tables
2. Generate 8 Sydney restaurants, 50 guests, and ~600 bookings (historical + upcoming)
3. Seed ChromaDB vector memory from historical booking outcomes
4. Print confirmation and the API URL

Interactive API docs are available at: http://localhost:8000/docs

---

## Key Endpoints

### Health check
```bash
curl http://localhost:8000/
```

### List all restaurants
```bash
curl http://localhost:8000/restaurants
```

### List upcoming bookings (next 7 days)
```bash
curl http://localhost:8000/bookings
```

### Filter by restaurant and date
```bash
curl "http://localhost:8000/bookings?restaurant_id=r1&date=2026-03-16"
```

### Score a single booking with the AI agent
```bash
curl -X POST http://localhost:8000/bookings/b1234567890/score
```

### Score all unscored upcoming bookings synchronously
```bash
curl -X POST http://localhost:8000/score/now
```

### Queue batch scoring in the background (returns immediately)
```bash
curl -X POST http://localhost:8000/score/batch
```

### Get guest profile and booking history
```bash
curl http://localhost:8000/guests/g_vip_01
```

### Filter guests by tag or VIP status
```bash
curl "http://localhost:8000/guests?vip_only=true"
curl "http://localhost:8000/guests?tag=high_risk"
curl "http://localhost:8000/guests?high_risk=true"
```

### Live Sydney weather forecast
```bash
curl http://localhost:8000/weather
curl http://localhost:8000/weather/2026-03-16
```

### Dashboard summary (today's bookings, risk breakdown, revenue at risk)
```bash
curl http://localhost:8000/dashboard/summary
```

### Prediction accuracy stats
```bash
curl http://localhost:8000/dashboard/accuracy
```

### Today's at-risk bookings
```bash
curl http://localhost:8000/dashboard/at-risk
```

---

## How the Agent Works

When `POST /bookings/{id}/score` is called, the following loop runs:

1. **Context assembly** — the booking details (guest ID, date, time, party size, deposit status, channel, lead time) are passed to Claude claude-opus-4-6 as the initial user message.

2. **Tool call loop (max 8 iterations)**:
   - `get_guest_profile` — fetches SQLite guest record including total bookings, no-show rate, spend, tags, and notes. This is always the first call and the strongest signal.
   - `get_weather_forecast` — hits Open-Meteo (no API key needed) for the booking date. Rain >5 mm and extreme heat (>33°C) raise risk.
   - `get_slot_history` — queries SQLite for historical no-show rates on the same day-of-week and hour at the same restaurant.
   - `get_similar_past_cases` — queries ChromaDB (embedded, no server needed) for the three most semantically similar historical bookings and their outcomes.
   - `submit_risk_assessment` — Claude calls this when it has enough data. This terminates the loop.

3. **Persistence** — the risk score, level, reasons, and recommended action are written back to the `bookings` table. A row is appended to `prediction_logs` for accuracy tracking.

4. **Response** — the API returns the full `risk_result` dict plus a `reasoning_steps` list showing which tools were called and what they returned.

---

## Risk Score Guide

| Score | Level    | Recommended action                                    |
|-------|----------|-------------------------------------------------------|
| 0-25  | low      | Standard automated reminder only                      |
| 26-50 | medium   | Send confirmation request SMS 48 hrs before           |
| 51-75 | high     | Personal phone call, activate waitlist                |
| 76-100| critical | Call immediately, consider releasing table at T-2 hrs |

---

## Production Upgrade Path

| Concern              | Current (dev)                  | Production recommendation                         |
|----------------------|-------------------------------|---------------------------------------------------|
| Database             | SQLite (`nbi.db`)              | PostgreSQL via SQLAlchemy + Alembic migrations    |
| Vector store         | ChromaDB embedded              | ChromaDB server, Pinecone, or pgvector            |
| Background jobs      | FastAPI `BackgroundTasks`      | Celery + Redis for reliable queuing               |
| Auth                 | None                           | OAuth2 / API key middleware                       |
| Rate limiting        | None                           | slowapi or API gateway                            |
| Secrets              | `.env` file                    | AWS Secrets Manager / Vault                       |
| Observability        | `print()` statements           | Structured logging (structlog), OpenTelemetry     |
| Deployment           | `python main.py`               | Docker + gunicorn, ECS/Cloud Run, or Railway      |
| Model version        | claude-opus-4-6 (hardcoded)       | Config-driven, support fallback model             |
| Accuracy feedback    | Manual `was_correct` updates   | Nightly outcome reconciliation job                |
