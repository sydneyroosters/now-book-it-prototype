import type { RiskLevel } from "@/data/bookings";

interface RiskBadgeProps {
  level: RiskLevel;
  score: number;
}

const config: Record<RiskLevel, { label: string; dot: string; text: string; bg: string }> = {
  low: {
    label: "Low",
    dot: "bg-risk-low",
    text: "text-risk-low",
    bg: "bg-risk-low-bg",
  },
  medium: {
    label: "Medium",
    dot: "bg-risk-medium",
    text: "text-risk-medium",
    bg: "bg-risk-medium-bg",
  },
  high: {
    label: "High",
    dot: "bg-risk-high",
    text: "text-risk-high",
    bg: "bg-risk-high-bg",
  },
};

const RiskBadge = ({ level, score }: RiskBadgeProps) => {
  const c = config[level];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider ${c.bg} ${c.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label} ({score}%)
    </span>
  );
};

export default RiskBadge;
