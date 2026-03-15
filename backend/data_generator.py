"""
NBI No-Show Prediction Engine — Sample Data Generator
Generates 8 Sydney restaurants, 50 guests across 7 behavioural archetypes,
historical bookings (past 12 months), and upcoming bookings (next 7 days).
"""

import sqlite3
import json
import random
import uuid
from datetime import datetime, timedelta, date

import database

# ---------------------------------------------------------------------------
# Restaurant data
# ---------------------------------------------------------------------------

RESTAURANTS = [
    # New South Wales
    {"id": "r1",  "name": "Aria Sydney",               "suburb": "Circular Quay",  "cuisine": "Modern Australian",      "capacity": 120, "lat": -33.8599, "lon": 151.2090, "avg_spend": 180, "tier": "fine_dining",  "state": "NSW"},
    {"id": "r2",  "name": "Lucio's Italian",            "suburb": "Paddington",     "cuisine": "Italian",                "capacity": 75,  "lat": -33.8838, "lon": 151.2268, "avg_spend": 95,  "tier": "casual_fine",  "state": "NSW"},
    {"id": "r3",  "name": "The Grounds of Alexandria",  "suburb": "Alexandria",     "cuisine": "Cafe/Brunch",            "capacity": 200, "lat": -33.9100, "lon": 151.1944, "avg_spend": 45,  "tier": "casual",       "state": "NSW"},
    {"id": "r4",  "name": "Ester Restaurant",           "suburb": "Chippendale",    "cuisine": "Wood-fired Contemporary","capacity": 60,  "lat": -33.8872, "lon": 151.1986, "avg_spend": 110, "tier": "casual_fine",  "state": "NSW"},
    {"id": "r5",  "name": "Quay Restaurant",            "suburb": "The Rocks",      "cuisine": "Contemporary",           "capacity": 90,  "lat": -33.8591, "lon": 151.2069, "avg_spend": 220, "tier": "fine_dining",  "state": "NSW"},
    {"id": "r6",  "name": "Momofuku Seiobo",            "suburb": "Pyrmont",        "cuisine": "Contemporary Asian",     "capacity": 40,  "lat": -33.8680, "lon": 151.1935, "avg_spend": 195, "tier": "fine_dining",  "state": "NSW"},
    {"id": "r7",  "name": "Fabbrica Surry Hills",       "suburb": "Surry Hills",    "cuisine": "Italian",                "capacity": 85,  "lat": -33.8876, "lon": 151.2108, "avg_spend": 70,  "tier": "casual",       "state": "NSW"},
    {"id": "r8",  "name": "Totto Ramen",                "suburb": "Sydney CBD",     "cuisine": "Japanese",               "capacity": 45,  "lat": -33.8688, "lon": 151.2093, "avg_spend": 35,  "tier": "casual",       "state": "NSW"},
    # Victoria
    {"id": "r9",  "name": "Vue de monde",               "suburb": "Melbourne CBD",  "cuisine": "Modern French",          "capacity": 55,  "lat": -37.8210, "lon": 144.9690, "avg_spend": 220, "tier": "fine_dining",  "state": "VIC"},
    {"id": "r10", "name": "Attica",                     "suburb": "Ripponlea",      "cuisine": "Contemporary",           "capacity": 40,  "lat": -37.8740, "lon": 144.9980, "avg_spend": 195, "tier": "fine_dining",  "state": "VIC"},
    {"id": "r11", "name": "Supernormal",                "suburb": "Melbourne CBD",  "cuisine": "Contemporary Asian",     "capacity": 110, "lat": -37.8180, "lon": 144.9700, "avg_spend": 90,  "tier": "casual_fine",  "state": "VIC"},
    # Queensland
    {"id": "r12", "name": "Goma Restaurant",            "suburb": "South Brisbane", "cuisine": "Contemporary",           "capacity": 80,  "lat": -27.4698, "lon": 153.0183, "avg_spend": 120, "tier": "casual_fine",  "state": "QLD"},
    {"id": "r13", "name": "Rick Shores",                "suburb": "Broadbeach",     "cuisine": "Modern Australian",      "capacity": 70,  "lat": -28.0432, "lon": 153.4312, "avg_spend": 130, "tier": "casual_fine",  "state": "QLD"},
    # Western Australia
    {"id": "r14", "name": "Wildflower",                 "suburb": "Perth CBD",      "cuisine": "Contemporary",           "capacity": 50,  "lat": -31.9514, "lon": 115.8617, "avg_spend": 210, "tier": "fine_dining",  "state": "WA"},
    {"id": "r15", "name": "Long Chim Perth",            "suburb": "Perth CBD",      "cuisine": "Thai",                   "capacity": 90,  "lat": -31.9556, "lon": 115.8590, "avg_spend": 85,  "tier": "casual_fine",  "state": "WA"},
    # South Australia
    {"id": "r16", "name": "Orana",                      "suburb": "Adelaide CBD",   "cuisine": "Modern Australian",      "capacity": 45,  "lat": -34.9282, "lon": 138.5999, "avg_spend": 230, "tier": "fine_dining",  "state": "SA"},
    {"id": "r17", "name": "Africola",                   "suburb": "Adelaide CBD",   "cuisine": "Modern African",         "capacity": 60,  "lat": -34.9248, "lon": 138.6030, "avg_spend": 95,  "tier": "casual_fine",  "state": "SA"},
    # Tasmania
    {"id": "r18", "name": "Franklin",                   "suburb": "Hobart CBD",     "cuisine": "Contemporary",           "capacity": 55,  "lat": -42.8821, "lon": 147.3272, "avg_spend": 110, "tier": "casual_fine",  "state": "TAS"},
    # Northern Territory
    {"id": "r19", "name": "Pee Wees at the Point",      "suburb": "East Point",     "cuisine": "Modern Australian",      "capacity": 120, "lat": -12.4611, "lon": 130.8234, "avg_spend": 120, "tier": "casual_fine",  "state": "NT"},
    # Australian Capital Territory
    {"id": "r20", "name": "Temporada",                  "suburb": "Canberra CBD",   "cuisine": "Modern Australian",      "capacity": 70,  "lat": -35.2809, "lon": 149.1300, "avg_spend": 100, "tier": "casual_fine",  "state": "ACT"},
]

