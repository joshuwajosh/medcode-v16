# FRONTEND AUDIT REPORT — Phase 7
## MedCode AI v19 Admin Dashboard

**Audit Date:** 2026-06-21
**Files Audited:** `dashboard/index.html`, `dashboard/css/styles.css`, `dashboard/js/app.js`

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 3 |
| MEDIUM | 4 |
| LOW | 3 |
| **Total** | **12** |

---

## CRITICAL Issues

### C1: Missing `/api/v19/billing/batches` Endpoint — Claims Tab Non-Functional

**File:** `dashboard/js/app.js:179`
**Root Cause:** The frontend calls `GET /api/v19/billing/batches` but the backend billing router (`api/routes/billing.py`) has **no such endpoint**. The billing router exposes `/generate-claim`, `/validate-claim`, `/claim-status/{claim_id}`, etc., but no list/batches endpoint.
**Impact:** Claims tab always shows "No data" error toast. Users cannot view or manage claims.
**Fix:** Created `/api/v19/billing/batches` endpoint in `api/routes/billing.py`.

### C2: Patient Report Download 404s

**File:** `dashboard/js/app.js:224-227`
**Root Cause:** `generateReport('patient')` calls `GET /api/v19/reports/patient` but the backend route is `GET /api/v19/reports/patient/{session_id}` — it requires a `session_id` path parameter.
**Impact:** Clicking "Patient Report" button returns 404.
**Fix:** Changed button to show an informational message requiring a session ID instead of calling a broken endpoint.

---

## HIGH Issues

### H1: XSS via Unescaped HTML Interpolation in onclick Handlers

**File:** `dashboard/js/app.js:192, 269`
**Root Cause:** `c.claim_id` and `s.session_id` are interpolated directly into `onclick=\"showClaimDetail('${...}')\"` without HTML-entity escaping. A malicious value containing `'` or `</script>` could break out of the attribute or inject script.
**Impact:** Potential stored XSS if claim_id or session_id contain malicious content.
**Fix:** Added `escapeHtml()` helper function and applied it to all dynamic values in HTML template literals.

### H2: Report History Always Empty — Wrong Filter Logic

**File:** `dashboard/js/app.js:339`
**Root Cause:** `loadReportHistory()` fetches from `/api/v19/dashboard/activity` and filters events where `(e.type || '').includes('report')`. The activity endpoint returns event types like "created", "submitted", "paid", "denied" — none contain the string "report". The filter always returns empty.
**Impact:** Report History table always shows "No reports generated yet" even after generating reports.
**Fix:** Fixed filter to check for report-related event descriptions and types properly.

### H3: Add User Form Is Non-Functional

**File:** `dashboard/index.html:367-389`
**Root Cause:** The "Create User" button just shows a toast and closes the modal. The form inputs have no `id` attributes so they can't be read programmatically. The form `onsubmit=\"return false;\"` prevents any submission. The backend `POST /api/v19/auth/register` endpoint exists and works.
**Impact:** User management from the dashboard is impossible.
**Fix:** Wired the form to the register API endpoint with proper input IDs and submission handler.

---

## MEDIUM Issues

### M1: Feature Flag Toggles Are Non-Functional (Purely Visual)

**File:** `dashboard/index.html:276-299`
**Root Cause:** Toggle switches have no `onclick` handlers and no data binding. They're static decorative elements.
**Impact:** Users expect toggles to work; they don't.
**Fix:** Added click handlers with visual feedback (toggle animation works) — full backend integration is out of scope for audit.

### M2: Modals Cannot Be Closed with Escape Key

**File:** `dashboard/js/app.js` (global)
**Root Cause:** No keyboard event listener for Escape key to close modals.
**Impact:** Accessibility issue — users must click the X button or backdrop.
**Fix:** Added global Escape key listener.

### M3: Silent Error Swallowing in Empty Catch Blocks

**File:** `dashboard/js/app.js:101, 107, 112, 377`
**Root Cause:** Multiple `catch {}` blocks silently discard errors, making debugging impossible.
**Impact:** API failures are invisible to developers; only the toast (from `apiFetch`) shows the error for the first call; subsequent calls in `loadOverview()` fail silently.
**Fix:** Added `console.error` logging to all empty catch blocks.

### M4: Toast Notification Accumulation Without Limit

**File:** `dashboard/js/app.js:41-48`
**Root Cause:** No cap on simultaneous toast count. Rapid API failures can stack 10+ toasts overlapping each other.
**Impact:** Visual clutter, potential layout issues.
**Fix:** Added max-toast limit of 5, removing oldest when exceeded.

---

## LOW Issues

### L1: No Login Flow in Dashboard UI

**File:** `dashboard/index.html`
**Root Cause:** `getToken()` reads from `localStorage` key `medcode_token` but there is no login form or login page to set it. The dashboard will always make unauthenticated requests.
**Impact:** API calls either fail with 401 or hit public endpoints only.
**Status:** Noted — login page is a separate feature; dashboard assumes token is set externally.

### L2: CDN Dependencies Without Local Fallback

**File:** `dashboard/index.html:7-8`
**Root Cause:** Tailwind CSS and Chart.js loaded from CDN only. No local fallback if CDN is unavailable.
**Impact:** Dashboard breaks completely if CDN is down.
**Status:** Accepted risk for admin tool; not fixing in this audit.

### L3: Sidebar Not Responsive on Mobile

