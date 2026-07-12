import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart3, CheckCircle, Clock } from "lucide-react";
import { getCourseLanguageDisplay } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import EmptyState from "@/components/enhanced/EmptyState";
import StatCard from "@/components/enhanced/StatCard";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

export const ManagerGroupProgressPage = () => {
  const { t } = useLanguage();
  const [overview, setOverview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseProgress, setCourseProgress] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    try {
      const { data } = await API.get("/groups/overview");
      setOverview(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourseProgress = async (courseId) => {
    setLoadingDetails(true);
    try {
      const { data } = await API.get(`/groups/course/${courseId}/progress`);
      setCourseProgress(data);
      setSelectedCourse(courseId);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="manager-progress-page">
        <PageHeader overline="Manager" title="Group Training Progress" description={t("manager.monitorProgress")} />

        {loading ? (
          <SkeletonGrid n={3} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Course List */}
            <div className="lg:col-span-1 space-y-4">
              <p className="overline">{t("manager.coursesTitle")}</p>
              {overview.length > 0 ? overview.map((course) => (
                <Card
                  key={course.course_id}
                  className={`card-swiss cursor-pointer ${
                    selectedCourse === course.course_id
                      ? "border-[#002FA7] ring-2 ring-[#002FA7]/20"
                      : ""
                  }`}
                  onClick={() => fetchCourseProgress(course.course_id)}
                  data-testid={`course-progress-${course.course_id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-sm line-clamp-2">{course.course_title}</h3>
                      <Badge className="bg-[#002FA7] text-white rounded-sm text-xs ml-2">
                        {getCourseLanguageDisplay(course.language, { short: true })}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500 mb-2">
                      <span>{course.total_enrolled} enrolled</span>
                      <span>{course.completed} completed</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Completion Rate</span>
                        <span className="font-medium">{course.completion_rate}%</span>
                      </div>
                      <Progress value={course.completion_rate} className="h-2" />
                    </div>
                    {course.average_score > 0 && (
                      <p className="text-xs text-slate-500 mt-2">
                        {t("manager.avgScore")}: <span className="font-medium text-[#002FA7]">{course.average_score}%</span>
                      </p>
                    )}
                  </CardContent>
                </Card>
              )) : (
                <EmptyState icon={BarChart3} title={t("manager.noCoursesWithEnrollments")} testId="manager-progress-empty-courses" />
              )}
            </div>

            {/* Course Details */}
            <div className="lg:col-span-2">
              {loadingDetails ? (
                <SkeletonGrid n={1} />
              ) : courseProgress ? (
                <div className="space-y-6">
                  {/* Summary Stats */}
                  <Card className="card-swiss">
                    <CardHeader>
                      <CardTitle className="font-display text-lg">{courseProgress.course_title}</CardTitle>
                      <CardDescription>Passing Score: {courseProgress.passing_score}%</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger">
                        <StatCard label={t("manager.totalEnrolled")} value={courseProgress.summary.total_enrolled} testId="stat-group-enrolled" />
                        <StatCard label={t("manager.completedLabel")} value={courseProgress.summary.completed} testId="stat-group-completed" />
                        <StatCard label={t("manager.inProgressLabel")} value={courseProgress.summary.in_progress} testId="stat-group-in-progress" />
                        <StatCard label={t("manager.avgScore")} value={`${courseProgress.summary.average_score}%`} testId="stat-group-avg-score" />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Student List */}
                  <Card className="card-swiss">
                    <CardHeader>
                      <CardTitle className="font-display text-lg">Student Progress</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-slate-50 border-b border-slate-200">
                            <tr>
                              <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("manager.studentColumn")}</th>
                              <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("manager.statusColumn")}</th>
                              <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("manager.scoreColumn")}</th>
                              <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("manager.lessonsColumn")}</th>
                              <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("manager.attemptsColumn")}</th>
                              <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("manager.lastActivityColumn")}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {courseProgress.students.map((student) => (
                              <tr key={student.user_id} className="border-b border-slate-100" data-testid={`student-row-${student.user_id}`}>
                                <td className="p-4">
                                  <div className="flex items-center gap-3">
                                    <Avatar className="w-8 h-8">
                                      <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                                        {student.user_name?.charAt(0)?.toUpperCase()}
                                      </AvatarFallback>
                                    </Avatar>
                                    <div>
                                      <p className="font-medium text-sm">{student.user_name}</p>
                                      <p className="text-xs text-slate-500">{student.user_email}</p>
                                    </div>
                                  </div>
                                </td>
                                <td className="p-4">
                                  <Badge className={`rounded-sm text-xs ${
                                    student.completed 
                                      ? "bg-green-100 text-green-700" 
                                      : "bg-yellow-100 text-yellow-700"
                                  }`}>
                                    {student.completed ? (
                                      <><CheckCircle className="w-3 h-3 mr-1" /> {t("common.completed")}</>
                                    ) : (
                                      <><Clock className="w-3 h-3 mr-1" /> {t("dashboard.inProgress")}</>
                                    )}
                                  </Badge>
                                </td>
                                <td className="p-4">
                                  {student.completed ? (
                                    <span className={`font-medium ${
                                      student.score >= courseProgress.passing_score ? "text-green-600" : "text-red-600"
                                    }`}>
                                      {student.score}%
                                    </span>
                                  ) : (
                                    <span className="text-slate-400">-</span>
                                  )}
                                </td>
                                <td className="p-4 text-sm text-slate-600">
                                  {student.lessons_total > 0 ? (
                                    <span>{student.lessons_completed}/{student.lessons_total} ({student.lesson_progress_percent}%)</span>
                                  ) : (
                                    <span className="text-slate-400">-</span>
                                  )}
                                </td>
                                <td className="p-4 text-sm text-slate-600">{student.quiz_attempts}</td>
                                <td className="p-4 text-sm text-slate-500">
                                  {student.last_activity ? new Date(student.last_activity).toLocaleDateString() : "-"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <EmptyState icon={BarChart3} title={t("manager.selectCoursePrompt")} testId="manager-progress-select-prompt" />
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

