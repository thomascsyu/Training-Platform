import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Award, BarChart3, BookOpen, GraduationCap, Home, LogOut, Menu, Users
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";

export const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = user?.role === "admin" ? [
    { icon: Home, label: t("nav.dashboard"), path: "/dashboard" },
    { icon: BookOpen, label: t("dashboard.manageCourses"), path: "/admin/courses" },
    { icon: Users, label: t("nav.companies"), path: "/admin/companies" },
    { icon: Users, label: t("nav.users"), path: "/admin/users" },
    { icon: Users, label: t("nav.bulkEnroll"), path: "/admin/bulk-enroll" },
    { icon: BarChart3, label: t("nav.groupProgress"), path: "/manager/progress" },
    { icon: BarChart3, label: t("nav.analytics"), path: "/admin/analytics" }
  ] : user?.role === "client_manager" ? [
    { icon: Home, label: t("nav.dashboard"), path: "/dashboard" },
    { icon: BarChart3, label: t("nav.groupProgress"), path: "/manager/progress" },
    { icon: BookOpen, label: t("nav.courses"), path: "/courses" },
    { icon: BookOpen, label: t("nav.myCourses"), path: "/my-courses" },
    { icon: Award, label: t("nav.certificates"), path: "/certificates" }
  ] : [
    { icon: Home, label: t("nav.dashboard"), path: "/dashboard" },
    { icon: BookOpen, label: t("nav.myCourses"), path: "/my-courses" },
    { icon: Award, label: t("nav.certificates"), path: "/certificates" }
  ];

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? "w-64" : "w-20"} bg-white border-r border-slate-200 transition-all duration-200 flex flex-col`}>
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          {sidebarOpen && (
            <Link to="/" className="flex items-center gap-2">
              <GraduationCap className="w-6 h-6 text-[#002FA7]" />
              <span className="font-medium text-[#0A0B10]">LearnHub</span>
            </Link>
          )}
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} className="rounded-sm" data-testid="toggle-sidebar-btn">
            <Menu className="w-5 h-5" />
          </Button>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <Button
              key={item.path}
              variant="ghost"
              className={`w-full justify-start rounded-sm ${sidebarOpen ? "" : "px-0 justify-center"}`}
              onClick={() => navigate(item.path)}
              data-testid={`nav-${item.label.toLowerCase().replace(" ", "-")}`}
            >
              <item.icon className="w-5 h-5" />
              {sidebarOpen && <span className="ml-3">{item.label}</span>}
            </Button>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-200">
          <div className={`flex items-center gap-3 ${sidebarOpen ? "" : "justify-center"}`}>
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                {user?.name?.charAt(0)?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name}</p>
                <p className="text-xs text-slate-500 capitalize">{user?.role?.replace("_", " ")}</p>
              </div>
            )}
          </div>
          <Button 
            variant="ghost" 
            className={`w-full mt-3 text-slate-600 rounded-sm ${sidebarOpen ? "justify-start" : "px-0 justify-center"}`}
            onClick={logout}
            data-testid="logout-btn"
          >
            <LogOut className="w-5 h-5" />
            {sidebarOpen && <span className="ml-3">{t("nav.logout")}</span>}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};

