/**
 * PageHeader — consistent overline + Clash Display title + action slot.
 * Use at the top of every dashboard page so hierarchy reads identically
 * across student, manager, and admin views.
 *
 * Props: overline, title, description, children (actions, right-aligned)
 */
export default function PageHeader({ overline, title, description, children }) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 pb-6 mb-6 border-b border-slate-200 animate-enter">
      <div className="space-y-1.5">
        {overline && <p className="overline">{overline}</p>}
        <h1 className="font-display text-2xl sm:text-3xl tracking-tight text-slate-900">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-slate-600 max-w-2xl leading-relaxed">{description}</p>
        )}
      </div>
      {children && <div className="flex items-center gap-2 shrink-0">{children}</div>}
    </header>
  );
}
