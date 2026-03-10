import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { fetchPendingCases, submitReview, type ReviewCase } from '../lib/api';

interface Props {
  clinicianId: string;
}

const priorityTone: Record<string, string> = {
  critical: 'text-rose-700 bg-rose-100 border-rose-200',
  high: 'text-orange-700 bg-orange-100 border-orange-200',
  medium: 'text-amber-700 bg-amber-100 border-amber-200',
  low: 'text-emerald-700 bg-emerald-100 border-emerald-200'
};

export function ClinicianDashboard({ clinicianId }: Props) {
  const queryClient = useQueryClient();
  const [selectedCase, setSelectedCase] = useState<ReviewCase | null>(null);
  const [decision, setDecision] = useState<'approved' | 'rejected' | 'escalated' | 'in_review'>(
    'approved'
  );
  const [overrideUrgency, setOverrideUrgency] = useState<string>('');
  const [notes, setNotes] = useState('');

  const reviewQuery = useQuery({
    queryKey: ['pending-cases', clinicianId],
    queryFn: () => fetchPendingCases(clinicianId),
    refetchInterval: 30000
  });

  useEffect(() => {
    if (!selectedCase && reviewQuery.data?.cases.length) {
      setSelectedCase(reviewQuery.data.cases[0]);
    }
  }, [reviewQuery.data?.cases, selectedCase]);

  const submitMutation = useMutation({
    mutationFn: submitReview,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['pending-cases', clinicianId] });
      setSelectedCase(null);
      setNotes('');
      setOverrideUrgency('');
      setDecision('approved');
    }
  });

  const cases = reviewQuery.data?.cases ?? [];

  return (
    <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="surface-panel">
        <div className="flex items-center justify-between gap-4">
          <div>
            <span className="eyebrow">Clinician review</span>
            <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
              Live queue for human oversight.
            </h2>
          </div>
          <div className="rounded-full border border-white/60 bg-white/70 px-4 py-2 text-sm text-[color:var(--ink-soft)]">
            {reviewQuery.isLoading ? 'Loading' : `${cases.length} active`}
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {cases.map((caseItem) => (
            <button
              key={caseItem.case_id}
              type="button"
              onClick={() => setSelectedCase(caseItem)}
              className={clsx(
                'w-full rounded-[24px] border p-4 text-left transition',
                selectedCase?.case_id === caseItem.case_id
                  ? 'border-[color:var(--accent)] bg-[color:var(--surface-strong)] shadow-[0_24px_50px_rgba(15,23,42,0.08)]'
                  : 'border-white/60 bg-white/70 hover:border-[color:var(--line-strong)]'
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div
                    className={clsx(
                      'inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.2em]',
                      priorityTone[caseItem.priority] ?? 'text-slate-700 bg-slate-100 border-slate-200'
                    )}
                  >
                    {caseItem.priority}
                  </div>
                  <p className="mt-3 text-lg font-semibold text-[color:var(--ink-strong)]">
                    {caseItem.predicted_urgency}
                  </p>
                </div>
                <span className="text-xs text-[color:var(--ink-muted)]">
                  {new Date(caseItem.created_at).toLocaleString()}
                </span>
              </div>
              <div className="mt-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--ink-muted)]">
                    Confidence
                  </p>
                  <p className="mt-1 text-sm font-medium text-[color:var(--ink-strong)]">
                    {(caseItem.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="min-w-[120px]">
                  <div className="h-2 overflow-hidden rounded-full bg-[color:var(--line-soft)]">
                    <div
                      className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-soft))]"
                      style={{ width: `${Math.max(caseItem.confidence * 100, 4)}%` }}
                    />
                  </div>
                </div>
              </div>
            </button>
          ))}

          {!reviewQuery.isLoading && cases.length === 0 && (
            <div className="rounded-[24px] border border-dashed border-[color:var(--line-strong)] bg-white/50 p-8 text-center text-sm text-[color:var(--ink-soft)]">
              No pending review cases. High-urgency or low-confidence assessments will appear here
              automatically.
            </div>
          )}
        </div>
      </div>

      <div className="surface-panel">
        {selectedCase ? (
          <>
            <span className="eyebrow">Decisioning</span>
            <h3 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
              {selectedCase.predicted_urgency}
            </h3>
            <p className="mt-2 text-sm text-[color:var(--ink-soft)]">
              Case {selectedCase.case_id} created {new Date(selectedCase.created_at).toLocaleString()}
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <div className="metric-tile">
                <span className="metric-label">Status</span>
                <span className="metric-value text-base capitalize">{selectedCase.status}</span>
              </div>
              <div className="metric-tile">
                <span className="metric-label">Priority</span>
                <span className="metric-value text-base capitalize">{selectedCase.priority}</span>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <label className="field-group">
                <span className="field-label">Decision</span>
                <select
                  value={decision}
                  onChange={(event) =>
                    setDecision(
                      event.target.value as 'approved' | 'rejected' | 'escalated' | 'in_review'
                    )
                  }
                  className="input-shell"
                >
                  <option value="approved">Approve</option>
                  <option value="escalated">Escalate</option>
                  <option value="in_review">Mark in review</option>
                  <option value="rejected">Reject</option>
                </select>
              </label>

              <label className="field-group">
                <span className="field-label">Override urgency</span>
                <select
                  value={overrideUrgency}
                  onChange={(event) => setOverrideUrgency(event.target.value)}
                  className="input-shell"
                >
                  <option value="">Keep model urgency</option>
                  <option value="Low Urgency">Low Urgency</option>
                  <option value="Medium Urgency">Medium Urgency</option>
                  <option value="High Urgency">High Urgency</option>
                </select>
              </label>

              <label className="field-group">
                <span className="field-label">Clinical note</span>
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  className="input-shell min-h-32 resize-y"
                  placeholder="Capture the reasoning for approval, escalation, or override."
                />
              </label>

              {submitMutation.error && (
                <p className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {(submitMutation.error as Error).message}
                </p>
              )}

              <button
                type="button"
                onClick={() =>
                  submitMutation.mutate({
                    case_id: selectedCase.case_id,
                    clinician_id: clinicianId,
                    decision,
                    notes: notes.trim() || null,
                    override_urgency:
                      (overrideUrgency as 'Low Urgency' | 'Medium Urgency' | 'High Urgency' | '') ||
                      null
                  })
                }
                disabled={submitMutation.isPending}
                className="primary-button w-full"
              >
                {submitMutation.isPending ? 'Submitting decision...' : 'Submit clinician review'}
              </button>
            </div>
          </>
        ) : (
          <>
            <span className="eyebrow">Decisioning</span>
            <h3 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
              Select a case to review.
            </h3>
            <p className="mt-3 text-sm leading-6 text-[color:var(--ink-soft)]">
              The queue prioritizes high-risk and low-confidence assessments. Choosing a case reveals
              decision controls for approval, escalation, or urgency override.
            </p>
          </>
        )}
      </div>
    </section>
  );
}
