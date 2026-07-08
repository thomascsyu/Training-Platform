import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Loader2 } from "lucide-react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

const formatDate = (value) => {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return "—";
  }
};

const statusStyles = {
  completed: "bg-green-100 text-green-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  not_started: "bg-slate-100 text-slate-700",
};

const statusLabels = {
  completed: "Completed",
  in_progress: "In Progress",
  not_started: "Not Started",
};

export const AdminCompanyDashboardPage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { companyId } = useParams();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      if (!companyId) return;
      setLoading(true);
      try {
        const { data } = await API.get(`/companies/${companyId}/dashboard`);
        setDashboard(data);
        setSelectedUserId(data.users?.[0]?.user_id || null);
      } catch (e) {
        toast.error(formatError(e));
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [companyId]);

  const selectedUser = useMemo(() => {
    if (!selectedUserId || !dashboard?.users) return null;
    return dashboard.users.find((user) => user.user_id === selectedUserId) || null;
  }, [dashboard, selectedUserId]);

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-company-dashboard-page">
        <div className="flex flex-col gap-4 mb-8">
          <Button
            variant="outline"
            className="w-fit rounded-sm"
            onClick={() => navigate("/admin/companies")}
            data-testid="back-to-companies-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> {t("companies.manageCompanies")}
          </Button>

          <div className="flex flex-col gap-2">
            <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
              {dashboard?.company?.name || "Company Dashboard"}
            </h1>
            <p className="text-slate-600">
              {dashboard?.company?.description || "Track users and training progress for this company."}
            </p>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : !dashboard ? (
          <Card className="bg-white border border-slate-200 rounded-sm p-8 text-center text-slate-600">
            Unable to load company dashboard.
          </Card>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              <Card className="bg-white border border-slate-200 rounded-sm p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide">Users</p>
                <p className="text-2xl font-medium text-[#0A0B10] mt-2">{dashboard.summary.total_users}</p>
              </Card>
              <Card className="bg-white border border-slate-200 rounded-sm p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide">Assigned Trainings</p>
                <p className="text-2xl font-medium text-[#0A0B10] mt-2">{dashboard.summary.total_trainings}</p>
              </Card>
              <Card className="bg-white border border-slate-200 rounded-sm p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide">Completion Rate</p>
                <p className="text-2xl font-medium text-[#0A0B10] mt-2">{dashboard.summary.completion_rate}%</p>
              </Card>
              <Card className="bg-white border border-slate-200 rounded-sm p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide">Average Progress</p>
                <p className="text-2xl font-medium text-[#0A0B10] mt-2">
                  {dashboard.summary.average_progress_percent}%
                </p>
              </Card>
            </div>

            <Card className="bg-white border border-slate-200 rounded-sm overflow-hidden">
              <div className="p-4 border-b border-slate-200">
                <h2 className="font-medium text-[#0A0B10]">Users in this Company</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("users.name")}</th>
                      <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("users.email")}</th>
                      <th className="text-left p-4 font-medium text-slate-600 text-sm">Completed</th>
                      <th className="text-left p-4 font-medium text-slate-600 text-sm">In Progress</th>
                      <th className="text-left p-4 font-medium text-slate-600 text-sm">Not Started</th>
                      <th className="text-left p-4 font-medium text-slate-600 text-sm">Overall Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.users.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-slate-500">
                          {t("users.noUsers")}
                        </td>
                      </tr>
                    ) : (
                      dashboard.users.map((user) => (
                        <tr
                          key={user.user_id}
                          className={`border-b border-slate-100 cursor-pointer ${
                            selectedUserId === user.user_id ? "bg-[#002FA7]/5" : ""
                          }`}
                          onClick={() => setSelectedUserId(user.user_id)}
                          data-testid={`company-dashboard-user-${user.user_id}`}
                        >
                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <Avatar className="w-8 h-8">
                                <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                                  {user.user_name?.charAt(0)?.toUpperCase()}
                                </AvatarFallback>
                              </Avatar>
                              <span className="font-medium">{user.user_name}</span>
                            </div>
                          </td>
                          <td className="p-4 text-slate-600">{user.user_email}</td>
                          <td className="p-4 text-slate-600">{user.summary.completed_trainings}</td>
                          <td className="p-4 text-slate-600">{user.summary.in_progress_trainings}</td>
                          <td className="p-4 text-slate-600">{user.summary.not_started_trainings}</td>
                          <td className="p-4">
                            <div className="min-w-[140px] space-y-1">
                              <p className="text-sm font-medium text-slate-700">
                                {user.summary.overall_progress_percent}%
                              </p>
                              <Progress value={user.summary.overall_progress_percent} className="h-2" />
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {selectedUser && (
              <Card className="bg-white border border-slate-200 rounded-sm overflow-hidden">
                <div className="p-4 border-b border-slate-200">
                  <h2 className="font-medium text-[#0A0B10]">Training Progress for {selectedUser.user_name}</h2>
                  <p className="text-sm text-slate-500 mt-1">
                    Joined on {formatDate(selectedUser.created_at)}
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="text-left p-4 font-medium text-slate-600 text-sm">Training</th>
                        <th className="text-left p-4 font-medium text-slate-600 text-sm">Status</th>
                        <th className="text-left p-4 font-medium text-slate-600 text-sm">Progress</th>
                        <th className="text-left p-4 font-medium text-slate-600 text-sm">{t("dashboard.score")}</th>
                        <th className="text-left p-4 font-medium text-slate-600 text-sm">Attempts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedUser.trainings.map((training) => (
                        <tr key={training.course_id} className="border-b border-slate-100">
                          <td className="p-4 font-medium">{training.course_title}</td>
                          <td className="p-4">
                            <Badge
                              className={`rounded-sm text-xs ${
                                statusStyles[training.status] || "bg-slate-100 text-slate-700"
                              }`}
                            >
                              {statusLabels[training.status] || training.status}
                            </Badge>
                          </td>
                          <td className="p-4 min-w-[180px]">
                            <div className="space-y-1">
                              <p className="text-sm font-medium text-slate-700">{training.progress_percent}%</p>
                              <Progress value={training.progress_percent} className="h-2" />
                              <p className="text-xs text-slate-500">
                                {training.lessons_completed}/{training.lessons_total} lessons completed
                              </p>
                            </div>
                          </td>
                          <td className="p-4 text-slate-600">
                            {training.completed ? `${training.score}%` : "—"}
                          </td>
                          <td className="p-4 text-slate-600">{training.quiz_attempts}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
