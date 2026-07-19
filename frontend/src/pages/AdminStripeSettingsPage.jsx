import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, CreditCard, Loader2 } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

export const AdminStripeSettingsPage = () => {
  const { t } = useLanguage();
  const [settings, setSettings] = useState(null);
  const [apiKey, setApiKey] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [apiKeyChanged, setApiKeyChanged] = useState(false);
  const [webhookChanged, setWebhookChanged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const { data } = await API.get("/admin/stripe-settings");
      setSettings(data);
      setApiKey(data.api_key || "");
      setWebhookSecret(data.webhook_secret || "");
      setApiKeyChanged(false);
      setWebhookChanged(false);
      setTestResult(null);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {};
      if (apiKeyChanged) payload.api_key = apiKey.trim();
      if (webhookChanged) payload.webhook_secret = webhookSecret.trim();
      await API.put("/admin/stripe-settings", payload);
      toast.success(t("stripeSettings.saved"));
      await loadSettings();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const payload = {};
      if (apiKeyChanged && apiKey.trim()) {
        payload.api_key = apiKey.trim();
      }
      const { data } = await API.post("/admin/stripe-settings/test", payload);
      setTestResult(data);
      if (data.connected) {
        toast.success(t("stripeSettings.connectionOk"));
      } else {
        toast.error(data.error || t("stripeSettings.connectionFailed"));
      }
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setTesting(false);
    }
  };

  const sourceLabel = (source) => {
    if (source === "database") return t("stripeSettings.sourceDatabase");
    if (source === "environment") return t("stripeSettings.sourceEnvironment");
    return t("stripeSettings.notConfigured");
  };

  const statusBadge = () => {
    if (testResult) {
      return testResult.connected ? (
        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-green-200">
          <Activity className="w-3 h-3 mr-1" />
          {t("stripeSettings.connectionOk")}
        </Badge>
      ) : (
        <Badge variant="destructive">
          <Activity className="w-3 h-3 mr-1" />
          {t("stripeSettings.connectionFailed")}
        </Badge>
      );
    }
    return settings?.api_key_configured ? (
      <Badge variant="secondary">{sourceLabel(settings.api_key_source)}</Badge>
    ) : (
      <Badge variant="outline">{t("stripeSettings.notConfigured")}</Badge>
    );
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-stripe-settings-page">
        <PageHeader
          overline="Admin"
          title={t("stripeSettings.title")}
          description={t("stripeSettings.description")}
        />

        {loading ? (
          <SkeletonGrid n={1} />
        ) : (
          <div className="space-y-6 max-w-3xl">
            <Card className="card-swiss">
              <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
                <CardTitle className="font-display flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-[#002FA7]" />
                  {t("stripeSettings.credentials")}
                </CardTitle>
                {statusBadge()}
              </CardHeader>
              <CardContent className="space-y-6">
                <p className="text-sm text-slate-600">{t("stripeSettings.hint")}</p>

                <div className="space-y-2">
                  <Label htmlFor="stripe-api-key">{t("stripeSettings.apiKey")}</Label>
                  <Input
                    id="stripe-api-key"
                    type="password"
                    autoComplete="off"
                    value={apiKey}
                    onChange={(e) => {
                      setApiKey(e.target.value);
                      setApiKeyChanged(true);
                      setTestResult(null);
                    }}
                    placeholder={t("stripeSettings.apiKeyPlaceholder")}
                    className="rounded-sm"
                    data-testid="stripe-api-key-input"
                  />
                  <p className="text-xs text-slate-500">{t("stripeSettings.apiKeyHint")}</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="stripe-webhook-secret">{t("stripeSettings.webhookSecret")}</Label>
                  <Input
                    id="stripe-webhook-secret"
                    type="password"
                    autoComplete="off"
                    value={webhookSecret}
                    onChange={(e) => {
                      setWebhookSecret(e.target.value);
                      setWebhookChanged(true);
                    }}
                    placeholder={t("stripeSettings.webhookSecretPlaceholder")}
                    className="rounded-sm"
                    data-testid="stripe-webhook-secret-input"
                  />
                  <p className="text-xs text-slate-500">{t("stripeSettings.webhookSecretHint")}</p>
                  {settings?.webhook_secret_configured && (
                    <p className="text-xs text-slate-400">
                      {t("stripeSettings.currentSource", {
                        source: sourceLabel(settings.webhook_secret_source),
                      })}
                    </p>
                  )}
                </div>

                <div className="flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-sm"
                    onClick={handleTest}
                    disabled={testing || (!settings?.api_key_configured && !(apiKeyChanged && apiKey.trim()))}
                    data-testid="stripe-test-btn"
                  >
                    {testing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        {t("stripeSettings.testing")}
                      </>
                    ) : (
                      t("stripeSettings.testConnection")
                    )}
                  </Button>
                  <Button
                    type="button"
                    className="btn-primary"
                    onClick={handleSave}
                    disabled={saving || (!apiKeyChanged && !webhookChanged)}
                    data-testid="stripe-save-btn"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        {t("stripeSettings.saving")}
                      </>
                    ) : (
                      t("stripeSettings.save")
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
