import AdminHeader from "@/components/AdminHeader";
import AdminSubHeader from "@/components/AdminSubHeader";
import AdminSidebar from "@/components/AdminSidebar";
import NoShowPredictor from "@/components/NoShowPredictor";

const Index = () => {
  return (
    <div className="flex flex-col h-screen">
      <AdminHeader />
      <AdminSubHeader />
      <div className="flex flex-1 overflow-hidden">
        <AdminSidebar />
        <NoShowPredictor />
      </div>
    </div>
  );
};

export default Index;