# ---------------------------------------------------------------------------
# Guest archetypes
# ---------------------------------------------------------------------------

# (first_name, last_name, email_domain)
GUEST_NAMES = [
    # Anglo-Australian (NSW/VIC)
    ("James", "Harrison"), ("Sophie", "Mitchell"), ("Oliver", "Thompson"), ("Emma", "Williams"),
    ("Liam", "Anderson"), ("Charlotte", "Clarke"), ("Noah", "Roberts"), ("Olivia", "Taylor"),
    ("William", "Brown"), ("Amelia", "Wilson"),
    # East Asian
    ("Wei", "Chen"), ("Mei", "Zhang"), ("Jian", "Liu"), ("Ling", "Wang"), ("Hao", "Li"),
    ("Yuki", "Tanaka"), ("Kenji", "Nakamura"), ("Sakura", "Yamamoto"), ("Min", "Park"),
    ("Soo-Jin", "Kim"),
    # Southern European
    ("Marco", "Rossi"), ("Sofia", "Ferrara"), ("Luca", "Moretti"), ("Isabella", "Conti"),
    ("Antonio", "De Luca"), ("Valentina", "Ricci"), ("Giovanni", "Esposito"),
    ("Claudia", "Bianchi"),
    # Middle Eastern / South Asian
    ("Omar", "Al-Rashid"), ("Fatima", "Hassan"), ("Amir", "Khalil"), ("Nadia", "Mansour"),
    ("Rania", "Aziz"), ("Tariq", "Ibrahim"), ("Priya", "Sharma"), ("Rajesh", "Patel"),
    ("Arjun", "Mehta"), ("Ananya", "Gupta"),
    # Anglo / Irish
    ("Patrick", "O'Brien"), ("Siobhan", "Murphy"), ("Declan", "Flynn"), ("Aoife", "Kelly"),
    ("Ciarán", "Walsh"), ("Niamh", "Ryan"), ("Connor", "McCarthy"), ("Brigid", "O'Connor"),
    ("Finn", "Doyle"), ("Clodagh", "Brennan"),
    # Victoria
    ("Ethan", "Davidson"), ("Chloe", "Barnes"), ("Jack", "Fleming"), ("Emily", "Gordon"),
    ("Thomas", "Reid"), ("Hannah", "Price"),
    # Queensland
    ("Lachlan", "Young"), ("Isabelle", "Martin"), ("Hayden", "Evans"), ("Brooke", "White"),
    # Western Australia
    ("Dylan", "Cox"), ("Samantha", "Hughes"), ("Cameron", "Morgan"), ("Jade", "Scott"),
    # South Australia
    ("Blake", "Turner"), ("Mia", "Collins"), ("Riley", "Stewart"), ("Zoe", "Baker"),
    # First Nations / diverse Australian
    ("Jarrah", "Anderson"), ("Mirri", "Williams"),
    # African / Latin American / Eastern European backgrounds common in Australia
    ("Yusuf", "Al-Farsi"), ("Layla", "Mahmoud"), ("Pedro", "Da Silva"), ("Mei-Lin", "Tan"),
    ("Sanjay", "Kumar"), ("Aisha", "Okafor"), ("Nikolai", "Petrov"), ("Amara", "Diallo"),
    # Additional
    ("Lucas", "Bennett"), ("Zara", "Nguyen"), ("Isla", "Fraser"), ("Marcus", "Thornton"),
]
# Keep backward-compatible alias
SYDNEY_NAMES = GUEST_NAMES

