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

// ============ LANDING PAGE ============
export const LandingPage = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const { data } = await API.get("/courses");
      setCourses(data.slice(0, 6));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      {/* Header */}
      <header className="backdrop-blur-xl bg-white/80 border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 md:px-12 lg:px-24 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="logo">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium tracking-tight text-[#0A0B10]">LearnHub</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link to="/courses" className="text-slate-600 hover:text-[#002FA7] transition-colors" data-testid="nav-courses">{t("nav.courses")}</Link>
            {user ? (
              <>
                <Link to="/dashboard" className="text-slate-600 hover:text-[#002FA7] transition-colors" data-testid="nav-dashboard">{t("nav.dashboard")}</Link>
                <Button onClick={() => navigate("/dashboard")} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="get-started-btn">
                  {t("nav.dashboard")}
                </Button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-slate-600 hover:text-[#002FA7] transition-colors" data-testid="nav-login">{t("nav.login")}</Link>
                <Button onClick={() => navigate("/register")} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="get-started-btn">
                  {t("nav.getStarted")}
                </Button>
              </>
            )}
            <LanguageSwitcher />
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-24 lg:py-32 px-6 md:px-12 lg:px-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#002FA7]/5 to-transparent" />
        <div className="container mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
          <div>
            <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-4">{t("landing.overline")}</p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl tracking-tight font-medium text-[#0A0B10] mb-6">
              {t("landing.headline")}
            </h1>
            <p className="text-base leading-relaxed text-slate-600 mb-8 max-w-lg">
              {t("landing.subheadline")}
            </p>
            <div className="flex gap-4">
              <Button 
                onClick={() => navigate(user ? "/dashboard" : "/register")} 
                className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm px-8 py-6 text-lg"
                data-testid="hero-cta-btn"
              >
                {t("landing.startLearning")}
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
              <Button 
                variant="outline" 
                onClick={() => navigate("/courses")} 
                className="border-slate-200 hover:bg-slate-50 rounded-sm px-8 py-6 text-lg"
                data-testid="browse-courses-btn"
              >
                {t("landing.browseCourses")}
              </Button>
            </div>
          </div>
          <div className="hidden lg:block">
            <img 
              src="https://images.pexels.com/photos/3137073/pexels-photo-3137073.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" 
              alt="Learning" 
              className="rounded-sm shadow-lg"
            />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 md:px-12 lg:px-24 bg-white">
        <div className="container mx-auto">
          <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-4 text-center">{t("landing.featuresOverline")}</p>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl tracking-tight font-medium text-[#0A0B10] mb-12 text-center">
            {t("landing.featuresTitle")}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: Video, title: t("landing.features.videoCourses"), desc: t("landing.features.videoCoursesDesc") },
              { icon: FileText, title: t("landing.features.quizzes"), desc: t("landing.features.quizzesDesc") },
              { icon: Award, title: t("landing.features.certificates"), desc: t("landing.features.certificatesDesc") },
              { icon: MessageSquare, title: t("landing.features.forums"), desc: t("landing.features.forumsDesc") },
              { icon: Bot, title: t("landing.features.aiAssistant"), desc: t("landing.features.aiAssistantDesc") },
              { icon: Download, title: t("landing.features.materials"), desc: t("landing.features.materialsDesc") },
            ].map((f, i) => (
              <Card key={i} className="bg-white border border-slate-200 rounded-sm hover:-translate-y-1 hover:shadow-md transition-all duration-200" data-testid={`feature-card-${i}`}>
                <CardContent className="p-6">
                  <f.icon className="w-8 h-8 text-[#002FA7] mb-4" />
                  <h3 className="text-xl font-medium text-[#0A0B10] mb-2">{f.title}</h3>
                  <p className="text-slate-600">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Courses Preview */}
      {courses.length > 0 && (
        <section className="py-24 px-6 md:px-12 lg:px-24 bg-[#F4F5F7]">
          <div className="container mx-auto">
            <div className="flex justify-between items-center mb-12">
              <div>
                <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-2">{t("landing.popularCourses")}</p>
                <h2 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
                  {t("landing.startJourney")}
                </h2>
              </div>
              <Button variant="outline" onClick={() => navigate("/courses")} className="border-slate-200 rounded-sm" data-testid="view-all-courses-btn">
                {t("landing.viewAll")} <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="py-12 px-6 md:px-12 lg:px-24 bg-[#0A0B10] text-white">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-6 h-6 text-[#002FA7]" />
            <span className="font-medium">LearnHub</span>
          </div>
          <p className="text-slate-400 text-sm">{t("landing.footer")}</p>
        </div>
      </footer>
    </div>
  );
};

