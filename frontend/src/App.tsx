import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowPathIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

import {
  enrolBiometric,
  fetchComplianceKey,
  fetchHealth,
  runTriage,
  type EnrollmentResponse,
  type TriageResponse
} from './lib/api';
import { useSyntheticBiometric } from './hooks/useSyntheticBiometric';
import { AuditSignature } from './components/AuditSignature';
import { TriageResult } from './components/TriageResult';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080';

export default function App() {
  const { generate, vectorLength } = useSyntheticBiometric();
  const [symptoms, setSymptoms] = useState('');
  const [vector, setVector] = useState<number[]>([]);
  const [token, setToken] = useState<EnrollmentResponse | null>(null);
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);

  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 60000
  });

  const complianceKeyQuery = useQuery({
    queryKey: ['compliance-key'],
    queryFn: fetchComplianceKey
  });

  const enrollMutation = useMutation({
    mutationFn: enrolBiometric,
    onSuccess: (resp) => {
      setToken(resp);
    }
  });

  const triageMutation = useMutation({
    mutationFn: runTriage,
    onSuccess: (resp) => {
      setTriageResult(resp);
    }
  });

  const serviceStatus = useMemo(() => {
    if (healthQuery.isLoading) return 'checking';
    if (healthQuery.error) return 'offline';
    return healthQuery.data?.status === 'ok' ? 'online' : 'degraded';
  }, [healthQuery.data?.status, healthQuery.error, healthQuery.isLoading]);

  const handleGenerate = () => {
    const next = generate();
    setVector(next);
  };

  const handleEnroll = async () => {
    const current = vector.length === vectorLength ? vector : generate();
    setVector(current);
    await enrollMutation.mutateAsync(current);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!symptoms.trim()) return;

    const payload: Parameters<typeof runTriage>[0] = {
      symptoms: symptoms.trim()
    };

    if (token?.token_id && vector.length === vectorLength) {
      payload.biometric_token = token.token_id;
      payload.biometric_vector = vector;
    }

    await triageMutation.mutateAsync(payload);
  };

  const isBusy = triageMutation.isPending || enrollMutation.isPending;

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-3 text-center sm:text-left">
        <div className="inline-flex items-center justify-center gap-2 self-center rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-200 sm:self-start">
          CareSense X
        </div>
        <h1 className="text-3xl font-bold text-white sm:text-4xl">Biometric Triage Command Center</h1>
        <p className="max-w-3xl text-sm text-slate-300 sm:text-base">
          Authenticate with privacy-preserving biometrics, submit encrypted symptom narratives, and capture
          real-time compliance signatures. API Base: <code className="text-cyan-300">{API_BASE}</code>
        </p>
        <div className="mt-1 flex items-center justify-center gap-2 sm:justify-start">
          <span className="text-xs uppercase tracking-wide text-slate-400">API Status:</span>
          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase ${
              serviceStatus === 'online'
                ? 'bg-emerald-500/20 text-emerald-300'
                : serviceStatus === 'checking'
                  ? 'bg-slate-700/50 text-slate-200'
                  : 'bg-rose-500/20 text-rose-300'
            }`}
          >
            {serviceStatus}
          </span>
        </div>
      </header>

      <main className="grid gap-8 lg:grid-cols-[2fr_1fr]">
        <section className="space-y-6">
          <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white">Symptom Narrative</h2>
            <p className="mt-1 text-sm text-slate-400">
              Provide a natural-language description. Sensitive data stays encrypted throughout the workflow.
            </p>
            <label className="mt-5 block text-sm font-medium text-slate-200" htmlFor="symptoms">
              Symptoms
            </label>
            <textarea
              id="symptoms"
              name="symptoms"
              required
              minLength={10}
              value={symptoms}
              onChange={(event) => setSymptoms(event.target.value)}
              placeholder="Ex: Difficulty breathing, chest tightness, rapid pulse, and brown mucus for 2 days."
              className="mt-2 h-40 w-full rounded-xl border border-slate-700 bg-slate-950/70 p-3 text-sm text-slate-100 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/40"
            />

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={isBusy}
                className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-2 text-sm font-semibold text-cyan-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {triageMutation.isPending ? (
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircleIcon className="h-4 w-4" />
                )}
                Run Secure Triage
              </button>
              <span className="text-xs text-slate-400">
                Biometric guardrails {token?.token_id ? 'enabled' : 'pending enrolment'}.
              </span>
            </div>

            {triageMutation.error && (
              <p className="mt-4 rounded-md border border-rose-500/60 bg-rose-950/60 p-3 text-sm text-rose-200">
                {(triageMutation.error as Error).message}
              </p>
            )}
          </form>

          <TriageResult result={triageResult} />
          <AuditSignature signature={triageResult?.audit_reference ?? token?.ciphertext} />
        </section>

        <aside className="space-y-6">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white">Biometric Enrolment</h2>
            <p className="mt-1 text-sm text-slate-400">
              Generate or stream a normalised embedding to enrol. Synthetic data shown for demo purposes.
            </p>
            <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950/50 p-4 text-xs text-slate-300">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">Vector ({vector.length || vectorLength} dims)</span>
                <button
                  type="button"
                  onClick={handleGenerate}
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-3 py-1 text-xs font-medium text-slate-200 transition hover:border-cyan-400 hover:text-cyan-200"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                  Regenerate
                </button>
              </div>
              <code className="mt-3 block max-h-40 overflow-auto whitespace-pre-wrap text-[11px] leading-5 text-cyan-200">
                {vector.length ? JSON.stringify(vector, null, 2) : '[]'}
              </code>
            </div>

            <div className="mt-4 flex flex-col gap-3">
              <button
                type="button"
                onClick={handleEnroll}
                disabled={enrollMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-5 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {enrollMutation.isPending ? (
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircleIcon className="h-4 w-4" />
                )}
                Enrol Biometric
              </button>
              {token?.token_id && (
                <div className="rounded-lg border border-emerald-500/50 bg-emerald-500/10 p-3 text-xs text-emerald-100">
                  <p className="font-semibold text-emerald-200">Token ID</p>
                  <p className="break-words font-mono text-[11px]">{token.token_id}</p>
                </div>
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
            <h2 className="text-lg font-semibold text-white">Compliance Ledger</h2>
            <p className="mt-1 text-sm text-slate-400">
              Retrieve the Ed25519 public key to verify ledger signatures. Rotate via secure ops pipeline.
            </p>
            {complianceKeyQuery.data ? (
              <pre className="mt-3 max-h-56 overflow-auto rounded-lg border border-slate-700 bg-slate-950/60 p-3 text-[11px] leading-5 text-slate-200">
                {complianceKeyQuery.data.public_key_pem}
              </pre>
            ) : complianceKeyQuery.isLoading ? (
              <p className="mt-3 text-xs text-slate-400">Fetching public key…</p>
            ) : (
              <p className="mt-3 text-xs text-rose-300">
                Failed to load compliance key: {(complianceKeyQuery.error as Error)?.message}
              </p>
            )}
            <p className="mt-4 text-xs text-slate-500">
              Validate ledger entries by verifying <code>audit_reference</code> signatures against this key.
            </p>
          </section>
        </aside>
      </main>

      <footer className="border-t border-slate-800 pt-6 text-xs text-slate-500">
        <p>
          Version <span className="font-mono text-slate-300">{String(__APP_VERSION__)}</span>. Crafted for
          privacy-first clinical automation.
        </p>
      </footer>
    </div>
  );
}
