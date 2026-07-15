import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Award, Download, Palette, Settings, Loader2, Info, Eye } from "lucide-react";
import { API, formatError } from "@/lib/api";
import {
  CERTIFICATE_BACKGROUNDS,
  DEFAULT_CERTIFICATE_BACKGROUND,
  backgroundLabel,
} from "@/lib/certificateBackgrounds";
import { previewCertificateId } from "@/lib/certificateId";
import { courseLanguages, courseLanguageShortNames } from "@/i18n";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { CertificateBackgroundPicker } from "@/components/CertificateBackgroundPicker";
import { CertificateTemplatesPanel } from "@/components/certificates/CertificateTemplatesPanel";
import PageHeader from "@/components/enhanced/PageHeader";
import StatCard from "@/components/enhanced/StatCard";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";

const CERTIFICATE_TABS = new Set(["issued", "templates"]);

const emptyCustomizeForm = () => ({
  certificate_id: "",
  template: "default",
  primary_color: "#002FA7",
  secondary_color: "#0A0B10",
  background: DEFAULT_CERTIFICATE_BACKGROUND,
  apply_to_course: false,
});

const emptySettingsForm = () => ({
  id_format: "CERT-{year}-{seq:6}",
  default_background: DEFAULT_CERTIFICATE_BACKGROUND,
  default_primary_color: "#002fa7",
  default_secondary_color: "#0a0b10",
  next_sequence: 1,
});

const emptyPreviewForm = () => ({
  course_id: "",
  use_sample_course: false,
  course_title: "Sample Course",
  user_id: "",
  use_sample_student: true,
  user_name: "Jane Doe",
  score: 92,
  primary_color: "#002FA7",
  secondary_color: "#0A0B10",
  background: DEFAULT_CERTIFICATE_BACKGROUND,
  language: "en",
});

