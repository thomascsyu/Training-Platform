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
import { SkeletonGrid } from "@/components/enhanced/Skeletons";
import EmptyState from "@/components/enhanced/EmptyState";

export const CoursesPage = () => {
  const { t } = useLanguage();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("all");

  const fetchCourses = useCallback(async () => {
    try {
      let url = "/courses";
      const params = new URLSearchParams();
      if (selectedLanguage && selectedLanguage !== "all") {
        params.append("language", selectedLanguage);
      }
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      const { data } = await API.get(url);
      setCourses(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [selectedLanguage]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const filteredCourses = courses.filter((course) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      course.title?.toLowerCase().includes(query) ||
      course.description?.toLowerCase().includes(query)
    );
  });

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
        </div>

        {loading ? (
          <SkeletonGrid n={6} />
        ) : filteredCourses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger">
            {filteredCourses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        ) : (
          <EmptyState icon={BookOpen} title={t("courses.noCourses")} testId="courses-page-empty" />
        )}
      </div>
    </div>
  );
};
