import { TrendingUp, TrendingDown } from 'lucide-react';

/**
 * StatCard — "control room" stat widget for admin/student dashboards.
 * Mono tabular numerals, overline label, optional delta vs previous period.
 *
 * Props:
 *  label:   string            e.g. "Total enrollments"
 *  value:   string | number   e.g. 1284 or "92%"
 *  icon:    Lucide component  optional
 *  delta:   number            optional, +/- percent vs last period
 *  hint:    string            optional footnote, e.g. "last 30 days"
 *  testId:  string            data-testid value
 */
export default function StatCard({ label, value, icon: Icon, delta, hint, testId }) {
  const up = typeof delta === 'number' && delta >= 0;

  return (
    <div data-testid={testId || `stat-${label}`} className="card-swiss p-6 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <p className="overline">{label}</p>
        {Icon && (
          <span className="grid place-items-center w-9 h-9 bg-[#002FA7]/[0.06] text-[#002FA7] rounded-none sm:rounded-sm">
            <Icon className="w-5 h-5" aria-hidden="true" />
          </span>
        )}
      </div>

      <p className="font-mono tabular text-3xl font-medium text-slate-900 leading-none">
        {value}
      </p>

      {(typeof delta === 'number' || hint) && (
        <div className="flex items-center gap-2 text-xs">
          {typeof delta === 'number' && (
            <span
              className={`inline-flex items-center gap-1 font-semibold ${
                up ? 'text-emerald-600' : 'text-red-600'
              }`}
            >
              {up ? (
                <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" aria-hidden="true" />
              )}
              {up ? '+' : ''}
              {delta}%
            </span>
          )}
          {hint && <span className="text-slate-500">{hint}</span>}
        </div>
      )}
    </div>
  );
}
