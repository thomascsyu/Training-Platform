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

import { CourseCard } from "@/components/CourseCard";

export const CoursesPage = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("all");

  useEffect(() => {
    fetchCourses();
  }, [selectedLanguage]);

  const fetchCourses = async () => {
    try {
      let url = "/courses";
      const params = new URLSearchParams();
      if (selectedLanguage && selectedLanguage !== "all") {
        params.append("language", selectedLanguage);
      }
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      const { data } = await API.get(url);
      setCourses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredCourses = courses.filter(course => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return course.title?.toLowerCase().includes(query) || 
           course.description?.toLowerCase().includes(query);
  });

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      {/* Header */}
      <header className="backdrop-blur-xl bg-white/80 border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 md:px-12 lg:px-24 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium tracking-tight text-[#0A0B10]">LearnHub</span>
          </Link>
          <nav className="flex items-center gap-4">
            <LanguageSwitcher />
            {user ? (
              <Button onClick={() => window.location.href = "/dashboard"} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="dashboard-btn">
                {t("nav.dashboard")}
              </Button>
            ) : (
              <Button onClick={() => window.location.href = "/login"} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="login-btn">
                {t("nav.login")}
              </Button>
            )}
          </nav>
        </div>
      </header>

      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-12" data-testid="courses-page">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-6">
          {t("courses.allCourses")}
        </h1>
        
        {/* Search and Filter */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <Input 
              placeholder={t("courses.search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-sm border-slate-300"
              data-testid="course-search-input"
            />
          </div>
          <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
            <SelectTrigger className="w-[200px] rounded-sm border-slate-300" data-testid="language-filter">
              <Globe className="w-4 h-4 mr-2" />
              <SelectValue placeholder={t("courses.allLanguages")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("courses.allLanguages")}</SelectItem>
              {courseLanguages.map(lang => (
                <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : filteredCourses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">{t("courses.noCourses")}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

