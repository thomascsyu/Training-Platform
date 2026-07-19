import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft, Award, Bot, Globe, Loader2, Pencil, Plus, Trash2, Upload, Video, X
} from "lucide-react";
import { courseLanguages } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useCurrency } from "@/contexts/CurrencyContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { ThumbnailUpload } from "@/components/ThumbnailUpload";

const createEmptyQuizQuestion = () => ({
  question: "",
  options: ["", "", "", "", ""],
  correct_answer: 0,
});

const parseCsvLine = (line) => {
  const values = [];
  let current = "";
  let inQuotes = false;
  for (let idx = 0; idx < line.length; idx += 1) {
    const char = line[idx];
    if (char === "\"") {
      if (inQuotes && line[idx + 1] === "\"") {
        current += "\"";
        idx += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (char === "," && !inQuotes) {
      values.push(current.trim());
      current = "";
      continue;
    }
    current += char;
  }
  values.push(current.trim());
  return values;
};

const parseQuizCsv = (text) => {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return { questions: [], errors: ["CSV is empty."] };
  }

  const firstRow = parseCsvLine(lines[0]).map((col) => col.toLowerCase());
  const hasHeader = firstRow[0] === "question";
  const dataRows = hasHeader ? lines.slice(1) : lines;
  const questions = [];
  const errors = [];

  dataRows.forEach((line, rowIdx) => {
    const columns = parseCsvLine(line).map((column) => column.replace(/^"|"$/g, "").trim());
    const lineNumber = hasHeader ? rowIdx + 2 : rowIdx + 1;
    if (columns.length < 7) {
      errors.push(`Line ${lineNumber}: expected 7 columns.`);
      return;
    }

    const [question, optionA, optionB, optionC, optionD, optionE, correctAnswerRaw] = columns;
    const options = [optionA, optionB, optionC, optionD, optionE].map((option) => option.trim());
    if (!question?.trim() || options.some((option) => !option)) {
      errors.push(`Line ${lineNumber}: question and options A-E are required.`);
      return;
    }

    const normalizedCorrect = (correctAnswerRaw || "").trim();
    const upperCorrect = normalizedCorrect.toUpperCase();
    let correctAnswerIndex = -1;

    if (["A", "B", "C", "D", "E"].includes(upperCorrect)) {
      correctAnswerIndex = ["A", "B", "C", "D", "E"].indexOf(upperCorrect);
    } else if (/^[0-4]$/.test(normalizedCorrect)) {
      correctAnswerIndex = parseInt(normalizedCorrect, 10);
    } else if (/^[1-5]$/.test(normalizedCorrect)) {
      correctAnswerIndex = parseInt(normalizedCorrect, 10) - 1;
    } else {
      const byOptionText = options.findIndex(
        (option) => option.toLowerCase() === normalizedCorrect.toLowerCase()
      );
      if (byOptionText >= 0) {
        correctAnswerIndex = byOptionText;
      }
    }

    if (correctAnswerIndex < 0 || correctAnswerIndex > 4) {
      errors.push(`Line ${lineNumber}: correct_answer must be A-E, 1-5, 0-4, or option text.`);
      return;
    }

    questions.push({
      question: question.trim(),
      options,
      correct_answer: correctAnswerIndex,
    });
  });

  return { questions, errors };
};

export const AdminCourseEditPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { currency } = useCurrency();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [course, setCourse] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [formData, setFormData] = useState(null);
  const [newLesson, setNewLesson] = useState({
    title: "",
    description: "",
    video_url: "",
    video_type: "youtube",
    order: 0,
  });
  const [addingLesson, setAddingLesson] = useState(false);
  const [editingLessonId, setEditingLessonId] = useState(null);
  const [editingLesson, setEditingLesson] = useState(null);
  const [savingLesson, setSavingLesson] = useState(false);
  const [thumbnailBusy, setThumbnailBusy] = useState(false);
  const [newMaterial, setNewMaterial] = useState({ name: "", url: "" });
  const [quizDraftTitle, setQuizDraftTitle] = useState("");
  const [quizDraftQuestions, setQuizDraftQuestions] = useState([]);
  const [quizQuestionDraft, setQuizQuestionDraft] = useState(createEmptyQuizQuestion);
  const [editingQuizId, setEditingQuizId] = useState(null);
  const [creatingQuiz, setCreatingQuiz] = useState(false);
  const [deletingQuizId, setDeletingQuizId] = useState(null);

  const fetchCourse = useCallback(async () => {
    try {
      const [{ data }, companiesRes] = await Promise.all([
        API.get(`/courses/${id}`),
        API.get("/companies")
      ]);
      setCompanies(companiesRes.data);
      setCourse(data);
      setFormData({
        title: data.title || "",
        description: data.description || "",
        thumbnail_url: data.thumbnail_url || "",
        video_url: data.video_url || "",
        video_type: data.video_type || "youtube",
        price: data.price || 0,
        original_price: data.original_price != null && data.original_price > 0 ? data.original_price : "",
        is_free: data.is_free ?? true,
        course_type: data.course_type || (data.is_free ? "free" : "payment_required"),
        is_private: data.is_private ?? false,
        passing_score: data.passing_score ?? 70,
        auto_issue_certificate: data.auto_issue_certificate ?? true,
        materials: Array.isArray(data.materials) ? data.materials : [],
        ai_assistant_enabled: data.ai_assistant_enabled ?? true,
        ai_assistant_prompt: data.ai_assistant_prompt || "",
        language: data.language || "en",
        category: data.category || "",
        company_ids: data.company_ids || [],
      });
      setQuizDraftTitle((prev) => prev || `Quiz ${(data.quizzes?.length || 0) + 1}`);
      setNewLesson((prev) => ({ ...prev, order: (data.lessons?.length || 0) + 1 }));
    } catch (e) {
      toast.error(formatError(e));
      navigate("/admin/courses");
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    fetchCourse();
  }, [fetchCourse]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const originalPriceValue = parseFloat(formData.original_price);
      const payload = {
        ...formData,
        original_price:
          formData.course_type === "free" || !Number.isFinite(originalPriceValue) || originalPriceValue <= 0
            ? null
            : originalPriceValue,
        materials: (formData.materials || [])
          .map((material) => ({
            name: material.name?.trim() || "",
            url: material.url?.trim() || "",
          }))
          .filter((material) => material.name && material.url),
        ai_assistant_prompt: formData.ai_assistant_prompt?.trim() || null,
      };
      await API.put(`/courses/${id}`, payload);
      toast.success(t("courses.courseUpdated"));
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleCompanyToggle = (companyId, checked) => {
    setFormData((prev) => ({
      ...prev,
      company_ids: checked
        ? [...prev.company_ids, companyId]
        : prev.company_ids.filter((id) => id !== companyId)
    }));
  };

  const handleMaterialChange = (index, field, value) => {
    setFormData((prev) => ({
      ...prev,
      materials: prev.materials.map((material, materialIdx) =>
        materialIdx === index ? { ...material, [field]: value } : material
      ),
    }));
  };

  const handleAddMaterial = () => {
    const name = newMaterial.name.trim();
    const url = newMaterial.url.trim();
    if (!name || !url) {
      return;
    }
    setFormData((prev) => ({
      ...prev,
      materials: [...prev.materials, { name, url }],
    }));
    setNewMaterial({ name: "", url: "" });
  };

  const handleRemoveMaterial = (index) => {
    setFormData((prev) => ({
      ...prev,
      materials: prev.materials.filter((_, materialIdx) => materialIdx !== index),
    }));
  };

  const handleQuizOptionChange = (optionIndex, value) => {
    setQuizQuestionDraft((prev) => {
      const nextOptions = [...prev.options];
      nextOptions[optionIndex] = value;
      return { ...prev, options: nextOptions };
    });
  };

  const handleAddQuizQuestion = () => {
    const question = quizQuestionDraft.question.trim();
    const options = quizQuestionDraft.options.map((option) => option.trim());
    if (!question || options.some((option) => !option)) {
      return;
    }
    setQuizDraftQuestions((prev) => [
      ...prev,
      { question, options, correct_answer: quizQuestionDraft.correct_answer },
    ]);
    setQuizQuestionDraft(createEmptyQuizQuestion());
  };

  const handleRemoveQuizQuestion = (index) => {
    setQuizDraftQuestions((prev) => prev.filter((_, questionIdx) => questionIdx !== index));
  };

  const handleQuizCsvImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const { questions, errors } = parseQuizCsv(text);

      if (questions.length > 0) {
        setQuizDraftQuestions((prev) => [...prev, ...questions]);
        toast.success(`Imported ${questions.length} quiz question${questions.length > 1 ? "s" : ""}.`);
      }

      if (errors.length > 0) {
        const preview = errors.slice(0, 3).join(" ");
        toast.message(`CSV warnings (${errors.length}): ${preview}`);
      }

      if (questions.length === 0 && errors.length > 0) {
        toast.error("No quiz questions were imported from CSV.");
      }
    } catch (e) {
      toast.error("Unable to read CSV file.");
    } finally {
      event.target.value = "";
    }
  };

  const handleCreateQuiz = async () => {
    const title = quizDraftTitle.trim();
    if (!title || quizDraftQuestions.length === 0) {
      return;
    }
    setCreatingQuiz(true);
    try {
      if (editingQuizId) {
        await API.put(`/quizzes/${editingQuizId}`, {
          title,
          questions: quizDraftQuestions,
        });
        toast.success("Quiz updated");
      } else {
        await API.post("/quizzes", {
          course_id: id,
          title,
          questions: quizDraftQuestions,
        });
        toast.success("Quiz created");
      }
      setQuizDraftQuestions([]);
      setQuizQuestionDraft(createEmptyQuizQuestion());
      setEditingQuizId(null);
      setQuizDraftTitle(`Quiz ${(course?.quizzes?.length || 0) + (editingQuizId ? 1 : 2)}`);
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setCreatingQuiz(false);
    }
  };

  const handleStartEditQuiz = async (quiz) => {
    try {
      const { data } = await API.get(`/quizzes/${quiz.id}`);
      setEditingQuizId(quiz.id);
      setQuizDraftTitle(data.title || "");
      setQuizDraftQuestions(Array.isArray(data.questions) ? data.questions : []);
      setQuizQuestionDraft(createEmptyQuizQuestion());
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const handleCancelEditQuiz = () => {
    setEditingQuizId(null);
    setQuizDraftQuestions([]);
    setQuizQuestionDraft(createEmptyQuizQuestion());
    setQuizDraftTitle(`Quiz ${(course?.quizzes?.length || 0) + 1}`);
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!window.confirm("Delete this quiz? Student attempts for this quiz will also be removed.")) return;
    setDeletingQuizId(quizId);
    try {
      await API.delete(`/quizzes/${quizId}`);
      toast.success("Quiz deleted");
      if (editingQuizId === quizId) {
        handleCancelEditQuiz();
      }
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setDeletingQuizId(null);
    }
  };

  const handleAddLesson = async () => {
    if (!newLesson.title.trim()) return;
    setAddingLesson(true);
    try {
      await API.post("/lessons", { ...newLesson, course_id: id });
      toast.success(t("courses.lessonAdded"));
      setNewLesson({
        title: "",
        description: "",
        video_url: "",
        video_type: "youtube",
        order: (course?.lessons?.length || 0) + 2,
      });
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setAddingLesson(false);
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    if (!window.confirm(t("courses.confirmDeleteLesson"))) return;
    try {
      await API.delete(`/lessons/${lessonId}`);
      toast.success(t("courses.lessonDeleted"));
      if (editingLessonId === lessonId) {
        setEditingLessonId(null);
        setEditingLesson(null);
      }
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const handleStartEditLesson = (lesson) => {
    setEditingLessonId(lesson.id);
    setEditingLesson({
      title: lesson.title || "",
      description: lesson.description || "",
      video_url: lesson.video_url || "",
      video_type: lesson.video_type || "youtube",
      order: lesson.order ?? 0,
    });
  };

  const handleCancelEditLesson = () => {
    setEditingLessonId(null);
    setEditingLesson(null);
  };

  const handleSaveLesson = async () => {
    if (!editingLesson?.title?.trim()) return;
    setSavingLesson(true);
    try {
      await API.put(`/lessons/${editingLessonId}`, editingLesson);
      toast.success(t("courses.lessonUpdated"));
      setEditingLessonId(null);
      setEditingLesson(null);
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSavingLesson(false);
    }
  };

  if (loading || !formData) {
    return (
      <DashboardLayout>
        <div className="flex justify-center py-24">
          <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl" data-testid="admin-course-edit-page">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="outline"
            onClick={() => navigate("/admin/courses")}
            disabled={thumbnailBusy}
            className="rounded-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> {t("courses.backToCourses")}
          </Button>
          <h1 className="text-2xl font-medium text-[#0A0B10]">{t("courses.editCourse")}</h1>
        </div>

        <Card className="card-swiss mb-6">
          <CardHeader>
            <CardTitle className="text-lg">{formData.title || t("courses.createNew")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t("courses.title")}</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label>{t("courses.description")}</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="rounded-sm"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("courses.language")}</Label>
                <Select value={formData.language} onValueChange={(v) => setFormData({ ...formData, language: v })}>
                  <SelectTrigger className="rounded-sm">
                    <Globe className="w-4 h-4 mr-2" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {courseLanguages.map((lang) => (
                      <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>{t("courses.category")}</Label>
                <Input
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="rounded-sm"
                  placeholder={t("courses.categoryPlaceholder")}
                />
              </div>
            </div>
            <ThumbnailUpload
              value={formData.thumbnail_url}
              courseId={id}
              onBusyChange={setThumbnailBusy}
              onChange={(thumbnail_url) => {
                setFormData((prev) => (prev ? { ...prev, thumbnail_url } : prev));
                setCourse((prev) => (prev ? { ...prev, thumbnail_url } : prev));
              }}
              testId="course-edit-thumbnail-upload"
            />
            <div className="space-y-2">
              <Label>{t("courses.videoUrl")}</Label>
              <Input
                value={formData.video_url}
                onChange={(e) => setFormData({ ...formData, video_url: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("courses.price")} ({currency.toUpperCase()})</Label>
                <Input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                  className="rounded-sm"
                  disabled={formData.course_type === "free"}
                  data-testid="course-edit-price-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t("courses.specialOfferOptional")}</Label>
                <Input
                  type="number"
                  value={formData.original_price}
                  onChange={(e) => setFormData({ ...formData, original_price: e.target.value })}
                  className="rounded-sm"
                  disabled={formData.course_type === "free"}
                  placeholder={t("courses.specialOfferPlaceholder")}
                  min={0}
                  step="0.01"
                  data-testid="course-edit-special-offer-input"
                />
                <p className="text-xs text-slate-500">{t("courses.specialOfferHint")}</p>
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("courses.passingScore")}</Label>
              <Input
                type="number"
                value={formData.passing_score}
                onChange={(e) => setFormData({ ...formData, passing_score: parseInt(e.target.value) || 70 })}
                className="rounded-sm"
                min={0}
                max={100}
              />
            </div>
            <div className="space-y-2 border border-slate-200 rounded-sm p-4">
              <div className="flex items-center gap-2">
                <Switch
                  checked={formData.auto_issue_certificate}
                  onCheckedChange={(v) => setFormData({ ...formData, auto_issue_certificate: v })}
                  data-testid="course-auto-issue-certificate-switch"
                />
                <Label>{t("courses.autoIssueCertificate")}</Label>
              </div>
              <p className="text-xs text-slate-500">{t("courses.autoIssueCertificateHint")}</p>
              <Button
                type="button"
                variant="outline"
                className="rounded-sm mt-2"
                onClick={() => navigate(`/admin/certificate-builder?course_id=${id}`)}
                data-testid="course-certificate-builder-btn"
              >
                <Award className="w-4 h-4 mr-2" />
                {t("certificateBuilder.openFromCourse")}
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("courses.courseType")}</Label>
                <Select
                  value={formData.course_type}
                  onValueChange={(v) => setFormData({
                    ...formData,
                    course_type: v,
                    is_free: v === "free",
                    price: v === "free" ? 0 : formData.price,
                    original_price: v === "free" ? "" : formData.original_price,
                  })}
                >
                  <SelectTrigger className="rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="free">{t("courses.free")}</SelectItem>
                    <SelectItem value="payment_required">{t("courses.paymentRequired")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 md:pt-6">
                <Switch
                  checked={formData.is_private}
                  onCheckedChange={(v) => setFormData({ ...formData, is_private: v })}
                />
                <Label>{t("courses.privateCourse")}</Label>
              </div>
            </div>
            <div className="space-y-3 border border-slate-200 rounded-sm p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-[#0A0B10]">
                <Bot className="w-4 h-4 text-[#002FA7]" />
                AI Assistant
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={formData.ai_assistant_enabled}
                  onCheckedChange={(value) => setFormData({ ...formData, ai_assistant_enabled: value })}
                />
                <Label>Enable AI assistant for this course</Label>
              </div>
              <Textarea
                value={formData.ai_assistant_prompt}
                onChange={(e) => setFormData({ ...formData, ai_assistant_prompt: e.target.value })}
                className="rounded-sm"
                rows={3}
                placeholder="Optional instructions for the assistant (e.g. keep answers concise, focus on ISO 9001 examples)."
                disabled={!formData.ai_assistant_enabled}
              />
            </div>
            <div className="space-y-3">
              <Label>Downloadable Materials</Label>
              {formData.materials?.length > 0 ? (
                <div className="space-y-2">
                  {formData.materials.map((material, idx) => (
                    <div key={`${material.name}-${idx}`} className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-2">
                      <Input
                        value={material.name || ""}
                        onChange={(e) => handleMaterialChange(idx, "name", e.target.value)}
                        placeholder="Material name"
                        className="rounded-sm"
                      />
                      <Input
                        value={material.url || ""}
                        onChange={(e) => handleMaterialChange(idx, "url", e.target.value)}
                        placeholder="https://..."
                        className="rounded-sm"
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        className="rounded-sm text-red-600"
                        onClick={() => handleRemoveMaterial(idx)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No downloadable materials added yet.</p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-2">
                <Input
                  value={newMaterial.name}
                  onChange={(e) => setNewMaterial((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Material name"
                  className="rounded-sm"
                />
                <Input
                  value={newMaterial.url}
                  onChange={(e) => setNewMaterial((prev) => ({ ...prev, url: e.target.value }))}
                  placeholder="https://..."
                  className="rounded-sm"
                />
                <Button
                  variant="outline"
                  className="rounded-sm"
                  onClick={handleAddMaterial}
                  disabled={!newMaterial.name.trim() || !newMaterial.url.trim()}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add
                </Button>
              </div>
              <p className="text-xs text-slate-500">Students will see these links under the Materials tab.</p>
            </div>
            <div className="space-y-2">
              <Label>Assigned Companies</Label>
              <div className="border border-slate-200 rounded-sm divide-y divide-slate-100" data-testid="course-edit-company-assignment">
                {companies.length > 0 ? (
                  companies.map((company) => (
                    <label
                      key={company.id}
                      className="flex items-start gap-3 p-3 hover:bg-slate-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={formData.company_ids.includes(company.id)}
                        onChange={(e) => handleCompanyToggle(company.id, e.target.checked)}
                        className="mt-1 w-4 h-4"
                        data-testid={`course-edit-company-${company.id}`}
                      />
                      <span>
                        <span className="block text-sm font-medium">{company.name}</span>
                        {company.description && (
                          <span className="block text-xs text-slate-500">{company.description}</span>
                        )}
                      </span>
                    </label>
                  ))
                ) : (
                  <p className="p-3 text-sm text-slate-500">Create companies before assigning courses to them.</p>
                )}
              </div>
              <p className="text-xs text-slate-500">
                Saving assigned companies auto-enrolls all student users in those companies.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="card-swiss mb-6">
          <CardHeader>
            <CardTitle className="text-lg">{t("courses.lessons")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {course.lessons?.length > 0 ? (
              <div className="space-y-2">
                {course.lessons.map((lesson, idx) => (
                  <div
                    key={lesson.id}
                    className="p-3 border border-slate-200 rounded-sm"
                  >
                    {editingLessonId === lesson.id ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-[#002FA7]">
                            {t("courses.editLesson")} #{idx + 1}
                          </p>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-sm h-8 w-8"
                            onClick={handleCancelEditLesson}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                        <Input
                          placeholder={t("courses.lessonTitle")}
                          value={editingLesson.title}
                          onChange={(e) => setEditingLesson({ ...editingLesson, title: e.target.value })}
                          className="rounded-sm"
                        />
                        <Textarea
                          placeholder={t("courses.lessonDescription")}
                          value={editingLesson.description}
                          onChange={(e) => setEditingLesson({ ...editingLesson, description: e.target.value })}
                          className="rounded-sm"
                          rows={2}
                        />
                        <Input
                          placeholder={t("courses.videoUrl")}
                          value={editingLesson.video_url}
                          onChange={(e) => setEditingLesson({ ...editingLesson, video_url: e.target.value })}
                          className="rounded-sm"
                        />
                        <Select
                          value={editingLesson.video_type}
                          onValueChange={(v) => setEditingLesson({ ...editingLesson, video_type: v })}
                        >
                          <SelectTrigger className="rounded-sm">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="youtube">{t("common.youtube")}</SelectItem>
                            <SelectItem value="vimeo">{t("common.vimeo")}</SelectItem>
                          </SelectContent>
                        </Select>
                        <div className="flex gap-2">
                          <Button
                            onClick={handleSaveLesson}
                            disabled={savingLesson || !editingLesson.title.trim()}
                            className="flex-1 btn-primary"
                          >
                            {savingLesson ? <Loader2 className="w-4 h-4 animate-spin" /> : t("courses.saveLesson")}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={handleCancelEditLesson}
                            className="rounded-sm"
                          >
                            {t("common.cancel")}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 bg-[#002FA7]/10 text-[#002FA7] rounded-sm flex items-center justify-center text-sm font-medium shrink-0">
                          {idx + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{lesson.title}</p>
                          {lesson.video_url && (
                            <Badge variant="secondary" className="text-xs mt-1">
                              <Video className="w-3 h-3 mr-1" /> {t("courses.hasVideo")}
                            </Badge>
                          )}
                        </div>
                        <Button
                          variant="outline"
                          size="icon"
                          className="rounded-sm"
                          onClick={() => handleStartEditLesson(lesson)}
                          data-testid={`edit-lesson-${lesson.id}`}
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          className="rounded-sm text-red-600"
                          onClick={() => handleDeleteLesson(lesson.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">{t("courses.noLessons")}</p>
            )}

            <Separator />

            <div className="space-y-3">
              <p className="text-sm font-medium">{t("courses.addLesson")}</p>
              <Input
                placeholder={t("courses.lessonTitle")}
                value={newLesson.title}
                onChange={(e) => setNewLesson({ ...newLesson, title: e.target.value })}
                className="rounded-sm"
              />
              <Textarea
                placeholder={t("courses.lessonDescription")}
                value={newLesson.description}
                onChange={(e) => setNewLesson({ ...newLesson, description: e.target.value })}
                className="rounded-sm"
                rows={2}
              />
              <Input
                placeholder={t("courses.videoUrl")}
                value={newLesson.video_url}
                onChange={(e) => setNewLesson({ ...newLesson, video_url: e.target.value })}
                className="rounded-sm"
              />
              <Button
                onClick={handleAddLesson}
                disabled={addingLesson || !newLesson.title.trim()}
                variant="outline"
                className="rounded-sm"
              >
                {addingLesson ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                  <><Plus className="w-4 h-4 mr-2" />{t("courses.addLesson")}</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="card-swiss mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Quiz Builder</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Existing Quizzes</Label>
              {course.quizzes?.length > 0 ? (
                <div className="space-y-2">
                  {course.quizzes.map((quiz, idx) => (
                    <div key={quiz.id} className="p-3 border border-slate-200 rounded-sm flex items-center gap-3">
                      <p className="font-medium flex-1">{idx + 1}. {quiz.title}</p>
                      <Button
                        variant="outline"
                        size="icon"
                        className="rounded-sm"
                        onClick={() => handleStartEditQuiz(quiz)}
                        data-testid={`edit-quiz-${quiz.id}`}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        className="rounded-sm text-red-600"
                        onClick={() => handleDeleteQuiz(quiz.id)}
                        disabled={deletingQuizId === quiz.id}
                        data-testid={`delete-quiz-${quiz.id}`}
                      >
                        {deletingQuizId === quiz.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No quizzes added yet.</p>
              )}
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium">
                  {editingQuizId ? "Edit multiple-choice quiz (A-E)" : "Create multiple-choice quiz (A-E)"}
                </p>
                {editingQuizId && (
                  <Button variant="ghost" className="rounded-sm" onClick={handleCancelEditQuiz}>
                    Cancel edit
                  </Button>
                )}
              </div>
              <Input
                value={quizDraftTitle}
                onChange={(e) => setQuizDraftTitle(e.target.value)}
                placeholder="Quiz title"
                className="rounded-sm"
              />

              <div className="space-y-3 border border-slate-200 rounded-sm p-3">
                <div className="space-y-1">
                  <Label htmlFor="quiz-csv-upload">Import Questions & Answers (CSV)</Label>
                  <p className="text-xs text-slate-500">
                    Required columns: question, option_a, option_b, option_c, option_d, option_e, correct_answer
                  </p>
                </div>
                <Input
                  id="quiz-csv-upload"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleQuizCsvImport}
                  className="rounded-sm"
                  data-testid="quiz-csv-upload"
                />
                <p className="text-xs text-slate-500">
                  correct_answer accepts A-E, 1-5, 0-4, or the exact option text.
                </p>
                <div className="bg-slate-50 border border-slate-200 rounded-sm p-3">
                  <p className="text-xs font-medium text-slate-700 mb-1">CSV format example</p>
                  <pre className="text-xs text-slate-600 whitespace-pre-wrap">
{`question,option_a,option_b,option_c,option_d,option_e,correct_answer
"What does PDCA stand for?","Plan","Do","Check","Act","Analyze","A"
"ISO 9001 focuses on?","Quality management","Food safety","Cybersecurity","Accounting","Marketing","Quality management"`}
                  </pre>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Upload className="w-3 h-3" />
                  Import appends questions to the current draft quiz.
                </div>
              </div>

              <div className="space-y-2 border border-slate-200 rounded-sm p-3">
                <Label>Question</Label>
                <Textarea
                  value={quizQuestionDraft.question}
                  onChange={(e) => setQuizQuestionDraft((prev) => ({ ...prev, question: e.target.value }))}
                  className="rounded-sm"
                  rows={2}
                  placeholder="Enter a question"
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {["A", "B", "C", "D", "E"].map((optionLabel, optionIdx) => (
                    <Input
                      key={optionLabel}
                      value={quizQuestionDraft.options[optionIdx]}
                      onChange={(e) => handleQuizOptionChange(optionIdx, e.target.value)}
                      placeholder={`Option ${optionLabel}`}
                      className="rounded-sm"
                    />
                  ))}
                </div>
                <div className="space-y-2">
                  <Label>Correct Answer</Label>
                  <Select
                    value={String(quizQuestionDraft.correct_answer)}
                    onValueChange={(value) => (
                      setQuizQuestionDraft((prev) => ({ ...prev, correct_answer: parseInt(value, 10) }))
                    )}
                  >
                    <SelectTrigger className="rounded-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["A", "B", "C", "D", "E"].map((optionLabel, optionIdx) => (
                        <SelectItem key={optionLabel} value={String(optionIdx)}>
                          {optionLabel}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  variant="outline"
                  className="rounded-sm"
                  onClick={handleAddQuizQuestion}
                  disabled={
                    !quizQuestionDraft.question.trim()
                    || quizQuestionDraft.options.some((option) => !option.trim())
                  }
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Question
                </Button>
              </div>

              {quizDraftQuestions.length > 0 && (
                <div className="space-y-2">
                  <Label>Questions in Draft Quiz</Label>
                  {quizDraftQuestions.map((question, questionIdx) => (
                    <div key={`draft-question-${questionIdx}`} className="p-3 border border-slate-200 rounded-sm space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">
                          {questionIdx + 1}. {question.question}
                        </p>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="rounded-sm h-8 w-8 text-red-600"
                          onClick={() => handleRemoveQuizQuestion(questionIdx)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                      <div className="text-xs text-slate-600 grid grid-cols-1 md:grid-cols-2 gap-1">
                        {question.options.map((option, optionIdx) => (
                          <span key={`question-${questionIdx}-option-${optionIdx}`}>
                            {["A", "B", "C", "D", "E"][optionIdx]}: {option}
                          </span>
                        ))}
                      </div>
                      <p className="text-xs text-[#002FA7]">
                        Correct answer: {["A", "B", "C", "D", "E"][question.correct_answer]}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <Button
                onClick={handleCreateQuiz}
                disabled={creatingQuiz || !quizDraftTitle.trim() || quizDraftQuestions.length === 0}
                className="btn-primary"
              >
                {creatingQuiz ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : editingQuizId ? (
                  "Save Quiz"
                ) : (
                  "Create Quiz"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Button
          onClick={handleSave}
          disabled={saving || thumbnailBusy || !formData.title}
          className="w-full btn-primary"
          data-testid="course-save-changes"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("courses.saveChanges")}
        </Button>
      </div>
    </DashboardLayout>
  );
};
