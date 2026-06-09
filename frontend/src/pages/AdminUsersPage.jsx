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

export const AdminUsersPage = () => {
  const { t } = useLanguage();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const { data } = await API.get("/users");
      setUsers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await API.put(`/users/${userId}/role?role=${newRole}`);
      toast.success(t("toast.roleUpdated"));
      fetchUsers();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-users-page">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-8">
          {t("users.manageUsers")}
        </h1>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.name")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.email")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.role")}</th>
                    <th className="text-left p-4 font-medium text-slate-600">{t("users.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-slate-100" data-testid={`user-row-${user.id}`}>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <Avatar className="w-8 h-8">
                            <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                              {user.name?.charAt(0)?.toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium">{user.name}</span>
                        </div>
                      </td>
                      <td className="p-4 text-slate-600">{user.email}</td>
                      <td className="p-4">
                        <Badge variant={user.role === "admin" ? "default" : "secondary"} className="rounded-sm capitalize">
                          {user.role?.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Select 
                          value={user.role} 
                          onValueChange={(v) => handleRoleChange(user.id, v)}
                        >
                          <SelectTrigger className="w-40 rounded-sm" data-testid={`role-select-${user.id}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="student">Student</SelectItem>
                            <SelectItem value="client_manager">{t("users.clientManager")}</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