export const AdminCertificatesPage = () => {
  const { t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const activeTab = CERTIFICATE_TABS.has(tabParam) ? tabParam : "issued";
  const [certificates, setCertificates] = useState([]);
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courseFilter, setCourseFilter] = useState("all");
  const [showCustomizeDialog, setShowCustomizeDialog] = useState(false);
  const [customizeForm, setCustomizeForm] = useState(emptyCustomizeForm());
  const [saving, setSaving] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [settingsForm, setSettingsForm] = useState(emptySettingsForm());
  const [savingSettings, setSavingSettings] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [previewForm, setPreviewForm] = useState(emptyPreviewForm());
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewPdfLoading, setPreviewPdfLoading] = useState(false);

  const setActiveTab = (tab) => {
    const next = new URLSearchParams(searchParams);
    if (tab === "issued") {
      next.delete("tab");
    } else {
      next.set("tab", tab);
    }
    setSearchParams(next, { replace: true });
  };

  const fetchCourses = useCallback(async () => {
    try {
      const { data } = await API.get("/courses", { params: { include_private: true } });
      setCourses(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchStudents = useCallback(async () => {
    try {
      const { data } = await API.get("/users", { params: { role: "student" } });
      setStudents(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchCertificates = useCallback(async () => {
    setLoading(true);
    try {
      const params = courseFilter !== "all" ? { course_id: courseFilter } : {};
      const { data } = await API.get("/certificates", { params });
      setCertificates(data);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  }, [courseFilter]);

  useEffect(() => {
    fetchCourses();
    fetchStudents();
  }, [fetchCourses, fetchStudents]);

  useEffect(() => {
    fetchCertificates();
  }, [fetchCertificates]);

  const openCustomize = (cert) => {
    setCustomizeForm({
      certificate_id: cert.id,
      template: cert.template || "default",
      primary_color: cert.primary_color || "#002FA7",
      secondary_color: cert.secondary_color || "#0A0B10",
      background: cert.background || DEFAULT_CERTIFICATE_BACKGROUND,
      apply_to_course: false,
    });
    setShowCustomizeDialog(true);
  };

  const handleCustomize = async () => {
    setSaving(true);
    try {
      await API.put(`/certificates/${customizeForm.certificate_id}/customize`, {
        template: customizeForm.template,
        primary_color: customizeForm.primary_color,
        secondary_color: customizeForm.secondary_color,
        background: customizeForm.background,
        apply_to_course: customizeForm.apply_to_course,
      });
      toast.success(t("adminCertificates.customized"));
      setShowCustomizeDialog(false);
      setCustomizeForm(emptyCustomizeForm());
      fetchCertificates();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const openSettings = async () => {
    setShowSettingsDialog(true);
    try {
      const { data } = await API.get("/certificate-settings");
      setSettingsForm({
        id_format: data.id_format,
        default_background: data.default_background,
        default_primary_color: data.default_primary_color,
        default_secondary_color: data.default_secondary_color,
        next_sequence: data.next_sequence,
      });
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const handleSaveSettings = async () => {
    setSavingSettings(true);
    try {
      const { data } = await API.put("/certificate-settings", {
        id_format: settingsForm.id_format,
        default_background: settingsForm.default_background,
        default_primary_color: settingsForm.default_primary_color,
        default_secondary_color: settingsForm.default_secondary_color,
      });
      setSettingsForm((prev) => ({ ...prev, next_sequence: data.next_sequence }));
      toast.success(t("certificateSettings.saved"));
      setShowSettingsDialog(false);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSavingSettings(false);
    }
  };

  const downloadCertificate = async (certId, certCode) => {
    try {
      const response = await API.get(`/certificates/${certId}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `certificate-${certCode}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const buildPreviewPayload = () => {
    const payload = {
      score: Number(previewForm.score) || 0,
      primary_color: previewForm.primary_color,
      secondary_color: previewForm.secondary_color,
      background: previewForm.background,
      language: previewForm.language,
    };

    if (previewForm.use_sample_course) {
      if (!previewForm.course_title.trim()) {
        toast.error(t("adminCertificates.previewCourseRequired"));
        return null;
      }
      payload.course_title = previewForm.course_title.trim();
    } else {
      if (!previewForm.course_id) {
        toast.error(t("adminCertificates.previewCourseRequired"));
        return null;
      }
      payload.course_id = previewForm.course_id;
    }

    if (previewForm.use_sample_student) {
      if (!previewForm.user_name.trim()) {
        toast.error(t("adminCertificates.previewStudentRequired"));
        return null;
      }
      payload.user_name = previewForm.user_name.trim();
    } else {
      if (!previewForm.user_id) {
        toast.error(t("adminCertificates.previewStudentRequired"));
        return null;
      }
      payload.user_id = previewForm.user_id;
    }

    return payload;
  };

  const openPreview = () => {
    const selected =
      courseFilter !== "all" ? courses.find((course) => course.id === courseFilter) : null;
    setPreviewForm({
      ...emptyPreviewForm(),
      course_id: selected?.id || "",
      language: selected?.language || "en",
      use_sample_course: !selected,
    });
    setPreviewHtml("");
    setShowPreviewDialog(true);
  };

  const handleCourseSelectForPreview = (courseId) => {
    const course = courses.find((item) => item.id === courseId);
    setPreviewForm((prev) => ({
      ...prev,
      course_id: courseId,
      use_sample_course: false,
      language: course?.language || prev.language,
    }));
  };

  const generatePreviewHtml = async () => {
    const payload = buildPreviewPayload();
    if (!payload) return;
    setPreviewLoading(true);
    try {
      const response = await API.post(
        "/certificates/preview",
        { ...payload, format: "html" },
        { responseType: "text" }
      );
      setPreviewHtml(typeof response.data === "string" ? response.data : String(response.data));
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setPreviewLoading(false);
    }
  };

  const downloadPreviewPdf = async () => {
    const payload = buildPreviewPayload();
    if (!payload) return;
    setPreviewPdfLoading(true);
    try {
      const response = await API.post(
        "/certificates/preview",
        { ...payload, format: "pdf" },
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "certificate-preview.pdf";
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setPreviewPdfLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-certificates-page">
        <PageHeader
          overline="Admin"
          title={t("adminCertificates.title")}
          description={
            activeTab === "templates"
              ? t("certificateTemplates.description")
              : t("adminCertificates.description")
          }
        >
          {activeTab === "issued" && (
            <Select value={courseFilter} onValueChange={setCourseFilter}>
              <SelectTrigger className="w-full sm:w-56 rounded-sm" data-testid="course-filter-select">
                <SelectValue placeholder={t("adminCertificates.filterByCourse")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("adminCertificates.allCourses")}</SelectItem>
                {courses.map((course) => (
                  <SelectItem key={course.id} value={course.id}>
                    {course.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button
            variant="outline"
            className="rounded-sm"
            onClick={openPreview}
            data-testid="certificate-preview-btn"
          >
            <Eye className="w-4 h-4 mr-2" /> {t("adminCertificates.preview")}
          </Button>
          <Button
            variant="outline"
            className="rounded-sm"
            onClick={openSettings}
            data-testid="certificate-settings-btn"
          >
            <Settings className="w-4 h-4 mr-2" /> {t("adminCertificates.manageAutoIssue")}
          </Button>
        </PageHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
          <TabsList className="card-swiss" data-testid="certificates-tabs">
            <TabsTrigger value="issued" className="rounded-sm" data-testid="certificates-tab-issued">
              {t("adminCertificates.tabIssued")}
            </TabsTrigger>
            <TabsTrigger value="templates" className="rounded-sm" data-testid="certificates-tab-templates">
              {t("adminCertificates.tabTemplates")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="issued" className="mt-6">
            <div className="mb-6 flex items-start gap-3 rounded-sm border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
              <Info className="w-4 h-4 mt-0.5 shrink-0" />
              <p>{t("adminCertificates.autoIssueNotice")}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <StatCard
                label={t("adminCertificates.totalCertificates")}
                value={certificates.length}
                icon={Award}
                testId="certificates-total-stat"
              />
            </div>

            {loading ? (
              <TableSkeleton rows={6} cols={7} />
            ) : certificates.length === 0 ? (
              <EmptyState
                icon={Award}
                title={t("adminCertificates.noCertificates")}
                description={t("adminCertificates.noCertificatesHint")}
                testId="certificates-empty"
              />
            ) : (
              <Card className="card-swiss overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.certificateId")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.course")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.student")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.score")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.language")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.issuedOn")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.validUntil")}</th>
                        <th className="text-left p-4 font-medium text-slate-600">{t("adminCertificates.actions")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {certificates.map((cert) => (
                        <tr key={cert.id} className="border-b border-slate-100" data-testid={`certificate-row-${cert.id}`}>
                          <td className="p-4 font-mono text-xs text-slate-600">{cert.certificate_id}</td>
                          <td className="p-4 text-slate-700">{cert.course_title}</td>
                          <td className="p-4 text-slate-700">{cert.user_name}</td>
                          <td className="p-4">
                            <Badge variant="secondary" className="rounded-sm">
                              {cert.score}%
                            </Badge>
                          </td>
                          <td className="p-4 text-slate-500 text-sm">
                            {courseLanguageShortNames[cert.language] || cert.language || "EN"}
                          </td>
                          <td className="p-4 text-slate-500 text-sm">
                            {cert.issued_at ? new Date(cert.issued_at).toLocaleDateString() : "—"}
                          </td>
                          <td className="p-4 text-sm">
                            {cert.valid_until ? (
                              <span className={cert.is_expired ? "text-red-600 font-medium" : "text-slate-500"}>
                                {new Date(cert.valid_until).toLocaleDateString()}
                                {cert.is_expired ? ` (${t("adminCertificates.expired")})` : ""}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                          <td className="p-4">
                            <div className="flex items-center gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                className="rounded-sm"
                                onClick={() => openCustomize(cert)}
                                data-testid={`customize-cert-btn-${cert.id}`}
                              >
                                <Palette className="w-4 h-4 mr-2" /> {t("adminCertificates.customize")}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="rounded-sm"
                                onClick={() => downloadCertificate(cert.id, cert.certificate_id)}
                                data-testid={`download-cert-btn-${cert.id}`}
                              >
                                <Download className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="templates" className="mt-6">
            <div className="mb-6 flex items-start gap-3 rounded-sm border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
              <Info className="w-4 h-4 mt-0.5 shrink-0" />
              <p>{t("adminCertificates.templatesNotice")}</p>
            </div>
            <CertificateTemplatesPanel />
          </TabsContent>
        </Tabs>

        <Dialog open={showCustomizeDialog} onOpenChange={setShowCustomizeDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t("adminCertificates.customizeCertificate")}</DialogTitle>
              <DialogDescription>{t("adminCertificates.customizeDescription")}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t("adminCertificates.primaryColor")}</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={customizeForm.primary_color}
                      onChange={(e) => setCustomizeForm({ ...customizeForm, primary_color: e.target.value })}
                      className="h-10 w-10 rounded-sm border border-slate-200"
                      data-testid="customize-primary-color"
                    />
                    <span className="text-sm text-slate-600">{customizeForm.primary_color}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t("adminCertificates.secondaryColor")}</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={customizeForm.secondary_color}
                      onChange={(e) => setCustomizeForm({ ...customizeForm, secondary_color: e.target.value })}
                      className="h-10 w-10 rounded-sm border border-slate-200"
                      data-testid="customize-secondary-color"
                    />
                    <span className="text-sm text-slate-600">{customizeForm.secondary_color}</span>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label>{t("adminCertificates.background")}</Label>
                <CertificateBackgroundPicker
                  value={customizeForm.background}
                  onChange={(background) => setCustomizeForm({ ...customizeForm, background })}
                  primaryColor={customizeForm.primary_color}
                  secondaryColor={customizeForm.secondary_color}
                  testIdPrefix="customize-background"
                />
              </div>
              <div className="flex items-center gap-3">
                <Switch
                  id="customize-apply-to-course"
                  checked={customizeForm.apply_to_course}
                  onCheckedChange={(checked) => setCustomizeForm({ ...customizeForm, apply_to_course: checked })}
                />
                <Label htmlFor="customize-apply-to-course">{t("adminCertificates.applyToCourse")}</Label>
              </div>
              <p className="text-xs text-slate-500">{t("adminCertificates.applyToCourseHint")}</p>
              <Button
                onClick={handleCustomize}
                disabled={saving}
                className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="customize-certificate-submit"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {saving ? t("common.loading") : t("common.save")}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{t("certificateSettings.title")}</DialogTitle>
              <DialogDescription>{t("certificateSettings.description")}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t("certificateSettings.idFormat")}</Label>
                <Input
                  value={settingsForm.id_format}
                  onChange={(e) => setSettingsForm({ ...settingsForm, id_format: e.target.value })}
                  className="rounded-sm font-mono text-sm"
                  data-testid="settings-id-format-input"
                />
                <p className="text-xs text-slate-500">{t("certificateSettings.idFormatHint")}</p>
                <div className="rounded-sm border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  <span className="text-slate-500">{t("certificateSettings.preview")}: </span>
                  <span className="font-mono text-slate-800" data-testid="settings-id-preview">
                    {previewCertificateId(settingsForm.id_format, {
                      sequence: settingsForm.next_sequence,
                    })}
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <Label>{t("certificateSettings.defaultBackground")}</Label>
                <Select
                  value={settingsForm.default_background}
                  onValueChange={(value) => setSettingsForm({ ...settingsForm, default_background: value })}
                >
                  <SelectTrigger className="rounded-sm" data-testid="settings-background-select">
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
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t("certificateSettings.defaultPrimaryColor")}</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settingsForm.default_primary_color}
                      onChange={(e) => setSettingsForm({ ...settingsForm, default_primary_color: e.target.value })}
                      className="h-10 w-10 rounded-sm border border-slate-200"
                      data-testid="settings-primary-color"
                    />
                    <span className="text-sm text-slate-600">{settingsForm.default_primary_color}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t("certificateSettings.defaultSecondaryColor")}</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={settingsForm.default_secondary_color}
                      onChange={(e) => setSettingsForm({ ...settingsForm, default_secondary_color: e.target.value })}
                      className="h-10 w-10 rounded-sm border border-slate-200"
                      data-testid="settings-secondary-color"
                    />
                    <span className="text-sm text-slate-600">{settingsForm.default_secondary_color}</span>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  variant="outline"
                  className="rounded-sm"
                  onClick={() => setShowSettingsDialog(false)}
                >
                  {t("certificateSettings.cancel")}
                </Button>
                <Button
                  onClick={handleSaveSettings}
                  disabled={savingSettings}
                  className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                  data-testid="save-certificate-settings-btn"
                >
                  {savingSettings ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  {t("certificateSettings.save")}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog
          open={showPreviewDialog}
          onOpenChange={(open) => {
            setShowPreviewDialog(open);
            if (!open) setPreviewHtml("");
          }}
        >
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{t("adminCertificates.previewCertificate")}</DialogTitle>
              <DialogDescription>{t("adminCertificates.previewDescription")}</DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Switch
                    id="preview-sample-course"
                    checked={previewForm.use_sample_course}
                    onCheckedChange={(checked) =>
                      setPreviewForm({ ...previewForm, use_sample_course: checked })
                    }
                    data-testid="preview-sample-course-switch"
                  />
                  <Label htmlFor="preview-sample-course">{t("adminCertificates.sampleCourse")}</Label>
                </div>
                {previewForm.use_sample_course ? (
                  <div className="space-y-2">
                    <Label>{t("adminCertificates.sampleCourseTitle")}</Label>
                    <Input
                      value={previewForm.course_title}
                      onChange={(e) => setPreviewForm({ ...previewForm, course_title: e.target.value })}
                      className="rounded-sm"
                      data-testid="preview-course-title-input"
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label>{t("adminCertificates.course")}</Label>
                    <Select value={previewForm.course_id || undefined} onValueChange={handleCourseSelectForPreview}>
                      <SelectTrigger className="rounded-sm" data-testid="preview-course-select">
                        <SelectValue placeholder={t("adminCertificates.selectCourse")} />
                      </SelectTrigger>
                      <SelectContent>
                        {courses.map((course) => (
                          <SelectItem key={course.id} value={course.id}>
                            {course.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <Switch
                    id="preview-sample-student"
                    checked={previewForm.use_sample_student}
                    onCheckedChange={(checked) =>
                      setPreviewForm({ ...previewForm, use_sample_student: checked })
                    }
                    data-testid="preview-sample-student-switch"
                  />
                  <Label htmlFor="preview-sample-student">{t("adminCertificates.sampleStudent")}</Label>
                </div>
                {previewForm.use_sample_student ? (
                  <div className="space-y-2">
                    <Label>{t("adminCertificates.sampleStudentName")}</Label>
                    <Input
                      value={previewForm.user_name}
                      onChange={(e) => setPreviewForm({ ...previewForm, user_name: e.target.value })}
                      className="rounded-sm"
                      data-testid="preview-student-name-input"
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label>{t("adminCertificates.student")}</Label>
                    <Select
                      value={previewForm.user_id || undefined}
                      onValueChange={(value) => setPreviewForm({ ...previewForm, user_id: value })}
                    >
                      <SelectTrigger className="rounded-sm" data-testid="preview-student-select">
                        <SelectValue placeholder={t("adminCertificates.selectStudent")} />
                      </SelectTrigger>
                      <SelectContent>
                        {students.map((student) => (
                          <SelectItem key={student.id} value={student.id}>
                            {student.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>{t("adminCertificates.scoreLabel")}</Label>
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    value={previewForm.score}
                    onChange={(e) => setPreviewForm({ ...previewForm, score: e.target.value })}
                    className="rounded-sm"
                    data-testid="preview-score-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label>{t("adminCertificates.language")}</Label>
                  <Select
                    value={previewForm.language}
                    onValueChange={(value) => setPreviewForm({ ...previewForm, language: value })}
                  >
                    <SelectTrigger className="rounded-sm" data-testid="preview-language-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {courseLanguages.map(({ value, label }) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("adminCertificates.primaryColor")}</Label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={previewForm.primary_color}
                        onChange={(e) => setPreviewForm({ ...previewForm, primary_color: e.target.value })}
                        className="h-10 w-10 rounded-sm border border-slate-200"
                        data-testid="preview-primary-color"
                      />
                      <span className="text-sm text-slate-600">{previewForm.primary_color}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>{t("adminCertificates.secondaryColor")}</Label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={previewForm.secondary_color}
                        onChange={(e) => setPreviewForm({ ...previewForm, secondary_color: e.target.value })}
                        className="h-10 w-10 rounded-sm border border-slate-200"
                        data-testid="preview-secondary-color"
                      />
                      <span className="text-sm text-slate-600">{previewForm.secondary_color}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>{t("adminCertificates.background")}</Label>
                  <Select
                    value={previewForm.background}
                    onValueChange={(value) => setPreviewForm({ ...previewForm, background: value })}
                  >
                    <SelectTrigger className="rounded-sm" data-testid="preview-background-select">
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
                </div>

                <p className="text-xs text-slate-500">{t("adminCertificates.previewHint")}</p>

                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={generatePreviewHtml}
                    disabled={previewLoading}
                    className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                    data-testid="generate-certificate-preview-btn"
                  >
                    {previewLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                    {t("adminCertificates.previewGenerate")}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={downloadPreviewPdf}
                    disabled={previewPdfLoading}
                    className="rounded-sm"
                    data-testid="download-certificate-preview-pdf-btn"
                  >
                    {previewPdfLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Download className="w-4 h-4 mr-2" />
                    )}
                    {t("adminCertificates.previewDownloadPdf")}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>{t("adminCertificates.preview")}</Label>
                <div className="border border-slate-200 rounded-sm overflow-hidden bg-slate-50 h-[520px]">
                  {previewHtml ? (
                    <iframe
                      title="Certificate preview"
                      srcDoc={previewHtml}
                      className="w-full h-full border-0"
                      data-testid="certificate-preview-iframe"
                    />
                  ) : (
                    <div className="h-full flex items-center justify-center text-sm text-slate-500 p-6 text-center">
                      {t("adminCertificates.previewDescription")}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};
