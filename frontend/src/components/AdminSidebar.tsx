import { CalendarDays, MessageSquare, Puzzle, Settings, Sparkles, Shield, Building2, MonitorSmartphone } from "lucide-react";

interface SidebarGroup {
  label: string;
  items: { name: string; icon: React.ElementType; active?: boolean }[];
}

const groups: SidebarGroup[] = [
  {
    label: "Venue info",
    items: [{ name: "Venue", icon: Building2 }],
  },
  {
    label: "Diary",
    items: [
      { name: "Booking widget", icon: MonitorSmartphone },
      { name: "Diary booking", icon: CalendarDays },
      { name: "No-Show Predictor", icon: Shield, active: true },
      { name: "Communication", icon: MessageSquare },
      { name: "Integrations", icon: Puzzle },
    ],
  },
  {
    label: "Gift cards",
    items: [
      { name: "Settings", icon: Settings },
      { name: "Setup", icon: Sparkles },
      { name: "Management", icon: CalendarDays },
    ],
  },
];

const AdminSidebar = () => {
  return (
    <aside className="w-56 bg-sidebar border-r border-sidebar-border shrink-0 overflow-y-auto">
      <div className="py-4">
        {groups.map((group) => (
          <div key={group.label} className="mb-4">
            <div className="px-5 mb-1 text-[11px] font-medium uppercase tracking-wider text-sidebar-muted">
              {group.label}
            </div>
            {group.items.map((item) => (
              <a
                key={item.name}
                href="#"
                className={`flex items-center gap-2.5 px-5 py-2 text-[13px] transition-colors ${
                  item.active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.name}
              </a>
            ))}
          </div>
        ))}
      </div>
    </aside>
  );
};

export default AdminSidebar;
