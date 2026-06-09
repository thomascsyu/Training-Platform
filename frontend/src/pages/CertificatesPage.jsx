import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams, useSearchParams, Link } from "react-router-dom";
import { Toaster, toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import {
  BookOpen, GraduationCap, Users, PlayCircle, Award, MessageSquare,
  Menu, X, LogOut, Settings, ChevronRight, Plus, Trash2, Edit,
  Download, Send, Bot, FileText, Video, CheckCircle, Clock,
  DollarSign, Lock, Globe, BarChart3, Home, Loader2, Search, Languages
} from "lucide-react";
import { courseLanguages, languageNames } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { LanguageProvider, useLanguage } from "@/contexts/LanguageContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

import { DashboardLayout } from "@/components/DashboardLayout";

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
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-8">
          My Certificates
        </h1>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : certificates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <Award className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-4">No certificates yet. Complete a course to earn your first certificate!</p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

