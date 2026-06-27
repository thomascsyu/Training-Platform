import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Award, BookOpen, GraduationCap, Loader2, Users } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";

export const AdminDashboard = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const { data } = await API.get("/stats/admin");
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="admin-dashboard">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
          {t("dashboard.adminDashboard")}
        </h1>
        <p className="text-slate-600">{t("dashboard.managePlatform")}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-[#002FA7]/10 rounded-sm">
                <BookOpen className="w-6 h-6 text-[#002FA7]" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.total_courses || 0}</p>
                <p className="text-sm text-slate-600">{t("dashboard.totalCourses")}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-sm">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.total_students || 0}</p>
                <p className="text-sm text-slate-600">{t("dashboard.totalStudents")}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-sm">
                <GraduationCap className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.total_enrollments || 0}</p>
                <p className="text-sm text-slate-600">{t("dashboard.totalEnrollments")}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-sm">
                <Award className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.completed_courses || 0}</p>
                <p className="text-sm text-slate-600">{t("dashboard.completions")}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardHeader>
            <CardTitle className="text-lg">{t("dashboard.quickActions")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={() => navigate("/admin/courses")} className="w-full justify-start bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="manage-courses-btn">
              <BookOpen className="w-4 h-4 mr-2" /> {t("dashboard.manageCourses")}
            </Button>
            <Button onClick={() => navigate("/admin/companies")} variant="outline" className="w-full justify-start rounded-sm" data-testid="manage-companies-btn">
              <Users className="w-4 h-4 mr-2" /> {t("companies.manageCompanies")}
            </Button>
            <Button onClick={() => navigate("/admin/users")} variant="outline" className="w-full justify-start rounded-sm" data-testid="manage-users-btn">
              <Users className="w-4 h-4 mr-2" /> {t("dashboard.manageUsers")}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

