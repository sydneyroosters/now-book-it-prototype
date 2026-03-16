"""
NBI No-Show Prediction Engine — Claude Agent
Scores individual bookings by running a tool-call loop with Claude claude-opus-4-6.
"""

import os
import json
import asyncio
from anthropic import Anthropic
from models import RiskResult
import database
import weather
import memory as mem

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "get_guest_profile",
        "description": "Retrieve complete guest profile including visit history, no-show rate, spend, tags, and notes. Always call this first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guest_id": {"type": "string", "description": "The guest ID"}
            },
            "required": ["guest_id"]
        }
    },
    {
        "name": "get_weather_forecast",
        "description": "Get Sydney weather forecast for a specific date. Returns condition, rain, temperature, wind, and risk level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
            },
            "required": ["date"]
        }
    },
    {
        "name": "get_slot_history",
        "description": "Get historical no-show rates for a specific time slot and day of week at this restaurant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hour": {"type": "integer", "description": "Hour of booking (0-23)"},
                "day_of_week": {"type": "integer", "description": "Day of week (0=Monday, 6=Sunday)"},
                "restaurant_id": {"type": "string"}
            },
            "required": ["hour", "day_of_week", "restaurant_id"]
        }
    },
    {
        "name": "get_similar_past_cases",
        "description": "Retrieve the most similar past bookings and their outcomes from memory. Use this to find patterns that match the current booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_description": {
                    "type": "string",
                    "description": "Plain English description of the current booking for similarity search"
                }
            },
            "required": ["booking_description"]
        }
    },
    {
        "name": "get_restaurant_profile",
        "description": "Get this restaurant's historical no-show rates by occasion type. Use this when the occasion is specific (birthday, anniversary, business_dinner) or when you want to know if this venue has a structurally high no-show rate for this type of booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string", "description": "The restaurant ID"},
                "occasion": {"type": "string", "description": "The booking occasion for context"}
            },
            "required": ["restaurant_id"]
        }
    },
    {
        "name": "get_guest_cancellation_patterns",
        "description": "Retrieve timing and frequency patterns of past cancellations and no-shows for this guest. Use this for any guest with prior history to detect chronic no-show or last-minute cancellation patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "guest_name": {"type": "string", "description": "Full name of the guest"},
                "phone": {"type": "string", "description": "Guest phone number"}
            },
            "required": ["guest_name", "phone"]
        }
    },
    {
        "name": "submit_risk_assessment",
        "description": "Submit the final risk assessment. Call this when you have enough information to make a confident prediction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_score": {"type": "integer", "description": "0-100 risk score"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "top_reasons": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3 specific reasons for this risk level"
                },
                "positive_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Factors that reduce risk"
                },
                "recommended_action": {
                    "type": "string",
                    "description": "Specific immediate action for staff"
                },
                "follow_up_action": {
                    "type": "string",
                    "description": "Secondary action if first fails"
                },
                "best_contact_time": {
                    "type": "string",
                    "description": "When to reach the guest"
                },
                "confidence": {"type": "integer", "description": "0-100 confidence in this prediction"},
                "revenue_at_risk": {"type": "integer", "description": "Estimated AUD at risk"}
            },
            "required": ["risk_score", "risk_level", "top_reasons", "recommended_action", "confidence", "revenue_at_risk"]
        }
    }
]

