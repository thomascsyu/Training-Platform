import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Activity, KeyRound } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

const PROVIDERS = ["deepseek", "xai"];

const emptyDraft = () => ({
  apiKey: "",
  model: "",
  enabled: true,
  keyChanged: false,
});

export const AdminAISettingsPage = () => {
  const { t } = useLanguage();
  const [settings, setSettings] = useState(null);
  const [draft, setDraft] = useState({
    deepseek: emptyDraft(),
    xai: emptyDraft(),
  });
  const [defaultProvider, setDefaultProvider] = useState("deepseek");
  const [defaultPrompt, setDefaultPrompt] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState({});
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const { data } = await API.get("/admin/ai-settings");
      setSettings(data);
      setDefaultProvider(data.default_provider || "deepseek");
      setDefaultPrompt(data.default_prompt || "");
      setDraft((prev) => {
        const next = { ...prev };
        for (const key of PROVIDERS) {
          const cfg = data.providers?.[key] || {};
          next[key] = {
            apiKey: cfg.api_key || "",
            model: cfg.model || "",
            enabled: cfg.enabled ?? true,
            keyChanged: false,
          };
        }
        return next;
      });
      setTestResults({});
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const updateDraft = (provider, field, value) => {
    setDraft((prev) => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        [field]: value,
        keyChanged: field === "apiKey" ? true : prev[provider].keyChanged,
      },
    }));
    setTestResults((prev) => ({ ...prev, [provider]: undefined }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        default_provider: defaultProvider,
        default_prompt: defaultPrompt,
        providers: {},
      };
      for (const key of PROVIDERS) {
        const d = draft[key];
        payload.providers[key] = {
          model: d.model,
          enabled: d.enabled,
        };
        if (d.keyChanged) {
          payload.providers[key].api_key = d.apiKey;
        }
      }
      await API.put("/admin/ai-settings", payload);
      toast.success(t("aiSettings.saved"));
      await loadSettings();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (provider) => {
    setTesting((prev) => ({ ...prev, [provider]: true }));
    try {
      const payload = { provider };
      const d = draft[provider];
      if (d.keyChanged && d.apiKey.trim()) {
        payload.api_key = d.apiKey.trim();
      }
      const { data } = await API.post("/admin/ai-settings/test", payload);
      setTestResults((prev) => ({ ...prev, [provider]: data }));
      if (data.connected) {
        toast.success(
          `${t("aiSettings.connectionOk")} (${t("aiSettings.latency", { ms: data.latency_ms })})`
        );
      } else {
        toast.error(data.error || t("aiSettings.connectionFailed"));
      }
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setTesting((prev) => ({ ...prev, [provider]: false }));
    }
  };

  const statusBadge = (provider) => {
    const result = testResults[provider];
    if (result) {
      return result.connected ? (
        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 border-green-200">
          <Activity className="w-3 h-3 mr-1" />
          {t("aiSettings.connectionOk")}
          {result.latency_ms != null && (
            <span className="ml-1">({t("aiSettings.latency", { ms: result.latency_ms })})</span>
          )}
        </Badge>
      ) : (
        <Badge variant="destructive">
          <Activity className="w-3 h-3 mr-1" />
          {t("aiSettings.connectionFailed")}
        </Badge>
      );
    }
    const hasKey = !!settings?.providers?.[provider]?.api_key;
    return hasKey ? (
      <Badge variant="secondary">
        {t("aiSettings.connectionOk")}
      </Badge>
    ) : (
      <Badge variant="outline">{t("aiSettings.notConfigured")}</Badge>
    );
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-ai-settings-page">
        <PageHeader overline="Admin" title={t("aiSettings.title")} description={t("aiSettings.description")} />

        {loading ? (
          <SkeletonGrid n={2} />
        ) : (
          <div className="space-y-6 max-w-3xl">
            <Card className="card-swiss">
              <CardHeader>
                <CardTitle className="font-display">{t("aiSettings.defaultProvider")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <Select value={defaultProvider} onValueChange={setDefaultProvider}>
                  <SelectTrigger className="w-full sm:w-64 rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="deepseek">{t("aiSettings.deepseek")}</SelectItem>
                    <SelectItem value="xai">{t("aiSettings.xai")}</SelectItem>
                  </SelectContent>
                </Select>

                <div className="space-y-2">
                  <Label htmlFor="default-prompt">{t("aiSettings.defaultPrompt")}</Label>
                  <Textarea
                    id="default-prompt"
                    value={defaultPrompt}
                    onChange={(e) => setDefaultPrompt(e.target.value)}
                    placeholder={t("aiSettings.defaultPromptPlaceholder")}
                    rows={4}
                    className="rounded-sm"
                  />
                  <p className="text-xs text-slate-500">{t("aiSettings.defaultPromptHint")}</p>
                </div>
              </CardContent>
            </Card>

            {PROVIDERS.map((provider) => (
              <Card key={provider} className="card-swiss">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-display flex items-center gap-2">
                      <KeyRound className="w-5 h-5 text-[#002FA7]" />
                      {t(`aiSettings.${provider}`)}
                    </CardTitle>
                    <div className="flex items-center gap-3">
                      {statusBadge(provider)}
                      <div className="flex items-center gap-2">
                        <Label htmlFor={`${provider}-enabled`} className="text-sm text-slate-600">
                          {t("aiSettings.enabled")}
                        </Label>
                        <Switch
                          id={`${provider}-enabled`}
                          checked={draft[provider].enabled}
                          onCheckedChange={(checked) => updateDraft(provider, "enabled", checked)}
                        />
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor={`${provider}-api-key`}>{t("aiSettings.apiKey")}</Label>
                    <Input
                      id={`${provider}-api-key`}
                      type="password"
                      value={draft[provider].apiKey}
                      onChange={(e) => updateDraft(provider, "apiKey", e.target.value)}
                      placeholder={settings?.providers?.[provider]?.api_key ? "••••••••" : ""}
                      className="rounded-sm"
                    />
                    <p className="text-xs text-slate-500">{t("aiSettings.apiKeyHint")}</p>
                    <p className="text-xs text-slate-400">{t(`aiSettings.${provider}Hint`)}</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor={`${provider}-model`}>{t("aiSettings.model")}</Label>
                    <Input
                      id={`${provider}-model`}
                      value={draft[provider].model}
                      onChange={(e) => updateDraft(provider, "model", e.target.value)}
                      className="rounded-sm"
                    />
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <Button
                      variant="outline"
                      onClick={() => handleTest(provider)}
                      disabled={testing[provider]}
                      className="rounded-sm"
                    >
                      {testing[provider] ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Activity className="w-4 h-4 mr-2" />
                      )}
                      {testing[provider] ? t("aiSettings.testing") : t("aiSettings.testConnection")}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}

            <div className="flex justify-end">
              <Button
                onClick={handleSave}
                disabled={saving}
                className="btn-primary"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {saving ? t("aiSettings.saving") : t("aiSettings.save")}
              </Button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
