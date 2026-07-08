import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Plus, Trash2, Edit, Loader2, Users, Building2 } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";

const emptyForm = { name: "", description: "", training_ids: [] };

export const AdminCompaniesPage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchCompanies();
    fetchTrainings();
  }, []);

  const fetchCompanies = async () => {
    try {
      const { data } = await API.get("/companies");
      setCompanies(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrainings = async () => {
    try {
      const { data } = await API.get("/courses?include_private=true");
      setTrainings(data);
    } catch (e) {
      console.error(e);
    }
  };

  const openCreateDialog = () => {
    setEditingCompany(null);
    setFormData(emptyForm);
    setShowDialog(true);
  };

  const openEditDialog = (company) => {
    setEditingCompany(company);
    setFormData({
      name: company.name,
      description: company.description || "",
      training_ids: company.training_ids || [],
    });
    setShowDialog(true);
  };

  const handleTrainingToggle = (trainingId, checked) => {
    setFormData((prev) => ({
      ...prev,
      training_ids: checked
        ? [...prev.training_ids, trainingId]
        : prev.training_ids.filter((id) => id !== trainingId),
    }));
  };

  const getTrainingName = (trainingId) =>
    trainings.find((training) => training.id === trainingId)?.title ||
    t("companies.unknownTraining");

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error(t("companies.nameRequired"));
      return;
    }

    setSaving(true);
    try {
      if (editingCompany) {
        await API.put(`/companies/${editingCompany.id}`, formData);
        toast.success(t("companies.updated"));
      } else {
        await API.post("/companies", formData);
        toast.success(t("companies.created"));
      }
      setShowDialog(false);
      setFormData(emptyForm);
      setEditingCompany(null);
      fetchCompanies();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (company) => {
    if (!window.confirm(t("companies.confirmDelete"))) return;

    try {
      await API.delete(`/companies/${company.id}`);
      toast.success(t("companies.deleted"));
      fetchCompanies();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const handleManageUsers = (companyId) => {
    navigate(`/admin/users?company_id=${companyId}`);
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-companies-page">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
          <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
            {t("companies.manageCompanies")}
          </h1>
          <Button
            onClick={openCreateDialog}
            className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
            data-testid="create-company-btn"
          >
            <Plus className="w-4 h-4 mr-2" /> {t("companies.createCompany")}
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : companies.length === 0 ? (
          <Card className="bg-white border border-slate-200 rounded-sm p-12 text-center">
            <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-600">{t("companies.noCompanies")}</p>
          </Card>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left p-4 font-medium text-slate-600">{t("companies.name")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("companies.description")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("companies.trainings")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => {
                    const selectedTrainings = company.trainings?.length
                      ? company.trainings
                      : (company.training_ids || []).map((trainingId) => ({
                        id: trainingId,
                        title: getTrainingName(trainingId),
                      }));

                    return (
                    <tr key={company.id} className="border-b border-slate-100" data-testid={`company-row-${company.id}`}>
                      <td className="p-4 font-medium">{company.name}</td>
                      <td className="p-4 text-slate-600">{company.description || "—"}</td>
                      <td className="p-4">
                        {selectedTrainings.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {selectedTrainings.map((training) => (
                              <Badge key={training.id} variant="secondary" className="rounded-sm">
                                {training.title}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-500">{t("companies.noTrainingsAssigned")}</span>
                        )}
                      </td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-sm"
                            onClick={() => handleManageUsers(company.id)}
                            data-testid={`manage-users-btn-${company.id}`}
                          >
                            <Users className="w-4 h-4 mr-1" /> {t("companies.manageUsers")}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-sm"
                            onClick={() => openEditDialog(company)}
                            data-testid={`edit-company-btn-${company.id}`}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-sm text-red-600 hover:text-red-700"
                            onClick={() => handleDelete(company)}
                            data-testid={`delete-company-btn-${company.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        <Dialog open={showDialog} onOpenChange={setShowDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {editingCompany ? t("companies.editCompany") : t("companies.createCompany")}
              </DialogTitle>
              <DialogDescription>{t("companies.formDescription")}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t("companies.name")}</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="rounded-sm"
                  data-testid="company-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t("companies.description")}</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="rounded-sm"
                  data-testid="company-description-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t("companies.selectTrainings")}</Label>
                <div className="border border-slate-200 rounded-sm divide-y divide-slate-100 max-h-48 overflow-y-auto" data-testid="company-training-assignment">
                  {trainings.length > 0 ? (
                    trainings.map((training) => (
                      <label
                        key={training.id}
                        className="flex items-start gap-3 p-3 hover:bg-slate-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={formData.training_ids.includes(training.id)}
                          onChange={(e) => handleTrainingToggle(training.id, e.target.checked)}
                          className="mt-1 w-4 h-4"
                          data-testid={`company-training-${training.id}`}
                        />
                        <span className="text-sm">{training.title}</span>
                      </label>
                    ))
                  ) : (
                    <p className="p-3 text-sm text-slate-500">{t("companies.noTrainingsAvailable")}</p>
                  )}
                </div>
                <p className="text-xs text-slate-500">{t("companies.assignTrainingsHint")}</p>
              </div>
              <Button
                onClick={handleSave}
                disabled={saving}
                className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="save-company-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("companies.save")}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};