EMAIL_DOMAINS = ["gmail.com", "icloud.com", "outlook.com", "yahoo.com.au", "bigpond.com", "hotmail.com"]

PREFERRED_TIMES = ["12:00", "12:30", "13:00", "18:30", "19:00", "19:30", "20:00", "20:30"]

FAVOURITE_ITEMS_POOL = [
    "Wagyu beef, Shiraz", "Pasta carbonara, Barolo", "Omakase menu",
    "Degustation with wine pairing", "Seafood platter, Chardonnay",
    "Wood-fired sourdough, natural wines", "Ramen, sake", "Truffle pasta, Pinot Noir",
    "Steamed dumplings, jasmine tea", "Ribeye, Cabernet Sauvignon",
    "Burrata, heirloom tomatoes", "Tonkotsu ramen, gyoza",
    "Tasting menu, champagne", "Pappardelle, Sangiovese",
    "Sashimi, sake", "Grilled octopus, Vermentino",
    "Beef tartare, Malbec", "Cauliflower steak, orange wine",
]

OCCASIONS_WEIGHTED = (
    ["general"] * 50 +
    ["birthday"] * 15 +
    ["date_night"] * 15 +
    ["business_dinner"] * 10 +
    ["anniversary"] * 10
)

CHANNELS_WEIGHTED = (
    ["online"] * 50 +
    ["phone"] * 30 +
    ["app"] * 15 +
    ["walk_in"] * 5
)


def _random_date_between(start: date, end: date) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def _random_past_date(days_back_min: int, days_back_max: int) -> date:
    today = date.today()
    return today - timedelta(days=random.randint(days_back_min, days_back_max))


def _make_email(first: str, last: str) -> str:
    first_clean = first.lower().replace("'", "").replace("-", "").replace("é", "e").replace("á", "a")
    last_clean = last.lower().replace(" ", "").replace("'", "").replace("-", "")
    domain = random.choice(EMAIL_DOMAINS)
    sep = random.choice([".", "_", ""])
    num = str(random.randint(1, 99)) if random.random() < 0.4 else ""
    return f"{first_clean}{sep}{last_clean}{num}@{domain}"


def _make_phone() -> str:
    return f"04{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"


def _deposit_chance(tier: str) -> bool:
    if tier == "fine_dining":
        return random.random() < 0.70
    elif tier == "casual_fine":
        return random.random() < 0.40
    else:
        return random.random() < 0.15


def _deposit_amount(tier: str, party_size: int, avg_spend: int) -> float:
    if tier == "fine_dining":
        return round(party_size * avg_spend * random.uniform(0.20, 0.30), 2)
    elif tier == "casual_fine":
        return round(party_size * random.uniform(25, 50), 2)
    else:
        return 0.0


def _lead_time_hours() -> float:
    """Weighted toward 24-168 hours, but can be 2-720."""
    bucket = random.random()
    if bucket < 0.05:
        return round(random.uniform(2, 6), 1)     # same day
    elif bucket < 0.15:
        return round(random.uniform(6, 24), 1)    # same/next day
    elif bucket < 0.55:
        return round(random.uniform(24, 168), 1)  # 1-7 days (most common)
    elif bucket < 0.85:
        return round(random.uniform(168, 336), 1) # 1-2 weeks
    else:
        return round(random.uniform(336, 720), 1) # 2-4 weeks


def _booking_time() -> str:
    hour = random.choice([12, 12, 13, 18, 19, 19, 20, 20, 21])
    minute = random.choice([0, 0, 15, 30, 30, 45])
    return f"{hour:02d}:{minute:02d}"


def _make_booking_id() -> str:
    return "b" + uuid.uuid4().hex[:10]


# ---------------------------------------------------------------------------
# Guest definitions
# ---------------------------------------------------------------------------

