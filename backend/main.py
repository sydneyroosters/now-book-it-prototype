"""
NBI No-Show Prediction Engine — FastAPI Application
"""

from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio
import database
import data_generator
import weather as weather_module
import memory as mem
import agent
import json
from datetime import datetime, date, timedelta
from typing import Optional, Literal
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

booking_memory = None


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global booking_memory
    print("Starting NBI No-Show Prediction Engine...")

    # 1. Initialise database schema
    database.init_db()
    print("Database initialised")

    # 2. Seed sample data (no-op if already populated)
    data_generator.generate_sample_data()
    print("Sample data ready")

    # 3. Seed ChromaDB vector memory
    booking_memory = mem.BookingMemory()
    conn = database.get_connection()
    booking_memory.seed_from_historical_bookings(conn)
    conn.close()
    print("Vector memory seeded")

    # 4. Pre-score upcoming bookings with weather-aware rule engine
    weather_map = await weather_module.get_sydney_weather()
    data_generator.pre_score_upcoming_bookings(weather_map)
    print("Upcoming bookings pre-scored")


    print("\nNBI API running at http://localhost:8000")
    print("Docs at http://localhost:8000/docs\n")

    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NBI No-Show Prediction Engine",
    description="AI-powered no-show prediction for Sydney restaurants.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    stats = database.get_accuracy_stats()
    upcoming = database.get_upcoming_bookings(days_ahead=7)
    high_risk = [b for b in upcoming if b.get("risk_level") in ("high", "critical")]
    return {
        "status": "ok",
        "service": "NBI No-Show Prediction Engine",
        "upcoming_bookings": len(upcoming),
        "high_risk_bookings": len(high_risk),
        "prediction_accuracy": stats.get("overall_accuracy"),
        "docs": "http://localhost:8000/docs"
    }


# ---------------------------------------------------------------------------
# Restaurants
# ---------------------------------------------------------------------------

@app.get("/restaurants", tags=["Restaurants"])
def list_restaurants():
    conn = database.get_connection()
    rows = conn.execute("SELECT * FROM restaurants").fetchall()
    conn.close()
    cols = ["id", "name", "suburb", "cuisine", "capacity", "lat", "lon", "avg_spend", "tier", "state"]
    return [dict(zip(cols, r)) for r in rows]


@app.get("/restaurants/{restaurant_id}", tags=["Restaurants"])
def get_restaurant(restaurant_id: str):
    r = database.get_restaurant(restaurant_id)
    if not r:
        raise HTTPException(404, "Restaurant not found")
    return r


@app.get("/restaurants/{restaurant_id}/bookings", tags=["Restaurants"])
def restaurant_bookings(restaurant_id: str, days_ahead: int = 7):
    return database.get_upcoming_bookings(days_ahead=days_ahead, restaurant_id=restaurant_id)


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

@app.get("/bookings", tags=["Bookings"])
def list_bookings(
    days_ahead: int = 7,
    restaurant_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    date: Optional[str] = None
):
    bookings = database.get_upcoming_bookings(
        days_ahead=days_ahead,
        restaurant_id=restaurant_id,
        risk_level=risk_level
    )
    if date:
        bookings = [b for b in bookings if b.get("booking_date") == date]
    return bookings


