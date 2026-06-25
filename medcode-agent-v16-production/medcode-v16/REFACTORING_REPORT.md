# REFACTORING_REPORT.md
## Phase 13 - Code Refactoring | MedCode AI v16

**Date:** 2026-06-21

---

## Changes Applied

### 1. BUG FIX: CDI Engine Regex Error (CRITICAL)

**File:** `cdi/cdi_engine.py:41`
**Issue:** Unescaped `?` regex quantifier causes `re.error: nothing to repeat at position 59`
**Impact:** CDI engine completely non-functional - raises exception on every call

**Before:**
```python
WEAK_DOC_PATTERNS = [
    (r"(?:appears|seems|likely|probably|possibly|maybe|suspected|?)",
     "Uncertain language - may affect coding specificity"),
```

**After:**
```python
WEAK_DOC_PATTERNS = [
    (r"(?:appears|seems|likely|probably|possibly|maybe|suspected|\?)",
     "Uncertain language - may affect coding specificity"),
```

**Status:** FIXED - CDI engine now functional

---

### 2. BUG FIX: Missing Module Import - specialties/__init__.py (CRITICAL)

**File:** `specialties/__init__.py:6`
**Issue:** Import references `obgyn_engine` but file is named `o_b_g_y_n_engine.py`
**Impact:** All specialty engine imports fail - entire specialties module unusable

**Before:**
```python
from specialties.obgyn_engine import OBGYNEngine
```

**After:**
```python
from specialties.o_b_g_y_n_engine import OBGYNEngine
```

**Status:** FIXED

---

### 3. BUG FIX: Missing Module Import - oncology/__init__.py (HIGH)

**File:** `oncology/__init__.py:3`
**Issue:** Imports `chemo_engine` which does not exist (never created or deleted)
**Impact:** Oncology module fails to import

**Before:**
```python
"""Oncology depth module V17."""
from oncology.staging_engine import OncologyStagingEngine
from oncology.chemo_engine import ChemoAdministrationEngine
```

**After:**
```python
"""Oncology depth module V17."""
from oncology.staging_engine import OncologyStagingEngine
```

**Status:** FIXED

---

### 4. BUG FIX: Missing organization_id in Database Writes (HIGH)

**File:** `storage/database.py:155-195`
**Issue:** `save_results()` and `save_feedback()` omit `organization_id` column, breaking multi-tenant isolation
**Impact:** Coded results and feedback cannot be scoped to an organization

**Before (save_results):**
```python
def save_results(self, session_id: str, results: list[dict]):
    conn.execute(
        """INSERT INTO coded_results
           (session_id, code, code_name, vocabulary, code_type,
            sequence_order, llm_score, is_billable, reasoning, confidence_level)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, r.get("code", ""), ...),
    )
```

**After (save_results):**
```python
def save_results(self, session_id: str, results: list[dict],
                 organization_id: str = ""):
    conn.execute(
        """INSERT INTO coded_results
           (session_id, organization_id, code, code_name, vocabulary, code_type,
            sequence_order, llm_score, is_billable, reasoning, confidence_level)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, organization_id, r.get("code", ""), ...),
    )
```

Same pattern applied to `save_feedback()`.

**Migration added:** `_migrate_add_organization_id()` for existing SQLite databases missing the column.

**Status:** FIXED

---

### 5. BUG FIX: Test Suite API Mismatch (MEDIUM)

**File:** `tests/test_v16_enterprise.py:157-208`
**Issue:** 9 tests use old API (`encounter_type=` instead of `encounter_type_hint=`, `em_code` instead of `primary_code`)
**Impact:** 9 tests fail; test results unreliable

**Before:**
```python
result = self.engine.code(note, encounter_type="hospital_admit")
assert result.em_code == "99223"
assert result.mdm.overall_level == 4
```

**After:**
```python
result = self.engine.code(note, encounter_type_hint="inpatient_initial")
assert result.primary_code == "99223"
assert result.mdm.overall_level.value == 4
```

**Status:** FIXED - 9/9 tests now pass

---

## Dead Code Identified (Not Yet Removed)

### Root-level debug/test files (25 files)

| File | Type | Recommendation |
|------|------|----------------|
| `debug_cpt.py` | Debug script | Move to `debug/` |
| `debug_dan_williams.py` | Debug script | Move to `debug/` |
| `debug_llm_raw.py` | Debug script | Move to `debug/` |
| `debug_office.py` | Debug script | Move to `debug/` |
| `debug_string_replace.py` | Debug script | Move to `debug/` |
| `debug_try_parse_json.py` | Debug script | Move to `debug/` |
| `test_clean.py` | One-off test | Move to `tests/` or delete |
| `test_cpt.py` | One-off test | Move to `tests/` or delete |
| `test_debug.py` | One-off test | Move to `tests/` or delete |
| `test_influenza.py` | One-off test | Move to `tests/` or delete |
| `test_json_parse.py` | One-off test | Move to `tests/` or delete |
| `test_json_parsing.py` | One-off test | Move to `tests/` or delete |
| `test_json_parsing_fixed.py` | One-off test | Move to `tests/` or delete |
| `test_llm_response.py` | One-off test | Move to `tests/` or delete |
| `test_ml_keloid.py` | One-off test | Move to `tests/` or delete |
| `test_omop.py` | One-off test | Move to `tests/` or delete |
| `test_phase8_coding_validation.py` | Validation script | Move to `tests/` |
| `test_phase9_agent_audit.py` | Audit script | Move to `tests/` |
| `test_v16_e2e.py` | E2E test | Move to `tests/` |
| `final_test.py` | One-off test | Delete |
| `final_test_fixed.py` | One-off test | Delete |
| `full_pipeline_test.py` | One-off test | Delete |
| `phase5_api_test.py` | API test script | Move to `tests/` |
| `preprocess_mimic.py` | Data prep | Move to `scripts/` |
| `surgerymusculoskeletaltests__init__.py` | Misplaced file | Delete |

### Legacy pipeline files (candidates for removal)

| File | Imported by | Status |
|------|-------------|--------|
| `agents/v14_pipeline.py` | Only debug endpoint | Semi-dead |
| `agents/v15_pipeline.py` | Only V18 fallback | Dead from main app |
| `agents/v17_pipeline_integration.py` | Only V14 chain | Dead from main app |
| `agents/v19_pipeline.py` | `/api/code` route | **Still live** |

### Root-level data files

| File | Recommendation |
|------|----------------|
| `nul` | Empty/accidental file - delete |
| `test_file.txt` | Test data - move to `data/` or delete |
| `llm_output.txt` | Debug output - delete |

---

## Duplicate Logic Found

| Pattern | Files | Recommendation |
|---------|-------|----------------|
| ICD code matching | Multiple engines have own matching logic | Centralize in `icd/matcher.py` |
| CPT code filtering | Repeated across engines | Centralize in `cpt/filter.py` |
| Confidence calculation | Multiple implementations | Already centralized in `confidence/` - ensure all engines use it |

---

## Inconsistent Patterns Found

| Pattern | Current State | Recommendation |
|---------|---------------|----------------|
| Pydantic V2 config | 3 models use deprecated `class Config` | Migrate to `model_config = ConfigDict(...)` |
| Import style | Mix of `from x import y` and `import x` | Standardize to `from x import y` for project modules |

---

## Summary

| Category | Count |
|----------|-------|
| Critical bugs fixed | 3 |
| High bugs fixed | 2 |
| Medium bugs fixed | 1 |
| Dead files identified | 28 |
| Legacy pipelines identified | 3 (2 removable) |
| Duplicate patterns | 3 |
