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

export const QuizPage = () => {
  const { id } = useParams();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchQuiz();
  }, [id]);

  const fetchQuiz = async () => {
    try {
      const { data } = await API.get(`/quizzes/${id}`);
      setQuiz(data);
      setAnswers(new Array(data.questions?.length || 0).fill(-1));
    } catch (e) {
      toast.error(formatError(e));
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (answers.some(a => a === -1)) {
      toast.error(t("toast.answerAll"));
      return;
    }
    
    setSubmitting(true);
    try {
      const { data } = await API.post(`/quizzes/${id}/submit`, { quiz_id: id, answers });
      setResult(data);
      if (data.passed) {
        toast.success(t("toast.passedQuiz"));
      } else {
        toast.error(t("toast.failedQuiz"));
      }
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F5F7]">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F5F7] py-8" data-testid="quiz-page">
      <div className="container mx-auto px-6 md:px-12 lg:px-24 max-w-3xl">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardHeader>
            <CardTitle className="text-xl tracking-tight">{quiz?.title}</CardTitle>
            <CardDescription>Answer all questions to complete the quiz</CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="text-center py-8">
                <div className={`w-24 h-24 rounded-full mx-auto mb-4 flex items-center justify-center ${
                  result.passed ? "bg-green-100" : "bg-red-100"
                }`}>
                  {result.passed ? (
                    <CheckCircle className="w-12 h-12 text-green-600" />
                  ) : (
                    <X className="w-12 h-12 text-red-600" />
                  )}
                </div>
                <h3 className="text-2xl font-medium mb-2">
                  {result.passed ? t("quiz.congratulations") : t("quiz.tryAgain")}
                </h3>
                <p className="text-slate-600 mb-4">
                  Your Score: <span className="font-medium">{result.score}%</span> ({result.correct}/{result.total} correct)
                </p>
                <p className="text-sm text-slate-500 mb-6">
                  Passing Score: {result.passing_score}%
                </p>
                <div className="flex gap-4 justify-center">
                  {result.passed ? (
                    <Button 
                      onClick={() => navigate("/certificates")}
                      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                      data-testid="view-certificate-btn"
                    >
                      <Award className="w-4 h-4 mr-2" /> View Certificate
                    </Button>
                  ) : (
                    <Button 
                      onClick={() => {
                        setResult(null);
                        setAnswers(new Array(quiz.questions?.length || 0).fill(-1));
                      }}
                      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                      data-testid="retry-btn"
                    >
                      Try Again
                    </Button>
                  )}
                  <Button 
                    onClick={() => navigate("/dashboard")}
                    variant="outline"
                    className="rounded-sm"
                    data-testid="back-dashboard-btn"
                  >
                    Back to Dashboard
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {quiz?.questions?.map((q, qIdx) => (
                  <div key={qIdx} className="border border-slate-200 rounded-sm p-4">
                    <p className="font-medium mb-4">
                      {qIdx + 1}. {q.question}
                    </p>
                    <div className="space-y-2">
                      {q.options?.map((opt, oIdx) => (
                        <label 
                          key={oIdx}
                          className={`flex items-center gap-3 p-3 rounded-sm border cursor-pointer transition-colors ${
                            answers[qIdx] === oIdx 
                              ? "border-[#002FA7] bg-[#002FA7]/5" 
                              : "border-slate-200 hover:bg-slate-50"
                          }`}
                          data-testid={`question-${qIdx}-option-${oIdx}`}
                        >
                          <input 
                            type="radio"
                            name={`question-${qIdx}`}
                            checked={answers[qIdx] === oIdx}
                            onChange={() => {
                              const newAnswers = [...answers];
                              newAnswers[qIdx] = oIdx;
                              setAnswers(newAnswers);
                            }}
                            className="w-4 h-4 text-[#002FA7]"
                          />
                          <span>{opt}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                
                <Button 
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm py-6"
                  data-testid="submit-quiz-btn"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : t("quiz.submit")}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

