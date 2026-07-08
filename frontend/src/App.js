import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { DashboardLayout } from "@/components/DashboardLayout";

import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { CoursesPage } from "@/pages/CoursesPage";
import { CourseDetailPage } from "@/pages/CourseDetailPage";
import { PaymentSuccessPage } from "@/pages/PaymentSuccessPage";
import { StudentDashboard } from "@/pages/StudentDashboard";
import { AdminDashboard } from "@/pages/AdminDashboard";
import { ManagerDashboard } from "@/pages/ManagerDashboard";
import { AdminAnalyticsPage } from "@/pages/AdminAnalyticsPage";
import { QuizPage } from "@/pages/QuizPage";
import { CertificatesPage } from "@/pages/CertificatesPage";
import { AdminCoursesPage } from "@/pages/AdminCoursesPage";
import { AdminUsersPage } from "@/pages/AdminUsersPage";
import { AdminCompaniesPage } from "@/pages/AdminCompaniesPage";
import { ManagerGroupProgressPage } from "@/pages/ManagerGroupProgressPage";
import { AdminBulkEnrollPage } from "@/pages/AdminBulkEnrollPage";
import { AdminCourseEditPage } from "@/pages/AdminCourseEditPage";

const DashboardRouter = () => {
  const { user } = useAuth();

  if (user?.role === "admin") {
    return (
      <DashboardLayout>
        <AdminDashboard />
      </DashboardLayout>
    );
  }
  if (user?.role === "client_manager") {
    return <ManagerDashboard />;
  }
  return (
    <DashboardLayout>
      <StudentDashboard />
    </DashboardLayout>
  );
};

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" richColors />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/courses/:id" element={<CourseDetailPage />} />
            <Route path="/payment/success" element={<PaymentSuccessPage />} />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardRouter />
                </ProtectedRoute>
              }
            />
            <Route
              path="/my-courses"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <StudentDashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/certificates"
              element={
                <ProtectedRoute>
                  <CertificatesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/quiz/:id"
              element={
                <ProtectedRoute>
                  <QuizPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/courses"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <AdminCoursesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/courses/:id/edit"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <AdminCourseEditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <AdminUsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/companies"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <AdminCompaniesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <DashboardLayout>
                    <AdminAnalyticsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/bulk-enroll"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <AdminBulkEnrollPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/manager/progress"
              element={
                <ProtectedRoute roles={["admin", "client_manager"]}>
                  <ManagerGroupProgressPage />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
