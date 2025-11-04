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
  audit_reference: z.string().nullable().optional()
});

const publicKeySchema = z.object({
  algorithm: z.string(),
  public_key_pem: z.string()
});

export type EnrollmentResponse = z.infer<typeof enrollmentSchema>;
export type TriageResponse = z.infer<typeof triageSchema>;
export type ComplianceKeyResponse = z.infer<typeof publicKeySchema>;

async function handleResponse<T>(response: Response, schema: z.ZodSchema<T>): Promise<T> {
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || response.statusText);
  }
  const json = await response.json();
  return schema.parse(json);
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

export async function fetchComplianceKey(): Promise<ComplianceKeyResponse> {
  const response = await fetch(`${API_BASE}/v1/compliance/public-key`);
  return handleResponse(response, publicKeySchema);
}

export async function fetchHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/v1/health`);
  if (!response.ok) {
    throw new Error('Service offline');
  }
  return response.json();
}
