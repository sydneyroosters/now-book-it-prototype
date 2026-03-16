import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { mockBookings, type Booking, type RiskLevel } from "@/data/bookings";

export interface Restaurant {
  id: string;
  name: string;
  suburb: string;
  cuisine: string;
  avg_spend: number;
  tier: string;
  lat: number;
  lon: number;
  state?: string;
}

export function useRestaurants() {
  return useQuery<Restaurant[]>({
    queryKey: ["restaurants"],
    queryFn: async () => {
      if (!API_BASE_URL) return [];
      const res = await fetch(`${API_BASE_URL}/restaurants`);
      if (!res.ok) throw new Error("Failed to fetch restaurants");
      return res.json();
    },
    staleTime: Infinity,
  });
}

const API_BASE_URL = import.meta.env.VITE_BOOKINGS_API_URL;

// Shape returned by the backend
interface BackendBooking {
  id: string;
  booking_date: string;
  booking_time: string;
  guest_name: string;
  guest_phone: string;
  party_size: number;
  booking_channel: string;
  status: string;
  risk_level: string | null;
  risk_score: number | null;
  risk_reasons: string | null;
  recommended_action: string | null;
  guest_tags: string | null;
  deposit_paid: number;
  deposit_amount: number;
  confirmed_response: number;
  confirmation_method: string | null;
  reminders_sent: number;
  reminders_ignored: number;
  occasion: string;
  restaurant_id: string;
  restaurant_name: string;
  avg_spend: number;
  tier: string;
  total_bookings: number;
  total_noshows: number;
  vip: number;
  guest_notes: string | null;
}

function mapStatus(backendStatus: string, confirmedResponse: number): Booking["status"] {
  if (backendStatus === "cancelled") return "cancelled";
  if (backendStatus === "completed") return "confirmed";
  // "upcoming" bookings are confirmed if the guest responded
  if (confirmedResponse) return "confirmed";
  return "unconfirmed";
}

function mapRiskLevel(level: string | null): RiskLevel {
  if (level === "critical") return "high";
  if (level === "low" || level === "medium" || level === "high") return level;
  return "low";
}

function parseTags(tags: string | null): string[] {
  if (!tags) return [];
  try {
    return JSON.parse(tags);
  } catch {
    return [];
  }
}

function parseReasons(reasons: string | null): string[] {
  if (!reasons) return [];
  try {
    return JSON.parse(reasons);
  } catch {
    return [];
  }
}

// Extend Booking with extra fields from the backend
declare module "@/data/bookings" {
  interface Booking {
    booking_date?: string;
    restaurant_id?: string;
    confirmation_method?: "email" | "sms" | "phone" | null;
    reminders_sent?: number;
    reminders_ignored?: number;
    deposit_amount?: number;
    occasion?: string;
    avg_spend?: number;
    tier?: string;
    guest_notes?: string | null;
    recommended_action?: string | null;
  }
}

function toFrontendBooking(b: BackendBooking): Booking {
  const noShowRate = b.total_bookings > 0
    ? Math.round((b.total_noshows / b.total_bookings) * 100)
    : 0;

  const riskFactors = parseReasons(b.risk_reasons).length > 0
    ? parseReasons(b.risk_reasons)
    : buildDefaultFactors(b, noShowRate);

  return {
    id: b.id,
    time: b.booking_time,
    guestName: b.guest_name,
    covers: b.party_size,
    table: "-",
    phone: b.guest_phone ?? "",
    riskLevel: mapRiskLevel(b.risk_level),
    riskScore: b.risk_score ?? 0,
    riskFactors,
    status: mapStatus(b.status, b.confirmed_response),
    notes: b.recommended_action ?? undefined,
    preferences: parseTags(b.guest_tags),
    booking_date: b.booking_date,
    restaurant_id: b.restaurant_id,
    confirmation_method: b.confirmation_method as any,
    reminders_sent: b.reminders_sent,
    reminders_ignored: b.reminders_ignored,
    deposit_amount: b.deposit_amount,
    occasion: b.occasion,
    avg_spend: b.avg_spend,
    tier: b.tier,
    guest_notes: b.guest_notes,
    recommended_action: b.recommended_action,
  } as Booking;
}

function buildDefaultFactors(b: BackendBooking, noShowRate: number): string[] {
  const factors: string[] = [];
  if (b.total_bookings <= 2) factors.push("New guest");
  else if (noShowRate >= 30) factors.push(`${noShowRate}% no-show history`);
  else factors.push(`${b.total_bookings} prior visits`);
  if (!b.deposit_paid) factors.push("No deposit");
  if (!b.confirmed_response) factors.push("Unconfirmed");
  if (b.vip) factors.push("VIP");
  if (b.occasion !== "general") factors.push(b.occasion.replace("_", " "));
  return factors;
}

async function fetchBookings(): Promise<Booking[]> {
  if (!API_BASE_URL) return mockBookings;

  const response = await fetch(`${API_BASE_URL}/bookings`);
  if (!response.ok) throw new Error(`Failed to fetch bookings: ${response.statusText}`);

  const data: BackendBooking[] = await response.json();
  return data.map(toFrontendBooking);
}

export function useBookings() {
  return useQuery({
    queryKey: ["bookings"],
    queryFn: fetchBookings,
    staleTime: 60_000,
  });
}

export interface ReasoningStep {
  tool: string;
  input: Record<string, unknown>;
  output_summary: string;
}

export interface ScoringResult {
  booking_id: string;
  risk_result: {
    risk_score: number;
    risk_level: string;
    top_reasons: string[];
    positive_factors: string[];
    recommended_action: string;
    follow_up_action?: string;
    best_contact_time?: string;
    confidence: number;
    revenue_at_risk: number;
  };
  reasoning_steps: ReasoningStep[];
}

export function useScoreBooking() {
  const queryClient = useQueryClient();

  return useMutation<ScoringResult, Error, string>({
    mutationFn: async (bookingId: string) => {
      const response = await fetch(`${API_BASE_URL}/bookings/${bookingId}/score`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Scoring failed");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
}

export function useRecordOutcome() {
  return useMutation({
    mutationFn: async ({ bookingId, outcome, notes = "" }: { bookingId: string; outcome: string; notes?: string }) => {
      const response = await fetch(`${API_BASE_URL}/bookings/${bookingId}/outcome`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ outcome, notes }),
      });
      if (!response.ok) throw new Error("Failed to record outcome");
      return response.json();
    },
    // No auto-refetch: the booking disappears from get_upcoming_bookings after status changes.
    // The caller updates local state directly instead.
  });
}
