import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Award, BookOpen, GraduationCap, Users } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";
import PageHeader from "@/components/enhanced/PageHeader";
import StatCard from "@/components/enhanced/StatCard";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

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
      <div className="p-6">
        <SkeletonGrid n={4} />
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="admin-dashboard">
      <PageHeader overline={t("dashboard.adminDashboard")} title={t("dashboard.adminDashboard")} description={t("dashboard.managePlatform")} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 stagger">
        <StatCard label={t("dashboard.totalCourses")} value={stats?.total_courses || 0} icon={BookOpen} testId="stat-total-courses" />
        <StatCard label={t("dashboard.totalStudents")} value={stats?.total_students || 0} icon={Users} testId="stat-total-students" />
        <StatCard label={t("dashboard.totalEnrollments")} value={stats?.total_enrollments || 0} icon={GraduationCap} testId="stat-total-enrollments" />
        <StatCard label={t("dashboard.completions")} value={stats?.completed_courses || 0} icon={Award} testId="stat-completions" />
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
            <Button onClick={() => navigate("/admin/certificates")} variant="outline" className="w-full justify-start rounded-sm" data-testid="manage-certificates-btn">
              <Award className="w-4 h-4 mr-2" /> {t("nav.certificates")}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

