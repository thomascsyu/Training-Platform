import "@/App.css";
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { DashboardLayout } from "@/components/DashboardLayout";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";

// Public landing page — small, eager is fine for first paint.
import { LandingPage } from "@/pages/LandingPage";

// Everything else loads on demand, splitting the bundle per route.
const LoginPage = lazy(() => import("@/pages/LoginPage").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/pages/RegisterPage").then((m) => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() => import("@/pages/ForgotPasswordPage").then((m) => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import("@/pages/ResetPasswordPage").then((m) => ({ default: m.ResetPasswordPage })));
const CoursesPage = lazy(() => import("@/pages/CoursesPage").then((m) => ({ default: m.CoursesPage })));
const CourseDetailPage = lazy(() => import("@/pages/CourseDetailPage").then((m) => ({ default: m.CourseDetailPage })));
const CheckoutPage = lazy(() => import("@/pages/CheckoutPage").then((m) => ({ default: m.CheckoutPage })));
const PaymentSuccessPage = lazy(() => import("@/pages/PaymentSuccessPage").then((m) => ({ default: m.PaymentSuccessPage })));
const StudentDashboard = lazy(() => import("@/pages/StudentDashboard").then((m) => ({ default: m.StudentDashboard })));
const AdminDashboard = lazy(() => import("@/pages/AdminDashboard").then((m) => ({ default: m.AdminDashboard })));
const ManagerDashboard = lazy(() => import("@/pages/ManagerDashboard").then((m) => ({ default: m.ManagerDashboard })));
const AdminAnalyticsPage = lazy(() => import("@/pages/AdminAnalyticsPage").then((m) => ({ default: m.AdminAnalyticsPage })));
const QuizPage = lazy(() => import("@/pages/QuizPage").then((m) => ({ default: m.QuizPage })));
const CertificatesPage = lazy(() => import("@/pages/CertificatesPage").then((m) => ({ default: m.CertificatesPage })));
const AdminCoursesPage = lazy(() => import("@/pages/AdminCoursesPage").then((m) => ({ default: m.AdminCoursesPage })));
const AdminUsersPage = lazy(() => import("@/pages/AdminUsersPage").then((m) => ({ default: m.AdminUsersPage })));
const AdminCompaniesPage = lazy(() => import("@/pages/AdminCompaniesPage").then((m) => ({ default: m.AdminCompaniesPage })));
const AdminCompanyDashboardPage = lazy(() => import("@/pages/AdminCompanyDashboardPage").then((m) => ({ default: m.AdminCompanyDashboardPage })));
const ManagerGroupProgressPage = lazy(() => import("@/pages/ManagerGroupProgressPage").then((m) => ({ default: m.ManagerGroupProgressPage })));
const AdminBulkEnrollPage = lazy(() => import("@/pages/AdminBulkEnrollPage").then((m) => ({ default: m.AdminBulkEnrollPage })));
const AdminCourseEditPage = lazy(() => import("@/pages/AdminCourseEditPage").then((m) => ({ default: m.AdminCourseEditPage })));
const AdminAISettingsPage = lazy(() => import("@/pages/AdminAISettingsPage").then((m) => ({ default: m.AdminAISettingsPage })));
const AdminStripeSettingsPage = lazy(() => import("@/pages/AdminStripeSettingsPage").then((m) => ({ default: m.AdminStripeSettingsPage })));
const AdminEmailNotificationsPage = lazy(() => import("@/pages/AdminEmailNotificationsPage").then((m) => ({ default: m.AdminEmailNotificationsPage })));
const AdminPaymentsPage = lazy(() => import("@/pages/AdminPaymentsPage").then((m) => ({ default: m.AdminPaymentsPage })));
const AdminCertificatesPage = lazy(() => import("@/pages/AdminCertificatesPage").then((m) => ({ default: m.AdminCertificatesPage })));
const AdminCertificateTemplatesPage = lazy(() => import("@/pages/AdminCertificateTemplatesPage").then((m) => ({ default: m.AdminCertificateTemplatesPage })));
const CertificateBuilderPage = lazy(() => import("@/pages/CertificateBuilderPage").then((m) => ({ default: m.CertificateBuilderPage })));

const RouteFallback = () => (
  // Skeletons beat spinners: layout doesn't jump when the chunk lands.
  <div className="p-6">
    <SkeletonGrid n={4} />
  </div>
);

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
          <Suspense fallback={<RouteFallback />}>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/courses" element={<CoursesPage />} />
              <Route path="/courses/:id" element={<CourseDetailPage />} />
              <Route path="/checkout/:courseId" element={<CheckoutPage />} />
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
                path="/admin/companies/:companyId/dashboard"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminCompanyDashboardPage />
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
                path="/admin/ai-settings"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminAISettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/stripe-settings"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminStripeSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/payments"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminPaymentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/email-notifications"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminEmailNotificationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/certificates"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminCertificatesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/certificate-builder"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <CertificateBuilderPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/certificate-templates"
                element={
                  <ProtectedRoute roles={["admin"]}>
                    <AdminCertificateTemplatesPage />
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
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
