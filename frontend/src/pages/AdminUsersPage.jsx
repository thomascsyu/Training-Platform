import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";
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
import { Plus, Trash2, Edit, Loader2, Upload } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { TableSkeleton } from "@/components/enhanced/Skeletons";

const emptyUserForm = {
  name: "",
  email: "",
  password: "",
  role: "student",
  company_id: "",
};

const parseCsvUsers = (text) => {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.map((line, index) => {
    const parts = line.split(",").map((part) => part.trim().replace(/^"|"$/g, ""));
    if (index === 0 && parts[0]?.toLowerCase() === "name") {
      return null;
    }
    return {
      name: parts[0] || "",
      email: parts[1] || "",
      password: parts[2] || "",
      role: parts[3] || "student",
    };
  }).filter(Boolean);
};

export const AdminUsersPage = () => {
  const { t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState(searchParams.get("company_id") || "all");
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState(emptyUserForm);
  const [importText, setImportText] = useState("");
  const [importCompanyId, setImportCompanyId] = useState(searchParams.get("company_id") || "");
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  useEffect(() => {
    const companyId = searchParams.get("company_id");
    if (companyId) {
      setSelectedCompany(companyId);
      setImportCompanyId(companyId);
    }
  }, [searchParams]);

  const fetchCompanies = async () => {
    try {
      const { data } = await API.get("/companies");
      setCompanies(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = selectedCompany !== "all" ? { company_id: selectedCompany } : {};
      const { data } = await API.get("/users", { params });
      setUsers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [selectedCompany]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCompanyFilterChange = (value) => {
    setSelectedCompany(value);
    if (value === "all") {
      searchParams.delete("company_id");
    } else {
      searchParams.set("company_id", value);
    }
    setSearchParams(searchParams);
  };

  const getCompanyName = (companyId) => {
    if (!companyId) return "—";
    return companies.find((c) => c.id === companyId)?.name || "—";
  };

  const openCreateDialog = () => {
    setEditingUser(null);
    setUserForm({
      ...emptyUserForm,
      company_id: selectedCompany !== "all" ? selectedCompany : "",
    });
    setShowUserDialog(true);
  };

  const openEditDialog = (user) => {
    setEditingUser(user);
    setUserForm({
      name: user.name,
      email: user.email,
      password: "",
      role: user.role,
      company_id: user.company_id || "",
    });
    setShowUserDialog(true);
  };

  const handleSaveUser = async () => {
    if (!userForm.name.trim() || !userForm.email.trim()) {
      toast.error(t("users.requiredFields"));
      return;
    }
    if (!editingUser && userForm.password.length < 8) {
      toast.error(t("users.passwordMinLength"));
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: userForm.name.trim(),
        email: userForm.email.trim(),
        role: userForm.role,
        company_id: userForm.company_id || null,
      };
      if (userForm.password) {
        payload.password = userForm.password;
      }

      if (editingUser) {
        await API.put(`/users/${editingUser.id}`, payload);
        toast.success(t("users.updated"));
      } else {
        await API.post("/users", { ...payload, password: userForm.password });
        toast.success(t("users.created"));
      }

      setShowUserDialog(false);
      setUserForm(emptyUserForm);
      setEditingUser(null);
      fetchUsers();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(t("users.confirmDelete"))) return;

    try {
      await API.delete(`/users/${user.id}`);
      toast.success(t("users.deleted"));
      fetchUsers();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await API.put(`/users/${userId}/role?role=${newRole}`);
      toast.success(t("toast.roleUpdated"));
      fetchUsers();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const handleImport = async () => {
    if (!importCompanyId) {
      toast.error(t("users.selectCompanyForImport"));
      return;
    }

    const rows = parseCsvUsers(importText);
    if (rows.length === 0) {
      toast.error(t("users.importEmpty"));
      return;
    }

    setImporting(true);
    try {
      const { data } = await API.post("/users/import", {
        company_id: importCompanyId,
        users: rows.map((row) => ({
          name: row.name,
          email: row.email,
          password: row.password || undefined,
          role: row.role || "student",
        })),
      });

      toast.success(data.message);
      if (data.error_count > 0 || data.skipped_count > 0) {
        toast.message(
          `${data.created_count} created, ${data.skipped_count} skipped, ${data.error_count} errors`
        );
      }
      setShowImportDialog(false);
      setImportText("");
      setSelectedCompany(importCompanyId);
      searchParams.set("company_id", importCompanyId);
      setSearchParams(searchParams);
      fetchUsers();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setImporting(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-users-page">
        <PageHeader overline="Admin" title={t("users.manageUsers")}>
          <Select value={selectedCompany} onValueChange={handleCompanyFilterChange}>
            <SelectTrigger className="w-full sm:w-56 rounded-sm" data-testid="company-filter-select">
              <SelectValue placeholder={t("users.filterByCompany")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("users.allCompanies")}</SelectItem>
              {companies.map((company) => (
                <SelectItem key={company.id} value={company.id}>
                  {company.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            className="rounded-sm"
            onClick={() => {
              setImportCompanyId(selectedCompany !== "all" ? selectedCompany : importCompanyId);
              setShowImportDialog(true);
            }}
            data-testid="import-users-btn"
          >
            <Upload className="w-4 h-4 mr-2" /> {t("users.importUsers")}
          </Button>
          <Button
            className="btn-primary"
            onClick={openCreateDialog}
            data-testid="add-user-btn"
          >
            <Plus className="w-4 h-4 mr-2" /> {t("users.addUser")}
          </Button>
        </PageHeader>

        {loading ? (
          <TableSkeleton rows={6} cols={5} />
        ) : (
          <Card className="card-swiss overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.name")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.email")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.company")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.role")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-500">
                        {t("users.noUsers")}
                      </td>
                    </tr>
                  ) : (
                    users.map((user) => (
                      <tr key={user.id} className="border-b border-slate-100" data-testid={`user-row-${user.id}`}>
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <Avatar className="w-8 h-8">
                              <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                                {user.name?.charAt(0)?.toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <span className="font-medium">{user.name}</span>
                          </div>
                        </td>
                        <td className="p-4 text-slate-600">{user.email}</td>
                        <td className="p-4 text-slate-600">{getCompanyName(user.company_id)}</td>
                        <td className="p-4">
                          <Badge variant={user.role === "admin" ? "default" : "secondary"} className="rounded-sm capitalize">
                            {user.role?.replace("_", " ")}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <div className="flex flex-wrap items-center gap-2">
                            <Select value={user.role} onValueChange={(v) => handleRoleChange(user.id, v)}>
                              <SelectTrigger className="w-36 rounded-sm" data-testid={`role-select-${user.id}`}>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="student">{t("users.student")}</SelectItem>
                                <SelectItem value="client_manager">{t("users.clientManager")}</SelectItem>
                                <SelectItem value="admin">{t("users.admin")}</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button
                              variant="outline"
                              size="sm"
                              className="rounded-sm"
                              onClick={() => openEditDialog(user)}
                              data-testid={`edit-user-btn-${user.id}`}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="rounded-sm text-red-600 hover:text-red-700"
                              onClick={() => handleDeleteUser(user)}
                              data-testid={`delete-user-btn-${user.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        <Dialog open={showUserDialog} onOpenChange={setShowUserDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{editingUser ? t("users.editUser") : t("users.addUser")}</DialogTitle>
              <DialogDescription>{t("users.formDescription")}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t("users.name")}</Label>
                <Input
                  value={userForm.name}
                  onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                  className="rounded-sm"
                  data-testid="user-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t("users.email")}</Label>
                <Input
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  className="rounded-sm"
                  data-testid="user-email-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{editingUser ? t("users.newPasswordOptional") : t("auth.password")}</Label>
                <Input
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  className="rounded-sm"
                  data-testid="user-password-input"
                />
              </div>
              <div className="space-y-2">
                <Label>{t("users.role")}</Label>
                <Select value={userForm.role} onValueChange={(v) => setUserForm({ ...userForm, role: v })}>
                  <SelectTrigger className="rounded-sm" data-testid="user-role-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="student">{t("users.student")}</SelectItem>
                    <SelectItem value="client_manager">{t("users.clientManager")}</SelectItem>
                    <SelectItem value="admin">{t("users.admin")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>{t("users.company")}</Label>
                <Select
                  value={userForm.company_id || "none"}
                  onValueChange={(v) => setUserForm({ ...userForm, company_id: v === "none" ? "" : v })}
                >
                  <SelectTrigger className="rounded-sm" data-testid="user-company-select">
                    <SelectValue placeholder={t("users.selectCompany")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">{t("users.noCompany")}</SelectItem>
                    {companies.map((company) => (
                      <SelectItem key={company.id} value={company.id}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleSaveUser}
                disabled={saving}
                className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="save-user-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("users.save")}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{t("users.importUsers")}</DialogTitle>
              <DialogDescription>{t("users.importDescription")}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t("users.company")}</Label>
                <Select value={importCompanyId} onValueChange={setImportCompanyId}>
                  <SelectTrigger className="rounded-sm" data-testid="import-company-select">
                    <SelectValue placeholder={t("users.selectCompany")} />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((company) => (
                      <SelectItem key={company.id} value={company.id}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>{t("users.csvData")}</Label>
                <Textarea
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  placeholder={t("users.csvPlaceholder")}
                  className="rounded-sm min-h-[180px] font-mono text-sm"
                  data-testid="import-csv-textarea"
                />
              </div>
              <Button
                onClick={handleImport}
                disabled={importing}
                className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="submit-import-btn"
              >
                {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : t("users.importUsers")}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};
