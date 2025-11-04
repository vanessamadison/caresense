# CareSense X Architecture Blueprint

## Core Principles

- **Zero-trust**: every client request must present biometric or device attestation.
- **Data minimisation**: PHI never leaves encrypted storage; only derived signals flow.
- **Cryptographic verifiability**: all triage actions produce Ed25519-signed audit trails and retrievable public keys.
- **Observability without exposure**: structured logs, metrics, and health endpoints omit patient payloads.

## Component Overview

| Layer | Services | Highlights |
| --- | --- | --- |
| Edge | Frontend SPA (Vite/React) | Secure proxy configuration, biometric enrolment wizard, triage dashboard |
| API | FastAPI | `/v1/triage`, `/v1/biometrics/enrol`, `/v1/compliance/public-key`, `/version` |
| Crypto | Pyfhel CKKS + Ed25519 | Homomorphic biometric comparison, signed ledgers |
| ML | Scikit-learn calibration pipeline | Differential privacy ready, model card + JSON metrics |
| Storage | Encrypted file store | Fernet key wrapping, hashed OCR lineage |

## Request Flow

1. Device collects biometric embedding (TensorFlow Lite / WASM) → hashed & normalised client-side.
2. SPA hits `/v1/biometrics/enrol` to obtain encrypted token.
3. Subsequent triage calls send symptoms + biometric token + ephemeral embedding for verification.
4. Backend validates via homomorphic distance, scores symptoms, and emits signed audit record.
5. Frontend displays urgency, recommended care, and provides copyable audit signature for compliance dashboards.

## Security Hardening Checklist

- Enforce HTTPS + HSTS at edge.
- Terminate TLS with post-quantum KEM (benchmark `kyber768` once widely supported).
- Rotate Fernet keys via KMS; store Ed25519 public key in transparent log.
- Run `make security-scan` in CI and feed results to SIEM.
- Attach build provenance (SLSA level 3) when containerising.

## Deployment Modes

- **Local Dev**: `make serve` + `yarn dev` with `.env.local` pointing to `http://localhost:8080`.
- **Prod**: Docker Compose or Kubernetes (ingress + secret mounts). Ensure `/app/data` is backed by encrypted volume.

## Pending Enhancements (v0.3)

- Confidential compute profile (AMD SEV-SNP/Nitro Enclaves).
- WebAuthn fallback for biometric factors.
- Streaming inference metrics via OpenTelemetry OTLP exporter.

