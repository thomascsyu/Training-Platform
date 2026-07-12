/**
 * Skeletons — mirror the real components' geometry so content doesn't
 * jump when data lands. Render these while queries are in flight instead
 * of spinners or blank screens.
 */

export function CourseCardSkeleton() {
  return (
    <div className="card-swiss overflow-hidden" aria-hidden="true">
      <div className="skeleton aspect-[16/9]" />
      <div className="p-5 space-y-3">
        <div className="skeleton h-3 w-20" />
        <div className="skeleton h-5 w-4/5" />
        <div className="skeleton h-4 w-full" />
        <div className="skeleton h-4 w-2/3" />
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="card-swiss p-6 space-y-4" aria-hidden="true">
      <div className="skeleton h-3 w-24" />
      <div className="skeleton h-8 w-16" />
      <div className="skeleton h-3 w-28" />
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div className="card-swiss divide-y divide-slate-100" aria-hidden="true">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="grid gap-4 p-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="skeleton h-4" style={{ width: `${60 + ((r + c) % 3) * 15}%` }} />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Grid helper: <SkeletonGrid n={6} Item={CourseCardSkeleton} /> */
export function SkeletonGrid({ n = 6, Item = CourseCardSkeleton, className = '' }) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 ${className}`}>
      {Array.from({ length: n }).map((_, i) => (
        <Item key={i} />
      ))}
    </div>
  );
}
