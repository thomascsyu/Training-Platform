import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

export const AdminAnalyticsPage = () => {
  const { t } = useLanguage();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const { data } = await API.get("/stats/admin/analytics");
      setAnalytics(data);
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

  const overview = analytics?.overview || {};

  return (
    <div className="p-6" data-testid="admin-analytics-page">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
          {t("nav.analytics")}
        </h1>
        <p className="text-slate-600">Platform-wide performance and engagement metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <p className="text-2xl font-medium">{overview.completion_rate || 0}%</p>
            <p className="text-sm text-slate-600">Course Completion Rate</p>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <p className="text-2xl font-medium">{overview.avg_lesson_progress_percent || 0}%</p>
            <p className="text-sm text-slate-600">Avg Lesson Progress</p>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <p className="text-2xl font-medium">{overview.total_certificates || 0}</p>
            <p className="text-sm text-slate-600">Certificates Issued</p>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <p className="text-2xl font-medium">{overview.total_lesson_completions || 0}</p>
            <p className="text-sm text-slate-600">Lessons Completed</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardHeader>
            <CardTitle className="text-lg">Quiz Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Total Attempts</span>
              <span className="font-medium">{analytics?.quiz_stats?.total_attempts || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Passed</span>
              <span className="font-medium text-green-600">{analytics?.quiz_stats?.passed || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Failed</span>
              <span className="font-medium text-red-600">{analytics?.quiz_stats?.failed || 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardHeader>
            <CardTitle className="text-lg">Platform Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Total Enrollments</span>
              <span className="font-medium">{overview.total_enrollments || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Completed Enrollments</span>
              <span className="font-medium">{overview.completed_enrollments || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Total Students</span>
              <span className="font-medium">{overview.total_students || 0}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white border border-slate-200 rounded-sm">
        <CardHeader>
          <CardTitle className="text-lg">Top Courses by Enrollment</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left p-4 font-medium text-slate-600 text-sm">Course</th>
                  <th className="text-left p-4 font-medium text-slate-600 text-sm">Enrollments</th>
                  <th className="text-left p-4 font-medium text-slate-600 text-sm">Completed</th>
                  <th className="text-left p-4 font-medium text-slate-600 text-sm">Rate</th>
                </tr>
              </thead>
              <tbody>
                {(analytics?.top_courses || []).map((course) => (
                  <tr key={course.course_id} className="border-b border-slate-100">
                    <td className="p-4 text-sm font-medium">{course.course_title}</td>
                    <td className="p-4 text-sm">{course.enrollments}</td>
                    <td className="p-4 text-sm">{course.completed}</td>
                    <td className="p-4 text-sm">{course.completion_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

