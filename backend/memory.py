import chromadb
from chromadb.utils import embedding_functions
import json
from datetime import datetime


class BookingMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="booking_outcomes",
            embedding_function=self.ef
        )

    def store_outcome(self, booking_id: str, booking_summary: str, outcome: str, risk_score: int):
        self.collection.upsert(
            ids=[booking_id],
            documents=[booking_summary],
            metadatas=[{"outcome": outcome, "risk_score": risk_score}]
        )

    def update_outcome_in_memory(self, booking_id: str, outcome: str):
        """Update the outcome label in ChromaDB when the real outcome is recorded."""
        try:
            existing = self.collection.get(ids=[booking_id])
            if not existing["ids"]:
                return
            doc = existing["documents"][0]
            meta = existing["metadatas"][0]
            # Rewrite document with updated outcome prefix
            doc_without_prefix = doc
            if doc.startswith("[OUTCOME:"):
                doc_without_prefix = doc[doc.index("]") + 2:]
            updated_doc = f"[OUTCOME: {outcome}] {doc_without_prefix}"
            meta["outcome"] = outcome
            self.collection.upsert(ids=[booking_id], documents=[updated_doc], metadatas=[meta])
        except Exception:
            pass

    def get_similar_cases(self, booking_summary: str, n: int = 5) -> list:
        count = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_texts=[booking_summary],
            n_results=min(n, count)
        )
        if not results["ids"][0]:
            return []
        cases = []
        for i, doc in enumerate(results["documents"][0]):
            cases.append({
                "summary": doc,
                "outcome": results["metadatas"][0][i]["outcome"],
                "risk_score": results["metadatas"][0][i]["risk_score"],
                "similarity_score": round(1 - results["distances"][0][i], 3)
            })
        return cases

    def seed_from_historical_bookings(self, db_conn):
        if self.collection.count() > 0:
            return
        # Pull historical completed/no_show bookings from SQLite and seed ChromaDB
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT b.id, b.booking_date, b.booking_time, b.party_size, b.deposit_paid,
                   b.booking_channel, b.lead_time_hours, b.occasion, b.status,
                   g.total_bookings, g.total_noshows, g.tags, g.notes,
                   r.suburb, r.tier, r.avg_spend
            FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            JOIN restaurants r ON b.restaurant_id = r.id
            WHERE b.status IN ('completed', 'no_show')
            LIMIT 500
        """)
        rows = cursor.fetchall()

        for row in rows:
            (bid, bdate, btime, party_size, deposit_paid, channel, lead_time,
             occasion, status, total_bookings, total_noshows, tags_json, notes,
             suburb, tier, avg_spend) = row

            tags = json.loads(tags_json) if tags_json else []
            noshow_rate = (total_noshows / total_bookings * 100) if total_bookings > 0 else 0

            try:
                dt = datetime.strptime(bdate, "%Y-%m-%d")
                day_name = dt.strftime("%A")
            except Exception:
                day_name = "Unknown"

            outcome = "no_show" if status == "no_show" else "showed_up"
            risk_score = 80 if status == "no_show" else 20

            summary = (
                f"[OUTCOME: {outcome}] "
                f"{'New guest' if total_bookings <= 2 else f'Returning guest with {total_bookings} visits'}, "
                f"{noshow_rate:.0f}% no-show rate, "
                f"{day_name} {btime}, party of {party_size}, "
                f"{'deposit paid' if deposit_paid else 'no deposit'}, "
                f"booked via {channel}, {lead_time or 0:.0f}hrs lead time, "
                f"{occasion} occasion, {suburb} venue ({tier}), "
                f"tags: {', '.join(tags) if tags else 'none'}"
            )

            self.store_outcome(bid, summary, outcome, risk_score)
