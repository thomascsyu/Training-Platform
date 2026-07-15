import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, Loader2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { CertificateBackgroundUpload } from "@/components/certificates/CertificateBackgroundUpload";
import { CERTIFICATE_BACKGROUNDS, backgroundLabel } from "@/lib/certificateBackgrounds";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

const DEFAULT_BODY =
  "This certifies that {{recipient_name}} has successfully completed {{course_title}} on {{completion_date}}.";

const PLACEHOLDERS = [
  "{{recipient_name}}",
  "{{course_title}}",
  "{{completion_date}}",
  "{{score}}",
  "{{certificate_id}}",
];

const emptyForm = () => ({
  scope: "all",
  course_id: "",
  template_id: null,
  name: "",
  orientation: "landscape",
  background: "plain",
  background_image_url: null,
  body_text: DEFAULT_BODY,
  primary_color: "#002fa7",
  secondary_color: "#0a0b10",
  is_default: true,
});

export const CertificateBuilderPage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState("configure");
  const [form, setForm] = useState(emptyForm);
  const [courses, setCourses] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const bodyRef = useRef(null);
  const previewTimer = useRef(null);
  const dirtyRef = useRef(false);

  const courseTitle = useMemo(() => {
    if (form.scope !== "course" || !form.course_id) return "Sample Course";
    return courses.find((c) => c.id === form.course_id)?.title || "Sample Course";
  }, [form.scope, form.course_id, courses]);

  const isValid = Boolean(
    form.name.trim() &&
      form.body_text.trim() &&
      (form.scope === "all" || form.course_id)
  );

  const markDirty = () => {
    dirtyRef.current = true;
  };

  const loadInitial = useCallback(async () => {
    setLoading(true);
    try {
      const [coursesRes, templatesRes] = await Promise.all([
        API.get("/courses"),
        API.get("/certificate-templates"),
      ]);
      const courseList = coursesRes.data || [];
      const templateList = templatesRes.data || [];
      setCourses(courseList);
      setTemplates(templateList);

      const next = emptyForm();
      const qCourse = searchParams.get("course_id");
      const qTemplate = searchParams.get("template_id");

      if (qTemplate) {
        const existing = templateList.find((tpl) => tpl.id === qTemplate);
        if (existing) {
          next.template_id = existing.id;
          next.name = existing.name || "";
          next.orientation = existing.orientation || "landscape";
          next.background = existing.background || "plain";
          next.background_image_url = existing.background_image_url || null;
          next.body_text = existing.body_text || DEFAULT_BODY;
          next.primary_color = existing.primary_color || "#002fa7";
          next.secondary_color = existing.secondary_color || "#0a0b10";
          next.is_default = Boolean(existing.is_default);
          if (existing.course_id) {
            next.scope = "course";
            next.course_id = existing.course_id;
          } else {
            next.scope = "all";
          }
        }
      } else if (qCourse) {
        next.scope = "course";
        next.course_id = qCourse;
        const linked = templateList.find((tpl) => tpl.course_id === qCourse);
        if (linked) {
          next.template_id = linked.id;
          next.name = linked.name || "";
          next.orientation = linked.orientation || "landscape";
          next.background = linked.background || "plain";
          next.background_image_url = linked.background_image_url || null;
          next.body_text = linked.body_text || DEFAULT_BODY;
          next.primary_color = linked.primary_color || "#002fa7";
          next.secondary_color = linked.secondary_color || "#0a0b10";
          next.is_default = false;
        } else {
          const course = courseList.find((c) => c.id === qCourse);
          next.name = course ? `${course.title} Certificate` : "Course Certificate";
          next.is_default = false;
        }
      }

      setForm(next);
    } catch (error) {
      toast.error(formatError(error));
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  const refreshPreview = useCallback(
    async (current) => {
      if (!current.body_text?.trim()) {
        setPreviewHtml("");
        return;
      }
      setPreviewLoading(true);
      try {
        const { data } = await API.post(
          "/certificates/preview",
          {
            course_id: current.scope === "course" && current.course_id ? current.course_id : undefined,
            course_title:
              current.scope === "course" && current.course_id ? undefined : courseTitle,
            user_name: "Jane Doe",
            score: 92,
            primary_color: current.primary_color,
            secondary_color: current.secondary_color,
            background: current.background,
            background_image_url: current.background_image_url || undefined,
            orientation: current.orientation,
            body_text: current.body_text,
            format: "html",
          },
          { responseType: "text" }
        );
        setPreviewHtml(typeof data === "string" ? data : String(data));
      } catch (error) {
        // Keep last good preview; surface soft error.
        console.warn("Certificate preview failed", error);
      } finally {
        setPreviewLoading(false);
      }
    },
    [courseTitle]
  );

  useEffect(() => {
    if (loading) return;
    if (previewTimer.current) clearTimeout(previewTimer.current);
    previewTimer.current = setTimeout(() => {
      refreshPreview(form);
    }, 300);
    return () => {
      if (previewTimer.current) clearTimeout(previewTimer.current);
    };
  }, [form, loading, refreshPreview]);

  const updateForm = (patch) => {
    markDirty();
    setForm((prev) => ({ ...prev, ...patch }));
  };

  const insertPlaceholder = (token) => {
    const el = bodyRef.current;
    if (!el) {
      updateForm({ body_text: `${form.body_text}${token}` });
      return;
    }
    const start = el.selectionStart ?? form.body_text.length;
    const end = el.selectionEnd ?? start;
    const next =
      form.body_text.slice(0, start) + token + form.body_text.slice(end);
    updateForm({ body_text: next });
    requestAnimationFrame(() => {
      el.focus();
      const pos = start + token.length;
      el.setSelectionRange(pos, pos);
    });
  };

  const handleStartFromTemplate = (templateId) => {
    if (templateId === "__none__") return;
    const existing = templates.find((tpl) => tpl.id === templateId);
    if (!existing) return;
    updateForm({
      name: form.name || existing.name,
      orientation: existing.orientation || "landscape",
      background: existing.background || "plain",
      background_image_url: existing.background_image_url || null,
      body_text: existing.body_text || DEFAULT_BODY,
      primary_color: existing.primary_color || "#002fa7",
      secondary_color: existing.secondary_color || "#0a0b10",
    });
  };

  const handleCancel = () => {
    if (dirtyRef.current && !window.confirm(t("certificateBuilder.discardConfirm"))) {
      return;
    }
    navigate("/admin/certificates?tab=templates");
  };

  const handleSave = async () => {
    if (!isValid) {
      toast.error(t("certificateBuilder.validationError"));
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        primary_color: form.primary_color,
        secondary_color: form.secondary_color,
        background: form.background,
        background_image_url: form.background_image_url,
        orientation: form.orientation,
        body_text: form.body_text.trim(),
        course_id: form.scope === "course" ? form.course_id : null,
        is_default: form.scope === "all",
      };

      if (form.template_id) {
        await API.put(`/certificate-templates/${form.template_id}`, payload);
      } else if (form.scope === "course") {
        const existingForCourse = templates.find(
          (tpl) => tpl.course_id === form.course_id
        );
        if (existingForCourse) {
          await API.put(`/certificate-templates/${existingForCourse.id}`, payload);
        } else {
          await API.post("/certificate-templates", payload);
        }
      } else {
        const defaultTpl = templates.find((tpl) => tpl.is_default && !tpl.course_id);
        if (defaultTpl && form.scope === "all") {
          await API.put(`/certificate-templates/${defaultTpl.id}`, {
            ...payload,
            is_default: true,
          });
        } else {
          await API.post("/certificate-templates", {
            ...payload,
            is_default: true,
          });
        }
      }

      toast.success(t("certificateBuilder.saved"));
      dirtyRef.current = false;
      if (form.scope === "course" && form.course_id) {
        navigate(`/admin/courses/${form.course_id}/edit`);
      } else {
        navigate("/admin/certificates?tab=templates");
      }
    } catch (error) {
      toast.error(formatError(error));
    } finally {
      setSaving(false);
    }
  };

  const previewFrameClass =
    form.orientation === "portrait"
      ? "w-full max-w-[320px] aspect-[8.5/11]"
      : "w-full max-w-[520px] aspect-[11/8.5]";

  const reviewFrameClass =
    form.orientation === "portrait"
      ? "w-full max-w-[480px] aspect-[8.5/11]"
      : "w-full max-w-[900px] aspect-[11/8.5]";

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="certificate-builder-page">
        <PageHeader
          title={t("certificateBuilder.title")}
          description={t("certificateBuilder.description")}
        >
          <Button variant="outline" className="rounded-sm" onClick={handleCancel}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t("common.cancel")}
          </Button>
        </PageHeader>

        {loading ? (
          <div className="flex items-center gap-2 text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            {t("common.loading")}
          </div>
        ) : step === "configure" ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <Card className="card-swiss p-6 space-y-5">
              <div className="space-y-2">
                <Label>{t("certificateBuilder.scope")}</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={form.scope === "all" ? "default" : "outline"}
                    className="rounded-sm"
                    onClick={() =>
                      updateForm({ scope: "all", course_id: "", is_default: true })
                    }
                    data-testid="builder-scope-all"
                  >
                    {t("certificateBuilder.scopeAll")}
                  </Button>
                  <Button
                    type="button"
                    variant={form.scope === "course" ? "default" : "outline"}
                    className="rounded-sm"
                    onClick={() => updateForm({ scope: "course", is_default: false })}
                    data-testid="builder-scope-course"
                  >
                    {t("certificateBuilder.scopeCourse")}
                  </Button>
                </div>
              </div>

              {form.scope === "course" && (
                <div className="space-y-2">
                  <Label>{t("certificateBuilder.course")}</Label>
                  <Select
                    value={form.course_id || undefined}
                    onValueChange={(value) => updateForm({ course_id: value })}
                  >
                    <SelectTrigger
                      className="rounded-sm"
                      data-testid="builder-course-select"
                    >
                      <SelectValue placeholder={t("adminCertificates.selectCourse")} />
                    </SelectTrigger>
                    <SelectContent>
                      {courses.map((course) => (
                        <SelectItem key={course.id} value={course.id}>
                          {course.title}
                          {course.is_private ? " (private)" : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="space-y-2">
                <Label>{t("certificateBuilder.startFrom")}</Label>
                <Select onValueChange={handleStartFromTemplate}>
                  <SelectTrigger className="rounded-sm" data-testid="builder-start-from">
                    <SelectValue placeholder={t("certificateBuilder.startFromHint")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">
                      {t("certificateBuilder.startFromHint")}
                    </SelectItem>
                    {templates.map((tpl) => (
                      <SelectItem key={tpl.id} value={tpl.id}>
                        {tpl.name}
                        {tpl.is_default ? ` (${t("certificateTemplates.default")})` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{t("certificateBuilder.templateName")}</Label>
                <Input
                  value={form.name}
                  onChange={(e) => updateForm({ name: e.target.value })}
                  className="rounded-sm"
                  maxLength={120}
                  data-testid="builder-template-name"
                />
              </div>

              <div className="space-y-2">
                <Label>{t("certificateBuilder.orientation")}</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={form.orientation === "landscape" ? "default" : "outline"}
                    className="rounded-sm"
                    onClick={() => updateForm({ orientation: "landscape" })}
                    data-testid="builder-orientation-landscape"
                  >
                    {t("certificateBuilder.landscape")}
                  </Button>
                  <Button
                    type="button"
                    variant={form.orientation === "portrait" ? "default" : "outline"}
                    className="rounded-sm"
                    onClick={() => updateForm({ orientation: "portrait" })}
                    data-testid="builder-orientation-portrait"
                  >
                    {t("certificateBuilder.portrait")}
                  </Button>
                </div>
              </div>

              <CertificateBackgroundUpload
                value={form.background_image_url}
                onChange={(url) => updateForm({ background_image_url: url })}
              />

              <div className="space-y-2">
                <Label>{t("certificateBuilder.presetBackground")}</Label>
                <Select
                  value={form.background}
                  onValueChange={(value) => updateForm({ background: value })}
                >
                  <SelectTrigger className="rounded-sm" data-testid="builder-preset-background">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CERTIFICATE_BACKGROUNDS.map((key) => (
                      <SelectItem key={key} value={key}>
                        {backgroundLabel(t, key)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-500">
                  {t("certificateBuilder.presetHint")}
                </p>
              </div>

              <div className="space-y-2">
                <Label>{t("certificateBuilder.bodyText")}</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {PLACEHOLDERS.map((token) => (
                    <Button
                      key={token}
                      type="button"
                      size="sm"
                      variant="outline"
                      className="rounded-sm text-xs"
                      onClick={() => insertPlaceholder(token)}
                      data-testid={`builder-placeholder-${token.replace(/[{}]/g, "")}`}
                    >
                      {token}
                    </Button>
                  ))}
                </div>
                <Textarea
                  ref={bodyRef}
                  value={form.body_text}
                  onChange={(e) => updateForm({ body_text: e.target.value })}
                  rows={5}
                  className="rounded-sm font-mono text-sm"
                  data-testid="builder-body-text"
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button
                  className="btn-primary rounded-sm"
                  disabled={!isValid}
                  onClick={() => setStep("review")}
                  data-testid="builder-continue-review"
                >
                  {t("certificateBuilder.continueReview")}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </Card>

            <Card className="card-swiss p-6 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-[#0A0B10]">
                  {t("certificateBuilder.livePreview")}
                </h3>
                {previewLoading && (
                  <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                )}
              </div>
              <p className="text-xs text-slate-500">{t("certificateBuilder.sampleNote")}</p>
              <div className="flex justify-center bg-slate-100 rounded-sm p-4 overflow-auto">
                <div
                  className={`${previewFrameClass} bg-white shadow-sm overflow-hidden`}
                  data-testid="builder-preview-frame"
                >
                  {previewHtml ? (
                    <iframe
                      title="certificate-preview"
                      srcDoc={previewHtml}
                      className="w-full h-full border-0"
                      sandbox=""
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-sm text-slate-400">
                      {t("certificateBuilder.previewEmpty")}
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </div>
        ) : (
          <div className="space-y-4" data-testid="builder-review-step">
            <Card className="card-swiss p-6 space-y-3">
              <h3 className="font-medium text-[#0A0B10]">
                {t("certificateBuilder.reviewTitle")}
              </h3>
              <p className="text-sm text-slate-600">
                {t("certificateBuilder.reviewHint")}
              </p>
              <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
                <li>{t("certificateBuilder.reviewCheckAlignment")}</li>
                <li>{t("certificateBuilder.reviewCheckReadability")}</li>
                <li>{t("certificateBuilder.reviewCheckImage")}</li>
              </ul>
              <div className="flex justify-center bg-slate-100 rounded-sm p-4 overflow-auto">
                <div className={`${reviewFrameClass} bg-white shadow-sm overflow-hidden`}>
                  {previewHtml ? (
                    <iframe
                      title="certificate-review"
                      srcDoc={previewHtml}
                      className="w-full h-full border-0"
                      sandbox=""
                    />
                  ) : null}
                </div>
              </div>
              <div className="flex justify-between pt-2">
                <Button
                  variant="outline"
                  className="rounded-sm"
                  onClick={() => setStep("configure")}
                  data-testid="builder-back-configure"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  {t("certificateBuilder.back")}
                </Button>
                <Button
                  className="btn-primary rounded-sm"
                  disabled={saving || !isValid}
                  onClick={handleSave}
                  data-testid="builder-save"
                >
                  {saving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  {t("certificateBuilder.save")}
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default CertificateBuilderPage;
