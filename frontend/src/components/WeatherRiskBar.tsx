import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { CloudRain, Sun, Cloud, Zap, Wind, RefreshCw } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_BOOKINGS_API_URL;

interface DayImpact {
  date: string;
  day_label: string;
  is_today: boolean;
  weather: {
    condition: string;
    rain_mm: number;
    temp_max: number;
    temp_min: number;
    wind_kmh: number;
    weather_risk: "low" | "medium" | "high";
  };
  total_bookings: number;
  total_covers: number;
  risk_breakdown: { low: number; medium: number; high: number; critical: number; unscored: number };
  at_risk_count: number;
  at_risk_pct: number;
  revenue_at_risk: number;
}

function WeatherIcon({ condition, risk }: { condition: string; risk: string }) {
  const cls = "w-4 h-4";
  if (risk === "high" || condition.toLowerCase().includes("thunder")) return <Zap className={cls} />;
  if (condition.toLowerCase().includes("rain") || condition.toLowerCase().includes("drizzle")) return <CloudRain className={cls} />;
  if (condition.toLowerCase().includes("wind")) return <Wind className={cls} />;
  if (condition.toLowerCase().includes("cloud") || condition.toLowerCase().includes("overcast")) return <Cloud className={cls} />;
  return <Sun className={cls} />;
}

const weatherRiskColor = {
  low: "text-muted-foreground",
  medium: "text-risk-medium",
  high: "text-risk-high",
};

const weatherBg = {
  low: "bg-card border-border",
  medium: "bg-risk-medium-bg border-risk-medium/20",
  high: "bg-risk-high-bg border-risk-high/20",
};

export default function WeatherRiskBar({
  selectedDate,
  onSelectDate,
  lat,
  lon,
  restaurantId,
  onFetchingChange,
}: {
  selectedDate: string;
  onSelectDate: (date: string) => void;
  lat?: number;
  lon?: number;
  restaurantId?: string;
  onFetchingChange?: (isFetching: boolean) => void;
}) {
  const params = new URLSearchParams();
  if (lat != null) params.set("lat", String(lat));
  if (lon != null) params.set("lon", String(lon));
  if (restaurantId) params.set("restaurant_id", restaurantId);

  const { data, isLoading, isFetching, dataUpdatedAt } = useQuery<DayImpact[]>({
    queryKey: ["weather-impact", lat, lon, restaurantId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/dashboard/weather-impact?${params}`);
      if (!res.ok) throw new Error("Failed");
      return res.json();
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
  });

  // Bubble fetching state up so parent can show a loader
  useEffect(() => {
    onFetchingChange?.(isFetching);
  }, [isFetching]);

  if (isLoading || !data) {
    return <div className="h-24 bg-card rounded-lg border border-border animate-pulse mb-4" />;
  }

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" }) : null;

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          7-Day Weather Impact
        </h2>
        {lastUpdated && (
          <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
            <RefreshCw className="w-3 h-3" />
            Updated {lastUpdated}
          </span>
        )}
      </div>

      <div className="grid grid-cols-7 gap-2">
        {data.map((day) => {
          const wr = day.weather.weather_risk;
          const isSelected = selectedDate === day.date;

          return (
            <button
              key={day.date}
              onClick={() => onSelectDate(isSelected ? "all" : day.date)}
              className={`relative flex flex-col items-center gap-1 p-2.5 rounded-lg border text-left transition-all
                ${isSelected
                  ? "ring-2 ring-primary ring-offset-1 border-primary/40 bg-primary/5"
                  : `${weatherBg[wr]} hover:opacity-80`
                }
              `}
            >
              {day.is_today && (
                <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] font-bold uppercase tracking-wider bg-primary text-white px-1.5 py-0.5 rounded-full">
                  Today
                </span>
              )}

              <span className="text-[11px] font-medium text-foreground mt-1">{day.day_label}</span>

              <span className={`${weatherRiskColor[wr]}`}>
                <WeatherIcon condition={day.weather.condition} risk={wr} />
              </span>

              <span className={`text-[10px] font-medium ${weatherRiskColor[wr]}`}>
                {day.weather.rain_mm > 0 ? `${day.weather.rain_mm}mm` : `${day.weather.temp_max}°`}
              </span>

              {day.total_bookings > 0 ? (
                <div className="w-full mt-0.5">
                  {/* Stacked risk bar */}
                  <div className="flex h-1.5 w-full rounded-full overflow-hidden gap-px">
                    {day.risk_breakdown.low > 0 && (
                      <div
                        className="bg-risk-low rounded-l-full"
                        style={{ flex: day.risk_breakdown.low }}
                      />
                    )}
                    {day.risk_breakdown.medium > 0 && (
                      <div className="bg-risk-medium" style={{ flex: day.risk_breakdown.medium }} />
                    )}
                    {day.risk_breakdown.high > 0 && (
                      <div className="bg-risk-high" style={{ flex: day.risk_breakdown.high }} />
                    )}
                    {day.risk_breakdown.critical > 0 && (
                      <div
                        className="bg-risk-high rounded-r-full opacity-80"
                        style={{ flex: day.risk_breakdown.critical }}
                      />
                    )}
                    {day.risk_breakdown.unscored > 0 && (
                      <div
                        className="bg-muted-foreground/30 rounded-r-full"
                        style={{ flex: day.risk_breakdown.unscored }}
                      />
                    )}
                  </div>
                  <span className="text-[10px] text-muted-foreground mt-0.5 block text-center">
                    {day.at_risk_count > 0 ? (
                      <span className="text-risk-high font-medium">{day.at_risk_count} at risk</span>
                    ) : (
                      `${day.total_bookings} bookings`
                    )}
                  </span>
                </div>
              ) : (
                <span className="text-[10px] text-muted-foreground">No bookings</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
