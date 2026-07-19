import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Activity, CheckCircle2, Copy, CreditCard, Loader2, ListOrdered } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

const looksLikePublishableKey = (value) => /^pk_(live|test)_/i.test((value || "").trim());
const looksLikeServerKey = (value) => /^(sk|rk)_(live|test)_/i.test((value || "").trim());
const looksLikeWebhookSecret = (value) => /^whsec_/i.test((value || "").trim());

const CURRENCY_OPTIONS = [
  "hkd", "usd", "sgd", "cny", "twd", "jpy", "krw", "eur", "gbp", "aud", "cad",
];

export const AdminStripeSettingsPage = () => {
  const { t } = useLanguage();
  const [settings, setSettings] = useState(null);
  const [apiKey, setApiKey] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [currency, setCurrency] = useState("hkd");
  const [apiKeyChanged, setApiKeyChanged] = useState(false);
  const [webhookChanged, setWebhookChanged] = useState(false);
  const [currencyChanged, setCurrencyChanged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const webhookUrl = useMemo(
    () => `${window.location.origin}/api/webhook/stripe`,
    []
  );

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const { data } = await API.get("/admin/stripe-settings");
      setSettings(data);
      setApiKey(data.api_key || "");
      setWebhookSecret(data.webhook_secret || "");
      setCurrency((data.currency || "hkd").toLowerCase());
      setApiKeyChanged(false);
      setWebhookChanged(false);
      setCurrencyChanged(false);
      setTestResult(null);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const validateBeforeSave = () => {
    if (apiKeyChanged && apiKey.trim()) {
      if (looksLikePublishableKey(apiKey)) {
        toast.error(t("stripeSettings.rejectPublishableKey"));
        return false;
      }
      if (!looksLikeServerKey(apiKey)) {
        toast.error(t("stripeSettings.rejectInvalidApiKey"));
        return false;
      }
    }
    if (webhookChanged && webhookSecret.trim() && !looksLikeWebhookSecret(webhookSecret)) {
      toast.error(t("stripeSettings.rejectInvalidWebhookSecret"));
      return false;
    }
    return true;
  };

  const handleSave = async () => {
    if (!validateBeforeSave()) return;

    setSaving(true);
    try {
      const payload = {};
      if (apiKeyChanged) payload.api_key = apiKey.trim();
      if (webhookChanged) payload.webhook_secret = webhookSecret.trim();
      if (currencyChanged) payload.currency = currency.trim().toLowerCase();
      await API.put("/admin/stripe-settings", payload);
      toast.success(t("stripeSettings.saved"));
      await loadSettings();
      // Reload so course prices refresh without a full page refresh.
      window.dispatchEvent(new Event("learnhub:currency-changed"));
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (apiKeyChanged && apiKey.trim()) {
      if (looksLikePublishableKey(apiKey)) {
        toast.error(t("stripeSettings.rejectPublishableKey"));
        return;
      }
      if (!looksLikeServerKey(apiKey)) {
        toast.error(t("stripeSettings.rejectInvalidApiKey"));
        return;
      }
    }

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

  const copyWebhookUrl = async () => {
    try {
      await navigator.clipboard.writeText(webhookUrl);
      toast.success(t("stripeSettings.webhookUrlCopied"));
    } catch {
      toast.error(t("stripeSettings.webhookUrlCopyFailed"));
    }
  };

  const sourceLabel = (source) => {
    if (source === "database") return t("stripeSettings.sourceDatabase");
    if (source === "environment") return t("stripeSettings.sourceEnvironment");
    if (source === "default") return t("stripeSettings.sourceDefault");
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

  const setupSteps = [
    t("stripeSettings.step1"),
    t("stripeSettings.step2"),
    t("stripeSettings.step3"),
    t("stripeSettings.step4"),
  ];

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-stripe-settings-page">
        <PageHeader
          overline="Admin"
          title={t("stripeSettings.title")}
          description={t("stripeSettings.description")}
        />

        {loading ? (
          <SkeletonGrid n={2} />
        ) : (
          <div className="space-y-6 max-w-3xl">
            <Card className="card-swiss" data-testid="stripe-setup-guide">
              <CardHeader>
                <CardTitle className="font-display flex items-center gap-2">
                  <ListOrdered className="w-5 h-5 text-[#002FA7]" />
                  {t("stripeSettings.setupTitle")}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ol className="list-decimal pl-5 space-y-2 text-sm text-slate-600">
                  {setupSteps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>

                <div className="space-y-2">
                  <Label htmlFor="stripe-webhook-url">{t("stripeSettings.webhookUrl")}</Label>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Input
                      id="stripe-webhook-url"
                      readOnly
                      value={webhookUrl}
                      className="rounded-sm font-mono text-xs sm:text-sm"
                      data-testid="stripe-webhook-url"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      className="rounded-sm shrink-0"
                      onClick={copyWebhookUrl}
                      data-testid="stripe-copy-webhook-url-btn"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      {t("stripeSettings.copyWebhookUrl")}
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500">{t("stripeSettings.webhookUrlHint")}</p>
                </div>
              </CardContent>
            </Card>

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
                  {settings?.api_key_configured && (
                    <p className="text-xs text-slate-400">
                      {t("stripeSettings.currentSource", {
                        source: sourceLabel(settings.api_key_source),
                      })}
                    </p>
                  )}
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

                <div className="space-y-2">
                  <Label htmlFor="stripe-currency">{t("stripeSettings.currency")}</Label>
                  <Select
                    value={currency}
                    onValueChange={(value) => {
                      setCurrency(value);
                      setCurrencyChanged(true);
                    }}
                  >
                    <SelectTrigger
                      id="stripe-currency"
                      className="rounded-sm"
                      data-testid="stripe-currency-select"
                    >
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CURRENCY_OPTIONS.map((code) => (
                        <SelectItem key={code} value={code}>
                          {code.toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">{t("stripeSettings.currencyHint")}</p>
                  {settings?.currency && (
                    <p className="text-xs text-slate-400">
                      {t("stripeSettings.currentSource", {
                        source: sourceLabel(settings.currency_source),
                      })}
                    </p>
                  )}
                </div>

                {testResult?.connected && (
                  <div
                    className="rounded-sm border border-green-200 bg-green-50 p-4 text-sm text-green-900 space-y-1"
                    data-testid="stripe-test-success-details"
                  >
                    <p className="font-medium flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      {t("stripeSettings.connectionOk")}
                    </p>
                    {testResult.account_id && (
                      <p>
                        {t("stripeSettings.accountId")}:{" "}
                        <span className="font-mono">{testResult.account_id}</span>
                      </p>
                    )}
                    <p>
                      {t("stripeSettings.mode")}:{" "}
                      {testResult.livemode
                        ? t("stripeSettings.modeLive")
                        : t("stripeSettings.modeTest")}
                    </p>
                    {testResult.default_currency && (
                      <p>
                        {t("stripeSettings.accountDefaultCurrency")}:{" "}
                        <span className="font-mono uppercase">
                          {testResult.default_currency}
                        </span>
                      </p>
                    )}
                  </div>
                )}

                {testResult && !testResult.connected && testResult.error && (
                  <div
                    className="rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-800"
                    data-testid="stripe-test-error-details"
                  >
                    {testResult.error}
                  </div>
                )}

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
                    disabled={saving || (!apiKeyChanged && !webhookChanged && !currencyChanged)}
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
