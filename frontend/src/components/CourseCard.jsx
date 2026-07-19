import { useNavigate } from "react-router-dom";
import { Globe, Lock } from "lucide-react";
import { getCourseLanguageDisplay } from "@/i18n";
import { CourseThumbnail } from "@/components/CourseThumbnail";
import { getCoursePriceDisplay } from "@/lib/coursePricing";
import { useLanguage } from "@/contexts/LanguageContext";

export const CourseCard = ({ course, showProgress = false, progress = 0 }) => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const pricing = getCoursePriceDisplay(course);

  return (
    <article
      className="card-swiss card-indexed group flex flex-col overflow-hidden cursor-pointer"
      onClick={() => navigate(`/courses/${course.id}`)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && navigate(`/courses/${course.id}`)}
      role="button"
      tabIndex={0}
      aria-label={course.title}
      data-testid={`course-card-${course.id}`}
    >
      <div className="relative aspect-video overflow-hidden bg-slate-100 border-b border-slate-200">
        <CourseThumbnail
          src={course.thumbnail_url}
          alt=""
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          fallbackClassName="w-full h-full grid place-items-center bg-[linear-gradient(135deg,#002FA7_0%,#001C63_100%)]"
          fallbackIconClassName="w-10 h-10 text-white/70"
        />
        <div className="absolute top-2 left-2 flex flex-wrap gap-1.5 max-w-[85%]">
          {course.language && (
            <span className="chip bg-white/95 text-slate-600 border border-slate-200">
              <Globe className="w-3 h-3" />
              {getCourseLanguageDisplay(course.language, { short: true })}
            </span>
          )}
          {pricing.isFree ? (
            <span className="chip chip-free bg-white/95">{t("courses.free")}</span>
          ) : pricing.hasOffer ? (
            <>
              <span
                className="chip chip-paid bg-white/95 tabular inline-flex items-center gap-1.5"
                data-testid={`course-card-special-offer-${course.id}`}
              >
                <span className="line-through opacity-70">{pricing.originalPriceLabel}</span>
                <span>{pricing.priceLabel}</span>
              </span>
              <span className="chip bg-amber-50 text-amber-800 border border-amber-200">
                {t("courses.specialOffer")}
              </span>
            </>
          ) : (
            <span className="chip chip-paid bg-white/95 tabular">{pricing.priceLabel}</span>
          )}
        </div>
        {course.is_private && (
          <span className="chip chip-private absolute top-2 right-2 bg-white/95">
            <Lock className="w-3 h-3" /> Private
          </span>
        )}
      </div>
      <div className="flex flex-col flex-1 p-4 gap-2">
        <h3 className="font-display text-lg leading-snug text-slate-900 line-clamp-1 group-hover:text-[#002FA7] transition-colors">
          {course.title}
        </h3>
        <p className="text-sm text-slate-600 leading-relaxed line-clamp-2">{course.description}</p>
        {showProgress && (
          <div className="mt-auto pt-2 flex items-center gap-2">
            <div className="h-1.5 flex-1 bg-slate-100 rounded-none overflow-hidden">
              <div className="h-full bg-[#002FA7] transition-[width] duration-500" style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} />
            </div>
            <span className="text-xs font-semibold text-slate-500 tabular">{progress}%</span>
          </div>
        )}
      </div>
    </article>
  );
};

