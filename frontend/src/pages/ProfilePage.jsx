import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API, formatError } from "@/lib/api";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";

export const ProfilePage = () => {
  const { user, checkAuth } = useAuth();
  const { t } = useLanguage();
  const [name, setName] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  useEffect(() => {
    setName(user?.name || "");
  }, [user]);

  const handleSaveProfile = async () => {
    if (!name.trim()) {
      toast.error(t("users.requiredFields"));
      return;
    }
    setSavingProfile(true);
    try {
      await API.put("/auth/me", { name: name.trim() });
      await checkAuth();
      toast.success(t("profile.updated"));
    } catch (error) {
      toast.error(formatError(error));
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error(t("profile.passwordRequired"));
      return;
    }
    if (newPassword.length < 8) {
      toast.error(t("users.passwordMinLength"));
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error(t("auth.passwordsMustMatch"));
      return;
    }

    setChangingPassword(true);
    try {
      await API.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.success(t("profile.passwordChanged"));
    } catch (error) {
      toast.error(formatError(error));
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 max-w-3xl space-y-6" data-testid="profile-page">
        <h1 className="text-2xl font-medium text-[#0A0B10]">{t("nav.profile")}</h1>

        <Card className="card-swiss">
          <CardHeader>
            <CardTitle>{t("profile.accountInfo")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t("users.email")}</Label>
              <Input value={user?.email || ""} disabled className="rounded-sm" />
            </div>
            <div className="space-y-2">
              <Label>{t("users.role")}</Label>
              <Input value={user?.role?.replace("_", " ") || ""} disabled className="rounded-sm capitalize" />
            </div>
            <div className="space-y-2">
              <Label>{t("users.name")}</Label>
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="rounded-sm"
                data-testid="profile-name-input"
              />
            </div>
            <Button
              onClick={handleSaveProfile}
              disabled={savingProfile}
              className="btn-primary"
              data-testid="profile-save-btn"
            >
              {savingProfile ? t("common.loading") : t("common.save")}
            </Button>
          </CardContent>
        </Card>

        <Card className="card-swiss">
          <CardHeader>
            <CardTitle>{t("profile.changePassword")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t("profile.currentPassword")}</Label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                className="rounded-sm"
                data-testid="profile-current-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label>{t("profile.newPassword")}</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                className="rounded-sm"
                minLength={8}
                data-testid="profile-new-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label>{t("auth.confirmPassword")}</Label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className="rounded-sm"
                minLength={8}
                data-testid="profile-confirm-password-input"
              />
            </div>
            <Button
              onClick={handleChangePassword}
              disabled={changingPassword}
              className="btn-primary"
              data-testid="profile-change-password-btn"
            >
              {changingPassword ? t("common.loading") : t("profile.changePassword")}
            </Button>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};
