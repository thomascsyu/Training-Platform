import { useState, useEffect, useCallback } from "react";
import { BookOpen, Globe, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { courseLanguages } from "@/i18n";
import { API } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { PublicSiteHeader } from "@/components/PublicSiteHeader";
import { CourseCard } from "@/components/CourseCard";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { SkeletonGrid } from "@/components/enhanced/Skeletons";
import EmptyState from "@/components/enhanced/EmptyState";

export const CoursesPage = () => {
  const { lang, t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 9;

  const fetchCourses = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        paginate: true,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        lang,
      };
      if (selectedLanguage && selectedLanguage !== "all") params.language = selectedLanguage;
      if (selectedCategory && selectedCategory !== "all") params.category = selectedCategory;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const { data } = await API.get("/courses", { params });
      setCourses(data.items || []);
      setTotal(data.total || 0);
      setCategories(data.categories || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [lang, page, searchQuery, selectedCategory, selectedLanguage]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  useEffect(() => {
    setPage(1);
  }, [searchQuery, selectedLanguage, selectedCategory]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div className="min-h-screen bg-[#F4F5F7]">
      <PublicSiteHeader variant="compact" />

      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-12" data-testid="courses-page">
        <h1 className="font-display text-2xl sm:text-3xl tracking-tight text-[#0A0B10] mb-6">
          {t("courses.allCourses")}
        </h1>

        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <Input
              placeholder={t("courses.search")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-sm border-slate-300"
              data-testid="course-search-input"
            />
          </div>
          <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
            <SelectTrigger
              className="w-[200px] rounded-sm border-slate-300"
              data-testid="language-filter"
            >
              <Globe className="w-4 h-4 mr-2" />
              <SelectValue placeholder={t("courses.allLanguages")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("courses.allLanguages")}</SelectItem>
              {courseLanguages.map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  {lang.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger
              className="w-[220px] rounded-sm border-slate-300"
              data-testid="category-filter"
            >
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
          <SkeletonGrid n={6} />
        ) : courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger">
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        ) : (
          <EmptyState icon={BookOpen} title={t("courses.noCourses")} testId="courses-page-empty" />
        )}

        {total > pageSize && (
          <Pagination className="mt-8">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(event) => {
                    event.preventDefault();
                    if (canPrev) setPage((prev) => prev - 1);
                  }}
                  className={!canPrev ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
              <PaginationItem className="px-3 text-sm text-slate-600">
                {page} / {totalPages}
              </PaginationItem>
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(event) => {
                    event.preventDefault();
                    if (canNext) setPage((prev) => prev + 1);
                  }}
                  className={!canNext ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
    </div>
  );
};
