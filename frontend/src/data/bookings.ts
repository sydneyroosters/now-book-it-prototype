export type RiskLevel = "low" | "medium" | "high";

export interface Booking {
  id: string;
  time: string;
  guestName: string;
  covers: number;
  table: string;
  phone: string;
  riskLevel: RiskLevel;
  riskScore: number;
  riskFactors: string[];
  status: "confirmed" | "unconfirmed" | "re-confirmed" | "cancelled" | "offer-sent";
  notes?: string;
  preferences?: string[];
}

export const mockBookings: Booking[] = [
  {
    id: "1",
    time: "17:30",
    guestName: "Sarah Mitchell",
    covers: 2,
    table: "4",
    phone: "+61 412 345 678",
    riskLevel: "low",
    riskScore: 12,
    riskFactors: ["Regular guest", "Always shows"],
    status: "confirmed",
    preferences: ["Prefers red wine", "Window seat"],
  },
  {
    id: "2",
    time: "18:00",
    guestName: "James Cooper",
    covers: 6,
    table: "8",
    phone: "+61 423 456 789",
    riskLevel: "high",
    riskScore: 87,
    riskFactors: ["First-timer", "Large party", "No phone answer"],
    status: "unconfirmed",
    preferences: [],
  },
  {
    id: "3",
    time: "18:30",
    guestName: "Emily Watson",
    covers: 4,
    table: "12",
    phone: "+61 434 567 890",
    riskLevel: "medium",
    riskScore: 45,
    riskFactors: ["Previous no-show", "Booked online"],
    status: "confirmed",
    preferences: ["Likes cocktails", "Celebrates birthdays here"],
  },
  {
    id: "4",
    time: "19:00",
    guestName: "Michael Torres",
    covers: 2,
    table: "3",
    phone: "+61 445 678 901",
    riskLevel: "low",
    riskScore: 8,
    riskFactors: ["VIP", "20+ visits"],
    status: "confirmed",
    preferences: ["Wine enthusiast", "Prefers booth"],
  },
  {
    id: "5",
    time: "19:00",
    guestName: "Jonathan Walters",
    covers: 4,
    table: "15",
    phone: "+61 456 789 012",
    riskLevel: "high",
    riskScore: 82,
    riskFactors: ["First-timer", "High value", "Weekend booking"],
    status: "unconfirmed",
    preferences: [],
  },
  {
    id: "6",
    time: "19:30",
    guestName: "Linda Park",
    covers: 3,
    table: "7",
    phone: "+61 467 890 123",
    riskLevel: "medium",
    riskScore: 52,
    riskFactors: ["Booked via 3rd party", "No deposit"],
    status: "unconfirmed",
    preferences: ["Likes white wine", "Dietary: vegetarian"],
  },
  {
    id: "7",
    time: "20:00",
    guestName: "David Chen",
    covers: 8,
    table: "20",
    phone: "+61 478 901 234",
    riskLevel: "high",
    riskScore: 91,
    riskFactors: ["First-timer", "Large party", "No deposit", "No phone answer"],
    status: "unconfirmed",
    preferences: [],
  },
  {
    id: "8",
    time: "20:00",
    guestName: "Rachel Adams",
    covers: 2,
    table: "5",
    phone: "+61 489 012 345",
    riskLevel: "low",
    riskScore: 15,
    riskFactors: ["Regular guest"],
    status: "confirmed",
    preferences: ["Wine lover", "Anniversary regular"],
  },
  {
    id: "9",
    time: "20:30",
    guestName: "Tom Bradley",
    covers: 5,
    table: "11",
    phone: "+61 490 123 456",
    riskLevel: "medium",
    riskScore: 38,
    riskFactors: ["Infrequent guest", "Large party"],
    status: "confirmed",
    preferences: ["Beer drinker", "Likes outdoor seating"],
  },
  {
    id: "10",
    time: "21:00",
    guestName: "Nina Patel",
    covers: 2,
    table: "2",
    phone: "+61 401 234 567",
    riskLevel: "low",
    riskScore: 5,
    riskFactors: ["VIP", "50+ visits"],
    status: "confirmed",
    preferences: ["Champagne lover", "Prefers quiet corner"],
  },
];
