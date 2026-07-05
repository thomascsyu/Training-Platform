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
  ArrowLeft, Globe, Loader2, Pencil, Plus, Trash2, Video, X
} from "lucide-react";
import { courseLanguages } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { ThumbnailUpload } from "@/components/ThumbnailUpload";

export const AdminCourseEditPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [course, setCourse] = useState(null);
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

  const fetchCourse = useCallback(async () => {
    try {
      const { data } = await API.get(`/courses/${id}`);
      setCourse(data);
      setFormData({
        title: data.title || "",
        description: data.description || "",
        thumbnail_url: data.thumbnail_url || "",
        video_url: data.video_url || "",
        video_type: data.video_type || "youtube",
        price: data.price || 0,
        is_free: data.is_free ?? true,
        is_private: data.is_private ?? false,
        passing_score: data.passing_score ?? 70,
        language: data.language || "en",
        category: data.category || "",
      });
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
      await API.put(`/courses/${id}`, formData);
      toast.success(t("courses.courseUpdated"));
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
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
          <Button variant="outline" onClick={() => navigate("/admin/courses")} className="rounded-sm">
            <ArrowLeft className="w-4 h-4 mr-2" /> {t("courses.backToCourses")}
          </Button>
          <h1 className="text-2xl font-medium text-[#0A0B10]">{t("courses.editCourse")}</h1>
        </div>

        <Card className="bg-white border border-slate-200 rounded-sm mb-6">
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
              onChange={(url) => setFormData({ ...formData, thumbnail_url: url })}
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
                <Label>{t("courses.price")}</Label>
                <Input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                  className="rounded-sm"
                  disabled={formData.is_free}
                />
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
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  checked={formData.is_free}
                  onCheckedChange={(v) => setFormData({ ...formData, is_free: v, price: v ? 0 : formData.price })}
                />
                <Label>{t("courses.freeCourse")}</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={formData.is_private}
                  onCheckedChange={(v) => setFormData({ ...formData, is_private: v })}
                />
                <Label>{t("courses.privateCourse")}</Label>
              </div>
            </div>
            <Button
              onClick={handleSave}
              disabled={saving || !formData.title}
              className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("courses.saveChanges")}
            </Button>
          </CardContent>
        </Card>

        <Card className="bg-white border border-slate-200 rounded-sm">
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
                            className="flex-1 bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
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
      </div>
    </DashboardLayout>
  );
};
