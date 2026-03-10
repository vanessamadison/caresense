import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';

interface Props {
  signature?: string | null;
}

export function AuditSignature({ signature }: Props) {
  const [copied, setCopied] = useState(false);

  if (!signature) {
    return null;
  }

  return (
    <section className="surface-panel">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-2xl">
          <span className="eyebrow">Compliance</span>
          <h3 className="mt-3 text-xl font-semibold text-[color:var(--ink-strong)]">
            Signed audit reference captured for this care event.
          </h3>
          <p className="mt-3 break-all rounded-2xl border border-white/60 bg-white/70 px-4 py-3 font-mono text-xs leading-6 text-[color:var(--ink-strong)]">
            {signature}
          </p>
          <p className="mt-3 text-sm text-[color:var(--ink-soft)]">
            This signature can be validated against the platform public key to confirm the triage
            event was written to the compliance ledger without tampering.
          </p>
        </div>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(signature);
            setCopied(true);
            setTimeout(() => setCopied(false), 2200);
          }}
          className="inline-flex items-center justify-center gap-2 rounded-full border border-[color:var(--line-strong)] bg-white/80 px-4 py-2 text-sm font-medium text-[color:var(--ink-strong)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent)]"
        >
          <ClipboardDocumentListIcon className="h-4 w-4" />
          {copied ? 'Copied' : 'Copy reference'}
        </button>
      </div>
    </section>
  );
}
