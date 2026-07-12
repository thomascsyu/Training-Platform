/**
 * EmptyState — an empty screen is an invitation to act, not a dead end.
 *
 * Props:
 *  icon:        Lucide component
 *  title:       what's empty ("No courses yet")
 *  description: what to do about it
 *  actionLabel: CTA text (optional)
 *  onAction:    CTA handler (optional)
 *  testId:      data-testid
 */
export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction, testId }) {
  return (
    <div
      data-testid={testId || 'empty-state'}
      className="card-swiss grid place-items-center text-center py-16 px-6"
    >
      <div className="max-w-sm space-y-4">
        {Icon && (
          <span className="mx-auto grid place-items-center w-14 h-14 bg-[#002FA7]/[0.06] text-[#002FA7] rounded-none sm:rounded-sm">
            <Icon className="w-7 h-7" aria-hidden="true" />
          </span>
        )}
        <h3 className="font-display text-xl text-slate-900">{title}</h3>
        {description && (
          <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
        )}
        {actionLabel && onAction && (
          <button
            type="button"
            className="btn-primary"
            onClick={onAction}
            data-testid={`${testId || 'empty-state'}-action`}
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
}
