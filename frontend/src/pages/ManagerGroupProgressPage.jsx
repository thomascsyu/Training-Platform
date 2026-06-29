import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart3, CheckCircle, Clock, Loader2 } from "lucide-react";
import { getCourseLanguageDisplay } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";

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
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-2">
          Group Training Progress
        </h1>
        <p className="text-slate-600 mb-8">{t("manager.monitorProgress")}</p>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Course List */}
            <div className="lg:col-span-1 space-y-4">
              <h2 className="font-medium text-slate-700">{t("manager.coursesTitle")}</h2>
              {overview.length > 0 ? overview.map((course) => (
                <Card 
                  key={course.course_id}
                  className={`bg-white border rounded-sm cursor-pointer transition-all ${
                    selectedCourse === course.course_id 
                      ? "border-[#002FA7] ring-2 ring-[#002FA7]/20" 
                      : "border-slate-200 hover:border-slate-300"
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
                <Card className="bg-white border border-slate-200 rounded-sm">
                  <CardContent className="p-8 text-center">
                    <p className="text-slate-500">{t("manager.noCoursesWithEnrollments")}</p>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Course Details */}
            <div className="lg:col-span-2">
              {loadingDetails ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
                </div>
              ) : courseProgress ? (
                <div className="space-y-6">
                  {/* Summary Stats */}
                  <Card className="bg-white border border-slate-200 rounded-sm">
                    <CardHeader>
                      <CardTitle className="text-lg">{courseProgress.course_title}</CardTitle>
                      <CardDescription>Passing Score: {courseProgress.passing_score}%</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-4 bg-slate-50 rounded-sm">
                          <p className="text-2xl font-medium text-[#0A0B10]">{courseProgress.summary.total_enrolled}</p>
                          <p className="text-xs text-slate-500">{t("manager.totalEnrolled")}</p>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-sm">
                          <p className="text-2xl font-medium text-green-600">{courseProgress.summary.completed}</p>
                          <p className="text-xs text-slate-500">{t("manager.completedLabel")}</p>
                        </div>
                        <div className="text-center p-4 bg-yellow-50 rounded-sm">
                          <p className="text-2xl font-medium text-yellow-600">{courseProgress.summary.in_progress}</p>
                          <p className="text-xs text-slate-500">{t("manager.inProgressLabel")}</p>
                        </div>
                        <div className="text-center p-4 bg-[#002FA7]/5 rounded-sm">
                          <p className="text-2xl font-medium text-[#002FA7]">{courseProgress.summary.average_score}%</p>
                          <p className="text-xs text-slate-500">{t("manager.avgScore")}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Student List */}
                  <Card className="bg-white border border-slate-200 rounded-sm">
                    <CardHeader>
                      <CardTitle className="text-lg">Student Progress</CardTitle>
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
                <Card className="bg-white border border-slate-200 rounded-sm">
                  <CardContent className="p-12 text-center">
                    <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-600">{t("manager.selectCoursePrompt")}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

