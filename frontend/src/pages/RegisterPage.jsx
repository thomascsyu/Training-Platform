import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GraduationCap, Loader2 } from "lucide-react";
import { formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";

export const RegisterPage = () => {
  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(email, password, name);
      toast.success(t("auth.signUp"));
      navigate("/dashboard");
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
          <CardTitle className="text-2xl tracking-tight">{t("auth.createAccount")}</CardTitle>
          <CardDescription>{t("auth.joinLearnHub")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t("auth.fullName")}</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="register-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t("auth.email")}</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="register-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t("auth.password")}</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                minLength={8}
                data-testid="register-password-input"
              />
            </div>
            <Button
              type="submit"
              className="w-full btn-primary"
              disabled={loading}
              data-testid="register-submit-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : t("auth.signUp")}
            </Button>
          </form>
          <p className="text-center text-sm text-slate-600 mt-4">
            {t("auth.haveAccount")}{" "}
            <Link to="/login" className="text-[#002FA7] hover:underline" data-testid="login-link">
              {t("auth.signIn")}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
