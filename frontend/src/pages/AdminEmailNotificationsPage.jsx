import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Bell, Loader2, Mail, Play, Save } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

const INACTIVE_EVENT_KEY = "inactive_enrolled";

export const AdminEmailNotificationsPage = () => {
  const [events, setEvents] = useState([]);
  const [placeholders, setPlaceholders] = useState([]);
  const [testEmail, setTestEmail] = useState("");
  const [testName, setTestName] = useState("Test Learner");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState({});
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const { data } = await API.get("/admin/email-notifications");
      setEvents(data.events || []);
      setPlaceholders(data.placeholders || []);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setLoading(false);
    }
  };

  const updateEvent = (key, field, value) => {
    setEvents((prev) =>
      prev.map((event) =>
        event.key === key ? { ...event, [field]: value } : event
      )
    );
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const payload = {
        events: Object.fromEntries(
          events.map((event) => [
            event.key,
            {
              enabled: event.enabled,
              subject: event.subject,
              html_content: event.html_content,
              text_content: event.text_content || "",
              inactivity_days: event.inactivity_days,
            },
          ])
        ),
      };
      const { data } = await API.put("/admin/email-notifications", payload);
      setEvents(data.events || []);
      setPlaceholders(data.placeholders || []);
      toast.success("Email notification settings saved.");
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSaving(false);
    }
  };

  const sendTest = async (eventKey) => {
    if (!testEmail.trim()) {
      toast.error("Enter a test email address first.");
      return;
    }
    setTesting((prev) => ({ ...prev, [eventKey]: true }));
    try {
      await API.post("/admin/email-notifications/test", {
        event_key: eventKey,
        email: testEmail.trim(),
        name: testName.trim() || "Test Learner",
      });
      toast.success("Test email triggered.");
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setTesting((prev) => ({ ...prev, [eventKey]: false }));
    }
  };

  const triggerInactivity = async () => {
    setTriggering(true);
    try {
      const { data } = await API.post("/admin/email-notifications/trigger-inactivity");
      toast.success(`${data.message}: ${data.triggered} triggered, ${data.skipped} skipped.`);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setTriggering(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-email-notifications-page">
        <PageHeader
          overline="Admin"
          title="Email Notifications"
          description="Choose which learner emails are sent, edit templates, and trigger reminder notifications."
        >
          <Button onClick={saveSettings} disabled={saving} className="btn-primary">
            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </PageHeader>

        {loading ? (
          <SkeletonGrid n={3} />
        ) : (
          <div className="space-y-6">
            <Card className="card-swiss">
              <CardHeader>
                <CardTitle className="font-display flex items-center gap-2">
                  <Mail className="w-5 h-5 text-[#002FA7]" />
                  Test and trigger
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 lg:grid-cols-[1fr_1fr_auto] gap-4 items-end">
                <div className="space-y-2">
                  <Label htmlFor="test-email">Test email</Label>
                  <Input
                    id="test-email"
                    type="email"
                    value={testEmail}
                    onChange={(e) => setTestEmail(e.target.value)}
                    placeholder="learner@example.com"
                    className="rounded-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="test-name">Test name</Label>
                  <Input
                    id="test-name"
                    value={testName}
                    onChange={(e) => setTestName(e.target.value)}
                    className="rounded-sm"
                  />
                </div>
                <Button
                  variant="outline"
                  className="rounded-sm"
                  onClick={triggerInactivity}
                  disabled={triggering}
                  data-testid="trigger-inactivity-email-btn"
                >
                  {triggering ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                  Trigger inactivity
                </Button>
              </CardContent>
            </Card>

            <Card className="card-swiss">
              <CardContent className="pt-6">
                <div className="flex flex-wrap gap-2">
                  <span className="text-sm font-medium text-slate-700 mr-2">Available placeholders:</span>
                  {placeholders.map((placeholder) => (
                    <Badge key={placeholder} variant="outline" className="font-mono rounded-sm">
                      {"{{"}{placeholder}{"}}"}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {events.map((event) => (
                <Card key={event.key} className="card-swiss">
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <CardTitle className="font-display flex items-center gap-2">
                          <Bell className="w-5 h-5 text-[#002FA7]" />
                          {event.label}
                        </CardTitle>
                        <p className="text-sm text-slate-500 mt-1">{event.description}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Label htmlFor={`${event.key}-enabled`} className="text-sm text-slate-600">
                          Enabled
                        </Label>
                        <Switch
                          id={`${event.key}-enabled`}
                          checked={!!event.enabled}
                          onCheckedChange={(checked) => updateEvent(event.key, "enabled", checked)}
                        />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {event.key === INACTIVE_EVENT_KEY && (
                      <div className="space-y-2">
                        <Label htmlFor={`${event.key}-days`}>No-login days before reminder</Label>
                        <Input
                          id={`${event.key}-days`}
                          type="number"
                          min="1"
                          max="365"
                          value={event.inactivity_days || 7}
                          onChange={(e) => updateEvent(event.key, "inactivity_days", Number(e.target.value))}
                          className="rounded-sm"
                        />
                      </div>
                    )}
                    <div className="space-y-2">
                      <Label htmlFor={`${event.key}-subject`}>Subject</Label>
                      <Input
                        id={`${event.key}-subject`}
                        value={event.subject || ""}
                        onChange={(e) => updateEvent(event.key, "subject", e.target.value)}
                        className="rounded-sm"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`${event.key}-html`}>HTML body</Label>
                      <Textarea
                        id={`${event.key}-html`}
                        value={event.html_content || ""}
                        onChange={(e) => updateEvent(event.key, "html_content", e.target.value)}
                        rows={8}
                        className="rounded-sm font-mono text-xs"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`${event.key}-text`}>Plain text body</Label>
                      <Textarea
                        id={`${event.key}-text`}
                        value={event.text_content || ""}
                        onChange={(e) => updateEvent(event.key, "text_content", e.target.value)}
                        rows={4}
                        className="rounded-sm font-mono text-xs"
                      />
                    </div>
                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        className="rounded-sm"
                        onClick={() => sendTest(event.key)}
                        disabled={testing[event.key]}
                        data-testid={`send-test-${event.key}-btn`}
                      >
                        {testing[event.key] ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Mail className="w-4 h-4 mr-2" />}
                        Send test
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
