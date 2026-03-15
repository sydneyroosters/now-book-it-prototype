import { Users } from "lucide-react";

const tabs = ["Account", "Venues", "Customers", "Admins & managers", "Shared tags"];

const AdminSubHeader = () => {
  return (
    <div className="bg-card border-b border-border px-6">
      <nav className="flex gap-0 -mb-px">
        {tabs.map((tab) => (
          <a
            key={tab}
            href="#"
            className={`px-4 py-2.5 text-sm transition-colors border-b-[3px] ${
              tab === "Venues"
                ? "border-primary text-primary font-medium"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </a>
        ))}
      </nav>
    </div>
  );
};

export default AdminSubHeader;
