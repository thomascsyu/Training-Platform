import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { BarChart3, BookOpen, ChevronRight, Users } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import EmptyState from "@/components/enhanced/EmptyState";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

export const ManagerDashboard = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [overview, setOverview] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/groups/overview")
      .then(({ data }) => setOverview(data))
      .catch(() => setOverview([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-8 max-w-7xl mx-auto">
          <SkeletonGrid n={3} />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-8 max-w-7xl mx-auto">
        <PageHeader overline={t("nav.groupProgress")} title={t("nav.dashboard")}>
          <Button
            onClick={() => navigate("/manager/progress")}
            className="btn-primary"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            {t("nav.groupProgress")}
          </Button>
        </PageHeader>

        {overview.length === 0 ? (
          <EmptyState icon={BookOpen} title={t("manager.noEnrollments")} testId="manager-dashboard-empty" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger">
            {overview.map((course) => (
              <Card
                key={course.course_id}
                className="card-swiss cursor-pointer"
                onClick={() => navigate("/manager/progress")}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="font-display text-lg line-clamp-2">
                    {course.course_title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4 text-sm text-slate-600">
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {course.total_enrolled} {t("manager.enrolledLabel")}
                    </span>
                    <span>{course.completed} {t("manager.completedLabel")}</span>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{t("manager.completionRate")}</span>
                      <span>{course.completion_rate}%</span>
                    </div>
                    <Progress value={course.completion_rate} className="h-2" />
                  </div>
                  <Button variant="ghost" size="sm" className="w-full justify-between rounded-sm">
                    {t("manager.viewDetails")} <ChevronRight className="w-4 h-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
