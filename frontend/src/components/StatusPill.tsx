import clsx from 'clsx';

interface Props {
  label: string;
}

const palette: Record<string, string> = {
  'High Urgency': 'bg-rose-600/20 text-rose-300 border border-rose-500/40',
  'Medium Urgency': 'bg-amber-500/20 text-amber-200 border border-amber-400/40',
  'Low Urgency': 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/40'
};

export function StatusPill({ label }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
        palette[label] ?? 'bg-slate-700/40 text-slate-200'
      )}
    >
      {label}
    </span>
  );
}
