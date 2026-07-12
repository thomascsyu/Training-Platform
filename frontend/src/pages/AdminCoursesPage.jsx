import { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Edit, Globe, Loader2, Plus, Search, Trash2 } from "lucide-react";
import { courseLanguages, getCourseLanguageDisplay } from "@/i18n";
import { API, formatError } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { TranslateDialog } from "@/components/TranslateDialog";
import { ThumbnailUpload } from "@/components/ThumbnailUpload";
import { CourseThumbnail } from "@/components/CourseThumbnail";
import PageHeader from "@/components/enhanced/PageHeader";
import EmptyState from "@/components/enhanced/EmptyState";
import { TableSkeleton } from "@/components/enhanced/Skeletons";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

export const AdminCoursesPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { lang, t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 10;
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    thumbnail_url: "",
    video_url: "",
    video_type: "youtube",
    price: 0,
    is_free: true,
    course_type: "free",
    is_private: false,
    passing_score: 70,
    language: "en",
    category: "",
    company_ids: []
  });
  const [creating, setCreating] = useState(false);

  const fetchCourses = useCallback(async () => {
    setLoading(true);
    try {
      const [coursesRes, companiesRes] = await Promise.all([
        API.get("/courses", {
          params: {
            include_private: true,
            paginate: true,
            skip: (page - 1) * pageSize,
            limit: pageSize,
            search: searchQuery || undefined,
            category: selectedCategory !== "all" ? selectedCategory : undefined,
            lang,
          },
        }),
        API.get("/companies"),
      ]);
      setCourses(coursesRes.data.items || []);
      setTotal(coursesRes.data.total || 0);
      setCategories(coursesRes.data.categories || []);
      setCompanies(companiesRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [lang, page, searchQuery, selectedCategory]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses, location.key]);

  useEffect(() => {
    setPage(1);
  }, [searchQuery, selectedCategory]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      await API.post("/courses", formData);
      toast.success(t("courses.createCourse") + " ✓");
      setShowCreateDialog(false);
      setFormData({
        title: "",
        description: "",
        thumbnail_url: "",
        video_url: "",
        video_type: "youtube",
        price: 0,
        is_free: true,
        course_type: "free",
        is_private: false,
        passing_score: 70,
        language: "en",
        category: "",
        company_ids: []
      });
      fetchCourses();
    } catch (e) {
      toast.error(formatError(e));
    } finally {
      setCreating(false);
    }
  };

  const handleCompanyToggle = (companyId, checked) => {
    setFormData((prev) => ({
      ...prev,
      company_ids: checked
        ? [...prev.company_ids, companyId]
        : prev.company_ids.filter((id) => id !== companyId)
    }));
  };

  const getCompanyName = (companyId) => {
    return companies.find((company) => company.id === companyId)?.name || "Unknown company";
  };

  const handleDelete = async (courseId) => {
    if (!window.confirm(t("toast.confirmDeleteCourse"))) return;
    
    try {
      await API.delete(`/courses/${courseId}`);
      toast.success(t("toast.courseDeleted"));
      fetchCourses();
    } catch (e) {
      toast.error(formatError(e));
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6" data-testid="admin-courses-page">
        <PageHeader overline="Admin" title={t("dashboard.manageCourses")}>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="btn-primary" data-testid="create-course-btn">
                <Plus className="w-4 h-4 mr-2" /> {t("courses.createCourse")}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{t("courses.createNew")}</DialogTitle>
                <DialogDescription>{t("courses.fillDetails")}</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pr-2">
                <div className="space-y-2">
                  <Label>{t("courses.title")}</Label>
                  <Input 
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="rounded-sm"
                    data-testid="course-title-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t("courses.description")}</Label>
                  <Textarea 
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="rounded-sm"
                    rows={4}
                    data-testid="course-description-input"
                  />
                </div>
                
                {/* Language Selection - NEW */}
                <div className="space-y-2">
                  <Label>{t("courses.language")}</Label>
                  <Select value={formData.language} onValueChange={(v) => setFormData({...formData, language: v})}>
                    <SelectTrigger className="rounded-sm" data-testid="course-language-select">
                      <Globe className="w-4 h-4 mr-2" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {courseLanguages.map(lang => (
                        <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <ThumbnailUpload
                  value={formData.thumbnail_url}
                  onChange={(url) => setFormData({ ...formData, thumbnail_url: url })}
                  testId="course-thumbnail-upload"
                />
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("courses.videoUrl")}</Label>
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
                      disabled={formData.course_type === "free"}
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
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>{t("courses.courseType")}</Label>
                    <Select
                      value={formData.course_type}
                      onValueChange={(v) => setFormData({
                        ...formData,
                        course_type: v,
                        is_free: v === "free",
                        price: v === "free" ? 0 : formData.price
                      })}
                    >
                      <SelectTrigger className="rounded-sm" data-testid="course-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="free">{t("courses.free")}</SelectItem>
                        <SelectItem value="payment_required">{t("courses.paymentRequired")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2 pt-6">
                    <Switch
                      checked={formData.is_private}
                      onCheckedChange={(v) => setFormData({...formData, is_private: v})}
                      data-testid="course-private-switch"
                    />
                    <Label>{t("courses.privateCourse")}</Label>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Assigned Companies</Label>
                  <div className="border border-slate-200 rounded-sm divide-y divide-slate-100" data-testid="course-company-assignment">
                    {companies.length > 0 ? (
                      companies.map((company) => (
                        <label
                          key={company.id}
                          className="flex items-start gap-3 p-3 hover:bg-slate-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={formData.company_ids.includes(company.id)}
                            onChange={(e) => handleCompanyToggle(company.id, e.target.checked)}
                            className="mt-1 w-4 h-4"
                            data-testid={`course-company-${company.id}`}
                          />
                          <span>
                            <span className="block text-sm font-medium">{company.name}</span>
                            {company.description && (
                              <span className="block text-xs text-slate-500">{company.description}</span>
                            )}
                          </span>
                        </label>
                      ))
                    ) : (
                      <p className="p-3 text-sm text-slate-500">Create companies before assigning courses to them.</p>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    Assigned company students are auto-enrolled. Leave blank to make the course available by normal visibility rules.
                  </p>
                </div>
                <Button 
                  onClick={handleCreate}
                  disabled={creating || !formData.title}
                  className="w-full bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
                  data-testid="submit-course-btn"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : t("courses.createCourse")}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </PageHeader>

        <div className="flex flex-col md:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              className="pl-9 rounded-sm"
              placeholder={t("courses.search")}
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              data-testid="admin-course-search-input"
            />
          </div>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-full md:w-56 rounded-sm" data-testid="admin-course-category-filter">
              <SelectValue placeholder={t("courses.category")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("courses.category")}</SelectItem>
              {categories.map((category) => (
                <SelectItem key={category} value={category}>
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <TableSkeleton rows={5} cols={1} />
        ) : courses.length > 0 ? (
          <div className="space-y-4">
            {courses.map((course) => (
              <Card key={course.id} className="card-swiss" data-testid={`admin-course-${course.id}`}>
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-24 h-16 bg-slate-100 rounded-sm overflow-hidden flex-shrink-0">
                    <CourseThumbnail
                      src={course.thumbnail_url}
                      alt={course.title}
                      testId={`admin-course-thumb-${course.id}`}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{course.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {course.language && (
                        <Badge className="bg-[#002FA7] text-white rounded-sm text-xs">
                          <Globe className="w-3 h-3 mr-1" />
                          {getCourseLanguageDisplay(course.language)}
                        </Badge>
                      )}
                      {(course.course_type || (course.is_free ? "free" : "payment_required")) === "free" ? (
                        <Badge variant="secondary" className="bg-green-100 text-green-700 rounded-sm text-xs">{t("courses.free")}</Badge>
                      ) : (
                        <Badge className="bg-amber-100 text-amber-700 rounded-sm text-xs">{t("courses.paymentRequired")} ${course.price}</Badge>
                      )}
                      {course.is_private && (
                        <Badge variant="outline" className="rounded-sm text-xs">Private</Badge>
                      )}
                      {(course.company_ids || []).map((companyId) => (
                        <Badge key={companyId} variant="outline" className="rounded-sm text-xs">
                          {getCompanyName(companyId)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <TranslateDialog courseId={course.id} courseTitle={course.title} onTranslated={fetchCourses} />
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
          <EmptyState
            icon={BookOpen}
            title="No courses created yet"
            actionLabel="Create Your First Course"
            onAction={() => setShowCreateDialog(true)}
            testId="admin-courses-empty"
          />
        )}

        {total > pageSize && (
          <Pagination className="mt-6">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(event) => {
                    event.preventDefault();
                    setPage((prev) => Math.max(1, prev - 1));
                  }}
                  className={page <= 1 ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
              <PaginationItem className="px-3 text-sm text-slate-600">
                {page} / {Math.max(1, Math.ceil(total / pageSize))}
              </PaginationItem>
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(event) => {
                    event.preventDefault();
                    if (page * pageSize < total) {
                      setPage((prev) => prev + 1);
                    }
                  }}
                  className={page * pageSize >= total ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
    </DashboardLayout>
  );
};