@app.get("/bookings/{booking_id}", tags=["Bookings"])
def get_booking(booking_id: str):
    b = database.get_booking(booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    if isinstance(b.get("risk_reasons"), str):
        try:
            b["risk_reasons"] = json.loads(b["risk_reasons"])
        except Exception:
            pass
    return b


@app.post("/bookings/{booking_id}/score", tags=["Scoring"])
async def score_booking(booking_id: str):
    """Score a single booking using the Claude agent."""
    b = database.get_booking(booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")

    result = await agent.score_booking(booking_id, memory_instance=booking_memory)
    risk = result["risk_result"]

    database.update_booking_risk(
        booking_id,
        risk["risk_score"],
        risk["risk_level"],
        json.dumps(risk.get("top_reasons", [])),
        risk.get("recommended_action", "")
    )
    database.log_prediction(
        booking_id,
        risk["risk_score"],
        risk["risk_level"],
        risk.get("confidence", 50),
        json.dumps([s["tool"] for s in result["reasoning_steps"]])
    )

    return {
        "booking_id": booking_id,
        "risk_result": risk,
        "reasoning_steps": result["reasoning_steps"]
    }


# ---------------------------------------------------------------------------
# Outcome recording (feedback loop)
# ---------------------------------------------------------------------------

class OutcomeRequest(BaseModel):
    outcome: Literal["completed", "no_show", "cancelled"]
    notes: str = ""


@app.post("/bookings/{booking_id}/outcome", tags=["Bookings"])
def record_booking_outcome(booking_id: str, body: OutcomeRequest):
    """Record the actual outcome of a booking. Updates both SQLite and ChromaDB vector memory."""
    b = database.get_booking(booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    conn = database.get_connection()
    database.record_outcome(conn, booking_id, body.outcome, body.notes)
    conn.close()
    if booking_memory:
        booking_memory.update_outcome_in_memory(booking_id, body.outcome)
    return {"status": "recorded", "booking_id": booking_id, "outcome": body.outcome}


# ---------------------------------------------------------------------------
# Bulk scoring
# ---------------------------------------------------------------------------

@app.post("/score/now", tags=["Scoring"])
async def score_all_now():
    """Score all unscored upcoming bookings synchronously. May take several minutes."""
    bookings = database.get_upcoming_bookings(days_ahead=7)
    unscored = [b for b in bookings if not b.get("risk_score")]
    results = []
    for b in unscored:
        try:
            result = await agent.score_booking(b["id"], memory_instance=booking_memory)
            risk = result["risk_result"]
            database.update_booking_risk(
                b["id"], risk["risk_score"], risk["risk_level"],
                json.dumps(risk.get("top_reasons", [])), risk.get("recommended_action", "")
            )
            database.log_prediction(
                b["id"], risk["risk_score"], risk["risk_level"],
                risk.get("confidence", 50),
                json.dumps([s["tool"] for s in result["reasoning_steps"]])
            )
            results.append({
                "booking_id": b["id"],
                "risk_level": risk["risk_level"],
                "score": risk["risk_score"]
            })
        except Exception as e:
            results.append({"booking_id": b["id"], "error": str(e)})
    return {"scored": len(results), "results": results}


@app.post("/score/batch", tags=["Scoring"])
async def score_batch(background_tasks: BackgroundTasks):
    """Queue all unscored upcoming bookings for background scoring. Returns immediately."""
    bookings = database.get_upcoming_bookings(days_ahead=7)
    unscored = [b for b in bookings if not b.get("risk_score")]

    async def run_batch():
        for b in unscored:
            try:
                result = await agent.score_booking(b["id"], memory_instance=booking_memory)
                risk = result["risk_result"]
                database.update_booking_risk(
                    b["id"], risk["risk_score"], risk["risk_level"],
                    json.dumps(risk.get("top_reasons", [])), risk.get("recommended_action", "")
                )
                database.log_prediction(
                    b["id"], risk["risk_score"], risk["risk_level"],
                    risk.get("confidence", 50),
                    json.dumps([s["tool"] for s in result["reasoning_steps"]])
                )
            except Exception as e:
                print(f"Error scoring {b['id']}: {e}")

    background_tasks.add_task(run_batch)
    return {"status": "started", "bookings_queued": len(unscored)}


# ---------------------------------------------------------------------------
# Guests
# ---------------------------------------------------------------------------

@app.get("/guests", tags=["Guests"])
def list_guests(
    vip_only: bool = False,
    high_risk: bool = False,
    tag: Optional[str] = None
):
    conn = database.get_connection()
    query = "SELECT * FROM guests"
    conditions = []
    params = []
    if vip_only:
        conditions.append("vip = 1")
    if high_risk:
        conditions.append("(CAST(total_noshows AS FLOAT) / NULLIF(total_bookings, 0)) > 0.3")
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f'%"{tag}"%')
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    rows = conn.execute(query, params).fetchall()
    conn.close()

    cols = [
        "id", "name", "email", "phone", "total_bookings", "total_noshows", "total_spend",
        "member_since", "vip", "preferred_time", "favourite_items", "notes", "tags"
    ]
    guests = []
    for r in rows:
        g = dict(zip(cols, r))
        if isinstance(g.get("tags"), str):
            try:
                g["tags"] = json.loads(g["tags"])
            except Exception:
                pass
        guests.append(g)
    return guests


@app.get("/guests/{guest_id}", tags=["Guests"])
def get_guest(guest_id: str):
    guest = database.get_guest(guest_id)
    if not guest:
        raise HTTPException(404, "Guest not found")
    bookings = database.get_guest_bookings(guest_id, limit=20)
    return {"guest": guest, "bookings": bookings}


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

@app.get("/weather", tags=["Weather"])
async def get_weather():
    """Full 7-day Sydney weather forecast from Open-Meteo."""
    return await weather_module.get_sydney_weather()


@app.get("/weather/{date}", tags=["Weather"])
async def get_weather_date(date: str):
    """Weather for a specific date (YYYY-MM-DD)."""
    weather_map = await weather_module.get_sydney_weather()
    return weather_module.get_weather_for_date(weather_map, date)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/dashboard/summary", tags=["Dashboard"])
def dashboard_summary():
    """Today's booking summary: covers, risk breakdown, revenue at risk."""
    today = datetime.now().date().isoformat()
    bookings = database.get_upcoming_bookings(days_ahead=1)
    today_bookings = [b for b in bookings if b.get("booking_date") == today]
    covers = sum(b.get("party_size", 0) for b in today_bookings)

    risk_breakdown = {"low": 0, "medium": 0, "high": 0, "critical": 0, "unscored": 0}
    revenue_at_risk = 0

    for b in today_bookings:
        rl = b.get("risk_level")
        if rl in risk_breakdown:
            risk_breakdown[rl] += 1
        else:
            risk_breakdown["unscored"] += 1
        if rl in ("high", "critical"):
            revenue_at_risk += b.get("party_size", 2) * b.get("avg_spend", 80)

    return {
        "date": today,
        "total_bookings": len(today_bookings),
        "total_covers": covers,
        "risk_breakdown": risk_breakdown,
        "revenue_at_risk": revenue_at_risk
    }


@app.get("/dashboard/accuracy", tags=["Dashboard"])
def dashboard_accuracy():
    """Prediction accuracy stats across all logged predictions."""
    return database.get_accuracy_stats()


@app.get("/dashboard/weather-impact", tags=["Dashboard"])
async def dashboard_weather_impact(
    lat: float = Query(default=weather_module.DEFAULT_LAT, description="Restaurant latitude"),
    lon: float = Query(default=weather_module.DEFAULT_LON, description="Restaurant longitude"),
    restaurant_id: Optional[str] = Query(default=None, description="Filter bookings by restaurant"),
):
    """
    7-day view: for each day, shows weather forecast + risk breakdown + revenue at risk.
    Powers the real-time weather impact strip on the frontend.
    Refreshes weather from Open-Meteo every hour.
    """
    try:
        weather_map = await weather_module.get_sydney_weather(lat, lon)
    except Exception:
        weather_map = {}
    today = datetime.now().date()
    result = []

    for i in range(7):
        day = today + timedelta(days=i)
        date_str = day.isoformat()
        weather = weather_module.get_weather_for_date(weather_map, date_str)

        bookings = database.get_upcoming_bookings(days_ahead=1 + i)
        day_bookings = [
            b for b in bookings
            if b.get("booking_date") == date_str
            and (not restaurant_id or b.get("restaurant_id") == restaurant_id)
        ]

        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0, "unscored": 0}
        revenue_at_risk = 0
        total_covers = 0

        for b in day_bookings:
            rl = b.get("risk_level")
            if rl in risk_counts:
                risk_counts[rl] += 1
            else:
                risk_counts["unscored"] += 1
            if rl in ("high", "critical"):
                revenue_at_risk += (b.get("party_size") or 2) * (b.get("avg_spend") or 80)
            total_covers += b.get("party_size") or 0

        total = len(day_bookings)
        at_risk = risk_counts["high"] + risk_counts["critical"]

        result.append({
            "date": date_str,
            "day_label": day.strftime("%a %-d %b"),
            "is_today": i == 0,
            "weather": weather,
            "total_bookings": total,
            "total_covers": total_covers,
            "risk_breakdown": risk_counts,
            "at_risk_count": at_risk,
            "at_risk_pct": round(at_risk / total * 100) if total > 0 else 0,
            "revenue_at_risk": revenue_at_risk,
        })

    return result


@app.get("/dashboard/at-risk", tags=["Dashboard"])
def dashboard_at_risk():
    """Today's high-risk and critical bookings."""
    bookings_high = database.get_upcoming_bookings(days_ahead=1, risk_level="high")
    bookings_critical = database.get_upcoming_bookings(days_ahead=1, risk_level="critical")
    return {
        "high_risk": bookings_high,
        "critical": bookings_critical,
        "total": len(bookings_high) + len(bookings_critical)
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
