import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { GraduationCap, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLanguage } from "@/contexts/LanguageContext";
import { formatError, resetPassword } from "@/lib/api";

export const ResetPasswordPage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const token = useMemo(() => (searchParams.get("token") || "").trim(), [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) {
      toast.error(t("auth.invalidResetLink"));
      return;
    }
    if (password !== confirmPassword) {
      toast.error(t("auth.passwordsMustMatch"));
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      toast.success(t("auth.passwordResetSuccess"));
      navigate("/login");
    } catch (err) {
      toast.error(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-white border border-slate-200 rounded-sm">
        <CardHeader className="text-center">
          <Link to="/" className="flex items-center justify-center gap-2 mb-4">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium text-[#0A0B10]">LearnHub</span>
          </Link>
          <CardTitle className="text-2xl tracking-tight">{t("auth.resetPassword")}</CardTitle>
          <CardDescription>{t("auth.resetPasswordHelp")}</CardDescription>
        </CardHeader>
        <CardContent>
          {!token ? (
            <div className="space-y-4">
              <p className="text-sm text-slate-700">{t("auth.invalidResetLink")}</p>
              <Link to="/forgot-password" className="text-[#002FA7] hover:underline text-sm">
                {t("auth.requestNewResetLink")}
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">{t("auth.newPassword")}</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                  required
                  minLength={8}
                  data-testid="reset-password-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t("auth.confirmPassword")}</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                  required
                  minLength={8}
                  data-testid="reset-confirm-password-input"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                disabled={loading}
                data-testid="reset-password-submit-btn"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  t("auth.updatePassword")
                )}
              </Button>
            </form>
          )}

          <p className="text-center text-sm text-slate-600 mt-4">
            <Link to="/login" className="text-[#002FA7] hover:underline">
              {t("auth.backToSignIn")}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
