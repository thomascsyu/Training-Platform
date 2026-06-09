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

import { DashboardLayout } from "@/components/DashboardLayout";

export const AdminBulkEnrollPage = () => {
  const { t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [coursesRes, usersRes] = await Promise.all([
        API.get("/courses?include_private=true"),
        API.get("/users?role=student")
      ]);
      setCourses(coursesRes.data);
      setStudents(usersRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkEnroll = async () => {
    if (!selectedCourse || selectedStudents.length === 0) {
      toast.error(t("groups.selectCourseAndStudents"));
      return;
    }
    
    setEnrolling(true);
    try {
      const { data } = await API.post("/enrollments", {
        course_id: selectedCourse,
        user_ids: selectedStudents
      });
      toast.success(data.message);
      setSelectedStudents([]);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-bulk-enroll-page">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-8">
          {t("dashboard.bulkEnrollTitle")}
        </h1>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg">{t("dashboard.selectCourse")}</CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                  <SelectTrigger className="rounded-sm" data-testid="select-course-dropdown">
                    <SelectValue placeholder={t("dashboard.chooseCourse")} />
                  </SelectTrigger>
                  <SelectContent>
                    {courses.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg">{t("dashboard.selectStudents")}</CardTitle>
                <CardDescription>
                  {selectedStudents.length} selected
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-60 border border-slate-200 rounded-sm">
                  {students.map((s) => (
                    <label 
                      key={s.id}
                      className="flex items-center gap-3 p-3 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0"
                      data-testid={`student-${s.id}`}
                    >
                      <input 
                        type="checkbox"
                        checked={selectedStudents.includes(s.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedStudents([...selectedStudents, s.id]);
                          } else {
                            setSelectedStudents(selectedStudents.filter(id => id !== s.id));
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                          {s.name?.charAt(0)?.toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-sm">{s.name}</p>
                        <p className="text-xs text-slate-500">{s.email}</p>
                      </div>
                    </label>
                  ))}
                </ScrollArea>
                <Button 
                  onClick={handleBulkEnroll}
                  disabled={enrolling || !selectedCourse || selectedStudents.length === 0}
                  className="w-full mt-4 bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                  data-testid="bulk-enroll-btn"
                >
                  {enrolling ? <Loader2 className="w-4 h-4 animate-spin" /> : t("dashboard.enrollCount").replace("{count}", selectedStudents.length)}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
