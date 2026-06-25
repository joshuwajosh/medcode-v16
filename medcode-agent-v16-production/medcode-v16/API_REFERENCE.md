# MedCode AI V19 - API Reference

Base URL: http://localhost:8000 (dev) or https://your-domain.com (production)

All API endpoints require JWT Bearer token unless marked as [PUBLIC].

## Authentication
- POST /api/v19/auth/login - Login, returns access + refresh tokens [PUBLIC]
- POST /api/v19/auth/register - Create new user (admin only)
- POST /api/v19/auth/refresh - Refresh access token [PUBLIC]
- POST /api/v19/auth/logout - Invalidate session
- POST /api/v19/auth/emergency-access - Break-glass access (admin)

## Clinical Coding
- POST /api/v19/code - Code a clinical note
- POST /api/v19/clinical-notes/parse - Parse note to CPT/ICD suggestions

## Billing
- POST /api/v19/billing/generate-claim - Generate claim from coded data
- POST /api/v19/billing/validate-claim - Validate + denial prediction
- POST /api/v19/billing/cms1500 - Generate CMS-1500 form data
- POST /api/v19/billing/ub04 - Generate UB-04 form data
- POST /api/v19/billing/edi-837 - Generate EDI 837 file
- POST /api/v19/billing/submit-claim - Full submission workflow
- POST /api/v19/billing/batch - Submit batch of claims
- GET /api/v19/billing/batches - List batches
- GET /api/v19/billing/denial-patterns - Common denial patterns
- GET /api/v19/billing/pos-codes - Place of service codes

## Reports (PDF)
- GET /api/v19/reports/hipaa-compliance - HIPAA compliance PDF
- GET /api/v19/reports/claim-summary - Claim summary PDF
- GET /api/v19/reports/coding-accuracy - Coding accuracy PDF
- GET /api/v19/reports/patient/{session_id} - Patient coding PDF

## Webhooks
- POST /api/v19/webhooks - Register webhook
- GET /api/v19/webhooks - List webhooks
- DELETE /api/v19/webhooks/{id} - Unregister webhook

## Tenants (Multi-Tenant)
- POST /api/v19/tenants - Create tenant (admin)
- GET /api/v19/tenants - List tenants (admin)
- PUT /api/v19/tenants/{id} - Update tenant

## Dashboard
- GET /api/v19/dashboard/stats - Summary statistics
- GET /api/v19/dashboard/activity - Recent activity feed
- GET /api/v19/dashboard/charts - Chart data (30-day trend)

## HL7 FHIR R4
- GET /fhir/Patient/{id} - Patient resource
- GET /fhir/Encounter/{id} - Encounter resource
- GET /fhir/DocumentReference/{id} - Clinical document
- POST /fhir/DocumentReference - Upload clinical note
- GET /fhir/Concept/ - Code lookup
- GET /fhir/ValueSet - CPT/ICD value sets
- GET /fhir/metadata - CapabilityStatement

## Health
- GET /health - Health check [PUBLIC]
- GET /ready - Readiness check [PUBLIC]
- GET /live - Liveness check [PUBLIC]
- GET /docs - Swagger UI [PUBLIC]
- GET /redoc - ReDoc API docs [PUBLIC]

## Rate Limits
- Default: 60 requests/minute per IP
- Burst: 20 requests
- Configurable via RATE_LIMIT_RPM env var
