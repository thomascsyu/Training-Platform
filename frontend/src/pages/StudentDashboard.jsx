import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Award, BookOpen, CheckCircle, ChevronRight } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";
import { CourseThumbnail } from "@/components/CourseThumbnail";
import PageHeader from "@/components/enhanced/PageHeader";
import StatCard from "@/components/enhanced/StatCard";
import EmptyState from "@/components/enhanced/EmptyState";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

export const StudentDashboard = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, enrollRes] = await Promise.all([
        API.get("/stats/student"),
        API.get("/enrollments/my")
      ]);
      setStats(statsRes.data);
      setEnrollments(enrollRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <SkeletonGrid n={3} />
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="student-dashboard">
      <PageHeader
        overline={t("dashboard.myCourses")}
        title={`${t("dashboard.welcomeBack")}, ${user?.name}!`}
        description={t("dashboard.continueJourney")}
      >
        <Button variant="outline" onClick={() => navigate("/courses")} className="rounded-sm" data-testid="browse-more-btn">
          {t("dashboard.browseMore")} <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </PageHeader>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 stagger">
        <StatCard label={t("dashboard.enrolledCourses")} value={stats?.enrolled_courses || 0} icon={BookOpen} testId="stat-enrolled" />
        <StatCard label={t("dashboard.completedLabel")} value={stats?.completed_courses || 0} icon={CheckCircle} testId="stat-completed" />
        <StatCard label={t("dashboard.certificatesLabel")} value={stats?.certificates || 0} icon={Award} testId="stat-certificates" />
      </div>

      {/* Recent Enrollments */}
      <div className="mb-8">
        {enrollments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger">
            {enrollments.map((e) => (
              <article
                key={e.id}
                className="card-swiss card-indexed overflow-hidden cursor-pointer group"
                onClick={() => navigate(`/courses/${e.course_id}`)}
                data-testid={`enrollment-card-${e.course_id}`}
              >
                <div className="aspect-video bg-slate-100 relative overflow-hidden border-b border-slate-200">
                  <CourseThumbnail
                    src={e.course_thumbnail || e.thumbnail_url}
                    alt=""
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
                    fallbackClassName="w-full h-full grid place-items-center bg-[linear-gradient(135deg,#002FA7_0%,#001C63_100%)]"
                    fallbackIconClassName="w-10 h-10 text-white/70"
                  />
                  {e.completed && (
                    <Badge className="absolute top-2 right-2 bg-green-600 text-white rounded-sm">
                      <CheckCircle className="w-3 h-3 mr-1" /> {t("common.completed")}
                    </Badge>
                  )}
                </div>
                <div className="p-4">
                  <h3 className="font-display text-lg leading-snug text-slate-900 mb-2 group-hover:text-[#002FA7] transition-colors">{e.course_title}</h3>
                  {e.completed ? (
                    <p className="text-sm text-green-600 font-medium">{t("dashboard.score")}: {e.score}%</p>
                  ) : (
                    <>
                      <p className="text-sm text-slate-600 mb-2">{t("dashboard.inProgress")}</p>
                      {e.lessons_total > 0 && (
                        <div className="flex items-center gap-2">
                          <Progress value={e.progress_percent || 0} className="h-2 flex-1" />
                          <span className="text-xs text-slate-500 tabular">{e.progress_percent || 0}%</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={BookOpen}
            title={t("dashboard.noCoursesYet")}
            actionLabel={t("dashboard.startLearning")}
            onAction={() => navigate("/courses")}
            testId="student-dashboard-empty"
          />
        )}
      </div>
    </div>
  );
};

