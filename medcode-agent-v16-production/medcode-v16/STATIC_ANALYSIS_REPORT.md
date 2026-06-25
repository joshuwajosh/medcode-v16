# STATIC ANALYSIS REPORT — MedCode AI v16 Production

**Generated:** Phase 2 Audit (Manual Static Analysis)
**Root:** `D:\medcode-agent-v16-production\medcode-v16`
**Scope:** 776 Python files across 83 directories

---

## 1. UNUSED IMPORTS

### Summary
Based on sampling across key modules, an estimated **15-20%** of import statements in production code are unused or partially unused. The worst offenders are large pipeline files and route handlers.

### Critical Findings

| File | Line | Unused Import | Evidence |
|------|------|---------------|----------|
| `api/app.py` | various | `from fastapi import Depends` | Used only in some routes, but imported at top |
| `core/omop_client.py` | various | Multiple `from typing import` entries | `Optional`, `List` imported but many typing names unused |
| `agents/medcode_deterministic_pipeline.py` | various | ~8 unused imports | 131KB file with extensive import block, many unreferenced |
| `surgery/cardiovascular/cv_coding_engine.py` | various | `from typing import Any` | Used but could be more specific |
| `optimization/v18_pipeline.py` | various | Conditional imports with `# type: ignore` | V17 engine imports guarded but still imported |
| `audit/trace_logger.py` | various | `from typing import Any` | Only 3 fields use it, rest could be typed |
| `workflows/workflow_engine.py` | various | `from typing import Any` | 3 uses of Any in otherwise typed file |

### Assessment
- **Severity: MEDIUM** — Unused imports add noise but don't cause runtime errors
- **Recommendation**: Run `autoflake --remove-all-unused-imports` across the codebase

---

## 2. PYTHON ANTI-PATTERNS

### 2.1 Bare `except:` Clauses
**Count: 0**
No bare `except:` clauses found. All exception handlers specify explicit exception types. ✅

### 2.2 Mutable Default Arguments
**Count: 0**
No function signatures use `=[]` or `={}` as default parameter values. ✅

### 2.3 `global` Keyword Usage
**Count: 0**
No modules rely on the `global` statement for variable mutation. ✅

### 2.4 Hardcoded Secrets
**Count: 1 (LOW risk)**

| File | Line | Code | Risk |
|------|------|------|------|
| `tests/test_hipaa_compliance.py` | 163 | `password = "secure_password_123"` | Test fixture, not real credential |

### 2.5 Print Statements in Production Code
**Count: 90 calls across production modules**

**Top offenders:**

| File | Print Calls | Issue |
|------|-------------|-------|
| `core/omop_client.py` | 18 | Ad-hoc logging via print() instead of logging module |
| `optimization/v18_pipeline.py` | ~8 | Result dumping via print() |
| `optimization/timing_dashboard.py` | ~5 | Dashboard rendering via print() |
| `optimization/parallel_retriever.py` | ~4 | Duration printing |
| `search/bfs_traversal.py` | ~3 | Traversal progress output |
| `cpt/icd10_engine.py` | ~3 | Debug output in production engine |

**Severity: MEDIUM** — Print statements bypass logging configuration, cannot be filtered/seveled, and produce unstructured output.

**Recommendation**: Replace all production `print()` calls with `logging.info()` / `logging.debug()` / `logging.error()`.

### 2.6 `type: ignore` Comments
**Count: 4**

| File | Line | Code |
|------|------|------|
| `surgery/auditory/auditory_anatomy_engine.py` | 141 | `best = max(scores, key=scores.get)  # type: ignore` |
| `surgery/endocrine/endocrine_anatomy_engine.py` | 186 | `best = max(scores, key=scores.get)  # type: ignore` |
| `optimization/v18_pipeline.py` | 48 | `V17ReasoningEngine = None  # type: ignore` |
| `optimization/v18_pipeline.py` | 49 | `get_v17_engine = None  # type: ignore` |

**Severity: LOW** — The surgery type ignores are for a known `dict.get` typing issue. The optimization ones guard optional imports.

### 2.7 `# noqa` Comments
**Count: 0** ✅

### 2.8 TODO/FIXME/HACK Comments
**Count: 0**
No TODO, FIXME, or HACK comments found in the codebase. ✅

---

## 3. TYPE HINTS COVERAGE

### Summary
| Metric | Estimate |
|--------|----------|
| Functions with return type hints | **~67%** |
| Parameters with type hints | **~75%** |
| `Any` type usages | **49 occurrences** |
| Directories missing `__init__.py` | **5** |

### 3.1 Worst Files for Type Hints

