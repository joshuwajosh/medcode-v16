"""
Phase 5 — API Validation Test Suite
Tests every API endpoint with TestClient from fastapi.testclient.
"""
import os
import sys
import json

# Suppress env validation for testing
os.environ["MEDCODE_ENV"] = "development"
os.environ["TESTING"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from api.app import app
from security.auth import get_auth_service

client = TestClient(app, raise_server_exceptions=False)

RESULTS = []

def record(name, method, url, status_code, ok, detail=""):
    RESULTS.append({
        "endpoint": f"{method} {url}",
        "name": name,
        "expected_status": status_code,
        "got_status": ok,
        "pass": status_code == ok,
        "detail": detail[:200] if detail else "",
    })
    mark = "PASS" if status_code == ok else "FAIL"
    detail_short = detail[:80] if detail else ""
    print(f"  [{mark}] {method} {url} - expected {status_code}, got {ok}" + (f" ({detail_short})" if detail_short else ""))


def get_admin_token():
    auth = get_auth_service()
    from security.constants import Role
    # Create admin user if not exists
    try:
        existing = None
        for u in auth._users.values():
            if u.username == "admin":
                existing = u
                break
        if existing is None:
            auth.create_user("admin", "admin123", role=Role.ADMIN)
    except Exception as e:
        print(f"  Could not create admin user: {e}")
    result = auth.authenticate("admin", "admin123", "127.0.0.1")
    if result is None:
        return ""
    if result and "access_token" in result:
        return result["access_token"]
    return ""


def test_health_endpoints(token):
    print("\n=== HEALTH ENDPOINTS ===")
    r = client.get("/health")
    record("GET /health", "GET", "/health", 200, r.status_code)

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = client.get("/fhir/metadata", headers=headers)
    record("GET /fhir/metadata", "GET", "/fhir/metadata", 200, r.status_code)


def test_dashboard_endpoints():
    print("\n=== DASHBOARD ENDPOINTS ===")
    r = client.get("/api/v19/dashboard/stats")
    record("GET /api/v19/dashboard/stats", "GET", "/api/v19/dashboard/stats", 200, r.status_code)

    r = client.get("/api/v19/dashboard/activity")
    record("GET /api/v19/dashboard/activity", "GET", "/api/v19/dashboard/activity", 200, r.status_code)

    r = client.get("/api/v19/dashboard/charts")
    record("GET /api/v19/dashboard/charts", "GET", "/api/v19/dashboard/charts", 200, r.status_code)


def test_billing_endpoints(token):
    print("\n=== BILLING ENDPOINTS ===")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # POST /api/v19/billing/generate-claim
    r = client.post("/api/v19/billing/generate-claim", json={
        "cpt_codes": [{"code": "99213", "description": "Office Visit"}],
        "icd_codes": [{"code": "J06.9", "description": "Upper Respiratory Infection"}],
    }, headers=headers)
    record("POST /billing/generate-claim", "POST", "/api/v19/billing/generate-claim", 200, r.status_code, r.text[:200])

    # POST /api/v19/billing/validate-claim
    r = client.post("/api/v19/billing/validate-claim", json={
        "cpt_codes": [{"code": "99213", "description": "Office Visit"}],
        "icd_codes": [{"code": "J06.9", "description": "Upper Respiratory Infection"}],
    }, headers=headers)
    record("POST /billing/validate-claim", "POST", "/api/v19/billing/validate-claim", 200, r.status_code, r.text[:200])

    # POST /api/v19/billing/cms1500
    r = client.post("/api/v19/billing/cms1500", json={
        "cpt_codes": [{"code": "99213", "description": "Office Visit"}],
        "icd_codes": [{"code": "J06.9", "description": "Upper Respiratory Infection"}],
    }, headers=headers)
    record("POST /billing/cms1500", "POST", "/api/v19/billing/cms1500", 200, r.status_code, r.text[:200])

    # POST /api/v19/billing/edi-837
    r = client.post("/api/v19/billing/edi-837", json={
        "cpt_codes": [{"code": "99213", "description": "Office Visit"}],
        "icd_codes": [{"code": "J06.9", "description": "Upper Respiratory Infection"}],
    }, headers=headers)
    record("POST /billing/edi-837", "POST", "/api/v19/billing/edi-837", 200, r.status_code, r.text[:200])

    # POST /api/v19/billing/submit-claim
    r = client.post("/api/v19/billing/submit-claim", json={
        "cpt_codes": [{"code": "99213", "description": "Office Visit"}],
        "icd_codes": [{"code": "J06.9", "description": "Upper Respiratory Infection"}],
    }, headers=headers)
    record("POST /billing/submit-claim", "POST", "/api/v19/billing/submit-claim", 200, r.status_code, r.text[:200])

    # POST /api/v19/billing/batch
    r = client.post("/api/v19/billing/batch", json={
        "claims": [{
            "cpt_codes": [{"code": "99213", "description": "Office Visit"}],
            "icd_codes": [{"code": "J06.9", "description": "Upper Respiratory Infection"}],
        }],
    }, headers=headers)
    record("POST /billing/batch", "POST", "/api/v19/billing/batch", 200, r.status_code, r.text[:200])

    # GET /api/v19/billing/batches
    r = client.get("/api/v19/billing/batches", headers=headers)
    record("GET /billing/batches", "GET", "/api/v19/billing/batches", 200, r.status_code, r.text[:200])

    # GET /api/v19/billing/denial-patterns
    r = client.get("/api/v19/billing/denial-patterns", headers=headers)
    record("GET /billing/denial-patterns", "GET", "/api/v19/billing/denial-patterns", 200, r.status_code, r.text[:200])

    # GET /api/v19/billing/pos-codes
    r = client.get("/api/v19/billing/pos-codes", headers=headers)
    record("GET /billing/pos-codes", "GET", "/api/v19/billing/pos-codes", 200, r.status_code, r.text[:200])


def test_reports_endpoints(token):
    print("\n=== REPORTS ENDPOINTS ===")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # GET /api/v19/reports/hipaa-compliance (returns PDF)
    r = client.get("/api/v19/reports/hipaa-compliance", headers=headers)
    record("GET /reports/hipaa-compliance", "GET", "/api/v19/reports/hipaa-compliance", 200, r.status_code)

    # GET /api/v19/reports/claim-summary (returns PDF)
    r = client.get("/api/v19/reports/claim-summary", headers=headers)
    record("GET /reports/claim-summary", "GET", "/api/v19/reports/claim-summary", 200, r.status_code)


def test_webhooks_endpoints(token):
    print("\n=== WEBHOOKS ENDPOINTS ===")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # POST /api/v19/webhooks
    r = client.post("/api/v19/webhooks", json={
        "organization_id": "org-test",
        "url": "https://example.com/webhook",
        "events": ["claim.submitted"],
        "secret": "test_secret_123",
    }, headers=headers)
    record("POST /webhooks", "POST", "/api/v19/webhooks", 200, r.status_code, r.text[:200])

    # GET /api/v19/webhooks
    r = client.get("/api/v19/webhooks?organization_id=org-test", headers=headers)
    record("GET /webhooks", "GET", "/api/v19/webhooks", 200, r.status_code, r.text[:200])


def test_tenants_endpoints(token):
    print("\n=== TENANTS ENDPOINTS ===")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # POST /api/v19/tenants
    r = client.post("/api/v19/tenants", json={
        "name": "Test Organization",
        "plan": "enterprise",
    }, headers=headers)
    record("POST /tenants", "POST", "/api/v19/tenants", 200, r.status_code, r.text[:200])

    # GET /api/v19/tenants
    r = client.get("/api/v19/tenants", headers=headers)
    record("GET /tenants", "GET", "/api/v19/tenants", 200, r.status_code, r.text[:200])


def test_clinical_notes_endpoint(token):
    print("\n=== CLINICAL NOTES ENDPOINTS ===")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # POST /api/v19/clinical-notes/parse
    r = client.post("/api/v19/clinical-notes/parse", json={
        "note_text": "Patient presents with acute bronchitis. Administered nebulizer treatment.",
        "note_type": "progress",
    }, headers=headers)
    record("POST /clinical-notes/parse", "POST", "/api/v19/clinical-notes/parse", 200, r.status_code, r.text[:200])


def test_coding_endpoint(token):
    print("\n=== CODING ENDPOINTS ===")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # POST /api/v19/code
    r = client.post("/api/v19/code", json={
        "note": "Patient presents with chest pain, shortness of breath. ECG shows ST elevation. Troponin elevated. Diagnosis: Acute STEMI.",
        "mdm_level": "high",
    }, headers=headers)
    record("POST /code (V19)", "POST", "/api/v19/code", 200, r.status_code, r.text[:200])


def test_auth_endpoints(token):
    print("\n=== AUTH ENDPOINTS ===")
    # Login (public)
    r = client.post("/api/v19/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    record("POST /auth/login", "POST", "/api/v19/auth/login", 200, r.status_code, r.text[:200])

    # Refresh (public)
    r = client.post("/api/v19/auth/refresh", json={
        "refresh_token": "invalid_token",
    })
    record("POST /auth/refresh (invalid)", "POST", "/api/v19/auth/refresh", 401, r.status_code, r.text[:200])

    # Auth stats (public per middleware for dashboard)
    r = client.get("/api/v19/auth/stats")
    record("GET /auth/stats (public)", "GET", "/api/v19/auth/stats", 200, r.status_code, r.text[:200])


def main():
    print("=" * 60)
    print("  PHASE 5 — API VALIDATION TEST SUITE")
    print("=" * 60)

    # Get auth token
    token = get_admin_token()
    if not token:
        print("\nWARNING: Could not get auth token. Authenticated endpoints may 401.")

    test_health_endpoints(token)
    test_dashboard_endpoints()
    test_auth_endpoints(token)
    test_billing_endpoints(token)
    test_reports_endpoints(token)
    test_webhooks_endpoints(token)
    test_tenants_endpoints(token)
    test_clinical_notes_endpoint(token)
    test_coding_endpoint(token)

    # Summary
    passed = sum(1 for r in RESULTS if r["pass"])
    failed = sum(1 for r in RESULTS if not r["pass"])
    total = len(RESULTS)

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} PASSED, {failed} FAILED")
    print(f"{'='*60}")

    if failed:
        print("\nFAILED ENDPOINTS:")
        for r in RESULTS:
            if not r["pass"]:
                print(f"  - {r['endpoint']}: expected {r['expected_status']}, got {r['got_status']} — {r['detail']}")

    # Write results to JSON for report generation
    with open("phase5_results.json", "w") as f:
        json.dump({"results": RESULTS, "summary": {"total": total, "passed": passed, "failed": failed}}, f, indent=2)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
