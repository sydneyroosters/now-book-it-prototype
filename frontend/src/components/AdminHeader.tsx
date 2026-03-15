import nowBookItIcon from "@/assets/nowbookit-logo.png";

const navItems = ["Enquiries", "Registered", "Accounts", "Gift Cards", "Users", "Advanced Search"];

const AdminHeader = () => {
  return (
    <header className="bg-header text-header-foreground">
      <div className="flex items-center px-6 h-14">
        <div className="flex items-center gap-2.5 mr-10">
          <img src={nowBookItIcon} alt="Now Book It" className="w-28 h-10" />
        </div>
        <nav className="flex items-center">
          {navItems.map((item) => (
            <a
              key={item}
              href="#"
              className={`px-3.5 py-4 text-sm transition-colors ${
                item === "Accounts"
                  ? "text-header-foreground border-b-[3px] border-primary font-medium"
                  : "text-header-foreground/65 hover:text-header-foreground/90 border-b-[3px] border-transparent"
              }`}
            >
              {item}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
};

export default AdminHeader;