SYSTEM_PROMPT = """You are an expert hospitality operations AI for NBI, a leading Australian restaurant booking platform.

Your job is to predict no-show risk for restaurant bookings with high accuracy.

You reason like an experienced reservations manager who has seen thousands of bookings.
You know that no-shows cost restaurants real money and that false alarms annoy good guests.

Your reasoning process:
1. Always start by getting the guest profile — this is your strongest signal
2. Get the weather for the booking date — rain and extreme heat spike no-shows
3. Check the slot history — some time slots are structurally riskier
4. Look for similar past cases — pattern matching improves accuracy
5. For non-trivial bookings, check restaurant profile and guest cancellation patterns for extra precision
6. Weigh all signals together — no single signal is definitive
7. Submit your assessment with specific, actionable recommendations

Risk score guide:
- 0-25: Low — standard reminder only
- 26-50: Medium — send confirmation request 48hrs out
- 51-75: High — personal outreach required, consider waitlist
- 76-100: Critical — call directly, consider releasing table, activate waitlist now

Confirmation method rules — ALWAYS apply these adjustments:
- Phone confirmation: reduce score by 25-30 points. A guest who spoke with staff or actively called is highly committed.
- SMS confirmation: reduce score by 18-22 points. An active reply takes effort; it signals intent.
- Email confirmation: reduce score by 14-18 points. Acknowledged the booking — meaningfully reduces risk.
- No confirmation: add 8-12 points. Unresponsive guests are significantly more likely to no-show.
These reductions apply on top of all other factors. A high-risk archetype who confirmed via phone should rarely exceed medium risk.

Reminder response rules:
- Each reminder ignored adds +8 to risk score. A guest who ignores 2+ reminders is showing disengagement.

Occasion adjustments:
- birthday / anniversary: -5 (personal milestone — high commitment to attend)
- work_function / business_dinner: +5 (plans change, corporate bookings cancel more)

Deposit adequacy (per head = deposit_amount / party_size):
- >$50/head: -10 (strong financial commitment)
- $20-50/head: -5 (moderate commitment)
- <$20/head or no deposit: no reduction

Restaurant tier adjustments:
- fine_dining: -5 (guests self-select; investment in the occasion is high)
- fast_casual / casual: +5 (lower barrier to booking, lower commitment signal)

Venue history (from get_restaurant_profile):
- If the occasion no-show rate at this restaurant exceeds 20%: +10

Guest cancellation patterns (from get_guest_cancellation_patterns):
- Pattern = "chronic" (3+ no-shows): +20
- Pattern = "unreliable" (1-2 no-shows or 2+ last-minute cancels): +15
- last_minute_count >= 2: add an additional +8

Be specific. "Send a confirmation SMS by 3pm today" is useful. "Follow up with guest" is not.
Always quantify revenue at risk (party_size × avg_spend)."""


