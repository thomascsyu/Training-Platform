import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
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
import { Award, Download, Palette, Settings, Loader2, Info, FileCheck } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { CERTIFICATE_BACKGROUNDS, backgroundLabel } from "@/lib/certificateBackgrounds";
import { previewCertificateId } from "@/lib/certificateId";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import StatCard from "@/components/enhanced/StatCard";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";

const emptyCustomizeForm = () => ({
  certificate_id: "",
  template: "default",
  primary_color: "#002FA7",
  secondary_color: "#0A0B10",
  background: "plain",
  apply_to_course: false,
});

const emptySettingsForm = () => ({
  id_format: "CERT-{year}-{seq:6}",
  default_background: "plain",
  default_primary_color: "#002fa7",
  default_secondary_color: "#0a0b10",
  next_sequence: 1,
});

export const AdminCertificatesPage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [certificates, setCertificates] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courseFilter, setCourseFilter] = useState("all");
  const [showCustomizeDialog, setShowCustomizeDialog] = useState(false);
  const [customizeForm, setCustomizeForm] = useState(emptyCustomizeForm());
  const [saving, setSaving] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [settingsForm, setSettingsForm] = useState(emptySettingsForm());
  const [savingSettings, setSavingSettings] = useState(false);

  const fetchCourses = useCallback(async () => {
    try {
      const { data } = await API.get("/courses", { params: { include_private: true } });
      setCourses(data);
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
  }, [fetchCourses]);

  useEffect(() => {
    fetchCertificates();
  }, [fetchCertificates]);

  const openCustomize = (cert) => {
    setCustomizeForm({
      certificate_id: cert.id,
      template: cert.template || "default",
      primary_color: cert.primary_color || "#002FA7",
      secondary_color: cert.secondary_color || "#0A0B10",
      background: cert.background || "plain",
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

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-certificates-page">
        <PageHeader
          overline="Admin"
          title={t("adminCertificates.title")}
          description={t("adminCertificates.description")}
        >
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
          <Button
            variant="outline"
            className="rounded-sm"
            onClick={() => navigate("/admin/certificates/templates")}
            data-testid="manage-certificate-templates-btn"
          >
            <FileCheck className="w-4 h-4 mr-2" /> {t("certificateTemplates.manageTemplates")}
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
          <TableSkeleton rows={6} cols={6} />
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
                <Select
                  value={customizeForm.background}
                  onValueChange={(value) => setCustomizeForm({ ...customizeForm, background: value })}
                >
                  <SelectTrigger className="rounded-sm" data-testid="customize-background-select">
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
      </div>
    </DashboardLayout>
  );
};
