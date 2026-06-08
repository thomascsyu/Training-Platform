import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams, useSearchParams, Link } from "react-router-dom";
import { Toaster, toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import {
  BookOpen, GraduationCap, Users, PlayCircle, Award, MessageSquare,
  Menu, X, LogOut, Settings, ChevronRight, Plus, Trash2, Edit,
  Download, Send, Bot, FileText, Video, CheckCircle, Clock,
  DollarSign, Lock, Globe, BarChart3, Home, Loader2, Search, Languages
} from "lucide-react";
import { courseLanguages, languageNames } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { LanguageProvider, useLanguage } from "@/contexts/LanguageContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

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
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="student-dashboard">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
          {t("dashboard.welcomeBack")}, {user?.name}!
        </h1>
        <p className="text-slate-600">{t("dashboard.continueJourney")}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-[#002FA7]/10 rounded-sm">
              <BookOpen className="w-6 h-6 text-[#002FA7]" />
            </div>
            <div>
              <p className="text-2xl font-medium">{stats?.enrolled_courses || 0}</p>
              <p className="text-sm text-slate-600">{t("dashboard.enrolledCourses")}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-sm">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-medium">{stats?.completed_courses || 0}</p>
              <p className="text-sm text-slate-600">{t("dashboard.completedLabel")}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-sm">
              <Award className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-medium">{stats?.certificates || 0}</p>
              <p className="text-sm text-slate-600">{t("dashboard.certificatesLabel")}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Enrollments */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-medium">{t("dashboard.myCourses")}</h2>
          <Button variant="outline" onClick={() => navigate("/courses")} className="rounded-sm" data-testid="browse-more-btn">
            {t("dashboard.browseMore")} <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
        {enrollments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {enrollments.map((e) => (
              <Card 
                key={e.id} 
                className="bg-white border border-slate-200 rounded-sm cursor-pointer hover:-translate-y-1 hover:shadow-md transition-all"
                onClick={() => navigate(`/courses/${e.course_id}`)}
                data-testid={`enrollment-card-${e.course_id}`}
              >
                <div className="aspect-video bg-slate-100 relative overflow-hidden">
                  {e.course_thumbnail ? (
                    <img src={e.course_thumbnail} alt={e.course_title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5">
                      <BookOpen className="w-12 h-12 text-[#002FA7]/40" />
                    </div>
                  )}
                  {e.completed && (
                    <Badge className="absolute top-2 right-2 bg-green-600 text-white rounded-sm">
                      <CheckCircle className="w-3 h-3 mr-1" /> {t("common.completed")}
                    </Badge>
                  )}
                </div>
                <CardContent className="p-4">
                  <h3 className="font-medium text-[#0A0B10] mb-2">{e.course_title}</h3>
                  {e.completed ? (
                    <p className="text-sm text-green-600">{t("dashboard.score")}: {e.score}%</p>
                  ) : (
                    <>
                      <p className="text-sm text-slate-600 mb-2">{t("dashboard.inProgress")}</p>
                      {e.lessons_total > 0 && (
                        <div className="flex items-center gap-2">
                          <Progress value={e.progress_percent || 0} className="h-2 flex-1" />
                          <span className="text-xs text-slate-500">{e.progress_percent || 0}%</span>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-4">You haven't enrolled in any courses yet</p>
              <Button onClick={() => navigate("/courses")} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="start-learning-btn">
                Start Learning
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

