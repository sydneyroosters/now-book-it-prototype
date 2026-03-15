import { Phone, MessageSquare, Send, Sparkles, Loader2, Mail, PhoneCall, Gift } from "lucide-react";
import type { Booking } from "@/data/bookings";
import RiskBadge from "./RiskBadge";
import { useScoreBooking } from "@/hooks/useBookings";

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
};

const statusLabels: Record<string, string> = {
  confirmed: "Confirmed",
  "re-confirmed": "Re-confirmed",
  "offer-sent": "Offer Sent",
  unconfirmed: "Unconfirmed",
  cancelled: "Cancelled",
};

const BookingRow = ({ booking, onSendOffer }: BookingRowProps) => {
  const isActionable = booking.status === "unconfirmed";
  const isNonLowRisk = booking.riskLevel !== "low";
  const isUnscored = booking.riskScore === 0 && !booking.riskFactors.some(f => f.includes("history") || f.includes("visits"));
  const { mutate: scoreBooking, isPending: isScoring } = useScoreBooking();

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

      {/* Risk badge */}
      <div className="w-32 shrink-0">
        <RiskBadge level={booking.riskLevel} score={booking.riskScore} />
      </div>

      {/* Risk factors */}
      <div className="flex-1 min-w-0 flex flex-wrap gap-1 pr-4">
        {booking.riskFactors.map((factor) => (
          <span
            key={factor}
            className="text-[11px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded whitespace-nowrap"
          >
            {factor}
          </span>
        ))}
      </div>

      {/* Actions */}
      <div className="w-52 shrink-0 flex justify-end gap-1.5">
        {isUnscored && (
          <button
            onClick={() => scoreBooking(booking.id)}
            disabled={isScoring}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap bg-primary/10 text-primary border border-primary/20 rounded-md shadow-sm hover:bg-primary/20 transition-colors disabled:opacity-50"
          >
            {isScoring ? <Loader2 className="w-3 h-3 shrink-0 animate-spin" /> : <Sparkles className="w-3 h-3 shrink-0" />}
            {isScoring ? "Scoring…" : "AI Score"}
          </button>
        )}
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
