# Now Book It — No-Show Predictor

A prototype AI-powered no-show prediction engine for restaurant bookings. Predicts which guests are likely to no-show using a rule-based scoring engine with real weather data, and surfaces personalised retention offers to reduce revenue loss.

---

## What It Does

- Scores every upcoming booking with a risk level (low / medium / high / critical) based on guest history, booking signals, and live weather forecasts
- Displays a 7-day weather impact bar showing rain, temperature, and at-risk booking counts per day
- Lets staff send personalised deposit requests or incentive offers to high-risk guests before they no-show
- Supports 20 restaurants across all Australian states and territories

---

## Architecture

```
now-book-it/
├── backend/    FastAPI + SQLite + Open-Meteo weather API
└── frontend/   React + Vite + Tailwind CSS
```

### Backend

- **FastAPI** — REST API served via uvicorn
- **SQLite** — ephemeral database at `/tmp/nbi.db`, regenerated on each deploy with synthetic data
- **Open-Meteo** — free weather API (no key required), fetched per restaurant location, cached 1 hour
- **Rule-based scoring engine** — scores all upcoming bookings at startup using guest archetypes, booking signals, and weather risk
- **Synthetic data** — 20 restaurants, 80 guests across 7 behavioural archetypes, 28 days of upcoming bookings

### Frontend

- **React + Vite + TypeScript**
- **TanStack Query** — data fetching with 30-second polling
- **Tailwind CSS** — dark-mode UI with risk-colour design tokens
- **Lucide React** — icons

---

## Scoring Signals

Each booking is scored 1–99 based on:

| Signal | Effect |
|---|---|
| Guest archetype (chronic no-show, VIP, etc.) | Base score range |
| Confirmed via phone | −30 |
| Confirmed via SMS | −22 |
| Confirmed via email | −18 |
| No confirmation | +10 |
| No deposit | +8 |
| Large party (>5) | +5 |
| Same-day booking | +12 |
| High weather risk | +12–20 |
| Medium weather risk | +5–10 |
| VIP guest | −15 |
| Deposit paid | −8 |

Scores map to: **Low** (<26) · **Medium** (26–50) · **High** (51–75) · **Critical** (76+)

---

## Running Locally

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
bun install          # or: npm install
bun run dev          # or: npm run dev
```

Set `VITE_BOOKINGS_API_URL=http://localhost:8000` in `frontend/.env`.

---

## Deployment

Both services are deployed on [Railway](https://railway.app):

- **Backend**: Python service via Nixpacks, starts with `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend**: Static build via Nixpacks + Caddy, built with `bun run build`

Required Railway environment variables:

| Variable | Service | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Backend | For AI re-scoring endpoint |
| `VITE_BOOKINGS_API_URL` | Frontend | Backend public URL |

---

## Synthetic Data

Generated on each cold start. All dates and times are anchored to **Australia/Sydney** timezone.

- **20 restaurants** across NSW, VIC, QLD, WA, SA, TAS, NT, ACT
- **80 guests** across 7 archetypes: new customer, reliable regular, VIP loyal, occasional visitor, unreliable, chronic no-show, big spender
- **28 days** of upcoming bookings (3–6 per restaurant per day)
- **12 months** of historical bookings for pattern context
