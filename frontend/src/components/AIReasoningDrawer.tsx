import { X, User, CloudSun, Clock, Brain, Building2, UserX, Sparkles, CheckCircle2, AlertTriangle, TrendingUp } from "lucide-react";
import type { ScoringResult, ReasoningStep } from "@/hooks/useBookings";

const TOOL_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  get_guest_profile: {
    label: "Guest Profile",
    icon: <User className="w-3.5 h-3.5" />,
    color: "text-blue-500 bg-blue-500/10 border-blue-500/20",
  },
  get_weather_forecast: {
    label: "Weather Forecast",
    icon: <CloudSun className="w-3.5 h-3.5" />,
    color: "text-sky-500 bg-sky-500/10 border-sky-500/20",
  },
  get_slot_history: {
    label: "Slot History",
    icon: <Clock className="w-3.5 h-3.5" />,
    color: "text-purple-500 bg-purple-500/10 border-purple-500/20",
  },
  get_similar_past_cases: {
    label: "Similar Past Cases",
    icon: <Brain className="w-3.5 h-3.5" />,
    color: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  },
  get_restaurant_profile: {
    label: "Restaurant Profile",
    icon: <Building2 className="w-3.5 h-3.5" />,
    color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
  },
  get_guest_cancellation_patterns: {
    label: "Cancellation Patterns",
    icon: <UserX className="w-3.5 h-3.5" />,
    color: "text-rose-500 bg-rose-500/10 border-rose-500/20",
  },
  submit_risk_assessment: {
    label: "Final Assessment",
    icon: <Sparkles className="w-3.5 h-3.5" />,
    color: "text-primary bg-primary/10 border-primary/20",
  },
};

const RISK_COLORS: Record<string, string> = {
  low: "text-risk-low bg-risk-low-bg border-risk-low/20",
  medium: "text-risk-medium bg-risk-medium-bg border-risk-medium/20",
  high: "text-risk-high bg-risk-high-bg border-risk-high/20",
  critical: "text-risk-high bg-risk-high-bg border-risk-high/20",
};

interface Props {
  open: boolean;
  guestName: string;
  result: ScoringResult;
  onClose: () => void;
}

export default function AIReasoningDrawer({ open, guestName, result, onClose }: Props) {
  if (!open) return null;

  const { risk_result, reasoning_steps } = result;
  const riskColor = RISK_COLORS[risk_result.risk_level] ?? RISK_COLORS.medium;

  // Steps excluding the final assessment (shown separately)
  const signalSteps = reasoning_steps.filter((s) => s.tool !== "submit_risk_assessment");
  const toolsUsed = [...new Set(reasoning_steps.map((s) => s.tool))];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-[460px] bg-card border-l border-border shadow-2xl flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
            </div>
            <div>
              <div className="text-sm font-semibold text-foreground">AI Reasoning</div>
              <div className="text-xs text-muted-foreground">{guestName}</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-muted transition-colors text-muted-foreground"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">

          {/* Final Score Card */}
          <div className={`rounded-lg border p-4 ${riskColor}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wider opacity-70 mb-1">Risk Assessment</div>
                <div className="text-2xl font-bold">{risk_result.risk_score}/100</div>
                <div className="text-sm font-semibold capitalize mt-0.5">{risk_result.risk_level} risk</div>
              </div>
              <div className="text-right">
                <div className="text-[11px] font-semibold uppercase tracking-wider opacity-70 mb-1">Revenue at Risk</div>
                <div className="text-xl font-bold">${risk_result.revenue_at_risk.toLocaleString()}</div>
                <div className="text-xs opacity-70 mt-0.5">{risk_result.confidence}% confidence</div>
              </div>
            </div>

            {risk_result.recommended_action && (
              <div className="mt-3 pt-3 border-t border-current/20">
                <div className="text-[11px] font-semibold uppercase tracking-wider opacity-70 mb-1">Recommended Action</div>
                <div className="text-xs font-medium">{risk_result.recommended_action}</div>
              </div>
            )}
          </div>

          {/* Risk Reasons */}
          {risk_result.top_reasons.length > 0 && (
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">Risk Signals</div>
              <div className="space-y-1.5">
                {risk_result.top_reasons.map((reason, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-foreground">
                    <AlertTriangle className="w-3 h-3 text-risk-high shrink-0 mt-0.5" />
                    {reason}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Positive Factors */}
          {risk_result.positive_factors && risk_result.positive_factors.length > 0 && (
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">Positive Factors</div>
              <div className="space-y-1.5">
                {risk_result.positive_factors.map((factor, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-foreground">
                    <CheckCircle2 className="w-3 h-3 text-risk-low shrink-0 mt-0.5" />
                    {factor}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-border" />

          {/* Signal Timeline */}
          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <TrendingUp className="w-3.5 h-3.5 text-muted-foreground" />
              <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Reasoning Chain ({toolsUsed.length} signals)
              </div>
            </div>

            <div className="relative space-y-0">
              {/* Vertical line */}
              <div className="absolute left-[13px] top-3 bottom-3 w-px bg-border" />

              {signalSteps.map((step, i) => {
                const meta = TOOL_META[step.tool] ?? {
                  label: step.tool,
                  icon: <Brain className="w-3.5 h-3.5" />,
                  color: "text-muted-foreground bg-muted border-border",
                };

                return (
                  <div key={i} className="relative flex gap-3 pb-4 last:pb-0">
                    {/* Icon dot */}
                    <div className={`shrink-0 w-7 h-7 rounded-full border flex items-center justify-center z-10 ${meta.color}`}>
                      {meta.icon}
                    </div>
                    {/* Content */}
                    <div className="flex-1 min-w-0 pt-0.5">
                      <div className="text-xs font-semibold text-foreground">{meta.label}</div>
                      <div className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                        {step.output_summary}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {risk_result.follow_up_action && (
            <>
              <div className="border-t border-border" />
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Follow-up</div>
                <div className="text-xs text-muted-foreground">{risk_result.follow_up_action}</div>
              </div>
            </>
          )}

          {risk_result.best_contact_time && (
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Best Contact Time</div>
              <div className="text-xs text-muted-foreground">{risk_result.best_contact_time}</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
