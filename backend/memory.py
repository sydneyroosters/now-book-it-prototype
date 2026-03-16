"""
Stub memory module — ChromaDB removed for Railway deployment.
Similar-cases lookup returns empty; all other scoring signals remain active.
"""


class BookingMemory:
    def get_similar_cases(self, booking_summary: str, n: int = 5) -> list:
        return []

    def seed_from_historical_bookings(self, db_conn):
        pass

    def update_outcome_in_memory(self, booking_id: str, outcome: str):
        pass

    def store_outcome(self, booking_id: str, booking_summary: str, outcome: str, risk_score: int):
        pass
