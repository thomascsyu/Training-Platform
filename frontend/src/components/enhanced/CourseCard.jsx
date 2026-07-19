import { useState } from 'react';
import { BookOpen, Lock, Globe2, ArrowUpRight } from 'lucide-react';
import { getCoursePriceDisplay } from '@/lib/coursePricing';

/**
 * CourseCard — Swiss card with a 3px Klein index rule, lazy-loaded
 * thumbnail with a geometric fallback, price/visibility chips and an
 * optional progress rail for enrolled students.
 *
 * Props:
 *  course:   { id, title, description, thumbnail_url, price, original_price,
 *              is_free, is_private, language, category }
 *  progress: number 0–100 (optional — shown only if provided)
 *  onOpen:   (course) => void
 *  t:        i18n translate fn (optional; falls back to English)
 */
const LANG_LABELS = { en: 'EN', 'zh-TW': '繁中', 'zh-CN': '简中', ja: '日本語', ko: '한국어' };

export default function CourseCard({ course, progress, onOpen, t = (s) => s }) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImage = course.thumbnail_url && !imgFailed;
  const pricing = getCoursePriceDisplay(course);

  return (
    <article
      data-testid={`course-card-${course.id}`}
      className="card-swiss card-indexed group flex flex-col cursor-pointer"
      onClick={() => onOpen?.(course)}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onOpen?.(course)}
      role="button"
      tabIndex={0}
      aria-label={course.title}
    >
      {/* Thumbnail — fixed ratio prevents layout shift */}
      <div className="relative aspect-[16/9] overflow-hidden bg-slate-100 border-b border-slate-200">
        {showImage ? (
          <img
            src={course.thumbnail_url}
            alt=""
            loading="lazy"
            decoding="async"
            onError={() => setImgFailed(true)}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          /* Geometric fallback — no broken-image icons, ever */
          <div className="h-full w-full grid place-items-center bg-[linear-gradient(135deg,#002FA7_0%,#001C63_100%)]">
            <BookOpen className="w-8 h-8 text-white/70" aria-hidden="true" />
          </div>
        )}

        {/* Chips overlay */}
        <div className="absolute top-2 left-2 flex flex-wrap gap-1.5 max-w-[85%]">
          {pricing.isFree ? (
            <span className="chip chip-free bg-white/95">{t('Free')}</span>
          ) : pricing.hasOffer ? (
            <>
              <span className="chip chip-paid bg-white/95 tabular inline-flex items-center gap-1.5">
                <span className="line-through opacity-70">{pricing.originalPriceLabel}</span>
                <span>{pricing.priceLabel}</span>
              </span>
              <span className="chip bg-amber-50 text-amber-800 border border-amber-200">
                {t('Special offer')}
              </span>
            </>
          ) : (
            <span className="chip chip-paid bg-white/95 tabular">
              {pricing.priceLabel}
            </span>
          )}
          {course.is_private && (
            <span className="chip chip-private bg-white/95">
              <Lock className="w-3 h-3" aria-hidden="true" /> {t('Private')}
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-col flex-1 p-5 gap-2">
        {course.category && <p className="overline">{course.category}</p>}

        <h3 className="font-display text-lg leading-snug text-slate-900 line-clamp-2 group-hover:text-[#002FA7] transition-colors">
          {course.title}
        </h3>

        {course.description && (
          <p className="text-sm text-slate-600 leading-relaxed line-clamp-2">
            {course.description}
          </p>
        )}

        <div className="mt-auto pt-3 flex items-center justify-between border-t border-slate-100">
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500">
            <Globe2 className="w-3.5 h-3.5" aria-hidden="true" />
            {LANG_LABELS[course.language] || course.language || 'EN'}
          </span>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#002FA7] opacity-0 group-hover:opacity-100 transition-opacity">
            {t('Open course')} <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
          </span>
        </div>
      </div>

      {/* Progress rail — full-bleed, sits on the card's bottom edge */}
      {typeof progress === 'number' && (
        <div
          className="h-1 bg-slate-100"
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={t('Course progress')}
        >
          <div
            className="h-full bg-[#002FA7] transition-[width] duration-500"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}
    </article>
  );
}