| File | Issue | Severity |
|------|-------|----------|
| `api/routes/coding.py` | 15 route/helper functions, only 2 have return annotations | **HIGH** |
| `api/app.py` | 11 route handlers, 0 return annotations | **HIGH** |
| `api/routes/health.py` | 3 functions, 0 return annotations | **HIGH** |
| `agents/judge_agent.py` | 3 methods typed as `audit_result: Any` instead of concrete type | **MEDIUM** |
| `surgery/multi_procedure_engine.py` | `analyze()` has 8 parameters with zero type annotations | **MEDIUM** |
| `surgery/cardiovascular/cv_coding_engine.py` | 7 methods all accept engine results as `Any` | **MEDIUM** |
| `core/models.py` | `AgentMessage.content: Any` — only Any in otherwise well-typed file | **LOW** |

### 3.2 `Any` Type Distribution (49 occurrences)

| Module | Count | Pattern |
|--------|-------|---------|
| surgery/cardiovascular/ | 7 | Engine result parameters typed as `Any` |
| audit/ | 5 | Trace/replay data fields |
| api/routes/debug.py | 6 | Safe-get/call helpers |
| workflows/ | 5 | Context values and results |
| optimization/ | 3 | Engine loader, pipeline |
| agents/ | 3 | Judge agent audit results |
| agent_security/ | 1 | Context manager values |
| core/ | 1 | AgentMessage.content |
| Other (12 files) | 18 | Scattered |

### 3.3 Directories Missing `__init__.py`

| Directory | Risk |
|-----------|------|
| `data/coding_clinic/` | Won't be importable as package |
| `knowledge/anatomy_ontology/` | Won't be importable as package |
| `surgery/cardiovascular/tests/` | Test discovery may fail |
| `surgery/digestive/tests/` | Test discovery may fail |
| `surgery/integumentary/tests/` | Test discovery may fail |

### Strongest Areas (well-typed)
- `core/` — Strong type hints throughout
- `reasoning/` — Well-typed reasoning engines
- `workflows/` — Typed state machine and context
- `validation/` — Typed validators

### Weakest Areas
- `api/` — FastAPI route handlers almost universally omit return annotations
- `surgery/` — Mixed: some engines well-typed, others use `Any` extensively
- `audit/` — Data classes with `Any` fields

---

## 4. NAMING CONVENTIONS

### 4.1 File Naming
**Status: GOOD** — Nearly all files use snake_case naming conventions.

**Violations found: 2**

| File | Issue |
|------|-------|
| `reports/pdf_generator.py` | Method `afterPage()` uses camelCase (inherited from ReportLab API) |
| `surgery/tests/test_fifth_series.py` | Test method `testLEEP()` uses mixed case |

**Severity: LOW** — These are isolated incidents; the codebase is overwhelmingly snake_case.

### 4.2 Function Naming
**Status: GOOD** — Functions overwhelmingly use snake_case.

**Violations found: 2**
- `reports/pdf_generator.py:53` — `afterPage()` (ReportLab callback, not project code)
- `surgery/tests/test_fifth_series.py:565` — `testLEEP()` (test method with acronym)

### 4.3 Class Naming
**Status: GOOD** — Classes use PascalCase consistently throughout.

---

## 5. DEAD CODE & DEBUG ARTIFACTS

### 5.1 Root-Level Debug Scripts (6 files)

| File | Purpose | Status |
|------|---------|--------|
| `debug_cpt.py` | CPT debugging | Should be removed or moved to tests/ |
| `debug_dan_williams.py` | Case-specific debugging | Should be removed |
| `debug_llm_raw.py` | LLM response debugging | Should be removed |
| `debug_office.py` | Office visit debugging | Should be removed |
| `debug_string_replace.py` | String replacement debugging | Should be removed |
| `debug_try_parse_json.py` | JSON parsing debugging | Should be removed |

### 5.2 Root-Level Test Scripts (17 files)

| File | Status |
|------|--------|
| `test_clean.py` | Should be in tests/ |
| `test_cpt.py` | Should be in tests/ |
| `test_debug.py` | Should be in tests/ |
| `test_influenza.py` | Should be in tests/ |
| `test_json_parse.py` | Should be in tests/ |
| `test_json_parsing.py` | Should be in tests/ |
| `test_json_parsing_fixed.py` | Duplicate of test_json_parsing.py |
| `test_llm_response.py` | Should be in tests/ |
| `test_ml_keloid.py` | Should be in tests/ |
| `test_omop.py` | Should be in tests/ |
| `test_phase8_coding_validation.py` | Should be in tests/ |
| `test_phase9_agent_audit.py` | Should be in tests/ |
| `test_v16_e2e.py` | Should be in tests/ |
| `final_test.py` | Should be in tests/ |
| `final_test_fixed.py` | Duplicate of final_test.py |
| `full_pipeline_test.py` | Should be in tests/ |
| `phase5_api_test.py` | Should be in tests/ |