def _build_guests(names_list) -> list:
    """Build 80 guest records across 7 archetypes."""
    guests = []
    today = date.today()
    name_iter = iter(names_list)

    def next_name():
        return next(name_iter)

    # ---- new_customer (15) ----
    for i in range(15):
        fn, ln = next_name()
        member_since = _random_date_between(today - timedelta(days=90), today - timedelta(days=7))
        guests.append({
            "id": f"g_new_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": random.randint(1, 2),
            "total_noshows": 0,
            "total_spend": round(random.uniform(40, 200), 2),
            "member_since": member_since.isoformat(),
            "vip": False,
            "preferred_time": random.choice(PREFERRED_TIMES),
            "favourite_items": random.choice(FAVOURITE_ITEMS_POOL),
            "notes": random.choice([
                "First visit", "Referred by a friend", "Found us on Instagram",
                "New to the area", "Trying us for the first time"
            ]),
            "tags": [],
            "archetype": "new_customer",
        })

    # ---- reliable_regular (18) ----
    for i in range(18):
        fn, ln = next_name()
        visits = random.randint(8, 25)
        noshows = random.randint(0, 1)
        spend = round(visits * random.uniform(60, 160), 2)
        member_since = _random_date_between(today - timedelta(days=1460), today - timedelta(days=180))
        extra_tags = random.sample(["wine_lover", "early_bird", "window_table", "regular"], k=random.randint(1, 3))
        if "regular" not in extra_tags:
            extra_tags.append("regular")
        guests.append({
            "id": f"g_reg_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": visits,
            "total_noshows": noshows,
            "total_spend": spend,
            "member_since": member_since.isoformat(),
            "vip": False,
            "preferred_time": random.choice(PREFERRED_TIMES),
            "favourite_items": random.choice(FAVOURITE_ITEMS_POOL),
            "notes": random.choice([
                "Loves the seasonal menu", "Always sits at the bar",
                "Requests specific waiter when available", "Loyal customer for years",
                "Celebrates most occasions here"
            ]),
            "tags": extra_tags,
            "archetype": "reliable_regular",
        })

    # ---- vip_loyal (8) ----
    for i in range(8):
        fn, ln = next_name()
        visits = random.randint(20, 40)
        spend = round(random.uniform(3000, 8000), 2)
        member_since = _random_date_between(today - timedelta(days=1460), today - timedelta(days=365))
        notes_options = [
            "Always orders degustation", "Prefers sommelier service",
            "Celebrates anniversary here every year", "Brings clients for business dinners regularly",
            "Has standing reservation on the first Friday of each month",
            "Knows the head chef personally"
        ]
        guests.append({
            "id": f"g_vip_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": visits,
            "total_noshows": 0,
            "total_spend": spend,
            "member_since": member_since.isoformat(),
            "vip": True,
            "preferred_time": random.choice(["19:00", "19:30", "20:00"]),
            "favourite_items": random.choice([
                "Degustation with wine pairing", "Wagyu beef, Penfolds Grange",
                "Omakase menu, sake", "Tasting menu, champagne",
                "Truffle pasta, aged Barolo"
            ]),
            "notes": random.choice(notes_options),
            "tags": ["vip", "regular"],
            "archetype": "vip_loyal",
        })

    # ---- occasional_visitor (15) ----
    for i in range(15):
        fn, ln = next_name()
        visits = random.randint(3, 7)
        noshows = random.randint(0, 1)
        spend = round(visits * random.uniform(50, 130), 2)
        member_since = _random_date_between(today - timedelta(days=1095), today - timedelta(days=180))
        guests.append({
            "id": f"g_occ_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": visits,
            "total_noshows": noshows,
            "total_spend": spend,
            "member_since": member_since.isoformat(),
            "vip": False,
            "preferred_time": random.choice(PREFERRED_TIMES),
            "favourite_items": random.choice(FAVOURITE_ITEMS_POOL),
            "notes": random.choice([
                "Comes in for special occasions", "Books months ahead for anniversaries",
                "Usually visits for birthdays", "Quarterly dining, always well-behaved",
                "Books far in advance and always shows"
            ]),
            "tags": ["occasional"],
            "archetype": "occasional_visitor",
        })

    # ---- unreliable (12) ----
    for i in range(12):
        fn, ln = next_name()
        visits = random.randint(5, 15)
        noshows = random.randint(2, 4)
        spend = round((visits - noshows) * random.uniform(40, 100), 2)
        member_since = _random_date_between(today - timedelta(days=730), today - timedelta(days=90))
        guests.append({
            "id": f"g_unr_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": visits,
            "total_noshows": noshows,
            "total_spend": spend,
            "member_since": member_since.isoformat(),
            "vip": False,
            "preferred_time": random.choice(PREFERRED_TIMES),
            "favourite_items": random.choice(FAVOURITE_ITEMS_POOL),
            "notes": random.choice([
                "Has cancelled last minute twice",
                "No-showed on a Friday in March",
                "Called to cancel same day on two occasions",
                "Inconsistent — sometimes shows, sometimes doesn't",
                "Tends to forget bookings on busy weekends",
            ]),
            "tags": ["unreliable"],
            "archetype": "unreliable",
        })

    # ---- chronic_noshows (7) ----
    for i in range(7):
        fn, ln = next_name()
        visits = random.randint(4, 10)
        noshows = random.randint(3, 6)
        noshows = min(noshows, visits)
        spend = round((visits - noshows) * random.uniform(30, 80), 2)
        member_since = _random_date_between(today - timedelta(days=730), today - timedelta(days=90))
        guests.append({
            "id": f"g_chr_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": visits,
            "total_noshows": noshows,
            "total_spend": spend,
            "member_since": member_since.isoformat(),
            "vip": False,
            "preferred_time": random.choice(PREFERRED_TIMES),
            "favourite_items": random.choice(FAVOURITE_ITEMS_POOL),
            "notes": random.choice([
                "Called day-of to cancel 3 times",
                "Booked 4 times, only arrived twice",
                "High-risk: no-showed 3 out of last 5 bookings",
                "Never responds to reminders, frequent no-show",
                "Pattern of Saturday no-shows — flag for deposit requirement",
            ]),
            "tags": ["high_risk", "unreliable"],
            "archetype": "chronic_noshows",
        })

    # ---- big_spender (5) ----
    for i in range(5):
        fn, ln = next_name()
        visits = random.randint(6, 12)
        spend = round(random.uniform(5000, 12000), 2)
        member_since = _random_date_between(today - timedelta(days=1460), today - timedelta(days=365))
        notes_options = [
            "Orders Penfolds by the bottle",
            "Always brings clients for business dinners",
            "Requests private dining room when available",
        ]
        guests.append({
            "id": f"g_big_{i+1:02d}",
            "name": f"{fn} {ln}",
            "email": _make_email(fn, ln),
            "phone": _make_phone(),
            "total_bookings": visits,
            "total_noshows": 0,
            "total_spend": spend,
            "member_since": member_since.isoformat(),
            "vip": True,
            "preferred_time": random.choice(["19:00", "19:30", "20:00"]),
            "favourite_items": random.choice([
                "Penfolds Grange, wagyu degustation",
                "Dom Perignon, tasting menu",
                "Aged Barolo, whole roasted lamb",
            ]),
            "notes": notes_options[i % len(notes_options)],
            "tags": ["vip", "wine_lover", "big_spender"],
            "archetype": "big_spender",
        })

    return guests


