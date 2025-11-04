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
    <div className="rounded-lg border border-slate-700 bg-slate-900/80 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Audit Reference
          </h3>
          <p className="mt-1 break-words font-mono text-xs text-slate-100/90">{signature}</p>
        </div>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(signature);
            setCopied(true);
            setTimeout(() => setCopied(false), 2200);
          }}
          className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3 py-2 text-xs font-medium text-slate-50 transition hover:border-slate-400 hover:text-white"
        >
          <ClipboardDocumentListIcon className="h-4 w-4" />
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        Use this Ed25519 signature to verify the triage ledger entry via the compliance API.
      </p>
    </div>
  );
}
