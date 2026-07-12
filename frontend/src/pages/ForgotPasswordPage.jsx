import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { GraduationCap, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLanguage } from "@/contexts/LanguageContext";
import { formatError, requestPasswordReset } from "@/lib/api";

export const ForgotPasswordPage = () => {
  const { t } = useLanguage();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await requestPasswordReset(email);
      toast.success(t("auth.passwordResetEmailSent"));
    } catch (err) {
      toast.error(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6">
      <Card className="w-full max-w-md card-swiss card-indexed animate-enter">
        <CardHeader className="text-center">
          <Link to="/" className="flex items-center justify-center gap-2 mb-4">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="font-display text-xl text-[#0A0B10]">LearnHub</span>
          </Link>
          <CardTitle className="text-2xl tracking-tight">{t("auth.forgotPassword")}</CardTitle>
          <CardDescription>{t("auth.forgotPasswordHelp")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">{t("auth.email")}</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="forgot-password-email-input"
              />
            </div>
            <Button
              type="submit"
              className="w-full btn-primary"
              disabled={loading}
              data-testid="forgot-password-submit-btn"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                t("auth.sendResetLink")
              )}
            </Button>
          </form>

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