# ---------------------------------------------------------------------------
# Booking generation helpers
# ---------------------------------------------------------------------------

def _pick_restaurant() -> dict:
    return random.choice(RESTAURANTS)


def _confirmation_method(archetype: str, booking_channel: str, confirmed: bool) -> str | None:
    """If the guest confirmed, pick a realistic method based on archetype and channel."""
    if not confirmed:
        return None
    # Phone bookings prefer SMS/phone confirmation; online/app prefer email
    if booking_channel == "phone":
        weights = ["sms", "sms", "phone", "email"]
    elif booking_channel == "app":
        weights = ["sms", "sms", "email", "email"]
    else:  # online, walk_in
        weights = ["email", "email", "email", "sms"]
    # VIPs and big spenders more likely to call
    if archetype in ("vip_loyal", "big_spender"):
        weights = ["phone", "sms", "email"]
    return random.choice(weights)


def _confirmed_response_prob(archetype: str) -> bool:
    probs = {
        "reliable_regular": 0.85,
        "vip_loyal": 0.95,
        "big_spender": 0.95,
        "occasional_visitor": 0.75,
        "new_customer": 0.60,
        "unreliable": 0.40,
        "chronic_noshows": 0.25,
    }
    return random.random() < probs.get(archetype, 0.60)


def _noshow_prob(archetype: str) -> bool:
    probs = {
        "reliable_regular": 0.04,
        "vip_loyal": 0.01,
        "big_spender": 0.01,
        "occasional_visitor": 0.08,
        "new_customer": 0.10,
        "unreliable": 0.30,
        "chronic_noshows": 0.55,
    }
    return random.random() < probs.get(archetype, 0.10)


def _generate_historical_bookings(guests: list, all_restaurant_ids: list) -> list:
    """Generate 8-15 past bookings per guest across the last 12 months."""
    today = date.today()
    one_year_ago = today - timedelta(days=365)
    yesterday = today - timedelta(days=1)
    bookings = []

    for guest in guests:
        archetype = guest["archetype"]

        # New customers only get 1-2 recent historical bookings
        if archetype == "new_customer":
            count = random.randint(1, 2)
            start_range = today - timedelta(days=45)
        else:
            count = random.randint(8, 15)
            start_range = one_year_ago

        for _ in range(count):
            bdate = _random_date_between(start_range, yesterday)
            restaurant = random.choice(RESTAURANTS)
            party_size = random.randint(1, 8)
            channel = random.choice(CHANNELS_WEIGHTED)
            occasion = random.choice(OCCASIONS_WEIGHTED)
            dep_paid = _deposit_chance(restaurant["tier"])
            dep_amount = _deposit_amount(restaurant["tier"], party_size, restaurant["avg_spend"]) if dep_paid else 0.0
            lead = _lead_time_hours()
            confirmed = _confirmed_response_prob(archetype)
            conf_method = _confirmation_method(archetype, channel, confirmed)
            reminders_sent = random.randint(0, 3)
            reminders_ignored = random.randint(0, reminders_sent)

            # Determine outcome
            if _noshow_prob(archetype):
                status = "no_show"
            else:
                status = "completed"

            created_at = (bdate - timedelta(hours=lead)).isoformat()

            bookings.append({
                "id": _make_booking_id(),
                "restaurant_id": restaurant["id"],
                "guest_id": guest["id"],
                "booking_date": bdate.isoformat(),
                "booking_time": _booking_time(),
                "party_size": party_size,
                "occasion": occasion,
                "deposit_paid": 1 if dep_paid else 0,
                "deposit_amount": dep_amount,
                "booking_channel": channel,
                "confirmed_response": 1 if confirmed else 0,
                "confirmation_method": conf_method,
                "reminders_sent": reminders_sent,
                "reminders_ignored": reminders_ignored,
                "lead_time_hours": lead,
                "status": status,
                "created_at": created_at,
                "risk_score": None,
                "risk_level": None,
                "risk_reasons": None,
                "recommended_action": None,
            })

    return bookings


