import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { CheckCircle, Search, XCircle } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { PublicSiteHeader } from "@/components/PublicSiteHeader";
import { useLanguage } from "@/contexts/LanguageContext";

export const CertificateVerifyPage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { certificateId } = useParams();
  const [query, setQuery] = useState(certificateId || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const verify = async (code) => {
    if (!code?.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const { data } = await API.get(`/certificates/verify/${encodeURIComponent(code.trim())}`);
      setResult(data);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (certificateId) {
      verify(certificateId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [certificateId]);

  const handleSearch = () => {
    if (!query.trim()) return;
    navigate(`/certificates/verify/${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      <PublicSiteHeader variant="compact" />
      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-10 max-w-3xl" data-testid="certificate-verify-page">
        <h1 className="text-2xl font-medium text-[#0A0B10] mb-6">{t("certificate.verifyTitle")}</h1>
        <Card className="card-swiss mb-6">
          <CardContent className="p-6">
            <div className="flex gap-2">
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value.toUpperCase())}
                placeholder={t("certificate.enterCertificateId")}
                className="rounded-sm"
                data-testid="certificate-verify-input"
              />
              <Button onClick={handleSearch} className="btn-primary" disabled={loading} data-testid="certificate-verify-btn">
                <Search className="w-4 h-4 mr-2" />
                {t("certificate.verify")}
              </Button>
            </div>
          </CardContent>
        </Card>

        {loading && (
          <Card className="card-swiss">
            <CardContent className="p-6 text-slate-600">{t("common.loading")}</CardContent>
          </Card>
        )}

        {error && (
          <Card className="card-swiss border-red-200">
            <CardContent className="p-6 flex items-start gap-3 text-red-700">
              <XCircle className="w-5 h-5 mt-0.5" />
              <div>
                <p className="font-medium">{t("certificate.notVerified")}</p>
                <p className="text-sm">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {result && (
          <Card className="card-swiss border-green-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-700">
                <CheckCircle className="w-5 h-5" />
                {t("certificate.verified")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><span className="text-slate-500">{t("adminCertificates.certificateId")}:</span> {result.certificate_id}</p>
              <p><span className="text-slate-500">{t("adminCertificates.course")}:</span> {result.course_title}</p>
              <p><span className="text-slate-500">{t("adminCertificates.student")}:</span> {result.user_name}</p>
              <p><span className="text-slate-500">{t("adminCertificates.score")}:</span> {result.score}%</p>
              <p><span className="text-slate-500">{t("certificate.issuedOn")}:</span> {new Date(result.issued_at).toLocaleDateString()}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
