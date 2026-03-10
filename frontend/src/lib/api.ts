import { z } from 'zod';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080';

const enrollmentSchema = z.object({
  token_id: z.string(),
  ciphertext: z.string()
});

const triageSchema = z.object({
  urgency: z.string(),
  confidence: z.number(),
  recommended_care: z.string(),
  specialty: z.string(),
  next_steps: z.string(),
  confidence_band: z.string(),
  care_window: z.string(),
  summary: z.string(),
  generated_at: z.string(),
  biometric_verified: z.boolean(),
  review_recommended: z.boolean(),
  review_case_id: z.string().nullable().optional(),
  probability_breakdown: z.record(z.number()),
  model_version: z.string(),
  audit_reference: z.string().nullable().optional()
});

const publicKeySchema = z.object({
  algorithm: z.string(),
  public_key_pem: z.string()
});

const healthSchema = z.object({
  status: z.string()
});

const documentUploadSchema = z.object({
  file_hash: z.string(),
  text: z.string(),
  metadata: z.record(z.any()),
  pii_detected: z.record(z.boolean()),
  text_length: z.number(),
  warnings: z.array(z.string()).nullable().optional()
});

const reviewExplanationSchema = z.object({
  top_features: z.array(
    z.object({
      feature: z.string(),
      importance: z.number()
    })
  ),
  explanation_method: z.string()
});

const reviewCaseSchema = z.object({
  case_id: z.string(),
  predicted_urgency: z.string(),
  confidence: z.number(),
  status: z.string(),
  priority: z.string(),
  created_at: z.string(),
  reviewed_at: z.string().nullable().optional(),
  reviewer_id: z.string().nullable().optional(),
  clinician_decision: z.string().nullable().optional(),
  clinician_notes: z.string().nullable().optional(),
  override_reason: z.string().nullable().optional(),
  explanation: reviewExplanationSchema.nullable().optional()
});

const pendingCasesSchema = z.object({
  cases: z.array(reviewCaseSchema),
  total: z.number(),
  priority_filter: z.string().nullable().optional()
});

const submitReviewSchema = z.object({
  success: z.boolean(),
  case_id: z.string(),
  audit_signature: z.string().nullable().optional()
});

export type EnrollmentResponse = z.infer<typeof enrollmentSchema>;
export type TriageResponse = z.infer<typeof triageSchema>;
export type ComplianceKeyResponse = z.infer<typeof publicKeySchema>;
export type HealthResponse = z.infer<typeof healthSchema>;
export type DocumentUploadResponse = z.infer<typeof documentUploadSchema>;
export type ReviewCase = z.infer<typeof reviewCaseSchema>;
export type PendingCasesResponse = z.infer<typeof pendingCasesSchema>;
export type SubmitReviewResponse = z.infer<typeof submitReviewSchema>;

async function readError(response: Response): Promise<string> {
  try {
    const json = await response.clone().json();
    if (typeof json.detail === 'string') {
      return json.detail;
    }
  } catch {
    return (await response.text()) || response.statusText;
  }

  return response.statusText;
}

async function handleResponse<T>(response: Response, schema: z.ZodSchema<T>): Promise<T> {
  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return schema.parse(await response.json());
}

export async function enrolBiometric(vector: number[]): Promise<EnrollmentResponse> {
  const response = await fetch(`${API_BASE}/v1/biometrics/enrol`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vector })
  });

  return handleResponse(response, enrollmentSchema);
}

export async function runTriage(payload: {
  symptoms: string;
  biometric_token?: string;
  biometric_vector?: number[];
}): Promise<TriageResponse> {
  const response = await fetch(`${API_BASE}/v1/triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  return handleResponse(response, triageSchema);
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/v1/documents/upload`, {
    method: 'POST',
    body: formData
  });

  return handleResponse(response, documentUploadSchema);
}

export async function runDocumentTriage(payload: {
  file_hash: string;
  text: string;
  biometric_token?: string;
}): Promise<TriageResponse> {
  const response = await fetch(`${API_BASE}/v1/documents/triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  return handleResponse(response, triageSchema);
}

export async function fetchComplianceKey(): Promise<ComplianceKeyResponse> {
  const response = await fetch(`${API_BASE}/v1/compliance/public-key`);
  return handleResponse(response, publicKeySchema);
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/v1/health`);
  return handleResponse(response, healthSchema);
}

export async function fetchPendingCases(clinicianId: string): Promise<PendingCasesResponse> {
  const response = await fetch(
    `${API_BASE}/v1/review/pending?clinician_id=${encodeURIComponent(clinicianId)}`
  );

  return handleResponse(response, pendingCasesSchema);
}

export async function submitReview(payload: {
  case_id: string;
  clinician_id: string;
  decision: 'approved' | 'rejected' | 'escalated' | 'in_review';
  notes?: string | null;
  override_urgency?: 'Low Urgency' | 'Medium Urgency' | 'High Urgency' | null;
}): Promise<SubmitReviewResponse> {
  const response = await fetch(`${API_BASE}/v1/review/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  return handleResponse(response, submitReviewSchema);
}

export { API_BASE };