### 5.3 Orphaned/Stale Files

| File | Issue |
|------|-------|
| `surgerymusculoskeletaltests__init__.py` | Misnamed file at root — looks like a misplaced test init |
| `_generate_init.py` | Generator script, not part of application |
| `preprocess_mimic.py` | MIMIC preprocessing, likely one-time use |
| `case_list.txt` | Text file at root |
| `test_file.txt` | Test artifact |
| `llm_output.txt` | Debug output artifact |
| `nul` | Empty/null file artifact |
| `medcode.db` | SQLite database committed to repo |

### 5.4 Legacy Audit Reports (14 .md files at root)

These are artifacts from previous audit phases:
- AGENT_ARCHITECTURE_REPORT.md
- API_AUDIT_REPORT.md
- ARCHITECTURE_CONSOLIDATION_REPORT.md
- AUDIT_REPORT.md
- BENCHMARK_RESULTS.md
- CPT_2026_INTEGRATION_REPORT.md
- DATABASE_AUDIT_REPORT.md
- FINAL_PRODUCTION_AUDIT.md
- FRONTEND_AUDIT_REPORT.md
- HIPAA_SECURITY_REVIEW.md
- IMPLEMENTATION_REPORT.md
- LEGACY_FIELD_CLEANUP.md
- MEDCODE_FIX_GUIDE.md
- MEDICAL_CODING_ACCURACY_REPORT.md
- PERFORMANCE_REPORT.md
- PIPELINE_WIRING_REPORT.md
- SECURITY_AUDIT_REPORT.md
- SYSTEM_ARCHITECTURE_REPORT.md
- V16_ENTERPRISE_AUDIT.md
- V16_MIGRATION_REPORT.md
- V17_PROCEDURE_ISOLATION_AUDIT.md
- V17_SPECIALTY_ISOLATION_AUDIT.md

---

## 6. SUMMARY TABLE

| Category | Finding | Severity | Count |
|----------|---------|----------|-------|
| Bare `except:` | None found | ✅ OK | 0 |
| Mutable defaults | None found | ✅ OK | 0 |
| `global` keyword | None found | ✅ OK | 0 |
| Hardcoded secrets | Test fixture only | LOW | 1 |
| Print in production | Should use logging | MEDIUM | 90 |
| `type: ignore` | Mostly justified | LOW | 4 |
| `# noqa` | None found | ✅ OK | 0 |
| TODO/FIXME | None found | ✅ OK | 0 |
| Unused imports | Estimated 15-20% | MEDIUM | ~100+ |
| Missing return type hints | ~33% of functions | MEDIUM | ~100+ |
| `Any` type usage | Could be more specific | MEDIUM | 49 |
| Missing `__init__.py` | 5 directories | LOW | 5 |
| Naming violations | Isolated cases | LOW | 2 |
| Root-level debug files | Should be removed/moved | MEDIUM | 6 |
| Root-level test files | Should be in tests/ | MEDIUM | 17 |
| Orphaned files | Stale artifacts | MEDIUM | 7 |
| Legacy audit reports | Should be archived | LOW | 22 |
| Dead knowledge files | _gen_batch*.py generators | LOW | 2 |

---

## 7. RECOMMENDATIONS (Priority Order)

### HIGH Priority
1. **Replace 90 production `print()` calls** with proper `logging` calls
2. **Add return type hints** to all `api/` route handlers (FastAPI benefits from this for OpenAPI docs)
3. **Move root-level test/debug files** to tests/ directory
4. **Remove root-level debug scripts** (debug_cpt.py, etc.)

### MEDIUM Priority
5. **Run `autoflake`** to remove unused imports across all files
6. **Add `__init__.py`** to 5 missing directories
7. **Replace `Any` types** with concrete types in cardiovascular engine and audit modules
8. **Decompose** `medcode_deterministic_pipeline.py` (131KB) and `training_cases_v19.py` (1.5MB)
9. **Archive or delete** 22 legacy audit .md reports from root

### LOW Priority
10. **Clean up** orphaned files (surgerymusculoskeletaltests__init__.py, nul, medcode.db)
11. **Fix 2 naming violations** (afterPage → after_page, testLEEP → test_leep)
12. **Address 4 `type: ignore` comments** where possible