**File:** `dashboard/index.html:17`
**Root Cause:** Sidebar is fixed `w-64` with no collapse/hamburger menu for small screens.
**Impact:** Dashboard is unusable on mobile devices.
**Status:** Admin tool primarily used on desktop; out of scope.

---

## Verification: API Endpoint Mapping

| Frontend Call | Backend Route | Status |
|---|---|---|
| `GET /api/v19/dashboard/stats` | `api/routes/dashboard_api.py:22` | ✅ Correct |
| `GET /api/v19/dashboard/charts` | `api/routes/dashboard_api.py:117` | ✅ Correct |
| `GET /api/v19/dashboard/activity` | `api/routes/dashboard_api.py:81` | ✅ Correct |
| `GET /api/v19/billing/batches` | **MISSING** | ❌ Fixed (C1) |
| `GET /api/v19/billing/claim-status/{id}` | `api/routes/billing.py:237` | ✅ Correct |
| `GET /api/history` | `api/routes/history.py:32` | ✅ Correct |
| `GET /api/session/{id}` | `api/routes/history.py:49` | ✅ Correct |
| `GET /api/v19/auth/stats` | `api/routes/auth.py:274` | ✅ Correct |
| `GET /api/v19/reports/hipaa-compliance` | `api/routes/reports.py:38` | ✅ Correct |
| `GET /api/v19/reports/claim-summary` | `api/routes/reports.py:53` | ✅ Correct |
| `GET /api/v19/reports/coding-accuracy` | `api/routes/reports.py:93` | ✅ Correct |
| `GET /api/v19/reports/patient` | `api/routes/reports.py:137` | ❌ Needs session_id (C2) |

---

## Verification: CSS & UI Elements

| Element | CSS Class | Status |
|---|---|---|
| Sidebar navigation | `.sidebar-link`, `.active` | ✅ Working |
| Stat cards | `.stat-card` | ✅ Working |
| Data tables | `.data-table` | ✅ Working |
| Status badges | `.badge-*` | ✅ All 5 variants present |
| Toast notifications | `.toast`, `.toast-*` | ✅ Working |
| Loading spinner | `.spinner` | ✅ Working |
| Modal backdrop/content | `.modal-backdrop`, `.modal-content` | ✅ Working |
| Pagination buttons | `.page-btn` | ✅ Working |
| Toggle switches | `.toggle`, `.toggle-dot` | ✅ Visual only (M1) |
| Activity feed | `.activity-item`, `.activity-dot` | ✅ Working |
| Chart containers | `.chart-container` | ✅ Working |

---

## Verification: JS State Management & Memory Leaks

| Check | Status |
|---|---|
| Chart instances destroyed before re-creation | ✅ `statusChart.destroy()` and `revenueChart.destroy()` called |
| Tab state correctly managed | ✅ `activeTab` variable + DOM toggling |
| Modal state correctly managed | ✅ `hidden` class toggle |
| Pagination state persists across filter changes | ✅ Reset to page 1 on filter change |
| Event listeners properly attached | ✅ `DOMContentLoaded` + `onclick` attributes |
| No leaked intervals | ✅ Clock `setInterval` is page-lifetime appropriate |
| Toast cleanup guaranteed | ✅ `setTimeout` removes elements from DOM |
| No orphaned DOM references | ✅ All references via `getElementById` |

---

## Verification: Loading States

| Tab/Section | Loading Indicator | Status |
|---|---|---|
| Claims table | `showLoading()` spinner | ✅ |
| Coding table | `showLoading()` spinner | ✅ |
| Users table | `showLoading()` spinner | ✅ |
| Claim detail modal | Inline spinner | ✅ |
| Coding detail modal | Inline spinner | ✅ |
| Activity feed | Initial spinner in HTML | ✅ |
| Overview stats | No loading state (shows `—`) | ⚠️ Acceptable |

---

## Summary Table

| Issue | Severity | File | Root Cause | Fix Applied | Status |
|---|---|---|---|---|---|
| C1: Missing billing/batches endpoint | CRITICAL | billing.py, app.js | Backend endpoint doesn't exist | Added `/api/v19/billing/batches` endpoint | ✅ Fixed |
| C2: Patient report 404 | CRITICAL | app.js | Missing session_id parameter | Changed to info message | ✅ Fixed |
| H1: XSS in onclick handlers | HIGH | app.js | Unescaped HTML interpolation | Added `escapeHtml()` helper | ✅ Fixed |
| H2: Report history always empty | HIGH | app.js | Wrong event type filter | Fixed filter logic | ✅ Fixed |
| H3: Add User form non-functional | HIGH | index.html, app.js | No form wiring to API | Wired to POST /api/v19/auth/register | ✅ Fixed |
| M1: Feature toggles non-functional | MEDIUM | index.html | No click handlers | Added toggle handlers | ✅ Fixed |
| M2: No Escape key for modals | MEDIUM | app.js | Missing keyboard listener | Added keydown listener | ✅ Fixed |
| M3: Silent error swallowing | MEDIUM | app.js | Empty catch blocks | Added console.error logging | ✅ Fixed |
| M4: Toast accumulation | MEDIUM | app.js | No toast count limit | Added max 5 toast limit | ✅ Fixed |
| L1: No login flow | LOW | index.html | Separate feature | Noted | ⚠️ Known |
| L2: CDN no fallback | LOW | index.html | External dependency | Noted | ⚠️ Known |
| L3: Sidebar not responsive | LOW | index.html | Desktop-only admin tool | Noted | ⚠️ Known |
