import { StatusPill } from './StatusPill';
import type { TriageResponse } from '../lib/api';

interface Props {
  result: TriageResponse | null;
}

export function TriageResult({ result }: Props) {
  if (!result) return null;

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl shadow-cyan-500/10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-white">Assessment Result</h2>
        <StatusPill label={result.urgency} />
      </div>
      <dl className="mt-4 grid gap-3 text-sm text-slate-200 sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Confidence</dt>
          <dd className="text-base font-semibold text-slate-50">
            {(result.confidence * 100).toFixed(1)}%
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Recommended Care</dt>
          <dd>{result.recommended_care}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Specialty</dt>
          <dd>{result.specialty}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Next Steps</dt>
          <dd>{result.next_steps}</dd>
        </div>
      </dl>
    </section>
  );
}
