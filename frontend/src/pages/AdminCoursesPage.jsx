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
import { TranslateDialog } from "@/components/TranslateDialog";

export const AdminCoursesPage = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    thumbnail_url: "",
    video_url: "",
    video_type: "youtube",
    price: 0,
    is_free: true,
    is_private: false,
    passing_score: 70,
    language: "en",
    category: ""
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const { data } = await API.get("/courses?include_private=true");
      setCourses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      await API.post("/courses", formData);
      toast.success(t("courses.createCourse") + " ✓");
      setShowCreateDialog(false);
      setFormData({
        title: "",
        description: "",
        thumbnail_url: "",
        video_url: "",
        video_type: "youtube",
        price: 0,
        is_free: true,
        is_private: false,
        passing_score: 70,
        language: "en",
        category: ""
      });
      fetchCourses();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (courseId) => {
    if (!window.confirm("Are you sure you want to delete this course?")) return;
    
    try {
      await API.delete(`/courses/${courseId}`);
      toast.success("Course deleted!");
      fetchCourses();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  // Get language display name
  const getLanguageDisplay = (langCode) => {
    const langMap = {
      "en": "English",
      "zh-TW": "繁體中文",
      "zh-CN": "简体中文",
      "ja": "日本語",
      "ko": "한국어"
    };
    return langMap[langCode] || langCode;
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-courses-page">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
            {t("dashboard.manageCourses")}
          </h1>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="create-course-btn">
                <Plus className="w-4 h-4 mr-2" /> {t("courses.createCourse")}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{t("courses.createNew")}</DialogTitle>
                <DialogDescription>{t("courses.fillDetails")}</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pr-2">
                <div className="space-y-2">
                  <Label>{t("courses.title")}</Label>
                  <Input 
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="rounded-sm"
                    data-testid="course-title-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t("courses.description")}</Label>
                  <Textarea 
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="rounded-sm"
                    rows={4}
                    data-testid="course-description-input"
                  />
                </div>
                
                {/* Language Selection - NEW */}
                <div className="space-y-2">
                  <Label>{t("courses.language")}</Label>
                  <Select value={formData.language} onValueChange={(v) => setFormData({...formData, language: v})}>
                    <SelectTrigger className="rounded-sm" data-testid="course-language-select">
                      <Globe className="w-4 h-4 mr-2" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {courseLanguages.map(lang => (
                        <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>{t("courses.thumbnailUrl")}</Label>
                  <Input 
                    value={formData.thumbnail_url}
                    onChange={(e) => setFormData({...formData, thumbnail_url: e.target.value})}
                    className="rounded-sm"
                    placeholder="https://..."
                    data-testid="course-thumbnail-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("courses.videoUrl")}</Label>
                    <Input 
                      value={formData.video_url}
                      onChange={(e) => setFormData({...formData, video_url: e.target.value})}
                      className="rounded-sm"
                      placeholder="YouTube or Vimeo URL"
                      data-testid="course-video-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Video Type</Label>
                    <Select value={formData.video_type} onValueChange={(v) => setFormData({...formData, video_type: v})}>
                      <SelectTrigger className="rounded-sm" data-testid="course-video-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="youtube">YouTube</SelectItem>
                        <SelectItem value="vimeo">Vimeo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Price ($)</Label>
                    <Input 
                      type="number"
                      value={formData.price}
                      onChange={(e) => setFormData({...formData, price: parseFloat(e.target.value) || 0})}
                      className="rounded-sm"
                      disabled={formData.is_free}
                      data-testid="course-price-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Passing Score (%)</Label>
                    <Input 
                      type="number"
                      value={formData.passing_score}
                      onChange={(e) => setFormData({...formData, passing_score: parseInt(e.target.value) || 70})}
                      className="rounded-sm"
                      min={0}
                      max={100}
                      data-testid="course-passing-score-input"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Switch 
                      checked={formData.is_free}
                      onCheckedChange={(v) => setFormData({...formData, is_free: v, price: v ? 0 : formData.price})}
                      data-testid="course-free-switch"
                    />
                    <Label>Free Course</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch 
                      checked={formData.is_private}
                      onCheckedChange={(v) => setFormData({...formData, is_private: v})}
                      data-testid="course-private-switch"
                    />
                    <Label>Private Course</Label>
                  </div>
                </div>
                <Button 
                  onClick={handleCreate}
                  disabled={creating || !formData.title}
                  className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                  data-testid="submit-course-btn"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Course"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : courses.length > 0 ? (
          <div className="space-y-4">
            {courses.map((course) => (
              <Card key={course.id} className="bg-white border border-slate-200 rounded-sm" data-testid={`admin-course-${course.id}`}>
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-24 h-16 bg-slate-100 rounded-sm overflow-hidden flex-shrink-0">
                    {course.thumbnail_url ? (
                      <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <BookOpen className="w-6 h-6 text-slate-300" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{course.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {course.language && (
                        <Badge className="bg-[#002FA7] text-white rounded-sm text-xs">
                          <Globe className="w-3 h-3 mr-1" />
                          {getLanguageDisplay(course.language)}
                        </Badge>
                      )}
                      {course.is_free ? (
                        <Badge variant="secondary" className="bg-green-100 text-green-700 rounded-sm text-xs">Free</Badge>
                      ) : (
                        <Badge className="bg-amber-100 text-amber-700 rounded-sm text-xs">${course.price}</Badge>
                      )}
                      {course.is_private && (
                        <Badge variant="outline" className="rounded-sm text-xs">Private</Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <TranslateDialog courseId={course.id} courseTitle={course.title} onTranslated={fetchCourses} />
                    <Button 
                      variant="outline" 
                      size="icon" 
                      className="rounded-sm"
                      onClick={() => navigate(`/admin/courses/${course.id}/edit`)}
                      data-testid={`edit-course-${course.id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="icon" 
                      className="rounded-sm text-red-600 hover:text-red-700"
                      onClick={() => handleDelete(course.id)}
                      data-testid={`delete-course-${course.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-4">No courses created yet</p>
              <Button onClick={() => setShowCreateDialog(true)} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm">
                Create Your First Course
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

