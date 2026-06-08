import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { BarChart3, BookOpen, ChevronRight, Loader2, Users } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";

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
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-8 max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-medium text-[#0A0B10]">{t("nav.dashboard")}</h1>
            <p className="text-slate-600 mt-1">{t("nav.groupProgress")}</p>
          </div>
          <Button
            onClick={() => navigate("/manager/progress")}
            className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            {t("nav.groupProgress")}
          </Button>
        </div>

        {overview.length === 0 ? (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">{t("manager.noEnrollments")}</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {overview.map((course) => (
              <Card
                key={course.course_id}
                className="bg-white border border-slate-200 rounded-sm hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigate("/manager/progress")}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg font-medium line-clamp-2">
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
