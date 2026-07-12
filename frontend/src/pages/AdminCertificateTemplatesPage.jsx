import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Edit, Eye, FileCheck, Loader2 } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";

const defaultSettings = () => ({
  course_id: "",
  course_title: "",
  passing_score: 70,
  primary_color: "#002fa7",
  secondary_color: "#0a0b10",
  background_url: "",
  validity_days: "",
});

export const AdminCertificateTemplatesPage = () => {
  const { t } = useLanguage();
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(defaultSettings());
  const [previewHtml, setPreviewHtml] = useState("");
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const { data } = await API.get("/certificate-templates/course-settings");
      setSettings(data);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const openEditor = async (row) => {
    const next = {
      ...row,
      background_url: row.background_url || "",
      validity_days: row.validity_days || "",
    };
    setEditing(next);
    setPreviewHtml("");
    setDialogOpen(true);
    await refreshPreview(next);
  };

  const updateEditing = (field, value) => {
    setEditing((prev) => ({ ...prev, [field]: value }));
  };

  const buildPayload = (source = editing) => ({
    primary_color: source.primary_color,
    secondary_color: source.secondary_color,
    background_url: source.background_url?.trim() || null,
    validity_days: source.validity_days ? Number(source.validity_days) : null,
  });

  const refreshPreview = async (source = editing) => {
    if (!source.course_id) return;
    setPreviewing(true);
    try {
      const { data } = await API.post(
        `/certificate-templates/course-settings/${source.course_id}/preview`,
        buildPayload(source),
      );
      setPreviewHtml(data.html);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setPreviewing(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await API.put(
        `/certificate-templates/course-settings/${editing.course_id}`,
        buildPayload(),
      );
      toast.success(t("certificateTemplates.updated"));
      setDialogOpen(false);
      fetchSettings();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-certificate-templates-page">
        <PageHeader
          overline="Admin"
          title={t("certificateTemplates.manageTemplates")}
          description={t("certificateTemplates.description")}
        />

        {loading ? (
          <TableSkeleton rows={5} cols={5} />
        ) : settings.length === 0 ? (
          <EmptyState
            icon={FileCheck}
            title={t("certificateTemplates.noCourses")}
            testId="admin-certificate-templates-empty"
          />
        ) : (
          <Card className="card-swiss overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left p-4 font-medium text-slate-600">
                      {t("certificateTemplates.course")}
                    </th>
                    <th className="text-left p-4 font-medium text-slate-600">
                      {t("certificateTemplates.primaryColor")}
                    </th>
                    <th className="text-left p-4 font-medium text-slate-600">
                      {t("certificateTemplates.secondaryColor")}
                    </th>
                    <th className="text-left p-4 font-medium text-slate-600">
                      {t("certificateTemplates.validity")}
                    </th>
                    <th className="text-left p-4 font-medium text-slate-600">
                      {t("users.actions")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {settings.map((row) => (
                    <tr
                      key={row.course_id}
                      className="border-b border-slate-100 hover:bg-slate-50/80"
                      data-testid={`certificate-course-row-${row.course_id}`}
                    >
                      <td className="p-4">
                        <p className="font-medium">{row.course_title}</p>
                        <p className="text-xs text-slate-500">
                          {t("courses.passingScore")}: {row.passing_score}%
                        </p>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-6 h-6 rounded-sm border border-slate-200 inline-block"
                            style={{ backgroundColor: row.primary_color }}
                          />
                          <span className="text-sm text-slate-600">{row.primary_color}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-6 h-6 rounded-sm border border-slate-200 inline-block"
                            style={{ backgroundColor: row.secondary_color }}
                          />
                          <span className="text-sm text-slate-600">{row.secondary_color}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        {row.validity_days
                          ? t("certificateTemplates.validForDays", { days: row.validity_days })
                          : t("certificateTemplates.noExpiration")}
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-sm"
                            onClick={() => openEditor(row)}
                            data-testid={`edit-certificate-settings-btn-${row.course_id}`}
                          >
                            <Edit className="w-4 h-4" />
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

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>
                {t("certificateTemplates.editCourseSettings")}
              </DialogTitle>
              <DialogDescription>{editing.course_title}</DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("certificateTemplates.primaryColor")}</Label>
                    <Input
                      type="color"
                      value={editing.primary_color}
                      onChange={(e) => updateEditing("primary_color", e.target.value)}
                      className="rounded-sm h-10 p-1"
                      data-testid="course-certificate-primary-color-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t("certificateTemplates.secondaryColor")}</Label>
                    <Input
                      type="color"
                      value={editing.secondary_color}
                      onChange={(e) => updateEditing("secondary_color", e.target.value)}
                      className="rounded-sm h-10 p-1"
                      data-testid="course-certificate-secondary-color-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t("certificateTemplates.backgroundUrl")}</Label>
                  <Input
                    value={editing.background_url}
                    onChange={(e) => updateEditing("background_url", e.target.value)}
                    placeholder="https://example.com/certificate-art.png"
                    className="rounded-sm"
                    data-testid="course-certificate-background-url-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t("certificateTemplates.validityDays")}</Label>
                  <Input
                    type="number"
                    min="1"
                    max="3650"
                    value={editing.validity_days}
                    onChange={(e) => updateEditing("validity_days", e.target.value)}
                    placeholder={t("certificateTemplates.noExpiration")}
                    className="rounded-sm"
                    data-testid="course-certificate-validity-days-input"
                  />
                  <p className="text-xs text-slate-500">
                    {t("certificateTemplates.validityHint")}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => refreshPreview()}
                    disabled={previewing}
                    className="rounded-sm"
                    data-testid="preview-course-certificate-btn"
                  >
                    {previewing ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Eye className="w-4 h-4 mr-2" />
                    )}
                    {t("certificateTemplates.preview")}
                  </Button>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                    className="rounded-sm"
                  >
                    {t("common.cancel")}
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={saving}
                    className="btn-primary"
                    data-testid="save-course-certificate-settings-btn"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    {t("certificateTemplates.saveSettings")}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label>{t("certificateTemplates.preview")}</Label>
                <div className="border border-slate-200 rounded-sm overflow-hidden bg-slate-50 h-[500px]">
                  <iframe
                    title="Certificate preview"
                    srcDoc={previewHtml}
                    className="w-full h-full border-0"
                    data-testid="course-certificate-preview-iframe"
                  />
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};
