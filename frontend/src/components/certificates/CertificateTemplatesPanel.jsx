import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Edit, Trash2, Loader2, FileCheck, Palette, Wand2 } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { CERTIFICATE_BACKGROUNDS, DEFAULT_CERTIFICATE_BACKGROUND, backgroundLabel } from "@/lib/certificateBackgrounds";
import { useLanguage } from "@/contexts/LanguageContext";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";
import { useNavigate } from "react-router-dom";

const emptyTemplate = () => ({
  id: null,
  name: "",
  html: "",
  primary_color: "#002fa7",
  secondary_color: "#0a0b10",
  background: DEFAULT_CERTIFICATE_BACKGROUND,
  is_default: false,
});

export const CertificateTemplatesPanel = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyTemplate());
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const { data } = await API.get("/certificate-templates");
      setTemplates(data);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setForm(emptyTemplate());
    setDialogOpen(true);
  };

  const openEdit = (template) => {
    setEditing(template);
    setForm({ ...template });
    setDialogOpen(true);
  };

  const handleGenerateDefault = async () => {
    setGenerating(true);
    try {
      const { data } = await API.post("/certificate-templates/render-default", {
        primary_color: form.primary_color,
        secondary_color: form.secondary_color,
        background: form.background,
      });
      setForm((prev) => ({ ...prev, html: data.html }));
      toast.success(t("certificateTemplates.generated"));
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error(t("certificateTemplates.nameRequired"));
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        html: form.html,
        primary_color: form.primary_color,
        secondary_color: form.secondary_color,
        background: form.background,
        is_default: form.is_default,
      };
      if (editing) {
        await API.put(`/certificate-templates/${editing.id}`, payload);
        toast.success(t("certificateTemplates.updated"));
      } else {
        await API.post("/certificate-templates", payload);
        toast.success(t("certificateTemplates.created"));
      }
      setDialogOpen(false);
      setForm(emptyTemplate());
      fetchTemplates();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (template) => {
    if (!window.confirm(t("certificateTemplates.deleteConfirm"))) return;

    try {
      await API.delete(`/certificate-templates/${template.id}`);
      toast.success(t("certificateTemplates.deleted"));
      fetchTemplates();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  return (
    <div data-testid="admin-certificate-templates-page">
      <div className="flex justify-end gap-2 mb-4">
        <Button
          variant="outline"
          className="rounded-sm"
          onClick={() => navigate("/admin/certificate-builder")}
          data-testid="create-with-builder-btn"
        >
          <Wand2 className="w-4 h-4 mr-2" /> {t("certificateTemplates.createWithBuilder")}
        </Button>
        <Button
          onClick={openCreate}
          className="btn-primary"
          data-testid="create-template-btn"
        >
          <Plus className="w-4 h-4 mr-2" /> {t("certificateTemplates.createTemplate")}
        </Button>
      </div>

      {loading ? (
        <TableSkeleton rows={5} cols={5} />
      ) : templates.length === 0 ? (
        <EmptyState
          icon={FileCheck}
          title={t("certificateTemplates.noTemplates")}
          testId="admin-certificate-templates-empty"
        />
      ) : (
        <Card className="card-swiss overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left p-4 font-medium text-slate-600">
                    {t("certificateTemplates.name")}
                  </th>
                  <th className="text-left p-4 font-medium text-slate-600">
                    {t("certificateTemplates.primaryColor")}
                  </th>
                  <th className="text-left p-4 font-medium text-slate-600">
                    {t("certificateTemplates.secondaryColor")}
                  </th>
                  <th className="text-left p-4 font-medium text-slate-600">
                    {t("certificateTemplates.default")}
                  </th>
                  <th className="text-left p-4 font-medium text-slate-600">
                    {t("users.actions")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {templates.map((template) => (
                  <tr
                    key={template.id}
                    className="border-b border-slate-100 hover:bg-slate-50/80"
                    data-testid={`template-row-${template.id}`}
                  >
                    <td className="p-4 font-medium">{template.name}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-6 h-6 rounded-sm border border-slate-200 inline-block"
                          style={{ backgroundColor: template.primary_color }}
                        />
                        <span className="text-sm text-slate-600">{template.primary_color}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-6 h-6 rounded-sm border border-slate-200 inline-block"
                          style={{ backgroundColor: template.secondary_color }}
                        />
                        <span className="text-sm text-slate-600">{template.secondary_color}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      {template.is_default ? (
                        <Badge className="bg-[#002FA7] text-white hover:bg-[#002FA7] rounded-sm">
                          {t("certificateTemplates.default")}
                        </Badge>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-sm"
                          onClick={() =>
                            navigate(`/admin/certificate-builder?template_id=${template.id}`)
                          }
                          data-testid={`builder-edit-template-btn-${template.id}`}
                          title={t("certificateTemplates.createWithBuilder")}
                        >
                          <Wand2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-sm"
                          onClick={() => openEdit(template)}
                          data-testid={`edit-template-btn-${template.id}`}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-sm text-red-600 hover:text-red-700"
                          onClick={() => handleDelete(template)}
                          data-testid={`delete-template-btn-${template.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
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
              {editing ? t("certificateTemplates.editTemplate") : t("certificateTemplates.createTemplate")}
            </DialogTitle>
            <DialogDescription>{t("certificateTemplates.description")}</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t("certificateTemplates.name")}</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="rounded-sm"
                  data-testid="template-name-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{t("certificateTemplates.primaryColor")}</Label>
                  <Input
                    type="color"
                    value={form.primary_color}
                    onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
                    className="rounded-sm h-10 p-1"
                    data-testid="template-primary-color-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t("certificateTemplates.secondaryColor")}</Label>
                  <Input
                    type="color"
                    value={form.secondary_color}
                    onChange={(e) => setForm({ ...form, secondary_color: e.target.value })}
                    className="rounded-sm h-10 p-1"
                    data-testid="template-secondary-color-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>{t("certificateTemplates.background")}</Label>
                <Select
                  value={form.background}
                  onValueChange={(value) => setForm({ ...form, background: value })}
                >
                  <SelectTrigger className="rounded-sm" data-testid="template-background-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CERTIFICATE_BACKGROUNDS.map((bg) => (
                      <SelectItem key={bg.id} value={bg.id}>
                        {backgroundLabel(t, bg.id)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-3">
                <Switch
                  id="template-default"
                  checked={form.is_default}
                  onCheckedChange={(checked) => setForm({ ...form, is_default: checked })}
                  data-testid="template-default-switch"
                />
                <Label htmlFor="template-default">{t("certificateTemplates.default")}</Label>
              </div>
              <div className="space-y-2">
                <Label>{t("certificateTemplates.html")}</Label>
                <Textarea
                  value={form.html}
                  onChange={(e) => setForm({ ...form, html: e.target.value })}
                  rows={10}
                  className="rounded-sm font-mono text-xs"
                  data-testid="template-html-input"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleGenerateDefault}
                  disabled={generating}
                  className="rounded-sm"
                  data-testid="generate-default-html-btn"
                >
                  {generating ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Palette className="w-4 h-4 mr-2" />
                  )}
                  {t("certificateTemplates.generateDefault")}
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
                  data-testid="save-template-btn"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  {t("certificateTemplates.save")}
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("certificateTemplates.preview")}</Label>
              <div className="border border-slate-200 rounded-sm overflow-hidden bg-slate-50 h-[500px]">
                <iframe
                  title="Certificate preview"
                  srcDoc={form.html}
                  className="w-full h-full border-0"
                  data-testid="template-preview-iframe"
                />
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