async def score_booking(booking_id: str, memory_instance=None) -> dict:
    """
    Run the Claude agent to score a single booking.
    Returns a dict with 'risk_result' and 'reasoning_steps'.
    Max iterations: 8
    """
    booking = database.get_booking(booking_id)
    if not booking:
        raise ValueError(f"Booking {booking_id} not found")

    deposit_per_head = (
        round(booking.get('deposit_amount', 0) / booking['party_size'], 2)
        if booking.get('deposit_paid') and booking['party_size'] > 0 else 0
    )
    booking_context = f"""
Booking to assess:
- Booking ID: {booking['id']}
- Restaurant: {booking.get('restaurant_name', 'Unknown')} ({booking.get('restaurant_suburb', '')})
- Restaurant tier: {booking.get('tier', 'casual')}
- Restaurant ID: {booking['restaurant_id']}
- Date: {booking['booking_date']} at {booking['booking_time']}
- Party size: {booking['party_size']}
- Guest ID: {booking['guest_id']}
- Guest name: {booking.get('guest_name', 'Unknown')}
- Guest phone: {booking.get('guest_phone', '')}
- Guest notes: {booking.get('guest_notes') or 'none'}
- Guest historical avg spend: ${booking.get('total_spend', 0):.0f} total
- Occasion: {booking.get('occasion', 'general')}
- Deposit paid: {bool(booking.get('deposit_paid', False))} (${booking.get('deposit_amount', 0):.2f} total, ${deposit_per_head:.2f}/head)
- Booking channel: {booking.get('booking_channel', 'online')}
- Lead time: {booking.get('lead_time_hours', 0)} hours
- Confirmed response: {bool(booking.get('confirmed_response', False))}
- Confirmation method: {booking.get('confirmation_method') or 'none'}
- Reminders sent: {booking.get('reminders_sent', 0)}, ignored: {booking.get('reminders_ignored', 0)}
- Restaurant avg spend: ${booking.get('avg_spend', 80)} per person

Please assess the no-show risk for this booking.
"""

    messages = [{"role": "user", "content": booking_context}]
    reasoning_steps = []
    result = None
    weather_cache = None

    for iteration in range(8):
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Add assistant response to conversation
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_result = None

            print(f"  [Tool] {tool_name}: {json.dumps(tool_input)[:100]}")

            try:
                if tool_name == "get_guest_profile":
                    guest = database.get_guest(tool_input["guest_id"])
                    past = database.get_guest_bookings(tool_input["guest_id"], limit=10)
                    noshow_rate = (
                        guest["total_noshows"] / guest["total_bookings"] * 100
                        if guest and guest["total_bookings"] > 0 else 0
                    )
                    tool_result = {
                        "guest": guest,
                        "noshow_rate_pct": round(noshow_rate, 1),
                        "recent_bookings_count": len(past),
                        "recent_bookings": past[:5]
                    }
                    step_summary = (
                        f"Guest: {guest.get('name', 'Unknown')}, "
                        f"{guest.get('total_bookings', 0)} visits, "
                        f"{noshow_rate:.0f}% no-show rate"
                    )

                elif tool_name == "get_weather_forecast":
                    if weather_cache is None:
                        weather_cache = await weather.get_sydney_weather()
                    tool_result = weather.get_weather_for_date(weather_cache, tool_input["date"])
                    step_summary = (
                        f"Weather: {tool_result.get('condition')}, "
                        f"rain={tool_result.get('rain_mm')}mm, "
                        f"risk={tool_result.get('weather_risk')}"
                    )

                elif tool_name == "get_slot_history":
                    tool_result = database.get_historical_slot_stats(
                        tool_input["hour"],
                        tool_input["day_of_week"],
                        tool_input["restaurant_id"]
                    )
                    step_summary = (
                        f"Slot history: {tool_result.get('noshow_rate_pct', 0):.1f}% "
                        f"no-show rate for this slot"
                    )

                elif tool_name == "get_restaurant_profile":
                    conn = database.get_connection()
                    tool_result = database.get_restaurant_noshow_rate(conn, tool_input["restaurant_id"])
                    conn.close()
                    occasion = tool_input.get("occasion", "")
                    occasion_rate = tool_result.get(occasion, {}).get("noshow_rate", 0) if occasion else 0
                    step_summary = (
                        f"Restaurant no-show profile: {len(tool_result)} occasions tracked"
                        + (f", {occasion} rate={occasion_rate}%" if occasion else "")
                    )

                elif tool_name == "get_guest_cancellation_patterns":
                    conn = database.get_connection()
                    tool_result = database.get_guest_cancellation_patterns(
                        conn, tool_input["guest_name"], tool_input.get("phone", "")
                    )
                    conn.close()
                    step_summary = (
                        f"Guest pattern: {tool_result.get('pattern', 'unknown')}, "
                        f"{tool_result.get('noshow_count', 0)} no-shows, "
                        f"{tool_result.get('last_minute_count', 0)} last-minute"
                    )

                elif tool_name == "get_similar_past_cases":
                    if memory_instance:
                        tool_result = memory_instance.get_similar_cases(tool_input["booking_description"])
                    else:
                        tool_result = []
                    step_summary = f"Found {len(tool_result)} similar past cases"

                elif tool_name == "submit_risk_assessment":
                    result = tool_input
                    step_summary = (
                        f"Assessment: {tool_input['risk_level']} risk "
                        f"({tool_input['risk_score']}/100)"
                    )
                    reasoning_steps.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "output_summary": step_summary
                    })
                    tool_result = {"status": "accepted"}

            except Exception as e:
                tool_result = {"error": str(e)}
                step_summary = f"Error: {str(e)}"

            if tool_name != "submit_risk_assessment":
                reasoning_steps.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "output_summary": step_summary
                })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(tool_result)
            })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if result is not None:
            break

        if response.stop_reason == "end_turn":
            break

    # Fallback if Claude didn't submit an assessment
    if result is None:
        result = {
            "risk_score": 50,
            "risk_level": "medium",
            "top_reasons": ["Unable to complete full assessment"],
            "positive_factors": [],
            "recommended_action": "Manual review required",
            "follow_up_action": "Contact guest directly",
            "best_contact_time": "As soon as possible",
            "confidence": 20,
            "revenue_at_risk": booking.get("party_size", 2) * booking.get("avg_spend", 80)
        }

    return {
        "risk_result": result,
        "reasoning_steps": reasoning_steps
    }
