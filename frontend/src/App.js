import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams, useSearchParams, Link } from "react-router-dom";
import axios from "axios";
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
  DollarSign, Lock, Globe, BarChart3, Home, Loader2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true
});

// Auth Context
const AuthContext = createContext(null);

const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const { data } = await API.get("/auth/me");
      setUser(data);
    } catch {
      setUser(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const { data } = await API.post("/auth/login", { email, password });
    setUser(data);
    return data;
  };

  const register = async (email, password, name, role = "student") => {
    const { data } = await API.post("/auth/register", { email, password, name, role });
    setUser(data);
    return data;
  };

  const logout = async () => {
    await API.post("/auth/logout");
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

const ProtectedRoute = ({ children, roles = [] }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F5F7]">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles.length > 0 && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Format API errors
const formatError = (error) => {
  const detail = error.response?.data?.detail;
  if (!detail) return error.message || "Something went wrong";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(e => e.msg || JSON.stringify(e)).join(" ");
  return String(detail);
};

// ============ LANDING PAGE ============
const LandingPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const { data } = await API.get("/courses");
      setCourses(data.slice(0, 6));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      {/* Header */}
      <header className="backdrop-blur-xl bg-white/80 border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 md:px-12 lg:px-24 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="logo">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium tracking-tight text-[#0A0B10]">LearnHub</span>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <Link to="/courses" className="text-slate-600 hover:text-[#002FA7] transition-colors" data-testid="nav-courses">Courses</Link>
            {user ? (
              <>
                <Link to="/dashboard" className="text-slate-600 hover:text-[#002FA7] transition-colors" data-testid="nav-dashboard">Dashboard</Link>
                <Button onClick={() => navigate("/dashboard")} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="get-started-btn">
                  Go to Dashboard
                </Button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-slate-600 hover:text-[#002FA7] transition-colors" data-testid="nav-login">Login</Link>
                <Button onClick={() => navigate("/register")} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="get-started-btn">
                  Get Started
                </Button>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-24 lg:py-32 px-6 md:px-12 lg:px-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#002FA7]/5 to-transparent" />
        <div className="container mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
          <div>
            <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-4">Online Learning Platform</p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl tracking-tight font-medium text-[#0A0B10] mb-6">
              Master New Skills with Expert-Led Courses
            </h1>
            <p className="text-base leading-relaxed text-slate-600 mb-8 max-w-lg">
              Access high-quality courses, take quizzes to test your knowledge, and earn certificates upon completion. Join thousands of learners today.
            </p>
            <div className="flex gap-4">
              <Button 
                onClick={() => navigate(user ? "/dashboard" : "/register")} 
                className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm px-8 py-6 text-lg"
                data-testid="hero-cta-btn"
              >
                Start Learning
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
              <Button 
                variant="outline" 
                onClick={() => navigate("/courses")} 
                className="border-slate-200 hover:bg-slate-50 rounded-sm px-8 py-6 text-lg"
                data-testid="browse-courses-btn"
              >
                Browse Courses
              </Button>
            </div>
          </div>
          <div className="hidden lg:block">
            <img 
              src="https://images.pexels.com/photos/3137073/pexels-photo-3137073.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" 
              alt="Learning" 
              className="rounded-sm shadow-lg"
            />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 md:px-12 lg:px-24 bg-white">
        <div className="container mx-auto">
          <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-4 text-center">Features</p>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl tracking-tight font-medium text-[#0A0B10] mb-12 text-center">
            Everything You Need to Succeed
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: Video, title: "Video Courses", desc: "Learn with high-quality video content from industry experts" },
              { icon: FileText, title: "Quizzes & Tests", desc: "Test your knowledge and track your progress with interactive quizzes" },
              { icon: Award, title: "Certificates", desc: "Earn customizable certificates upon successful course completion" },
              { icon: MessageSquare, title: "Community Forums", desc: "Connect with fellow learners and discuss course topics" },
              { icon: Bot, title: "AI Assistant", desc: "Get instant help from our AI-powered course assistant" },
              { icon: Download, title: "Downloadable Materials", desc: "Access course materials anytime, even offline" }
            ].map((f, i) => (
              <Card key={i} className="bg-white border border-slate-200 rounded-sm hover:-translate-y-1 hover:shadow-md transition-all duration-200" data-testid={`feature-card-${i}`}>
                <CardContent className="p-6">
                  <f.icon className="w-8 h-8 text-[#002FA7] mb-4" />
                  <h3 className="text-xl font-medium text-[#0A0B10] mb-2">{f.title}</h3>
                  <p className="text-slate-600">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Courses Preview */}
      {courses.length > 0 && (
        <section className="py-24 px-6 md:px-12 lg:px-24 bg-[#F4F5F7]">
          <div className="container mx-auto">
            <div className="flex justify-between items-center mb-12">
              <div>
                <p className="text-xs tracking-[0.2em] uppercase font-bold text-slate-500 mb-2">Popular Courses</p>
                <h2 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
                  Start Your Learning Journey
                </h2>
              </div>
              <Button variant="outline" onClick={() => navigate("/courses")} className="border-slate-200 rounded-sm" data-testid="view-all-courses-btn">
                View All <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="py-12 px-6 md:px-12 lg:px-24 bg-[#0A0B10] text-white">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-6 h-6 text-[#002FA7]" />
            <span className="font-medium">LearnHub</span>
          </div>
          <p className="text-slate-400 text-sm">© 2026 LearnHub. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

// ============ COURSE CARD ============
const CourseCard = ({ course, enrolled = false, showProgress = false, progress = 0 }) => {
  const navigate = useNavigate();
  
  return (
    <Card 
      className="bg-white border border-slate-200 rounded-sm hover:-translate-y-1 hover:shadow-md transition-all duration-200 cursor-pointer overflow-hidden"
      onClick={() => navigate(`/courses/${course.id}`)}
      data-testid={`course-card-${course.id}`}
    >
      <div className="aspect-video bg-slate-100 relative overflow-hidden">
        {course.thumbnail_url ? (
          <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5">
            <BookOpen className="w-12 h-12 text-[#002FA7]/40" />
          </div>
        )}
        {course.is_private && (
          <Badge className="absolute top-2 right-2 bg-slate-800 text-white rounded-sm">
            <Lock className="w-3 h-3 mr-1" /> Private
          </Badge>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="text-lg font-medium text-[#0A0B10] mb-2 line-clamp-1">{course.title}</h3>
        <p className="text-sm text-slate-600 line-clamp-2 mb-3">{course.description}</p>
        <div className="flex items-center justify-between">
          {course.is_free ? (
            <Badge variant="secondary" className="bg-green-100 text-green-700 rounded-sm">Free</Badge>
          ) : (
            <span className="font-medium text-[#002FA7]">${course.price?.toFixed(2)}</span>
          )}
          {showProgress && (
            <div className="flex items-center gap-2">
              <Progress value={progress} className="w-20 h-2" />
              <span className="text-xs text-slate-500">{progress}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// ============ AUTH PAGES ============
const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-white border border-slate-200 rounded-sm">
        <CardHeader className="text-center">
          <Link to="/" className="flex items-center justify-center gap-2 mb-4">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium text-[#0A0B10]">LearnHub</span>
          </Link>
          <CardTitle className="text-2xl tracking-tight">Welcome Back</CardTitle>
          <CardDescription>Sign in to continue learning</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input 
                id="email" 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="login-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input 
                id="password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="login-password-input"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
              disabled={loading}
              data-testid="login-submit-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign In"}
            </Button>
          </form>
          <p className="text-center text-sm text-slate-600 mt-4">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#002FA7] hover:underline" data-testid="register-link">
              Sign up
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(email, password, name, role);
      toast.success("Account created!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6">
      <Card className="w-full max-w-md bg-white border border-slate-200 rounded-sm">
        <CardHeader className="text-center">
          <Link to="/" className="flex items-center justify-center gap-2 mb-4">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium text-[#0A0B10]">LearnHub</span>
          </Link>
          <CardTitle className="text-2xl tracking-tight">Create Account</CardTitle>
          <CardDescription>Join LearnHub and start learning</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input 
                id="name" 
                value={name} 
                onChange={(e) => setName(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="register-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input 
                id="email" 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                data-testid="register-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input 
                id="password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-sm border-slate-300 focus:ring-[#002FA7]/20 focus:border-[#002FA7]"
                required
                minLength={6}
                data-testid="register-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label>Account Type</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger className="rounded-sm border-slate-300" data-testid="register-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="student">Student</SelectItem>
                  <SelectItem value="client_manager">Client Manager</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button 
              type="submit" 
              className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
              disabled={loading}
              data-testid="register-submit-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Account"}
            </Button>
          </form>
          <p className="text-center text-sm text-slate-600 mt-4">
            Already have an account?{" "}
            <Link to="/login" className="text-[#002FA7] hover:underline" data-testid="login-link">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

// ============ DASHBOARD LAYOUT ============
const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = user?.role === "admin" ? [
    { icon: Home, label: "Dashboard", path: "/dashboard" },
    { icon: BookOpen, label: "Courses", path: "/admin/courses" },
    { icon: Users, label: "Users", path: "/admin/users" },
    { icon: BarChart3, label: "Analytics", path: "/admin/analytics" }
  ] : user?.role === "client_manager" ? [
    { icon: Home, label: "Dashboard", path: "/dashboard" },
    { icon: Users, label: "Manage Groups", path: "/manager/groups" },
    { icon: BookOpen, label: "Courses", path: "/courses" }
  ] : [
    { icon: Home, label: "Dashboard", path: "/dashboard" },
    { icon: BookOpen, label: "My Courses", path: "/my-courses" },
    { icon: Award, label: "Certificates", path: "/certificates" }
  ];

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? "w-64" : "w-20"} bg-white border-r border-slate-200 transition-all duration-200 flex flex-col`}>
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          {sidebarOpen && (
            <Link to="/" className="flex items-center gap-2">
              <GraduationCap className="w-6 h-6 text-[#002FA7]" />
              <span className="font-medium text-[#0A0B10]">LearnHub</span>
            </Link>
          )}
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} className="rounded-sm" data-testid="toggle-sidebar-btn">
            <Menu className="w-5 h-5" />
          </Button>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <Button
              key={item.path}
              variant="ghost"
              className={`w-full justify-start rounded-sm ${sidebarOpen ? "" : "px-0 justify-center"}`}
              onClick={() => navigate(item.path)}
              data-testid={`nav-${item.label.toLowerCase().replace(" ", "-")}`}
            >
              <item.icon className="w-5 h-5" />
              {sidebarOpen && <span className="ml-3">{item.label}</span>}
            </Button>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-200">
          <div className={`flex items-center gap-3 ${sidebarOpen ? "" : "justify-center"}`}>
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                {user?.name?.charAt(0)?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name}</p>
                <p className="text-xs text-slate-500 capitalize">{user?.role?.replace("_", " ")}</p>
              </div>
            )}
          </div>
          <Button 
            variant="ghost" 
            className={`w-full mt-3 text-slate-600 rounded-sm ${sidebarOpen ? "justify-start" : "px-0 justify-center"}`}
            onClick={logout}
            data-testid="logout-btn"
          >
            <LogOut className="w-5 h-5" />
            {sidebarOpen && <span className="ml-3">Logout</span>}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};

// ============ STUDENT DASHBOARD ============
const StudentDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, enrollRes] = await Promise.all([
        API.get("/stats/student"),
        API.get("/enrollments/my")
      ]);
      setStats(statsRes.data);
      setEnrollments(enrollRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="student-dashboard">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-slate-600">Continue your learning journey</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-[#002FA7]/10 rounded-sm">
              <BookOpen className="w-6 h-6 text-[#002FA7]" />
            </div>
            <div>
              <p className="text-2xl font-medium">{stats?.enrolled_courses || 0}</p>
              <p className="text-sm text-slate-600">Enrolled Courses</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-sm">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-medium">{stats?.completed_courses || 0}</p>
              <p className="text-sm text-slate-600">Completed</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-sm">
              <Award className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-medium">{stats?.certificates || 0}</p>
              <p className="text-sm text-slate-600">Certificates</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Enrollments */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-medium">My Courses</h2>
          <Button variant="outline" onClick={() => navigate("/courses")} className="rounded-sm" data-testid="browse-more-btn">
            Browse More <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
        {enrollments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {enrollments.map((e) => (
              <Card 
                key={e.id} 
                className="bg-white border border-slate-200 rounded-sm cursor-pointer hover:-translate-y-1 hover:shadow-md transition-all"
                onClick={() => navigate(`/courses/${e.course_id}`)}
                data-testid={`enrollment-card-${e.course_id}`}
              >
                <div className="aspect-video bg-slate-100 relative overflow-hidden">
                  {e.course_thumbnail ? (
                    <img src={e.course_thumbnail} alt={e.course_title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5">
                      <BookOpen className="w-12 h-12 text-[#002FA7]/40" />
                    </div>
                  )}
                  {e.completed && (
                    <Badge className="absolute top-2 right-2 bg-green-600 text-white rounded-sm">
                      <CheckCircle className="w-3 h-3 mr-1" /> Completed
                    </Badge>
                  )}
                </div>
                <CardContent className="p-4">
                  <h3 className="font-medium text-[#0A0B10] mb-2">{e.course_title}</h3>
                  {e.completed ? (
                    <p className="text-sm text-green-600">Score: {e.score}%</p>
                  ) : (
                    <p className="text-sm text-slate-600">In Progress</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-4">You haven't enrolled in any courses yet</p>
              <Button onClick={() => navigate("/courses")} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="start-learning-btn">
                Start Learning
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

// ============ ADMIN DASHBOARD ============
const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const { data } = await API.get("/stats/admin");
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="admin-dashboard">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
          Admin Dashboard
        </h1>
        <p className="text-slate-600">Manage your learning platform</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-[#002FA7]/10 rounded-sm">
                <BookOpen className="w-6 h-6 text-[#002FA7]" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.total_courses || 0}</p>
                <p className="text-sm text-slate-600">Total Courses</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-sm">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.total_students || 0}</p>
                <p className="text-sm text-slate-600">Students</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-sm">
                <GraduationCap className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.total_enrollments || 0}</p>
                <p className="text-sm text-slate-600">Enrollments</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-sm">
                <Award className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-medium">{stats?.completed_courses || 0}</p>
                <p className="text-sm text-slate-600">Completions</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={() => navigate("/admin/courses")} className="w-full justify-start bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="manage-courses-btn">
              <BookOpen className="w-4 h-4 mr-2" /> Manage Courses
            </Button>
            <Button onClick={() => navigate("/admin/users")} variant="outline" className="w-full justify-start rounded-sm" data-testid="manage-users-btn">
              <Users className="w-4 h-4 mr-2" /> Manage Users
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============ COURSES LIST PAGE ============
const CoursesPage = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const { data } = await API.get("/courses");
      setCourses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      {/* Header */}
      <header className="backdrop-blur-xl bg-white/80 border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 md:px-12 lg:px-24 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium tracking-tight text-[#0A0B10]">LearnHub</span>
          </Link>
          <nav className="flex items-center gap-4">
            {user ? (
              <Button onClick={() => window.location.href = "/dashboard"} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="dashboard-btn">
                Dashboard
              </Button>
            ) : (
              <Button onClick={() => window.location.href = "/login"} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="login-btn">
                Login
              </Button>
            )}
          </nav>
        </div>
      </header>

      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-12" data-testid="courses-page">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-8">
          All Courses
        </h1>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No courses available yet</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

// ============ COURSE DETAIL PAGE ============
const CourseDetailPage = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [enrollment, setEnrollment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [forumPosts, setForumPosts] = useState([]);
  const [forumInput, setForumInput] = useState("");

  useEffect(() => {
    fetchCourse();
  }, [id]);

  const fetchCourse = async () => {
    try {
      const { data } = await API.get(`/courses/${id}`);
      setCourse(data);
      
      if (user) {
        // Check enrollment
        const enrollRes = await API.get("/enrollments/my");
        const enrolled = enrollRes.data.find(e => e.course_id === id);
        setEnrollment(enrolled);
        
        // Load chat and forum
        try {
          const [chatRes, forumRes] = await Promise.all([
            API.get(`/chat/${id}/history`),
            API.get(`/forums/${id}`)
          ]);
          setChatMessages(chatRes.data);
          setForumPosts(forumRes.data);
        } catch (e) {
          console.error(e);
        }
      }
    } catch (e) {
      toast.error(formatError(e));
      navigate("/courses");
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async () => {
    if (!user) {
      navigate("/login");
      return;
    }
    
    if (!course.is_free && course.price > 0) {
      // Redirect to payment
      setEnrolling(true);
      try {
        const { data } = await API.post("/payments/checkout", {
          course_id: id,
          origin_url: window.location.origin
        });
        window.location.href = data.url;
      } catch (e) {
        toast.error(formatError(e));
        setEnrolling(false);
      }
      return;
    }
    
    setEnrolling(true);
    try {
      await API.post("/enrollments", { course_id: id });
      toast.success("Enrolled successfully!");
      fetchCourse();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setEnrolling(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    setChatLoading(true);
    try {
      const { data } = await API.post("/chat", { course_id: id, message: chatInput });
      setChatMessages([...chatMessages, 
        { role: "user", content: chatInput },
        { role: "assistant", content: data.response }
      ]);
      setChatInput("");
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setChatLoading(false);
    }
  };

  const postToForum = async () => {
    if (!forumInput.trim()) return;
    
    try {
      const { data } = await API.post("/forums/posts", { course_id: id, content: forumInput });
      setForumPosts([data, ...forumPosts]);
      setForumInput("");
      toast.success("Posted!");
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  const getVideoEmbed = (url, type) => {
    if (!url) return null;
    
    if (type === "youtube") {
      const videoId = url.match(/(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/watch\?.+&v=))([\w-]{11})/)?.[1];
      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }
    } else if (type === "vimeo") {
      const videoId = url.match(/vimeo\.com\/(\d+)/)?.[1];
      if (videoId) {
        return `https://player.vimeo.com/video/${videoId}`;
      }
    }
    return url;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F5F7]">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      {/* Header */}
      <header className="backdrop-blur-xl bg-white/80 border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 md:px-12 lg:px-24 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <GraduationCap className="w-8 h-8 text-[#002FA7]" />
            <span className="text-xl font-medium tracking-tight text-[#0A0B10]">LearnHub</span>
          </Link>
          <nav className="flex items-center gap-4">
            {user && (
              <Button onClick={() => navigate("/dashboard")} variant="outline" className="rounded-sm" data-testid="back-dashboard-btn">
                Dashboard
              </Button>
            )}
          </nav>
        </div>
      </header>

      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-8" data-testid="course-detail-page">
        {/* Course Header */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            {course.video_url && (
              <div className="aspect-video bg-black rounded-sm overflow-hidden mb-6">
                <iframe
                  src={getVideoEmbed(course.video_url, course.video_type)}
                  className="w-full h-full"
                  allowFullScreen
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                />
              </div>
            )}
            <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-4">
              {course.title}
            </h1>
            <p className="text-slate-600 mb-4">{course.description}</p>
            <div className="flex gap-2">
              {course.is_free ? (
                <Badge className="bg-green-100 text-green-700 rounded-sm">Free</Badge>
              ) : (
                <Badge className="bg-[#002FA7] text-white rounded-sm">${course.price?.toFixed(2)}</Badge>
              )}
              {course.is_private && (
                <Badge variant="secondary" className="rounded-sm">
                  <Lock className="w-3 h-3 mr-1" /> Private
                </Badge>
              )}
            </div>
          </div>

          <div>
            <Card className="bg-white border border-slate-200 rounded-sm sticky top-24">
              <CardContent className="p-6">
                {enrollment ? (
                  <>
                    <div className="flex items-center gap-2 text-green-600 mb-4">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-medium">Enrolled</span>
                    </div>
                    {enrollment.completed && (
                      <div className="mb-4">
                        <p className="text-sm text-slate-600">Your Score: <span className="font-medium text-[#0A0B10]">{enrollment.score}%</span></p>
                      </div>
                    )}
                    <Button 
                      onClick={() => navigate(`/certificates`)} 
                      variant="outline" 
                      className="w-full rounded-sm"
                      disabled={!enrollment.completed}
                      data-testid="view-certificate-btn"
                    >
                      <Award className="w-4 h-4 mr-2" />
                      {enrollment.completed ? "View Certificate" : "Complete to get Certificate"}
                    </Button>
                  </>
                ) : (
                  <Button 
                    onClick={handleEnroll} 
                    className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                    disabled={enrolling}
                    data-testid="enroll-btn"
                  >
                    {enrolling ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : course.is_free ? (
                      "Enroll Now - Free"
                    ) : (
                      <>
                        <DollarSign className="w-4 h-4 mr-1" />
                        Buy Now - ${course.price?.toFixed(2)}
                      </>
                    )}
                  </Button>
                )}
                
                <Separator className="my-4" />
                
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Lessons</span>
                    <span className="font-medium">{course.lessons?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Quizzes</span>
                    <span className="font-medium">{course.quizzes?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Passing Score</span>
                    <span className="font-medium">{course.passing_score}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-white border border-slate-200 rounded-sm">
            <TabsTrigger value="overview" className="rounded-sm" data-testid="tab-overview">Overview</TabsTrigger>
            <TabsTrigger value="lessons" className="rounded-sm" data-testid="tab-lessons">Lessons</TabsTrigger>
            {enrollment && <TabsTrigger value="quizzes" className="rounded-sm" data-testid="tab-quizzes">Quizzes</TabsTrigger>}
            {enrollment && <TabsTrigger value="materials" className="rounded-sm" data-testid="tab-materials">Materials</TabsTrigger>}
            {enrollment && <TabsTrigger value="chat" className="rounded-sm" data-testid="tab-chat">AI Assistant</TabsTrigger>}
            {enrollment && <TabsTrigger value="forum" className="rounded-sm" data-testid="tab-forum">Forum</TabsTrigger>}
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardContent className="p-6">
                <h3 className="text-lg font-medium mb-4">About this course</h3>
                <p className="text-slate-600 whitespace-pre-wrap">{course.description}</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="lessons" className="mt-6">
            <div className="space-y-4">
              {course.lessons?.length > 0 ? course.lessons.map((lesson, idx) => (
                <Card key={lesson.id} className="bg-white border border-slate-200 rounded-sm">
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#002FA7]/10 rounded-sm flex items-center justify-center text-[#002FA7] font-medium">
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{lesson.title}</h4>
                      <p className="text-sm text-slate-600">{lesson.description}</p>
                    </div>
                    {lesson.video_url && <Video className="w-5 h-5 text-slate-400" />}
                  </CardContent>
                </Card>
              )) : (
                <Card className="bg-white border border-slate-200 rounded-sm">
                  <CardContent className="p-12 text-center">
                    <p className="text-slate-600">No lessons added yet</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="quizzes" className="mt-6">
            <div className="space-y-4">
              {course.quizzes?.length > 0 ? course.quizzes.map((quiz) => (
                <Card key={quiz.id} className="bg-white border border-slate-200 rounded-sm">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{quiz.title}</h4>
                      <p className="text-sm text-slate-600">Test your knowledge</p>
                    </div>
                    <Button 
                      onClick={() => navigate(`/quiz/${quiz.id}`)}
                      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                      data-testid={`take-quiz-${quiz.id}`}
                    >
                      Take Quiz
                    </Button>
                  </CardContent>
                </Card>
              )) : (
                <Card className="bg-white border border-slate-200 rounded-sm">
                  <CardContent className="p-12 text-center">
                    <p className="text-slate-600">No quizzes available yet</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="materials" className="mt-6">
            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardContent className="p-6">
                {course.materials?.length > 0 ? (
                  <div className="space-y-3">
                    {course.materials.map((m, idx) => (
                      <a 
                        key={idx}
                        href={m.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-3 border border-slate-200 rounded-sm hover:bg-slate-50 transition-colors"
                        data-testid={`material-${idx}`}
                      >
                        <FileText className="w-5 h-5 text-[#002FA7]" />
                        <span className="flex-1">{m.name}</span>
                        <Download className="w-4 h-4 text-slate-400" />
                      </a>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-600 text-center py-8">No downloadable materials available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="chat" className="mt-6">
            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Bot className="w-5 h-5 text-[#002FA7]" />
                  AI Course Assistant
                </CardTitle>
                <CardDescription>Ask questions about the course content</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-80 mb-4 border border-slate-200 rounded-sm p-4">
                  {chatMessages.length > 0 ? chatMessages.map((msg, idx) => (
                    <div key={idx} className={`mb-4 ${msg.role === "user" ? "text-right" : ""}`}>
                      <div className={`inline-block max-w-[80%] p-3 rounded-sm ${
                        msg.role === "user" ? "bg-[#002FA7] text-white" : "bg-slate-100 text-[#0A0B10]"
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  )) : (
                    <p className="text-slate-500 text-center py-8">Start a conversation with the AI assistant</p>
                  )}
                </ScrollArea>
                <div className="flex gap-2">
                  <Input 
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask a question..."
                    className="rounded-sm border-slate-300"
                    onKeyDown={(e) => e.key === "Enter" && sendChatMessage()}
                    data-testid="chat-input"
                  />
                  <Button 
                    onClick={sendChatMessage}
                    disabled={chatLoading}
                    className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                    data-testid="chat-send-btn"
                  >
                    {chatLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="forum" className="mt-6">
            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-[#002FA7]" />
                  Community Forum
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-6">
                  <Textarea 
                    value={forumInput}
                    onChange={(e) => setForumInput(e.target.value)}
                    placeholder="Share your thoughts or ask a question..."
                    className="rounded-sm border-slate-300 mb-2"
                    data-testid="forum-input"
                  />
                  <Button 
                    onClick={postToForum}
                    className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                    data-testid="forum-post-btn"
                  >
                    Post
                  </Button>
                </div>
                
                <div className="space-y-4">
                  {forumPosts.length > 0 ? forumPosts.map((post) => (
                    <div key={post.id} className="border border-slate-200 rounded-sm p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Avatar className="w-6 h-6">
                          <AvatarFallback className="text-xs bg-[#002FA7] text-white">
                            {post.user_name?.charAt(0)?.toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium text-sm">{post.user_name}</span>
                        <span className="text-xs text-slate-500">
                          {new Date(post.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-slate-700">{post.content}</p>
                      {post.replies?.length > 0 && (
                        <div className="ml-6 mt-3 space-y-2">
                          {post.replies.map((reply) => (
                            <div key={reply.id} className="border-l-2 border-slate-200 pl-3 py-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-sm">{reply.user_name}</span>
                                <span className="text-xs text-slate-500">
                                  {new Date(reply.created_at).toLocaleDateString()}
                                </span>
                              </div>
                              <p className="text-sm text-slate-600">{reply.content}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )) : (
                    <p className="text-slate-500 text-center py-8">No discussions yet. Be the first to post!</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// ============ QUIZ PAGE ============
const QuizPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetchQuiz();
  }, [id]);

  const fetchQuiz = async () => {
    try {
      const { data } = await API.get(`/quizzes/${id}`);
      setQuiz(data);
      setAnswers(new Array(data.questions?.length || 0).fill(-1));
    } catch (e) {
      toast.error(formatError(e));
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (answers.some(a => a === -1)) {
      toast.error("Please answer all questions");
      return;
    }
    
    setSubmitting(true);
    try {
      const { data } = await API.post(`/quizzes/${id}/submit`, { quiz_id: id, answers });
      setResult(data);
      if (data.passed) {
        toast.success("Congratulations! You passed!");
      } else {
        toast.error("You didn't pass. Try again!");
      }
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F5F7]">
        <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F5F7] py-8" data-testid="quiz-page">
      <div className="container mx-auto px-6 md:px-12 lg:px-24 max-w-3xl">
        <Card className="bg-white border border-slate-200 rounded-sm">
          <CardHeader>
            <CardTitle className="text-xl tracking-tight">{quiz?.title}</CardTitle>
            <CardDescription>Answer all questions to complete the quiz</CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="text-center py-8">
                <div className={`w-24 h-24 rounded-full mx-auto mb-4 flex items-center justify-center ${
                  result.passed ? "bg-green-100" : "bg-red-100"
                }`}>
                  {result.passed ? (
                    <CheckCircle className="w-12 h-12 text-green-600" />
                  ) : (
                    <X className="w-12 h-12 text-red-600" />
                  )}
                </div>
                <h3 className="text-2xl font-medium mb-2">
                  {result.passed ? "Congratulations!" : "Try Again"}
                </h3>
                <p className="text-slate-600 mb-4">
                  Your Score: <span className="font-medium">{result.score}%</span> ({result.correct}/{result.total} correct)
                </p>
                <p className="text-sm text-slate-500 mb-6">
                  Passing Score: {result.passing_score}%
                </p>
                <div className="flex gap-4 justify-center">
                  {result.passed ? (
                    <Button 
                      onClick={() => navigate("/certificates")}
                      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                      data-testid="view-certificate-btn"
                    >
                      <Award className="w-4 h-4 mr-2" /> View Certificate
                    </Button>
                  ) : (
                    <Button 
                      onClick={() => {
                        setResult(null);
                        setAnswers(new Array(quiz.questions?.length || 0).fill(-1));
                      }}
                      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                      data-testid="retry-btn"
                    >
                      Try Again
                    </Button>
                  )}
                  <Button 
                    onClick={() => navigate("/dashboard")}
                    variant="outline"
                    className="rounded-sm"
                    data-testid="back-dashboard-btn"
                  >
                    Back to Dashboard
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {quiz?.questions?.map((q, qIdx) => (
                  <div key={qIdx} className="border border-slate-200 rounded-sm p-4">
                    <p className="font-medium mb-4">
                      {qIdx + 1}. {q.question}
                    </p>
                    <div className="space-y-2">
                      {q.options?.map((opt, oIdx) => (
                        <label 
                          key={oIdx}
                          className={`flex items-center gap-3 p-3 rounded-sm border cursor-pointer transition-colors ${
                            answers[qIdx] === oIdx 
                              ? "border-[#002FA7] bg-[#002FA7]/5" 
                              : "border-slate-200 hover:bg-slate-50"
                          }`}
                          data-testid={`question-${qIdx}-option-${oIdx}`}
                        >
                          <input 
                            type="radio"
                            name={`question-${qIdx}`}
                            checked={answers[qIdx] === oIdx}
                            onChange={() => {
                              const newAnswers = [...answers];
                              newAnswers[qIdx] = oIdx;
                              setAnswers(newAnswers);
                            }}
                            className="w-4 h-4 text-[#002FA7]"
                          />
                          <span>{opt}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                
                <Button 
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm py-6"
                  data-testid="submit-quiz-btn"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Submit Quiz"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============ CERTIFICATES PAGE ============
const CertificatesPage = () => {
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
                    <Button variant="outline" className="rounded-sm" data-testid={`download-cert-${cert.id}`}>
                      <Download className="w-4 h-4 mr-2" /> Download
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

// ============ PAYMENT SUCCESS PAGE ============
const PaymentSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("checking");
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    }
  }, [sessionId]);

  const pollPaymentStatus = async (attempts = 0) => {
    if (attempts >= 5) {
      setStatus("timeout");
      return;
    }

    try {
      const { data } = await API.get(`/payments/status/${sessionId}`);
      if (data.payment_status === "paid") {
        setStatus("success");
      } else {
        setTimeout(() => pollPaymentStatus(attempts + 1), 2000);
      }
    } catch (e) {
      setStatus("error");
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex items-center justify-center p-6" data-testid="payment-success-page">
      <Card className="w-full max-w-md bg-white border border-slate-200 rounded-sm">
        <CardContent className="p-8 text-center">
          {status === "checking" && (
            <>
              <Loader2 className="w-12 h-12 animate-spin text-[#002FA7] mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Processing Payment...</h2>
              <p className="text-slate-600">Please wait while we confirm your payment.</p>
            </>
          )}
          {status === "success" && (
            <>
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Payment Successful!</h2>
              <p className="text-slate-600 mb-6">You have been enrolled in the course.</p>
              <Button 
                onClick={() => navigate("/my-courses")}
                className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                data-testid="go-to-courses-btn"
              >
                Go to My Courses
              </Button>
            </>
          )}
          {(status === "error" || status === "timeout") && (
            <>
              <X className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h2 className="text-xl font-medium mb-2">Something went wrong</h2>
              <p className="text-slate-600 mb-6">Please contact support if the issue persists.</p>
              <Button 
                onClick={() => navigate("/dashboard")}
                variant="outline"
                className="rounded-sm"
              >
                Back to Dashboard
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ============ ADMIN COURSES PAGE ============
const AdminCoursesPage = () => {
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    thumbnail_url: "",
    video_url: "",
    video_type: "youtube",
    price: 0,
    is_free: true,
    is_private: false,
    passing_score: 70
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const { data } = await API.get("/courses?include_private=true");
      setCourses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      await API.post("/courses", formData);
      toast.success("Course created!");
      setShowCreateDialog(false);
      setFormData({
        title: "",
        description: "",
        thumbnail_url: "",
        video_url: "",
        video_type: "youtube",
        price: 0,
        is_free: true,
        is_private: false,
        passing_score: 70
      });
      fetchCourses();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (courseId) => {
    if (!window.confirm("Are you sure you want to delete this course?")) return;
    
    try {
      await API.delete(`/courses/${courseId}`);
      toast.success("Course deleted!");
      fetchCourses();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-courses-page">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10]">
            Manage Courses
          </h1>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm" data-testid="create-course-btn">
                <Plus className="w-4 h-4 mr-2" /> Create Course
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Course</DialogTitle>
                <DialogDescription>Fill in the details to create a new course</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                <div className="space-y-2">
                  <Label>Title</Label>
                  <Input 
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="rounded-sm"
                    data-testid="course-title-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea 
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="rounded-sm"
                    rows={4}
                    data-testid="course-description-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Thumbnail URL</Label>
                  <Input 
                    value={formData.thumbnail_url}
                    onChange={(e) => setFormData({...formData, thumbnail_url: e.target.value})}
                    className="rounded-sm"
                    placeholder="https://..."
                    data-testid="course-thumbnail-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Video URL</Label>
                    <Input 
                      value={formData.video_url}
                      onChange={(e) => setFormData({...formData, video_url: e.target.value})}
                      className="rounded-sm"
                      placeholder="YouTube or Vimeo URL"
                      data-testid="course-video-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Video Type</Label>
                    <Select value={formData.video_type} onValueChange={(v) => setFormData({...formData, video_type: v})}>
                      <SelectTrigger className="rounded-sm" data-testid="course-video-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="youtube">YouTube</SelectItem>
                        <SelectItem value="vimeo">Vimeo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Price ($)</Label>
                    <Input 
                      type="number"
                      value={formData.price}
                      onChange={(e) => setFormData({...formData, price: parseFloat(e.target.value) || 0})}
                      className="rounded-sm"
                      disabled={formData.is_free}
                      data-testid="course-price-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Passing Score (%)</Label>
                    <Input 
                      type="number"
                      value={formData.passing_score}
                      onChange={(e) => setFormData({...formData, passing_score: parseInt(e.target.value) || 70})}
                      className="rounded-sm"
                      min={0}
                      max={100}
                      data-testid="course-passing-score-input"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Switch 
                      checked={formData.is_free}
                      onCheckedChange={(v) => setFormData({...formData, is_free: v, price: v ? 0 : formData.price})}
                      data-testid="course-free-switch"
                    />
                    <Label>Free Course</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch 
                      checked={formData.is_private}
                      onCheckedChange={(v) => setFormData({...formData, is_private: v})}
                      data-testid="course-private-switch"
                    />
                    <Label>Private Course</Label>
                  </div>
                </div>
                <Button 
                  onClick={handleCreate}
                  disabled={creating || !formData.title}
                  className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                  data-testid="submit-course-btn"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Course"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : courses.length > 0 ? (
          <div className="space-y-4">
            {courses.map((course) => (
              <Card key={course.id} className="bg-white border border-slate-200 rounded-sm" data-testid={`admin-course-${course.id}`}>
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-24 h-16 bg-slate-100 rounded-sm overflow-hidden flex-shrink-0">
                    {course.thumbnail_url ? (
                      <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <BookOpen className="w-6 h-6 text-slate-300" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{course.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {course.is_free ? (
                        <Badge variant="secondary" className="bg-green-100 text-green-700 rounded-sm text-xs">Free</Badge>
                      ) : (
                        <Badge className="bg-[#002FA7] text-white rounded-sm text-xs">${course.price}</Badge>
                      )}
                      {course.is_private && (
                        <Badge variant="outline" className="rounded-sm text-xs">Private</Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="icon" 
                      className="rounded-sm"
                      onClick={() => navigate(`/admin/courses/${course.id}/edit`)}
                      data-testid={`edit-course-${course.id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="icon" 
                      className="rounded-sm text-red-600 hover:text-red-700"
                      onClick={() => handleDelete(course.id)}
                      data-testid={`delete-course-${course.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white border border-slate-200 rounded-sm">
            <CardContent className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-4">No courses created yet</p>
              <Button onClick={() => setShowCreateDialog(true)} className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm">
                Create Your First Course
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

// ============ ADMIN USERS PAGE ============
const AdminUsersPage = () => {
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
      toast.success("Role updated!");
      fetchUsers();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-users-page">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-8">
          Manage Users
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
                    <th className="text-left p-4 font-medium text-slate-600">Name</th>
                    <th className="text-left p-4 font-medium text-slate-600">Email</th>
                    <th className="text-left p-4 font-medium text-slate-600">Role</th>
                    <th className="text-left p-4 font-medium text-slate-600">Actions</th>
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
                            <SelectItem value="client_manager">Client Manager</SelectItem>
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

// ============ CLIENT MANAGER GROUPS PAGE ============
const ManagerGroupsPage = () => {
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [coursesRes, usersRes] = await Promise.all([
        API.get("/courses?include_private=true"),
        API.get("/users?role=student")
      ]);
      setCourses(coursesRes.data);
      setStudents(usersRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkEnroll = async () => {
    if (!selectedCourse || selectedStudents.length === 0) {
      toast.error("Please select a course and at least one student");
      return;
    }
    
    setEnrolling(true);
    try {
      const { data } = await API.post("/enrollments", {
        course_id: selectedCourse,
        user_ids: selectedStudents
      });
      toast.success(data.message);
      setSelectedStudents([]);
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="manager-groups-page">
        <h1 className="text-2xl sm:text-3xl tracking-tight font-medium text-[#0A0B10] mb-8">
          Manage Group Enrollments
        </h1>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#002FA7]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg">Select Course</CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                  <SelectTrigger className="rounded-sm" data-testid="select-course-dropdown">
                    <SelectValue placeholder="Choose a course..." />
                  </SelectTrigger>
                  <SelectContent>
                    {courses.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            <Card className="bg-white border border-slate-200 rounded-sm">
              <CardHeader>
                <CardTitle className="text-lg">Select Students</CardTitle>
                <CardDescription>
                  {selectedStudents.length} selected
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-60 border border-slate-200 rounded-sm">
                  {students.map((s) => (
                    <label 
                      key={s.id}
                      className="flex items-center gap-3 p-3 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0"
                      data-testid={`student-${s.id}`}
                    >
                      <input 
                        type="checkbox"
                        checked={selectedStudents.includes(s.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedStudents([...selectedStudents, s.id]);
                          } else {
                            setSelectedStudents(selectedStudents.filter(id => id !== s.id));
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-[#002FA7] text-white text-sm">
                          {s.name?.charAt(0)?.toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-sm">{s.name}</p>
                        <p className="text-xs text-slate-500">{s.email}</p>
                      </div>
                    </label>
                  ))}
                </ScrollArea>
                <Button 
                  onClick={handleBulkEnroll}
                  disabled={enrolling || !selectedCourse || selectedStudents.length === 0}
                  className="w-full mt-4 bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                  data-testid="bulk-enroll-btn"
                >
                  {enrolling ? <Loader2 className="w-4 h-4 animate-spin" /> : `Enroll ${selectedStudents.length} Students`}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

// ============ MAIN APP ============
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" richColors />
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/courses/:id" element={<CourseDetailPage />} />
          <Route path="/payment/success" element={<PaymentSuccessPage />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardRouter />
            </ProtectedRoute>
          } />
          <Route path="/my-courses" element={
            <ProtectedRoute>
              <DashboardLayout><StudentDashboard /></DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/certificates" element={
            <ProtectedRoute>
              <CertificatesPage />
            </ProtectedRoute>
          } />
          <Route path="/quiz/:id" element={
            <ProtectedRoute>
              <QuizPage />
            </ProtectedRoute>
          } />

          {/* Admin Routes */}
          <Route path="/admin/courses" element={
            <ProtectedRoute roles={["admin"]}>
              <AdminCoursesPage />
            </ProtectedRoute>
          } />
          <Route path="/admin/users" element={
            <ProtectedRoute roles={["admin"]}>
              <AdminUsersPage />
            </ProtectedRoute>
          } />
          <Route path="/admin/analytics" element={
            <ProtectedRoute roles={["admin"]}>
              <DashboardLayout><AdminDashboard /></DashboardLayout>
            </ProtectedRoute>
          } />

          {/* Client Manager Routes */}
          <Route path="/manager/groups" element={
            <ProtectedRoute roles={["client_manager"]}>
              <ManagerGroupsPage />
            </ProtectedRoute>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

// Dashboard Router based on role
const DashboardRouter = () => {
  const { user } = useAuth();
  
  if (user?.role === "admin") {
    return <DashboardLayout><AdminDashboard /></DashboardLayout>;
  }
  if (user?.role === "client_manager") {
    return <DashboardLayout><StudentDashboard /></DashboardLayout>;
  }
  return <DashboardLayout><StudentDashboard /></DashboardLayout>;
};

export default App;
