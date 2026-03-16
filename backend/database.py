import sqlite3
import json
from datetime import datetime, timedelta
import os

DB_PATH = os.getenv("DB_PATH", "/tmp/nbi.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS restaurants (
        id TEXT PRIMARY KEY, name TEXT, suburb TEXT, cuisine TEXT,
        capacity INTEGER, lat REAL, lon REAL, avg_spend INTEGER, tier TEXT, state TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS guests (
        id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT,
        total_bookings INTEGER DEFAULT 0, total_noshows INTEGER DEFAULT 0,
        total_spend REAL DEFAULT 0, member_since TEXT, vip INTEGER DEFAULT 0,
        preferred_time TEXT, favourite_items TEXT, notes TEXT, tags TEXT DEFAULT '[]'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY, restaurant_id TEXT, guest_id TEXT,
        booking_date TEXT, booking_time TEXT, party_size INTEGER,
        occasion TEXT DEFAULT 'general', deposit_paid INTEGER DEFAULT 0,
        deposit_amount REAL DEFAULT 0, booking_channel TEXT DEFAULT 'online',
        confirmed_response INTEGER DEFAULT 0, confirmation_method TEXT,
        reminders_sent INTEGER DEFAULT 0,
        reminders_ignored INTEGER DEFAULT 0, lead_time_hours REAL DEFAULT 24,
        status TEXT DEFAULT 'upcoming', created_at TEXT,
        risk_score INTEGER, risk_level TEXT, risk_reasons TEXT, recommended_action TEXT,
        outcome_notes TEXT, cancelled_at TIMESTAMP,
        FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
        FOREIGN KEY (guest_id) REFERENCES guests(id)
    )""")

    # Migrate existing tables: add columns if they don't exist yet
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(bookings)").fetchall()}
    if "outcome_notes" not in existing_cols:
        c.execute("ALTER TABLE bookings ADD COLUMN outcome_notes TEXT")
    if "cancelled_at" not in existing_cols:
        c.execute("ALTER TABLE bookings ADD COLUMN cancelled_at TIMESTAMP")

    c.execute("""CREATE TABLE IF NOT EXISTS prediction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id TEXT,
        predicted_risk_score INTEGER, predicted_risk_level TEXT,
        actual_outcome TEXT, was_correct INTEGER,
        confidence INTEGER, signals_used TEXT, created_at TEXT
    )""")

    conn.commit()
    conn.close()


def get_guest(guest_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM guests WHERE id = ?", (guest_id,)).fetchone()
    conn.close()
    if not row:
        return None
    g = dict(row)
    if isinstance(g.get("tags"), str):
        try:
            g["tags"] = json.loads(g["tags"])
        except Exception:
            g["tags"] = []
    return g


def get_guest_bookings(guest_id: str, limit: int = 20) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM bookings WHERE guest_id = ? ORDER BY booking_date DESC, booking_time DESC LIMIT ?",
        (guest_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_restaurant(restaurant_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_upcoming_bookings(days_ahead: int = 7, restaurant_id: str = None, risk_level: str = None) -> list:
    conn = get_connection()
    today = datetime.now().date().isoformat()
    end = (datetime.now().date() + timedelta(days=days_ahead)).isoformat()

    query = """
        SELECT b.*, r.name as restaurant_name, r.suburb as restaurant_suburb,
               r.avg_spend, r.tier, g.name as guest_name, g.tags as guest_tags,
               g.total_bookings, g.total_noshows, g.vip
        FROM bookings b
        JOIN restaurants r ON b.restaurant_id = r.id
        JOIN guests g ON b.guest_id = g.id
        WHERE b.booking_date >= ? AND b.booking_date <= ?
        AND b.status IN ('upcoming', 'confirmed')
    """
    params = [today, end]

    if restaurant_id:
        query += " AND b.restaurant_id = ?"
        params.append(restaurant_id)
    if risk_level:
        query += " AND b.risk_level = ?"
        params.append(risk_level)

    query += " ORDER BY b.booking_date, b.booking_time"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_booking(booking_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("""
        SELECT b.*, r.name as restaurant_name, r.suburb as restaurant_suburb,
               r.avg_spend, r.tier, r.lat, r.lon,
               g.name as guest_name, g.email as guest_email, g.phone as guest_phone,
               g.total_bookings, g.total_noshows, g.total_spend, g.vip,
               g.tags as guest_tags, g.notes as guest_notes, g.preferred_time,
               g.favourite_items
        FROM bookings b
        JOIN restaurants r ON b.restaurant_id = r.id
        JOIN guests g ON b.guest_id = g.id
        WHERE b.id = ?
    """, (booking_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_booking_risk(booking_id: str, risk_score: int, risk_level: str, risk_reasons_json: str, recommended_action: str):
    conn = get_connection()
    conn.execute(
        "UPDATE bookings SET risk_score=?, risk_level=?, risk_reasons=?, recommended_action=? WHERE id=?",
        (risk_score, risk_level, risk_reasons_json, recommended_action, booking_id)
    )
    conn.commit()
    conn.close()


def log_prediction(booking_id: str, risk_score: int, risk_level: str, confidence: int, signals_used: str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO prediction_logs (booking_id, predicted_risk_score, predicted_risk_level,
           confidence, signals_used, created_at) VALUES (?,?,?,?,?,?)""",
        (booking_id, risk_score, risk_level, confidence, signals_used, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_accuracy_stats() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM prediction_logs").fetchone()[0]
    correct = conn.execute("SELECT COUNT(*) FROM prediction_logs WHERE was_correct = 1").fetchone()[0]

    by_level = {}
    for level in ["low", "medium", "high", "critical"]:
        lvl_total = conn.execute(
            "SELECT COUNT(*) FROM prediction_logs WHERE predicted_risk_level=?", (level,)
        ).fetchone()[0]
        lvl_correct = conn.execute(
            "SELECT COUNT(*) FROM prediction_logs WHERE predicted_risk_level=? AND was_correct=1", (level,)
        ).fetchone()[0]
        by_level[level] = {
            "total": lvl_total,
            "correct": lvl_correct,
            "accuracy": round(lvl_correct / lvl_total * 100, 1) if lvl_total > 0 else None
        }

    conn.close()
    return {
        "total_predictions": total,
        "confirmed_outcomes": correct,
        "overall_accuracy": round(correct / total * 100, 1) if total > 0 else None,
        "by_risk_level": by_level
    }


def get_restaurant_noshow_rate(conn, restaurant_id: str) -> dict:
    """Returns historical no-show rates by occasion for a restaurant."""
    rows = conn.execute("""
        SELECT occasion,
               COUNT(*) as total,
               SUM(CASE WHEN status='no_show' THEN 1 ELSE 0 END) as noshows
        FROM bookings
        WHERE restaurant_id = ? AND status IN ('confirmed', 'no_show', 'completed')
        GROUP BY occasion
    """, (restaurant_id,)).fetchall()
    result = {}
    for r in rows:
        total = r["total"]
        if total > 0:
            result[r["occasion"]] = {
                "total": total,
                "noshows": r["noshows"],
                "noshow_rate": round(r["noshows"] / total * 100, 1)
            }
    return result


def get_guest_cancellation_patterns(conn, guest_name: str, phone: str) -> dict:
    """Returns timing and frequency of past cancellations/no-shows for a guest."""
    rows = conn.execute("""
        SELECT status, booking_date, booking_time, lead_time_hours, cancelled_at
        FROM bookings
        WHERE (guest_name_lookup IS NOT NULL OR 1=1)
        AND id IN (
            SELECT b.id FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            WHERE g.name = ? OR g.phone = ?
        )
        AND status IN ('no_show', 'cancelled', 'completed')
        ORDER BY booking_date DESC LIMIT 20
    """, (guest_name, phone)).fetchall()

    noshow_count = sum(1 for r in rows if r["status"] == "no_show")
    cancelled_count = sum(1 for r in rows if r["status"] == "cancelled")
    total = len(rows)

    # Estimate last-minute cancels: lead_time_hours < 24
    last_minute = sum(
        1 for r in rows
        if r["status"] in ("no_show", "cancelled") and (r["lead_time_hours"] or 999) < 24
    )

    return {
        "total_history": total,
        "noshow_count": noshow_count,
        "cancelled_count": cancelled_count,
        "last_minute_count": last_minute,
        "noshow_rate_pct": round(noshow_count / total * 100, 1) if total > 0 else 0,
        "pattern": (
            "chronic" if noshow_count >= 3 else
            "unreliable" if noshow_count >= 1 or last_minute >= 2 else
            "reliable"
        )
    }


def record_outcome(conn, booking_id: str, outcome: str, notes: str = ""):
    """Record the actual outcome of a booking after the event."""
    cancelled_at = datetime.now().isoformat() if outcome == "cancelled" else None
    conn.execute(
        "UPDATE bookings SET status=?, outcome_notes=?, cancelled_at=? WHERE id=?",
        (outcome, notes, cancelled_at, booking_id)
    )
    conn.commit()


def get_historical_slot_stats(hour: int, day_of_week: int, restaurant_id: str) -> dict:
    conn = get_connection()
    # SQLite strftime %w: 0=Sunday. Convert Python Mon=0 to SQLite format: (dow+1)%7
    dow_sqlite = (day_of_week + 1) % 7

    rows = conn.execute("""
        SELECT status, COUNT(*) as cnt
        FROM bookings
        WHERE restaurant_id = ?
        AND CAST(strftime('%H', booking_time) AS INTEGER) = ?
        AND CAST(strftime('%w', booking_date) AS INTEGER) = ?
        AND status IN ('completed', 'no_show')
        GROUP BY status
    """, (restaurant_id, hour, dow_sqlite)).fetchall()

    conn.close()
    totals = {r["status"]: r["cnt"] for r in rows}
    total = sum(totals.values())
    noshows = totals.get("no_show", 0)

    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "restaurant_id": restaurant_id,
        "total_historical": total,
        "noshows": noshows,
        "noshow_rate_pct": round(noshows / total * 100, 1) if total > 0 else 0,
        "data_available": total > 5
    }
