import { useState } from "react";
import { Gift, Wine, DollarSign, Percent, X, Send, Sparkles } from "lucide-react";
import type { Booking } from "@/data/bookings";

interface OfferDialogProps {
  booking: Booking;
  open: boolean;
  onClose: () => void;
  onSend: (bookingId: string, offerId: string) => void;
}

interface OfferOption {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  personalized?: boolean;
}

function getOffers(booking: Booking): OfferOption[] {
  const isMedium = booking.riskLevel === "medium";
  const depositAmount = booking.covers <= 2 ? 25 : booking.covers <= 4 ? 50 : booking.covers <= 6 ? 75 : 100;
  const likesWine = booking.preferences?.some((p) => p.toLowerCase().includes("wine"));
  const likesCocktails = booking.preferences?.some((p) => p.toLowerCase().includes("cocktail"));
  const likesChampagne = booking.preferences?.some((p) => p.toLowerCase().includes("champagne"));
  const likesBeer = booking.preferences?.some((p) => p.toLowerCase().includes("beer"));

  // Medium risk: soft reward-based offers — no deposit pressure, just a nice incentive
  if (isMedium) {
    const offers: OfferOption[] = [
      {
        id: "medium-discount",
        title: "Get 10% off your total bill",
        description: `No deposit required — just a friendly nudge with a 10% discount off their entire bill on the night.`,
        icon: Percent,
      },
      {
        id: "medium-welcome-drink",
        title: "Complimentary welcome drink on arrival",
        description: `A no-strings offer: let them know a welcome drink is waiting. A warm gesture that encourages follow-through.`,
        icon: Gift,
      },
    ];

    if (likesWine) {
      offers.push({
        id: "medium-wine",
        title: "Complimentary glass of wine on arrival",
        description: `They love wine — surprise them with a complimentary glass when they arrive. No deposit needed.`,
        icon: Wine,
        personalized: true,
      });
    }

    if (likesCocktails) {
      offers.push({
        id: "medium-cocktail",
        title: "Complimentary house cocktail",
        description: `Based on their cocktail preferences — a free cocktail waiting at the table, no commitment required.`,
        icon: Gift,
        personalized: true,
      });
    }

    if (likesChampagne) {
      offers.push({
        id: "medium-champagne",
        title: "Complimentary glass of champagne",
        description: `They enjoy champagne — greet them with a complimentary glass as a warm welcome.`,
        icon: Wine,
        personalized: true,
      });
    }

    if (likesBeer) {
      offers.push({
        id: "medium-beer",
        title: "First round of drinks on us",
        description: `A casual, low-pressure offer — first round is on the house when they arrive.`,
        icon: Gift,
        personalized: true,
      });
    }

    return offers;
  }

  // High / critical risk: deposit-focused offers to lock in commitment
  const offers: OfferOption[] = [
    {
      id: "deposit-discount",
      title: `Pay $${depositAmount} deposit & get 5% off`,
      description: `Secure booking with a $${depositAmount} deposit (based on ${booking.covers} guests). The deposit is deducted from the final bill, plus a 5% discount.`,
      icon: Percent,
    },
    {
      id: "deposit-only",
      title: `Pay $${depositAmount} deposit to confirm`,
      description: `A refundable deposit of $${depositAmount} to guarantee the reservation. Fully deducted from the final bill.`,
      icon: DollarSign,
    },
  ];

  if (likesWine) {
    offers.push({
      id: "deposit-wine",
      title: `Pay $${depositAmount} deposit & get a free bottle of wine`,
      description: `We know they love wine! Secure with a $${depositAmount} deposit and surprise them with a complimentary bottle on arrival.`,
      icon: Wine,
      personalized: true,
    });
  }

  if (likesCocktails) {
    offers.push({
      id: "deposit-cocktails",
      title: `Pay $${depositAmount} deposit & get 2 free cocktails`,
      description: `Based on their cocktail preferences — secure with a deposit and welcome them with two house cocktails.`,
      icon: Gift,
      personalized: true,
    });
  }

  if (likesChampagne) {
    offers.push({
      id: "deposit-champagne",
      title: `Pay $${depositAmount} deposit & get a glass of champagne`,
      description: `They love champagne! Confirm with a deposit and greet them with a complimentary glass.`,
      icon: Wine,
      personalized: true,
    });
  }

  if (likesBeer) {
    offers.push({
      id: "deposit-beer",
      title: `Pay $${depositAmount} deposit & get a free round of beers`,
      description: `They enjoy beer — lock in the booking with a deposit and start them off with a round on the house.`,
      icon: Gift,
      personalized: true,
    });
  }

  if (!likesWine && !likesCocktails && !likesChampagne && !likesBeer) {
    offers.push({
      id: "deposit-dessert",
      title: `Pay $${depositAmount} deposit & get a free dessert`,
      description: `Secure the booking with a deposit and offer a complimentary dessert to sweeten the deal.`,
      icon: Gift,
    });
  }

  return offers;
}

const OfferDialog = ({ booking, open, onClose, onSend }: OfferDialogProps) => {
  const [selectedOffer, setSelectedOffer] = useState<string | null>(null);

  if (!open) return null;

  const offers = getOffers(booking);

  const handleSend = () => {
    if (selectedOffer) {
      onSend(booking.id, selectedOffer);
      setSelectedOffer(null);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-foreground/40" onClick={onClose} />

      {/* Dialog */}
      <div className="relative bg-card rounded-xl border border-border shadow-xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              {booking.riskLevel === "medium" ? "Send Soft Incentive" : "Send Offer"}
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              {booking.guestName} · {booking.covers} guests · {booking.time}
              {booking.riskLevel === "medium" && (
                <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider text-risk-medium bg-risk-medium-bg px-1.5 py-0.5 rounded-full">
                  Medium Risk
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Offers */}
        <div className="px-6 py-4 space-y-3 max-h-[400px] overflow-y-auto">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
            Choose an offer to send
          </p>
          {offers.map((offer) => (
            <button
              key={offer.id}
              onClick={() => setSelectedOffer(offer.id)}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                selectedOffer === offer.id
                  ? "border-primary bg-sidebar-accent"
                  : "border-border hover:border-muted-foreground/30 hover:bg-muted/50"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                    selectedOffer === offer.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                  }`}
                >
                  <offer.icon className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{offer.title}</span>
                    {offer.personalized && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-primary bg-sidebar-accent px-1.5 py-0.5 rounded-full">
                        <Sparkles className="w-2.5 h-2.5" />
                        Personalised
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{offer.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-4 border-t border-border bg-muted/30 rounded-b-xl">
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-muted-foreground bg-card border border-border rounded-md hover:bg-muted transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSend}
              disabled={!selectedOffer}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-foreground text-card rounded-md hover:opacity-90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5" />
              Send Offer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfferDialog;
