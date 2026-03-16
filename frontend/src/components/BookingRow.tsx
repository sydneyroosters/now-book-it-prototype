import { Phone, MessageSquare, Send, Mail, PhoneCall } from "lucide-react";
import type { Booking } from "@/data/bookings";
import RiskBadge from "./RiskBadge";

interface BookingRowProps {
  booking: Booking;
  onSendOffer: (booking: Booking) => void;
}

const statusStyles: Record<string, string> = {
  confirmed: "text-risk-low",
  "re-confirmed": "text-risk-low",
  "offer-sent": "text-primary",
  unconfirmed: "text-risk-medium",
  cancelled: "text-muted-foreground line-through",
  no_show: "text-risk-high",
  completed: "text-risk-low",
};

const statusLabels: Record<string, string> = {
  confirmed: "Confirmed",
  "re-confirmed": "Re-confirmed",
  "offer-sent": "Offer Sent",
  unconfirmed: "Unconfirmed",
  cancelled: "Cancelled",
  no_show: "No-Show",
  completed: "Completed",
};

const BookingRow = ({ booking, onSendOffer }: BookingRowProps) => {
  const isActionable = booking.status === "unconfirmed";
  const isNonLowRisk = booking.riskLevel !== "low";

  // Extra context signals
  const remindersIgnored = (booking as any).reminders_ignored ?? 0;
  const depositAmount = (booking as any).deposit_amount ?? 0;
  const occasion = (booking as any).occasion;
  const tier = (booking as any).tier;

  const extraSignals: string[] = [];
  if (remindersIgnored > 0) extraSignals.push(`${remindersIgnored} reminder${remindersIgnored > 1 ? "s" : ""} ignored`);
  if (depositAmount > 0) extraSignals.push(`$${depositAmount.toFixed(0)} deposit`);
  if (occasion && occasion !== "general") extraSignals.push(occasion.replace(/_/g, " "));
  if (tier === "fine_dining") extraSignals.push("fine dining");

  return (
    <div className="group flex items-center px-5 py-3.5 hover:bg-muted/50 transition-colors border-b border-border">
      {/* Time */}
      <div className="w-16 shrink-0 tabular-nums text-sm font-medium text-foreground">{booking.time}</div>

      {/* Guest info */}
      <div className="flex-1 min-w-0 pr-4">
        <div className="text-sm font-medium text-foreground truncate">{booking.guestName}</div>
        <div className="text-xs text-muted-foreground">
          {booking.covers} {booking.covers === 1 ? "Guest" : "Guests"} · Table {booking.table}
        </div>
      </div>

      {/* Status */}
      <div className="w-24 shrink-0">
        <span className={`text-xs font-medium ${statusStyles[booking.status] ?? "text-muted-foreground"}`}>
          {statusLabels[booking.status] ?? booking.status}
        </span>
        {(booking as any).confirmation_method && (
          <span className="flex items-center gap-0.5 mt-0.5 text-[10px] text-muted-foreground font-medium">
            {(booking as any).confirmation_method === "email" && <><Mail className="w-2.5 h-2.5" /> Email</>}
            {(booking as any).confirmation_method === "sms" && <><MessageSquare className="w-2.5 h-2.5" /> SMS</>}
            {(booking as any).confirmation_method === "phone" && <><PhoneCall className="w-2.5 h-2.5" /> Called</>}
          </span>
        )}
      </div>

      {/* Risk badge with reasoning tooltip */}
      <div className="w-32 shrink-0 relative group/risk">
        <RiskBadge level={booking.riskLevel} score={booking.riskScore} />
        {booking.riskFactors.length > 0 && (
          <div className="absolute left-0 top-full mt-1.5 z-40 hidden group-hover/risk:block w-64 bg-popover border border-border rounded-lg shadow-xl p-3 pointer-events-none">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Risk Signals</div>
            <ul className="space-y-1 mb-2">
              {booking.riskFactors.map((f) => (
                <li key={f} className="text-xs text-foreground flex items-start gap-1.5">
                  <span className="text-risk-high mt-0.5">·</span>{f}
                </li>
              ))}
            </ul>
            {(booking as any).recommended_action && (
              <>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Recommended Action</div>
                <p className="text-xs text-foreground">{(booking as any).recommended_action}</p>
              </>
            )}
          </div>
        )}
      </div>

      {/* Risk factors + extra signals */}
      <div className="flex-1 min-w-0 flex flex-wrap gap-1 pr-4">
        {booking.riskFactors.map((factor) => (
          <span
            key={factor}
            className="text-[11px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded whitespace-nowrap"
          >
            {factor}
          </span>
        ))}
        {extraSignals.map((sig) => (
          <span
            key={sig}
            className="text-[11px] text-primary/70 bg-primary/5 border border-primary/10 px-1.5 py-0.5 rounded whitespace-nowrap"
          >
            {sig}
          </span>
        ))}
      </div>

      {/* Actions */}
      <div className="w-56 shrink-0 flex justify-end gap-1.5 items-center">

        {/* Call / SMS / Send Offer */}
        {isActionable && isNonLowRisk ? (
          <>
            <button className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap bg-card border border-border rounded-md shadow-sm hover:bg-muted transition-colors">
              <Phone className="w-3 h-3 shrink-0" />
              Call
            </button>
            <button className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap bg-card border border-border rounded-md shadow-sm hover:bg-muted transition-colors">
              <MessageSquare className="w-3 h-3 shrink-0" />
              SMS
            </button>
            <button
              onClick={() => onSendOffer(booking)}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap bg-foreground text-card rounded-md shadow-sm hover:opacity-90 transition-colors"
            >
              <Send className="w-3 h-3 shrink-0" />
              Send Offer
            </button>
          </>
        ) : isNonLowRisk ? (
          <button
            onClick={() => onSendOffer(booking)}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap bg-foreground text-card rounded-md shadow-sm hover:opacity-90 transition-colors"
          >
            <Send className="w-3 h-3 shrink-0" />
            Send Offer
          </button>
        ) : (
          <span className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            No action needed
          </span>
        )}
      </div>
    </div>
  );
};

export default BookingRow;
