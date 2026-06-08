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

// ============ COURSE CARD ============
export const CourseCard = ({ course, enrolled = false, showProgress = false, progress = 0 }) => {
  const navigate = useNavigate();
  
  // Get language display name
  const getLanguageDisplay = (langCode) => {
    const langMap = {
      "en": "EN",
      "zh-TW": "繁中",
      "zh-CN": "简中",
      "ja": "日本",
      "ko": "한국"
    };
    return langMap[langCode] || langCode;
  };
  
  return (
    <Card 
      className="bg-white border border-slate-200 rounded-sm hover:-translate-y-1 hover:shadow-md transition-all duration-200 cursor-pointer overflow-hidden"
      onClick={() => navigate(`/courses/${course.id}`)}
      data-testid={`course-card-${course.id}`}
    >
      <div className="aspect-video bg-slate-100 relative overflow-hidden">
        {course.thumbnail_url ? (
          <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5">
            <BookOpen className="w-12 h-12 text-[#002FA7]/40" />
          </div>
        )}
        <div className="absolute top-2 left-2 flex gap-1">
          {course.language && (
            <Badge className="bg-[#002FA7] text-white rounded-sm text-xs">
              <Globe className="w-3 h-3 mr-1" />
              {getLanguageDisplay(course.language)}
            </Badge>
          )}
        </div>
        {course.is_private && (
          <Badge className="absolute top-2 right-2 bg-slate-800 text-white rounded-sm">
            <Lock className="w-3 h-3 mr-1" /> Private
          </Badge>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="text-lg font-medium text-[#0A0B10] mb-2 line-clamp-1">{course.title}</h3>
        <p className="text-sm text-slate-600 line-clamp-2 mb-3">{course.description}</p>
        <div className="flex items-center justify-between">
          {course.is_free ? (
            <Badge variant="secondary" className="bg-green-100 text-green-700 rounded-sm">Free</Badge>
          ) : (
            <span className="font-medium text-[#002FA7]">${course.price?.toFixed(2)}</span>
          )}
          {showProgress && (
            <div className="flex items-center gap-2">
              <Progress value={progress} className="w-20 h-2" />
              <span className="text-xs text-slate-500">{progress}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

