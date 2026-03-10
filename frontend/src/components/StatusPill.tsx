import clsx from 'clsx';

interface Props {
  label: string;
}

const palette: Record<string, string> = {
  'High Urgency': 'border-rose-300/65 bg-rose-100/80 text-rose-700',
  'Medium Urgency': 'border-amber-300/65 bg-amber-100/80 text-amber-700',
  'Low Urgency': 'border-emerald-300/65 bg-emerald-100/80 text-emerald-700'
};

export function StatusPill({ label }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em]',
        palette[label] ?? 'border-slate-300/70 bg-white/80 text-slate-700'
      )}
    >
      {label}
    </span>
  );
}
