# ADR-002: Security Model

## Status
Accepted

## Date
2025-01-15

## Context

MedCode AI processes Protected Health Information (PHI) under HIPAA regulations. The system must ensure:
- PHI is encrypted at rest and in transit
- All access to PHI is audit-logged
- Authentication and authorization are enforced
- Input sanitization prevents injection attacks
- Rate limiting prevents abuse

## Decision

### Defense-in-Depth Layers

The security model applies four concentric layers:

1. **Transport Security** — TLS termination via nginx reverse proxy. All HTTP traffic is upgraded to HTTPS.

2. **Authentication** — JWT Bearer tokens via `security/auth.py`. The `RequestLoggerMiddleware` logs all requests with user identity.

3. **Input Sanitization** — `SanitizationMiddleware` strips dangerous characters from all request bodies before they reach route handlers. PHI fields are detected and encrypted via Fernet (AES-128-CBC) using `security/encryption.py`.

4. **Audit Trail** — Every PHI access event is recorded in a tamper-evident hash chain (`audit/security_monitor.py`). The chain uses SHA-256 hashes linking each event to its predecessor.

### PHI Encryption

```python
from security.encryption import FieldLevelEncryption
enc = FieldLevelEncryption()
encrypted = enc.encrypt(plaintext)  # Fernet token
decrypted = enc.decrypt(encrypted)  # Original text
```

The encryption key is derived from the `PHI_ENCRYPTION_KEY` environment variable. Default dev keys are clearly marked as non-production.

### Route-Level Security

- All `/api/v19/*` routes require authentication
- Rate limiting is applied per-IP (configurable)
- Response bodies are filtered to remove internal error details in production
- Webhook signatures use HMAC-SHA256 for delivery verification

### Data Isolation

- SQLite databases are stored in the `data/` directory with restrictive file permissions
- No PHI is logged in plaintext — log entries use hashed identifiers
- Session data is encrypted at rest before database storage

## Consequences

**Positive:**
- HIPAA technical safeguards compliance (encryption, access controls, audit logs)
- Defense-in-depth means a single layer bypass doesn't expose PHI
- Tamper-evident audit chain provides forensic evidence

**Negative:**
- Fernet encryption adds ~1ms per field encryption/decryption
- Audit logging increases storage requirements
- Key management is a operational responsibility (key rotation schedule needed)

## Alternatives Considered

1. **Database-level encryption (TDE)** — Rejected because SQLite doesn't support TDE natively and field-level encryption provides more granular control.

2. **OAuth2/OIDC for auth** — Current JWT implementation is sufficient for the current deployment model. Migration to OAuth2 is planned for multi-tenant deployment.

3. **No audit logging** — Rejected for HIPAA compliance reasons.
