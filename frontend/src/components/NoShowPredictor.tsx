import { useState, useEffect, useRef } from "react";
import { AlertTriangle, Calendar, ChevronDown, Filter, Clock, Check } from "lucide-react";
import { type Booking, type RiskLevel } from "@/data/bookings";
import { useBookings, useRestaurants, type Restaurant } from "@/hooks/useBookings";
import BookingRow from "./BookingRow";
import OfferDialog from "./OfferDialog";
import WeatherRiskBar from "./WeatherRiskBar";

function useNow() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(id);
  }, []);
  return now;
}

const NoShowPredictor = () => {
  const { data, isLoading, isError } = useBookings();
  const { data: restaurants } = useRestaurants();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [filterRisk, setFilterRisk] = useState<RiskLevel | "all">("all");
  const [filterDate, setFilterDate] = useState<string>("all");
  const [offerBooking, setOfferBooking] = useState<Booking | null>(null);
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);
  const [venueOpen, setVenueOpen] = useState(false);
  const [isChangingVenue, setIsChangingVenue] = useState(false);
  const hasLoadedOnce = useRef(false);
  const venueRef = useRef<HTMLDivElement>(null);
  const now = useNow();

  // Default to first restaurant once loaded
  useEffect(() => {
    if (restaurants && restaurants.length > 0 && !selectedRestaurant) {
      setSelectedRestaurant(restaurants[0]);
    }
  }, [restaurants]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (venueRef.current && !venueRef.current.contains(e.target as Node)) {
        setVenueOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const todayStr = now.toISOString().slice(0, 10);
  const currentTimeStr = now.toTimeString().slice(0, 5); // "HH:MM"

  useEffect(() => {
    if (data) setBookings(data);
  }, [data]);

  const handleSendOffer = (bookingId: string, _offerId: string) => {
    setBookings((prev) =>
      prev.map((b) => (b.id === bookingId ? { ...b, status: "offer-sent" as const } : b))
    );
  };

  const restaurantBookings = selectedRestaurant
    ? bookings.filter((b) => (b as any).restaurant_id === selectedRestaurant.id)
    : bookings;

  const dateFiltered = filterDate === "all"
    ? restaurantBookings.filter((b) => {
        if ((b as any).booking_date === todayStr) return b.time >= currentTimeStr;
        return true;
      })
    : restaurantBookings.filter((b) => {
        if ((b as any).booking_date !== filterDate) return false;
        if (filterDate === todayStr) return b.time >= currentTimeStr;
        return true;
      });

  const filtered = filterRisk === "all"
    ? dateFiltered
    : dateFiltered.filter((b) => b.riskLevel === filterRisk);

  const highRiskCount = dateFiltered.filter(
    (b) => (b.riskLevel === "high") && b.status === "unconfirmed"
  ).length;

  const atRiskRevenue = dateFiltered
    .filter((b) => b.riskLevel === "high")
    .reduce((sum, b) => sum + b.covers * 80, 0);

  if (isLoading) {
    return <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">Loading bookings…</div>;
  }

  if (isError) {
    return <div className="flex-1 flex items-center justify-center text-sm text-risk-high">Failed to load bookings.</div>;
  }

  return (
    <div className="flex-1 overflow-auto p-6">
      {/* Venue selector */}
      <div className="bg-card rounded-lg border border-border p-4 mb-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-muted flex items-center justify-center shrink-0">
          <Calendar className="w-4 h-4 text-muted-foreground" />
        </div>

        {/* Dropdown */}
        <div className="relative" ref={venueRef}>
          <button
            onClick={() => setVenueOpen((v) => !v)}
            className="flex items-center gap-1.5 hover:opacity-70 transition-opacity"
          >
            <span className="text-base font-semibold text-foreground">
              {selectedRestaurant?.name ?? "Loading…"}
            </span>
            {selectedRestaurant && (
              <span className="text-xs text-muted-foreground font-normal">
                · {selectedRestaurant.suburb}{selectedRestaurant.state ? `, ${selectedRestaurant.state}` : ""}
              </span>
            )}
            <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${venueOpen ? "rotate-180" : ""}`} />
          </button>

          {venueOpen && restaurants && (
            <div className="absolute top-full left-0 mt-1 w-72 bg-card border border-border rounded-lg shadow-lg z-20 py-1 overflow-hidden">
              {restaurants.map((r) => (
                <button
                  key={r.id}
                  onClick={() => { setSelectedRestaurant(r); setVenueOpen(false); }}
                  className="w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-muted transition-colors text-left"
                >
                  <div>
                    <div className="font-medium text-foreground">{r.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {r.suburb}{r.state ? `, ${r.state}` : ""} · {r.cuisine}
                    </div>
                  </div>
                  {selectedRestaurant?.id === r.id && (
                    <Check className="w-3.5 h-3.5 text-primary shrink-0" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="ml-auto flex items-center gap-1.5 text-sm text-muted-foreground">
          <Clock className="w-4 h-4" />
          <span>
            {now.toLocaleDateString("en-AU", { weekday: "short", day: "numeric", month: "short" })}
            {" · "}
            {now.toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>
      </div>

      {/* Page title */}
      <h1 className="text-xl font-semibold text-foreground mb-1">No-Show Predictor</h1>
      <p className="text-sm text-muted-foreground mb-4">
        7-day bookings ranked by no-show risk. Weather updates every 30 seconds.
      </p>

      {/* Loading overlay — sits above the faded content */}
      {isChangingVenue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
          <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-4 py-2.5 shadow-lg text-sm text-muted-foreground">
            <svg className="w-4 h-4 animate-spin text-primary" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
            </svg>
            Loading {selectedRestaurant?.name}…
          </div>
        </div>
      )}

      {/* Content area — fade while switching venue */}
      <div className={`relative transition-opacity duration-300 ${isChangingVenue ? "opacity-40 pointer-events-none" : "opacity-100"}`}>

      {/* Weather + risk impact bar */}
      <WeatherRiskBar
        selectedDate={filterDate}
        onSelectDate={setFilterDate}
        lat={selectedRestaurant?.lat}
        lon={selectedRestaurant?.lon}
        restaurantId={selectedRestaurant?.id}
        onFetchingChange={(fetching) => {
          if (!hasLoadedOnce.current) {
            if (!fetching) hasLoadedOnce.current = true;
            return;
          }
          setIsChangingVenue(fetching);
        }}
      />

      {/* Alert bar */}
      {highRiskCount > 0 && (
        <div className="flex items-center bg-risk-high-bg border border-risk-high/20 rounded-lg px-4 py-3 mb-4">
          <AlertTriangle className="w-4 h-4 text-risk-high shrink-0" />
          <span className="text-sm text-risk-high font-medium ml-2">
            {highRiskCount} high-risk booking{highRiskCount > 1 ? "s" : ""} requiring attention
            {atRiskRevenue > 0 && (
              <span className="font-semibold">. ${atRiskRevenue.toLocaleString()} at risk</span>
            )}
          </span>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide mr-2">Risk:</span>
        {(["all", "high", "medium", "low"] as const).map((level) => (
          <button
            key={level}
            onClick={() => setFilterRisk(level)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
              filterRisk === level
                ? "bg-foreground text-card border-foreground"
                : "bg-card text-muted-foreground border-border hover:bg-muted"
            }`}
          >
            {level === "all" ? "All" : `${level.charAt(0).toUpperCase() + level.slice(1)} Risk`}
          </button>
        ))}
        {filterDate !== "all" && (
          <button
            onClick={() => setFilterDate("all")}
            className="ml-2 px-3 py-1.5 text-xs font-medium rounded-md border bg-primary/10 text-primary border-primary/20 hover:bg-primary/20 transition-colors"
          >
            Clear date filter
          </button>
        )}
        <span className="ml-auto text-xs text-muted-foreground">
          {filtered.length} booking{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg border border-border overflow-hidden shadow-sm">
        <div className="flex items-center px-5 py-3 border-b border-border bg-muted/50">
          <div className="w-16 shrink-0 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Time</div>
          <div className="flex-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Guest</div>
          <div className="w-24 shrink-0 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Status</div>
          <div className="w-32 shrink-0 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Risk</div>
          <div className="flex-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Factors</div>
          <div className="w-52 shrink-0 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground text-right">Actions</div>
        </div>

        {filtered.map((booking) => (
          <BookingRow
            key={booking.id}
            booking={booking}
            onSendOffer={setOfferBooking}
          />
        ))}

        {filtered.length === 0 && (
          <div className="px-6 py-12 text-center text-sm text-muted-foreground">
            No bookings match the selected filter.
          </div>
        )}
      </div>
      </div> {/* end venue-switching content wrapper */}

      {offerBooking && (
        <OfferDialog
          booking={offerBooking}
          open={!!offerBooking}
          onClose={() => setOfferBooking(null)}
          onSend={handleSendOffer}
        />
      )}


    </div>
  );
};

export default NoShowPredictor;
