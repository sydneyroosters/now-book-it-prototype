from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Restaurant(BaseModel):
    id: str
    name: str
    suburb: str
    cuisine: str
    capacity: int
    lat: float
    lon: float
    avg_spend: int
    tier: str  # fine_dining | casual_fine | casual


class Guest(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    total_bookings: int = 0
    total_noshows: int = 0
    total_spend: float = 0.0
    member_since: str
    vip: bool = False
    preferred_time: str
    favourite_items: str
    notes: str
    tags: List[str] = Field(default_factory=list)


class Booking(BaseModel):
    id: str
    restaurant_id: str
    guest_id: str
    booking_date: str
    booking_time: str
    party_size: int
    occasion: str = "general"
    deposit_paid: bool = False
    deposit_amount: float = 0.0
    booking_channel: str = "online"
    confirmed_response: bool = False
    reminders_sent: int = 0
    reminders_ignored: int = 0
    lead_time_hours: float = 24.0
    status: str = "upcoming"
    created_at: str
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_reasons: Optional[List[str]] = None
    recommended_action: Optional[str] = None


class PredictionLog(BaseModel):
    id: Optional[int] = None
    booking_id: str
    predicted_risk_score: int
    predicted_risk_level: str
    actual_outcome: Optional[str] = None
    was_correct: Optional[bool] = None
    confidence: int
    signals_used: List[str] = Field(default_factory=list)
    created_at: str


class RiskResult(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: str  # low | medium | high | critical
    top_reasons: List[str]
    positive_factors: List[str] = Field(default_factory=list)
    recommended_action: str
    follow_up_action: str = ""
    best_contact_time: str = ""
    confidence: int = Field(ge=0, le=100)
    revenue_at_risk: int
