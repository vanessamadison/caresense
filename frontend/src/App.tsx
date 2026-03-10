import {
  ArrowUpTrayIcon,
  CheckBadgeIcon,
  DocumentTextIcon,
  FingerPrintIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import { AuditSignature } from './components/AuditSignature';
import { ClinicianDashboard } from './components/ClinicianDashboard';
import { TriageResult } from './components/TriageResult';
import { useSyntheticBiometric } from './hooks/useSyntheticBiometric';
import {
  API_BASE,
  enrolBiometric,
  fetchComplianceKey,
  fetchHealth,
  runDocumentTriage,
  runTriage,
  uploadDocument,
  type DocumentUploadResponse,
  type EnrollmentResponse,
  type TriageResponse
} from './lib/api';

type ExperienceMode = 'intake' | 'review' | 'trust';

const experienceTabs: Array<{ id: ExperienceMode; label: string }> = [
  { id: 'intake', label: 'Patient intake' },
  { id: 'review', label: 'Clinician review' },
  { id: 'trust', label: 'Trust & compliance' }
];

const trustSignals = [
  {
    title: 'Session verification',
    body: 'A biometric check can be attached when the session needs stronger confirmation.'
  },
  {
    title: 'Signed records',
    body: 'Every triage and review event is returned with a verifiable audit signature.'
  },
  {
    title: 'Clinical fallback',
    body: 'High-risk and low-confidence cases are routed into clinician review automatically.'
  }
];

export default function App() {
  const { generate, vectorLength } = useSyntheticBiometric();
  const [experience, setExperience] = useState<ExperienceMode>('intake');
  const [symptoms, setSymptoms] = useState('');
  const [vector, setVector] = useState<number[]>([]);
  const [token, setToken] = useState<EnrollmentResponse | null>(null);
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);
  const [uploadedDocument, setUploadedDocument] = useState<DocumentUploadResponse | null>(null);
  const [selectedFileName, setSelectedFileName] = useState('');
  const [clinicianId, setClinicianId] = useState('dr_lane');

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
    onSuccess: (response) => setToken(response)
  });

  const triageMutation = useMutation({
    mutationFn: runTriage,
    onSuccess: (response) => {
      setTriageResult(response);
      setExperience('intake');
    }
  });

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: (response) => {
      setUploadedDocument(response);
      setExperience('intake');
    }
  });

  const documentTriageMutation = useMutation({
    mutationFn: runDocumentTriage,
    onSuccess: (response) => {
      setTriageResult(response);
      setExperience('intake');
    }
  });

  const handleGenerateVector = () => {
    setVector(generate());
  };

  const handleEnroll = async () => {
    const nextVector = vector.length === vectorLength ? vector : generate();
    setVector(nextVector);
    await enrollMutation.mutateAsync(nextVector);
  };

  const handleSubmitNarrative = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const payload: Parameters<typeof runTriage>[0] = {
      symptoms: symptoms.trim()
    };

    if (token?.token_id && vector.length === vectorLength) {
      payload.biometric_token = token.token_id;
      payload.biometric_vector = vector;
    }

    await triageMutation.mutateAsync(payload);
  };

  const handleDocumentChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setSelectedFileName(file.name);
    await uploadMutation.mutateAsync(file);
  };

  const serviceStatus = healthQuery.data?.status === 'ok' ? 'Online' : healthQuery.isLoading ? 'Checking' : 'Offline';
  const busy = triageMutation.isPending || enrollMutation.isPending || uploadMutation.isPending || documentTriageMutation.isPending;
  const complianceSnippet = complianceKeyQuery.data?.public_key_pem
    ? complianceKeyQuery.data.public_key_pem.split('\n').slice(0, 3).join('\n')
    : '';
  const verificationLabel = token?.token_id ? 'Verification ready' : 'Verification available';
  const routingLabel = triageResult?.review_recommended ? 'Clinician review queued' : 'Direct care guidance';

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 pb-12 pt-5 sm:px-6 lg:px-8">
        <header className="brand-header">
          <img src="/logo.png" alt="CareSense" className="brand-logo" />
          <p className="brand-copy">
            A quieter care intake that helps patients describe what is happening, attach a note if
            they have one, and receive the right level of follow-up.
          </p>
          <div className="brand-status">
            <span className={clsx('status-chip', serviceStatus === 'Online' ? 'status-chip-good' : serviceStatus === 'Checking' ? 'status-chip-neutral' : 'status-chip-alert')}>
              {serviceStatus}
            </span>
            <span className="status-chip status-chip-neutral">{verificationLabel}</span>
            <span className="status-chip status-chip-strong">{routingLabel}</span>
          </div>
        </header>

        <nav className="tab-shell">
          {experienceTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setExperience(tab.id)}
              className={clsx('tab-button', experience === tab.id && 'tab-button-active')}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {experience === 'intake' && (
          <main className="mt-8 space-y-6">
            <section className="grid auto-rows-fr gap-6 xl:grid-cols-2">
              <div className="surface-panel h-full">
                <span className="eyebrow">Start here</span>
                <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
                  Tell us what you are feeling.
                </h2>
                <p className="mt-3 text-sm leading-6 text-[color:var(--ink-soft)]">
                  Share the main symptoms, when they started, what has changed, and anything that is
                  making them better or worse.
                </p>

                <form className="mt-6 space-y-5" onSubmit={handleSubmitNarrative}>
                  <label className="field-group">
                    <span className="field-label">Symptom summary</span>
                    <textarea
                      id="symptoms"
                      required
                      minLength={10}
                      value={symptoms}
                      onChange={(event) => setSymptoms(event.target.value)}
                      placeholder="Example: tight chest, shortness of breath, worse when walking upstairs, started last night."
                      className="input-shell min-h-[180px] resize-y"
                    />
                  </label>

                  <div className="rounded-[24px] border border-white/60 bg-white/70 p-4">
                    <p className="text-sm font-medium text-[color:var(--ink-strong)]">A helpful note</p>
                    <p className="mt-2 text-sm leading-6 text-[color:var(--ink-soft)]">
                      Patients usually want to know three things quickly: how urgent this feels, what
                      to do next, and whether a clinician needs to review it.
                    </p>
                  </div>

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <button type="submit" disabled={busy} className="primary-button">
                      {triageMutation.isPending ? 'Reviewing symptoms...' : 'Get care guidance'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setExperience('review')}
                      className="secondary-button"
                    >
                      View review queue
                    </button>
                  </div>

                  {triageMutation.error && (
                    <p className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                      {(triageMutation.error as Error).message}
                    </p>
                  )}
                </form>
              </div>

              <section className="surface-panel h-full">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className="eyebrow">Optional step</span>
                    <h3 className="mt-3 text-xl font-semibold text-[color:var(--ink-strong)]">
                      Add a report or visit note.
                    </h3>
                    <p className="mt-3 text-sm leading-6 text-[color:var(--ink-soft)]">
                      Upload a file if the patient already has a discharge summary, message thread, or
                      intake note that should inform the recommendation.
                    </p>
                  </div>
                  <DocumentTextIcon className="h-6 w-6 text-[color:var(--accent)]" />
                </div>

                <label className="upload-dropzone mt-5">
                  <ArrowUpTrayIcon className="h-5 w-5" />
                  <span className="text-sm font-medium">
                    {selectedFileName || 'Choose PDF, DOCX, TXT, or email file'}
                  </span>
                  <span className="text-xs text-[color:var(--ink-muted)]">
                    Parser will extract text and flag basic PII signals before triage.
                  </span>
                  <input type="file" className="hidden" onChange={handleDocumentChange} />
                </label>

                {uploadMutation.error && (
                  <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {(uploadMutation.error as Error).message}
                  </p>
                )}

                {uploadedDocument && (
                  <div className="mt-5 rounded-[24px] border border-white/60 bg-white/70 p-4">
                    <p className="text-sm font-medium text-[color:var(--ink-strong)]">File ready for review</p>
                    <p className="mt-2 max-h-40 overflow-hidden text-sm leading-6 text-[color:var(--ink-soft)]">
                      {uploadedDocument.text}
                    </p>
                    <button
                      type="button"
                      onClick={() =>
                        documentTriageMutation.mutate({
                          file_hash: uploadedDocument.file_hash,
                          text: uploadedDocument.text,
                          biometric_token: token?.token_id
                        })
                      }
                      disabled={busy}
                      className="secondary-button mt-4 w-full"
                    >
                      {documentTriageMutation.isPending ? 'Reviewing file...' : 'Use this file for triage'}
                    </button>
                  </div>
                )}
              </section>
              <div className="h-full xl:col-span-2">
                <TriageResult result={triageResult} />
              </div>
            </section>

            <AuditSignature signature={triageResult?.audit_reference ?? token?.ciphertext} />
          </main>
        )}

        {experience === 'review' && (
          <main className="mt-8 space-y-6">
            <div className="surface-panel flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <span className="eyebrow">Review settings</span>
                <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
                  Keep clinician review easy to scan.
                </h2>
              </div>
              <label className="field-group w-full max-w-sm">
                <span className="field-label">Reviewer ID</span>
                <input
                  value={clinicianId}
                  onChange={(event) => setClinicianId(event.target.value)}
                  className="input-shell"
                />
              </label>
            </div>

            <ClinicianDashboard clinicianId={clinicianId} />
          </main>
        )}

        {experience === 'trust' && (
          <main className="mt-8 grid gap-6 xl:grid-cols-[1fr_1fr]">
            <section className="surface-panel">
              <span className="eyebrow">How this stays trustworthy</span>
              <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
                Built to feel calm, clear, and accountable.
              </h2>
              <div className="mt-8 space-y-4">
                {trustSignals.map((signal) => (
                  <div key={signal.title} className="rounded-[24px] border border-white/60 bg-white/70 p-5">
                    <div className="flex items-start gap-3">
                      <CheckBadgeIcon className="mt-0.5 h-5 w-5 text-[color:var(--accent)]" />
                      <div>
                        <p className="text-base font-semibold text-[color:var(--ink-strong)]">
                          {signal.title}
                        </p>
                        <p className="mt-2 text-sm leading-6 text-[color:var(--ink-soft)]">{signal.body}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="surface-panel">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="eyebrow">Verification key</span>
                  <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
                    Public record signature
                  </h2>
                </div>
                <ShieldCheckIcon className="h-6 w-6 text-[color:var(--accent)]" />
              </div>
              {complianceKeyQuery.isLoading ? (
                <p className="mt-6 text-sm text-[color:var(--ink-soft)]">Loading public key...</p>
              ) : complianceKeyQuery.error ? (
                <p className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {(complianceKeyQuery.error as Error).message}
                </p>
              ) : (
                <>
                  <pre className="mt-6 overflow-auto rounded-[24px] border border-white/60 bg-white/80 p-5 text-xs leading-6 text-[color:var(--ink-strong)]">
                    {complianceSnippet}
                  </pre>
                  <p className="mt-4 text-sm leading-6 text-[color:var(--ink-soft)]">
                    Use the public key to validate audit signatures returned by triage and clinician
                    review events. API base: {API_BASE}
                  </p>
                </>
              )}
            </section>

            <section className="surface-panel xl:col-span-2">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="eyebrow">Identity tools</span>
                  <h2 className="mt-3 text-2xl font-semibold text-[color:var(--ink-strong)]">
                    Optional session verification
                  </h2>
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-[color:var(--ink-soft)]">
                    Keep this off until you need it. When activated, a biometric token can be attached
                    to the triage request for stronger identity confirmation.
                  </p>
                </div>
                <FingerPrintIcon className="h-6 w-6 text-[color:var(--accent)]" />
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-[24px] border border-white/60 bg-white/70 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium text-[color:var(--ink-strong)]">
                      Verification state
                    </span>
                    <button type="button" onClick={handleGenerateVector} className="text-button">
                      Refresh vector
                    </button>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[color:var(--ink-soft)]">
                    {token?.token_id
                      ? `Verification is active. Token ${token.token_id.slice(0, 12)} is ready to attach to triage requests.`
                      : `Verification is currently off. Generate and enroll a ${vectorLength}-dimension vector only when you want to turn it on.`}
                  </p>
                  <pre className="mt-3 max-h-32 overflow-auto text-[11px] leading-5 text-[color:var(--ink-soft)]">
                    {vector.length ? JSON.stringify(vector, null, 2) : '[]'}
                  </pre>
                </div>

                <div className="rounded-[24px] border border-white/60 bg-white/70 p-4">
                  <p className="text-sm font-medium text-[color:var(--ink-strong)]">Activation</p>
                  <p className="mt-2 text-sm leading-6 text-[color:var(--ink-soft)]">
                    This requires the API to be reachable. If the backend is offline, verification will
                    not update because the token is created server-side.
                  </p>
                  {enrollMutation.error && (
                    <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                      {(enrollMutation.error as Error).message}
                    </p>
                  )}
                  <button type="button" onClick={handleEnroll} disabled={busy} className="primary-button mt-4 w-full">
                    {enrollMutation.isPending ? 'Activating verification...' : token?.token_id ? 'Refresh verification' : 'Activate verification'}
                  </button>
                </div>
              </div>
            </section>
          </main>
        )}
      </div>
    </div>
  );
}
