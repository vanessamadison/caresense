import clsx from 'clsx';

import type { TriageResponse } from '../lib/api';
import { StatusPill } from './StatusPill';

interface Props {
  result: TriageResponse | null;
}

const urgencyAccent: Record<string, string> = {
  'High Urgency': 'from-rose-500/22 via-orange-500/16 to-transparent',
  'Medium Urgency': 'from-amber-400/24 via-yellow-300/10 to-transparent',
  'Low Urgency': 'from-emerald-400/22 via-teal-300/10 to-transparent'
};

export function TriageResult({ result }: Props) {
  if (!result) {
    return (
      <section className="surface-panel flex h-full min-h-[320px] flex-col justify-between overflow-hidden">
        <div>
          <span className="eyebrow">Care guidance</span>
          <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
            Guidance will appear here after intake.
          </h2>
          <p className="mt-4 max-w-xl text-sm leading-6 text-[color:var(--ink-soft)]">
            Submit a symptom narrative or upload a medical document to generate a triage recommendation,
            confidence band, and review routing signal.
          </p>
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          <div className="metric-tile">
            <span className="metric-label">Model</span>
            <span className="metric-value">Awaiting input</span>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Review queue</span>
            <span className="metric-value">Standby</span>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Audit ledger</span>
            <span className="metric-value">Ready</span>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="surface-panel relative h-full overflow-hidden">
      <div
        className={clsx(
          'pointer-events-none absolute inset-0 bg-gradient-to-br opacity-100',
          urgencyAccent[result.urgency] ?? 'from-slate-200/10 via-transparent to-transparent'
        )}
      />
      <div className="relative">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-2xl">
            <span className="eyebrow">Care guidance</span>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-[color:var(--ink-strong)]">
              {result.summary}
            </h2>
            <p className="mt-3 text-sm leading-6 text-[color:var(--ink-soft)]">
              {result.next_steps}
            </p>
          </div>
          <StatusPill label={result.urgency} />
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="metric-tile">
            <span className="metric-label">Confidence</span>
            <span className="metric-value">{(result.confidence * 100).toFixed(1)}%</span>
            <span className="metric-note">{result.confidence_band}</span>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Recommended care</span>
            <span className="metric-value text-base">{result.recommended_care}</span>
            <span className="metric-note">{result.care_window}</span>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Specialty</span>
            <span className="metric-value text-base">{result.specialty}</span>
            <span className="metric-note">
              {result.biometric_verified ? 'Biometric verified' : 'Narrative-only session'}
            </span>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Review routing</span>
            <span className="metric-value text-base">
              {result.review_recommended ? 'Escalated' : 'Not required'}
            </span>
            <span className="metric-note">
              {result.review_case_id ? `Case ${result.review_case_id.slice(0, 8)}` : 'Auto-triaged'}
            </span>
          </div>
        </div>

        <div className="mt-8 rounded-[28px] border border-white/55 bg-white/68 p-5 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--ink-muted)]">
                Probability profile
              </p>
              <p className="mt-1 text-sm text-[color:var(--ink-soft)]">
                Model version {result.model_version} generated at{' '}
                {new Date(result.generated_at).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="mt-5 space-y-4">
            {Object.entries(result.probability_breakdown).map(([label, value]) => (
              <div key={label}>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="font-medium text-[color:var(--ink-strong)]">{label}</span>
                  <span className="text-[color:var(--ink-soft)]">{(value * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-[color:var(--line-soft)]">
                  <div
                    className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-soft))]"
                    style={{ width: `${Math.max(value * 100, 4)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
