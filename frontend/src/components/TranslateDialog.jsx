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

export const TranslateDialog = ({ courseId, courseTitle, onTranslated }) => {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [translating, setTranslating] = useState(false);
  const [result, setResult] = useState(null);

  const handleTranslate = async () => {
    if (!selectedLanguage) {
      toast.error("Please select a target language");
      return;
    }
    
    setTranslating(true);
    setResult(null);
    
    try {
      const { data } = await API.post(`/courses/${courseId}/create-translation?target_language=${selectedLanguage}`);
      setResult(data);
      toast.success(`Course translated to ${data.language_name}!`);
      if (onTranslated) onTranslated();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setTranslating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button 
          variant="outline" 
          size="icon" 
          className="rounded-sm"
          title="Auto-translate to other languages"
          data-testid={`translate-course-${courseId}`}
        >
          <Languages className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Languages className="w-5 h-5 text-[#002FA7]" />
            AI Auto-Translate
          </DialogTitle>
          <DialogDescription>
            Create a Hong Kong Traditional Chinese version of "{courseTitle}" using Deepseek AI (e.g. Audit → 審核, Quality → 品質)
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {!result ? (
            <>
              <div className="space-y-2">
                <Label>Target Language</Label>
                <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                  <SelectTrigger className="rounded-sm" data-testid="translate-language-select">
                    <SelectValue placeholder="Select language..." />
                  </SelectTrigger>
                  <SelectContent>
                    {courseLanguages.map(lang => (
                      <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="bg-slate-50 border border-slate-200 rounded-sm p-4">
                <h4 className="font-medium text-sm mb-2">What will be translated:</h4>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    Course title & description
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    All lesson titles & descriptions
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-slate-400" />
                    Quiz questions (separate action)
                  </li>
                </ul>
              </div>
              
              <Button 
                onClick={handleTranslate}
                disabled={translating || !selectedLanguage}
                className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="start-translation-btn"
              >
                {translating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Translating with AI...
                  </>
                ) : (
                  <>
                    <Bot className="w-4 h-4 mr-2" />
                    Create Translated Course
                  </>
                )}
              </Button>
            </>
          ) : (
            <div className="text-center py-4">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Translation Complete!</h3>
              <p className="text-slate-600 mb-2">
                New course created in {result.language_name}
              </p>
              <p className="text-sm text-slate-500 mb-4">
                "{result.title}"
              </p>
              <div className="flex gap-2 justify-center">
                <Button 
                  onClick={() => { setResult(null); setSelectedLanguage(""); }}
                  variant="outline"
                  className="rounded-sm"
                >
                  Translate to Another
                </Button>
                <Button 
                  onClick={() => setOpen(false)}
                  className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                >
                  Done
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

