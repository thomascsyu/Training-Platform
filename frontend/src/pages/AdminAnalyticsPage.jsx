import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import PageHeader from "@/components/enhanced/PageHeader";
import StatCard from "@/components/enhanced/StatCard";
import { SkeletonGrid, TableSkeleton } from "@/components/enhanced/Skeletons";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
      <div className="p-6 space-y-8">
        <SkeletonGrid n={4} />
        <TableSkeleton rows={4} cols={4} />
      </div>
    );
  }

  const overview = analytics?.overview || {};

  return (
    <div className="p-6" data-testid="admin-analytics-page">
      <PageHeader overline="Admin" title={t("nav.analytics")} description="Platform-wide performance and engagement metrics" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 stagger">
        <StatCard label="Course Completion Rate" value={`${overview.completion_rate || 0}%`} testId="stat-completion-rate" />
        <StatCard label="Avg Lesson Progress" value={`${overview.avg_lesson_progress_percent || 0}%`} testId="stat-lesson-progress" />
        <StatCard label="Certificates Issued" value={overview.total_certificates || 0} testId="stat-certificates-issued" />
        <StatCard label="Lessons Completed" value={overview.total_lesson_completions || 0} testId="stat-lessons-completed" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="card-swiss">
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

        <Card className="card-swiss">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="card-swiss">
          <CardHeader>
            <CardTitle className="text-lg">Enrollment Trend (14 days)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.enrollment_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" name="Enrollments" fill="#002FA7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="card-swiss">
          <CardHeader>
            <CardTitle className="text-lg">Revenue Trend (14 days)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics?.revenue_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="amount"
                  name="Revenue (USD)"
                  stroke="#16a34a"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
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

