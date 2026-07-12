import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Award, Download } from "lucide-react";
import { API, formatError } from "@/lib/api";
import { DashboardLayout } from "@/components/DashboardLayout";
import PageHeader from "@/components/enhanced/PageHeader";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";

export const CertificatesPage = () => {
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCertificates();
  }, []);

  const fetchCertificates = async () => {
    try {
      const { data } = await API.get("/certificates/my");
      setCertificates(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const downloadCertificate = async (certId, certCode) => {
    try {
      const response = await API.get(`/certificates/${certId}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `certificate-${certCode}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="certificates-page">
        <PageHeader overline="Achievements" title="My Certificates" />

        {loading ? (
          <TableSkeleton rows={3} cols={2} />
        ) : certificates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 stagger">
            {certificates.map((cert) => (
              <Card key={cert.id} className="bg-white border border-slate-200 rounded-sm overflow-hidden" data-testid={`certificate-${cert.id}`}>
                <div 
                  className="aspect-[16/10] p-8 flex flex-col items-center justify-center text-center"
                  style={{ 
                    background: `linear-gradient(135deg, ${cert.primary_color}15 0%, ${cert.secondary_color}15 100%)`,
                    borderBottom: `4px solid ${cert.primary_color}`
                  }}
                >
                  <Award className="w-16 h-16 mb-4" style={{ color: cert.primary_color }} />
                  <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-2">Certificate of Completion</p>
                  <h3 className="text-xl font-medium text-[#0A0B10] mb-2">{cert.course_title}</h3>
                  <p className="text-slate-600">Awarded to</p>
                  <p className="text-lg font-medium" style={{ color: cert.primary_color }}>{cert.user_name}</p>
                  <p className="text-sm text-slate-500 mt-4">Score: {cert.score}%</p>
                </div>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-500">Certificate ID: {cert.certificate_id}</p>
                      <p className="text-xs text-slate-500">
                        Issued: {new Date(cert.issued_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      className="rounded-sm"
                      onClick={() => downloadCertificate(cert.id, cert.certificate_id)}
                      data-testid={`download-cert-${cert.id}`}
                    >
                      <Download className="w-4 h-4 mr-2" /> Download PDF
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Award}
            title="No certificates yet"
            description="Complete a course to earn your first certificate!"
            testId="certificates-page-empty"
          />
        )}
      </div>
    </DashboardLayout>
  );
};