def _generate_upcoming_bookings(guests: list) -> list:
    """Generate 3-6 upcoming bookings per restaurant per day for the next 7 days."""
    today = date.today()
    bookings = []

    # Build a guest pool for quick random selection
    guest_pool = guests  # all guests can have upcoming bookings

    for day_offset in range(7):
        bdate = today + timedelta(days=day_offset)
        for restaurant in RESTAURANTS:
            num_bookings = random.randint(3, 6)
            for _ in range(num_bookings):
                guest = random.choice(guest_pool)
                archetype = guest["archetype"]
                party_size = random.randint(1, 8)
                channel = random.choice(CHANNELS_WEIGHTED)
                occasion = random.choice(OCCASIONS_WEIGHTED)
                dep_paid = _deposit_chance(restaurant["tier"])
                dep_amount = _deposit_amount(restaurant["tier"], party_size, restaurant["avg_spend"]) if dep_paid else 0.0
                lead = _lead_time_hours()
                confirmed = _confirmed_response_prob(archetype)
                conf_method = _confirmation_method(archetype, channel, confirmed)
                reminders_sent = random.randint(0, 2)
                reminders_ignored = random.randint(0, reminders_sent)
                btime = _booking_time()

                # created_at is in the past (lead_time_hours ago from booking date)
                booking_dt = datetime.combine(bdate, datetime.strptime(btime, "%H:%M").time())
                created_dt = booking_dt - timedelta(hours=lead)
                created_at = created_dt.isoformat()

                bookings.append({
                    "id": _make_booking_id(),
                    "restaurant_id": restaurant["id"],
                    "guest_id": guest["id"],
                    "booking_date": bdate.isoformat(),
                    "booking_time": btime,
                    "party_size": party_size,
                    "occasion": occasion,
                    "deposit_paid": 1 if dep_paid else 0,
                    "deposit_amount": dep_amount,
                    "booking_channel": channel,
                    "confirmed_response": 1 if confirmed else 0,
                    "confirmation_method": conf_method,
                    "reminders_sent": reminders_sent,
                    "reminders_ignored": reminders_ignored,
                    "lead_time_hours": lead,
                    "status": "upcoming",
                    "created_at": created_at,
                    "risk_score": None,
                    "risk_level": None,
                    "risk_reasons": None,
                    "recommended_action": None,
                })

    return bookings


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_sample_data():
    """Insert sample data only if tables are empty."""
    conn = database.get_connection()
    c = conn.cursor()

    # Check if already populated
    existing = c.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    # Shuffle names for variety
    names = list(SYDNEY_NAMES)
    random.seed(42)  # deterministic generation
    random.shuffle(names)

    # ---- Insert restaurants ----
    for r in RESTAURANTS:
        c.execute(
            "INSERT OR IGNORE INTO restaurants (id, name, suburb, cuisine, capacity, lat, lon, avg_spend, tier, state) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (r["id"], r["name"], r["suburb"], r["cuisine"], r["capacity"],
             r["lat"], r["lon"], r["avg_spend"], r["tier"], r.get("state"))
        )

    # ---- Build and insert guests ----
    guests = _build_guests(names)
    for g in guests:
        tags_json = json.dumps(g["tags"])
        c.execute(
            """INSERT OR IGNORE INTO guests
               (id, name, email, phone, total_bookings, total_noshows, total_spend,
                member_since, vip, preferred_time, favourite_items, notes, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (g["id"], g["name"], g["email"], g["phone"],
             g["total_bookings"], g["total_noshows"], g["total_spend"],
             g["member_since"], 1 if g["vip"] else 0,
             g["preferred_time"], g["favourite_items"], g["notes"], tags_json)
        )

    # ---- Generate and insert historical bookings ----
    restaurant_ids = [r["id"] for r in RESTAURANTS]
    historical = _generate_historical_bookings(guests, restaurant_ids)
    for b in historical:
        c.execute(
            """INSERT OR IGNORE INTO bookings
               (id, restaurant_id, guest_id, booking_date, booking_time, party_size,
                occasion, deposit_paid, deposit_amount, booking_channel,
                confirmed_response, confirmation_method, reminders_sent, reminders_ignored,
                lead_time_hours, status, created_at,
                risk_score, risk_level, risk_reasons, recommended_action)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (b["id"], b["restaurant_id"], b["guest_id"], b["booking_date"], b["booking_time"],
             b["party_size"], b["occasion"], b["deposit_paid"], b["deposit_amount"],
             b["booking_channel"], b["confirmed_response"], b.get("confirmation_method"),
             b["reminders_sent"], b["reminders_ignored"], b["lead_time_hours"],
             b["status"], b["created_at"],
             b["risk_score"], b["risk_level"], b["risk_reasons"], b["recommended_action"])
        )

    # ---- Generate and insert upcoming bookings ----
    upcoming = _generate_upcoming_bookings(guests)
    for b in upcoming:
        c.execute(
            """INSERT OR IGNORE INTO bookings
               (id, restaurant_id, guest_id, booking_date, booking_time, party_size,
                occasion, deposit_paid, deposit_amount, booking_channel,
                confirmed_response, confirmation_method, reminders_sent, reminders_ignored,
                lead_time_hours, status, created_at,
                risk_score, risk_level, risk_reasons, recommended_action)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (b["id"], b["restaurant_id"], b["guest_id"], b["booking_date"], b["booking_time"],
             b["party_size"], b["occasion"], b["deposit_paid"], b["deposit_amount"],
             b["booking_channel"], b["confirmed_response"], b.get("confirmation_method"),
             b["reminders_sent"], b["reminders_ignored"], b["lead_time_hours"],
             b["status"], b["created_at"],
             b["risk_score"], b["risk_level"], b["risk_reasons"], b["recommended_action"])
        )

    conn.commit()
    conn.close()

    print(f"  Generated {len(guests)} guests, {len(historical)} historical bookings, {len(upcoming)} upcoming bookings")


# ---------------------------------------------------------------------------
# Rule-based pre-scoring (no Claude needed — fast, weather-aware, demo-ready)
# ---------------------------------------------------------------------------

# Base risk score ranges per archetype tag
_ARCHETYPE_BASE = {
    "high_risk":  (75, 95),
    "unreliable": (52, 74),
    "new":        (35, 60),   # new_customer has no tags, detected by total_bookings
    "occasional": (25, 45),
    "regular":    (10, 30),
    "vip":        (5,  18),
    "big_spender":(5,  15),
}

_RISK_REASONS = {
    "high_risk":   ["Chronic no-show history (>40% rate)", "Previously cancelled day-of", "Booked 4 times, only arrived twice"],
    "unreliable":  ["Prior no-shows on record", "Last-minute cancellation history", "Low confirmation response rate"],
    "new":         ["First-time guest, no history", "Unknown reliability", "Booked online with no deposit"],
    "occasional":  ["Infrequent visitor", "Long gap since last visit", "No deposit paid"],
    "regular":     ["Returning guest with good record", "Confirmed via reminder"],
    "vip":         ["VIP — 20+ visits, zero no-shows", "High-value loyal guest"],
    "big_spender": ["Premium loyal guest", "Zero no-show history"],
    "no_deposit":  ["No deposit collected — low commitment signal"],
    "unconfirmed": ["Reminder sent, no response yet"],
    "large_party": ["Large party — higher cancellation risk"],
    "same_day":    ["Same-day booking — elevated volatility"],
    "weather_high":["Heavy rain forecast — weather-driven no-show risk elevated"],
    "weather_med": ["Adverse weather forecast for this date"],
}

_POSITIVE_FACTORS = {
    "deposit":           "Deposit paid — financial commitment reduces no-show probability",
    "confirmed_phone":   "Confirmed via phone call — strongest commitment signal",
    "confirmed_sms":     "Confirmed via SMS — guest actively responded",
    "confirmed_email":   "Confirmed via email — booking acknowledged",
    "confirmed_generic": "Guest confirmed via reminder",
    "vip":               "VIP guest with strong loyalty record",
    "regular":           "Returning guest with consistent attendance",
    "low_weather":       "Clear weather forecast — no weather risk",
}

def _archetype_from_tags(tags: list, total_bookings: int) -> str:
    if "high_risk" in tags:   return "high_risk"
    if "unreliable" in tags:  return "unreliable"
    if "big_spender" in tags: return "big_spender"
    if "vip" in tags:         return "vip"
    if "regular" in tags:     return "regular"
    if "occasional" in tags:  return "occasional"
    if total_bookings <= 2:   return "new"
    return "occasional"


def pre_score_upcoming_bookings(weather_map: dict) -> None:
    """
    Rule-based pre-scoring for all unscored upcoming bookings.
    Creates a realistic blend across the 7-day window:
    ~20% low, ~30% medium, ~30% high, ~20% critical
    Weather modifiers shift scores on rainy/extreme days.
    """
    conn = database.get_connection()
    today = datetime.now().date().isoformat()
    end = (datetime.now().date() + timedelta(days=7)).isoformat()

    rows = conn.execute("""
        SELECT b.id, b.booking_date, b.booking_time, b.party_size, b.deposit_paid,
               b.booking_channel, b.lead_time_hours, b.confirmed_response,
               b.confirmation_method, b.restaurant_id, g.tags, g.total_bookings,
               g.total_noshows, g.vip, r.avg_spend
        FROM bookings b
        JOIN guests g ON b.guest_id = g.id
        JOIN restaurants r ON b.restaurant_id = r.id
        WHERE b.booking_date >= ? AND b.booking_date <= ?
        AND b.status IN ('upcoming', 'confirmed')
    """, (today, end)).fetchall()

    rng = random.Random(99)  # deterministic for demo consistency

    scored = 0
    for row in rows:
        (bid, bdate, btime, party_size, deposit_paid, channel,
         lead_time, confirmed, conf_method, restaurant_id, tags_json,
         total_bookings, total_noshows, vip, avg_spend) = row

        tags = json.loads(tags_json) if tags_json else []
        archetype = _archetype_from_tags(tags, total_bookings)
        lo, hi = _ARCHETYPE_BASE[archetype]
        base = rng.randint(lo, hi)

        # Weather modifier
        weather = weather_map.get(bdate, {})
        w_risk = weather.get("weather_risk", "low")
        rain = weather.get("rain_mm", 0)
        if w_risk == "high":
            base += rng.randint(12, 20)
        elif w_risk == "medium":
            base += rng.randint(5, 10)

        # Booking signal modifiers
        if not deposit_paid:
            base += 8
        if not confirmed:
            base += 10
        if (party_size or 2) > 5:
            base += 5
        if (lead_time or 24) < 6:
            base += 12
        if channel == "online" and archetype in ("new", "occasional"):
            base += 3

        # Positive modifiers
        if deposit_paid:
            base -= 8
        if confirmed:
            # Confirmation method carries different signal strength:
            # phone = strongest (deliberate human interaction)
            # sms = strong (active response required)
            # email = good (acknowledged commitment)
            if conf_method == "phone":
                base -= 30
            elif conf_method == "sms":
                base -= 22
            elif conf_method == "email":
                base -= 18
            else:
                base -= 12
        if vip:
            base -= 15

        score = max(1, min(99, base))

        # Risk level
        if score >= 76:
            level = "critical"
        elif score >= 51:
            level = "high"
        elif score >= 26:
            level = "medium"
        else:
            level = "low"

        # Build reasons
        reasons = list(_RISK_REASONS.get(archetype, []))[:2]
        if w_risk == "high":
            reasons.append(_RISK_REASONS["weather_high"][0])
        elif w_risk == "medium":
            reasons.append(_RISK_REASONS["weather_med"][0])
        if not deposit_paid:
            reasons.append(_RISK_REASONS["no_deposit"][0])
        if not confirmed:
            reasons.append(_RISK_REASONS["unconfirmed"][0])
        if (party_size or 2) > 5:
            reasons.append(_RISK_REASONS["large_party"][0])
        reasons = reasons[:3]

        # Prepend confirmation signal — makes it visible in the UI risk factors
        if confirmed and conf_method:
            label = {
                "phone": "Confirmed via phone call",
                "sms":   "Confirmed via SMS",
                "email": "Confirmed via email",
            }.get(conf_method)
            if label:
                reasons = [label] + reasons[:2]

        # Positive factors
        positives = []
        if deposit_paid:
            positives.append(_POSITIVE_FACTORS["deposit"])
        if confirmed:
            conf_key = f"confirmed_{conf_method}" if conf_method in ("phone", "sms", "email") else "confirmed_generic"
            positives.append(_POSITIVE_FACTORS[conf_key])
        if vip:
            positives.append(_POSITIVE_FACTORS["vip"])
        if w_risk == "low":
            positives.append(_POSITIVE_FACTORS["low_weather"])

        revenue = (party_size or 2) * (avg_spend or 80)
        action = _recommended_action(level, rain, confirmed, deposit_paid)

        conn.execute(
            "UPDATE bookings SET risk_score=?, risk_level=?, risk_reasons=?, recommended_action=? WHERE id=?",
            (score, level, json.dumps(reasons), action, bid)
        )
        scored += 1

    conn.commit()
    conn.close()
    print(f"  Pre-scored {scored} upcoming bookings (rule-based, weather-aware)")


def _recommended_action(level: str, rain_mm: float, confirmed: bool, deposit_paid: bool) -> str:
    if level == "critical":
        return "Call guest directly within the hour — table release risk is high"
    if level == "high":
        if rain_mm > 10:
            return "Send personalised SMS with weather acknowledgement and confirmation link"
        if not confirmed:
            return "Send confirmation request now — guest has not responded to reminders"
        return "Personal phone call recommended — activate waitlist as backup"
    if level == "medium":
        if not deposit_paid:
            return "Send deposit request or offer pre-order to increase commitment"
        return "Send 48-hour confirmation SMS with easy one-click confirm"
    return "Standard 24-hour automated reminder is sufficient"
