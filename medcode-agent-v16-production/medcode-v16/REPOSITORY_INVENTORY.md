# REPOSITORY INVENTORY — MedCode AI v16 Production

**Generated:** Phase 1 Audit
**Root:** `D:\medcode-agent-v16-production\medcode-v16`

---

## 1. FOLDER TREE (Top-Level Directories)

```
medcode-v16/
├── api/                    # FastAPI application, routes, middleware
├── agents/                 # AI agent implementations (deterministic pipeline, judge, etc.)
├── agent_security/         # Agent-scoped security (context filter, exposure control)
├── analytics/              # Coding analytics and coder performance tracking
├── aapc/                   # AAPC-related logic
├── assertion/              # Assertion/validation helpers
├── audit/                  # Audit trail, trace logger, replay engine, decision store
├── audit_feedback/         # Audit feedback loops
├── auth/                   # Authentication, JWT, password hashing, role-based access
├── benchmark/              # Benchmarking utilities
├── benchmarks/             # Benchmark suites and runners
├── billing/                # Claim generation, CMS-1500, UB-04, EDI-837
├── candidate_generation/   # Code candidate generation logic
├── cdi/                    # Clinical Documentation Improvement
├── classification/         # Encounter and note classification
├── compliance/             # HIPAA compliance, audit, access control
├── confidence/             # Confidence scoring and calibration
├── config/                 # Configuration management
├── consensus/              # Multi-agent consensus engine
├── context_engine/         # Context management for coding
├── core/                   # Core models, OMOP client, tenant middleware
├── cpc/                    # CPC exam engine
├── cpt/                    # CPT section engines (surgery, cardiac, dermatology, etc.)
├── cpt_reasoning/          # CPT reasoning and selection
├── dashboard/              # Dashboard UI (HTML templates)
├── data/                   # Static data files and knowledge bases
├── debug/                  # Debug tracing tools
├── denials/                # Denial management
├── docs/                   # Documentation
├── documentation_quality/  # Documentation quality checks
├── em_engine/              # E/M (Evaluation & Management) engine
├── enterprise/             # Enterprise features (decision store, replay)
├── errorhandling_cases/    # Error handling test cases
├── evaluation/             # Evaluation metrics, audit failure rates
├── evidence/               # Evidence extraction, span mapping
├── evidence_engine/        # Evidence-based coding engine
├── experts/                # Specialty expert engines
├── explainability/         # Explanation engine for coding decisions
├── fhir/                   # FHIR R4 client and resources
├── icd/                    # ICD-10-CM knowledge base and engine
├── injury_reasoning/       # Injury and external cause reasoning
├── inpatient/              # Inpatient coding logic
├── knowledge/              # Training cases, prompt templates, knowledge bases
├── learning/               # Learning and adaptation modules
├── medical_necessity/      # Medical necessity validation
├── memory/                 # Agent memory management
├── ml/                     # Machine learning models, clinical NLP
├── model_gateway/          # LLM model gateway and routing
├── modifier/               # Modifier selection logic
├── modifier_engine/        # Extended modifier engine
├── monitoring/             # Application monitoring and alerting
├── nlp/                    # Natural language processing
├── observability/          # Distributed tracing, metrics, logging
├── oncology/               # Oncology-specific coding
├── ontology/               # Medical ontology mapping
├── operative/              # Operative note processing
├── optimization/           # Pipeline optimization (v18, parallel retriever, etc.)
├── payer_rules/            # Payer-specific rules engine
├── performance/            # Performance monitoring
├── physician_query/        # Physician query generation
├── privacy/                # PII detection, PHI filtering, HIPAA privacy
├── procedures/             # Procedure mapping and validation
├── rag/                    # RAG (Retrieval-Augmented Generation) indexing
├── reasoning/              # Core reasoning engines (specialty, modifier, bundling)
├── reports/                # Report generation (PDF, analytics)
├── resilience/             # Circuit breakers, fallback routing, retry logic
├── retrieval/              # Document retrieval for coding context
├── retrieval_constraints/  # Retrieval constraint enforcement
├── retrieval_security/     # Retrieval security filtering
├── review/                 # Clinical review workflows
├── routing/                # Request routing and pipeline orchestration
├── scripts/                # Utility scripts
├── sdk/                    # SDK wrappers
├── search/                 # ICD-10/CPT search, BFS traversal
├── security/               # Security utilities, audit, encryption
├── security_hardening/     # Security hardening measures
├── specialties/            # Specialty-specific engines
├── specialty_router/       # Specialty routing logic
├── storage/                # File and data storage
├── surgery/                # Surgery engines (18 subspecialties)
├── tests/                  # Main test suite
├── trauma/                 # Trauma coding engine
├── utils/                  # Text processing, logging utilities
├── validation/             # NCCI, bundling, modifier, LCD validators
└── workflows/              # Workflow engine, state machine, checkpoints
```

**Total top-level directories:** 83

---

## 2. MODULE COUNT BY CATEGORY

### Core Medical Coding
| Module | .py Files | Purpose |
|--------|-----------|---------|
| cpt/ | 14 | CPT section engines (surgery, cardiac, dermatology, observation, etc.) |
| cpt_reasoning/ | 5 | CPT code selection reasoning |
| icd/ | 4 | ICD-10-CM knowledge base and mapping |
| em_engine/ | 9 | E/M level selection |
| modifier/ | 2 | Modifier selection |
| modifier_engine/ | 1 | Extended modifier engine |
| inpatient/ | 2 | Inpatient coding |
| cpc/ | 2 | CPC exam engine |
| cdí/ | 2 | Clinical documentation improvement |
| candidate_generation/ | 2 | Code candidate generation |
| classification/ | 4 | Note classification |
| procedures/ | 3 | Procedure mapping |
| **Subtotal** | **50** | |

### Surgery & Specialties
| Module | .py Files | Purpose |
|--------|-----------|---------|
| surgery/ | 156 | 18 subspecialty engines + tests + workflows |
| specialties/ | 11 | Specialty-specific engines |
| specialty_router/ | 5 | Specialty routing |
| trauma/ | 2 | Trauma coding |
| oncology/ | 2 | Oncology coding |
| inpatient/ | 2 | Inpatient coding |
| **Subtotal** | **178** | |

### AI & Reasoning
| Module | .py Files | Purpose |
|--------|-----------|---------|
| agents/ | 18 | AI agents (deterministic pipeline, judge, etc.) |
| reasoning/ | 26 | Core reasoning engines |
| consensus/ | 5 | Multi-agent consensus |
| context_engine/ | 2 | Context management |
| evidence/ | 6 | Evidence extraction |
| evidence_engine/ | 5 | Evidence-based coding |
| injury_reasoning/ | 8 | Injury/external cause reasoning |
| ml/ | 2 | ML models, clinical NLP |
| nlp/ | 2 | Natural language processing |
| experts/ | 10 | Specialty expert engines |
| **Subtotal** | **84** | |

### Validation & Compliance
| Module | .py Files | Purpose |
|--------|-----------|---------|
| validation/ | 13 | NCCI, bundling, modifier, LCD validators |
| compliance/ | 18 | HIPAA compliance, audit |
| audit/ | 11 | Audit trail, trace, replay |
| assertion/ | 4 | Assertion helpers |
| medical_necessity/ | 1 | Medical necessity validation |
| **Subtotal** | **47** | |

### API & Frontend
| Module | .py Files | Purpose |
|--------|-----------|---------|
| api/ | 19 | FastAPI app, routes, middleware |
| dashboard/ | (HTML) | Dashboard UI |
| reports/ | 2 | Report generation |
| **Subtotal** | **21** | |

### Security & Privacy
| Module | .py Files | Purpose |
|--------|-----------|---------|
| auth/ | 5 | Authentication, JWT, RBAC |
| agent_security/ | 7 | Agent-scoped security |
| security/ | 26 | Security utilities |
| security_hardening/ | 5 | Security hardening |
| privacy/ | 9 | PII detection, PHI filtering |
| retrieval_security/ | 4 | Retrieval security |
| **Subtotal** | **56** | |

### Infrastructure & Operations
| Module | .py Files | Purpose |
|--------|-----------|---------|
| core/ | 14 | Core models, OMOP, tenant |
| config/ | (config) | Configuration |
| workflows/ | 7 | Workflow engine, state machine |
| resilience/ | 5 | Circuit breakers, fallback |
| observability/ | 9 | Tracing, metrics, logging |
| monitoring/ | 5 | Application monitoring |
| performance/ | 2 | Performance monitoring |
| optimization/ | 9 | Pipeline optimization |
| storage/ | 4 | File storage |
| fhir/ | 6 | FHIR R4 client |
| model_gateway/ | 3 | LLM gateway |
| rag/ | 7 | RAG indexing |
| retrieval/ | 6 | Document retrieval |
| retrieval_constraints/ | 2 | Retrieval constraints |
| search/ | 5 | ICD/CPT search |
| **Subtotal** | **95** | |

### Knowledge & Data
| Module | .py Files | Purpose |
|--------|-----------|---------|
| knowledge/ | 26 | Training cases, prompts, KBs |
| data/ | 29 | Static data files |
| learning/ | 4 | Learning modules |
| memory/ | 4 | Agent memory |
| ontology/ | 11 | Medical ontology |
| **Subtotal** | **74** | |

### Testing
| Module | .py Files | Purpose |
|--------|-----------|---------|
| tests/ | 54 | Main test suite |
| benchmarks/ | 16 | Benchmark suites |
| benchmark/ | 2 | Benchmarking utils |
| evaluation/ | 15 | Evaluation metrics |
| documentation_quality/ | 1 | Doc quality checks |
| **Subtotal** | **88** | |

### Utilities & Misc
| Module | .py Files | Purpose |
|--------|-----------|---------|
| utils/ | 3 | Text processing, logging |
| debug/ | 6 | Debug tracing |
| sdk/ | 1 | SDK wrappers |
| scripts/ | (scripts) | Utility scripts |
| audit_feedback/ | 2 | Audit feedback |
| billing/ | 13 | Claim generation, CMS-1500 |
| confidence/ | 10 | Confidence scoring |
| operative/ | 5 | Operative note processing |
| payer_rules/ | 5 | Payer rules |
| physician_query/ | 1 | Physician queries |
| review/ | 6 | Clinical review |
| routing/ | 5 | Request routing |
| denials/ | 2 | Denial management |
| aapc/ | (aapc) | AAPC logic |
| enterprise/ | 2 | Enterprise features |
| errorhandling_cases/ | (cases) | Error handling cases |
| explainability/ | 2 | Explanation engine |
| **Subtotal** | **80** | |

### Root-Level Files
| Category | Files |
|----------|-------|
| Entry points | main.py, run.py, prompts.py |
| Debug scripts (root) | debug_cpt.py, debug_dan_williams.py, debug_llm_raw.py, debug_office.py, debug_string_replace.py, debug_try_parse_json.py |
| Test scripts (root) | test_clean.py, test_cpt.py, test_debug.py, test_influenza.py, test_json_parse.py, test_json_parsing.py, test_json_parsing_fixed.py, test_llm_response.py, test_ml_keloid.py, test_omop.py, test_phase8_coding_validation.py, test_phase9_agent_audit.py, test_v16_e2e.py, final_test.py, final_test_fixed.py, full_pipeline_test.py, phase5_api_test.py |
| Audit reports (root) | 14 .md audit reports |
| Config | .env.example, requirements.txt, Dockerfile, docker-compose*.yml |

---

## 3. FILE COUNTS SUMMARY

| File Type | Count |
|-----------|-------|
| Python (.py) | **776** |
| Markdown (.md) | 33 |
| JSON (.json) | 58 |
| YAML (.yml) | 5 |
| HTML (.html) | 2 |
| SQL (.sql) | 1 |
| Shell scripts (.sh) | 4 |
| **Total estimated** | **~880** |

---

## 4. API ENDPOINT COUNT

**Total API endpoints: 108**

### Breakdown by Route File:

| Route File | Endpoint Count | Methods |
|------------|----------------|---------|
| api/app.py | 16 | GET, POST (health, ready, live, code, pipeline, metrics, audit) |
| api/routes/auth.py | 9 | POST (login, register, refresh, logout, revoke-all, emergency-access) |
| api/routes/billing.py | 12 | POST, GET (claims, CMS-1500, UB-04, EDI-837, payer rules) |
| api/routes/coding.py | 8 | POST (v15/code, v15/cpc, v15/batch, code, batch, v15/direct, v16/code) |
| api/routes/compliance.py | 9 | GET, POST (HIPAA, audit, access matrix, PHI log, alerts) |
| api/routes/fhir.py | 11 | GET, POST (Patient, Encounter, DocumentReference, Concept, ValueSet, metadata) |
| api/routes/search.py | 5 | GET (search, validate, hierarchy, map, suggest) |
| api/routes/batch.py | 4 | POST, GET (batch, status, retry) |
| api/routes/reports.py | 4 | GET (HIPAA, claim-summary, coding-accuracy, patient) |
| api/routes/history.py | 3 | GET, POST (history, session, feedback) |
| api/routes/dashboard_api.py | 3 | GET (stats, activity, charts) |
| api/routes/tenants.py | 5 | POST, GET, PUT, DELETE (CRUD) |
| api/routes/webhooks.py | 4 | POST, GET, DELETE (CRUD + deliveries) |
| api/routes/clinical_notes.py | 1 | POST (parse) |
| api/routes/debug.py | 2 | POST, GET (pipeline) |
| api/routes/timing.py | ~3+ | (timing endpoints) |
| api/routes/health.py | ~3+ | (health check endpoints) |

---

## 5. TEST FILE COUNT

**Total test files: 65** (in tests/ directory and surgery/tests/)
**Root-level test/debug scripts: 17**

### tests/ Directory (54 files)
- Integration tests: test_v16_*, test_v17_*, test_v18_*, test_v12_*
- Unit tests: test_compliance, test_orchestrator, test_specialty_router, etc.
- Regression tests: test_100_cases, test_1000_cases, test_20_real_patients
- Debug tests: debug_golden, debug_14_failures, debug_trauma_pipeline
- Helpers: run_regression_suite, run_full_regression, verify_training

### surgery/tests/ (11 files)
- test_surgical_engines.py, test_surgery_rag_adapter.py
- test_sixth_series.py, test_fifth_series.py
- Per-subspecialty: test_cv_engine, test_msk_engine, test_gi_engine, test_integumentary_engine, etc.

### Root-Level Test/Debug Scripts (17 files)
- test_clean.py, test_cpt.py, test_debug.py, test_influenza.py, etc.
- test_phase8_coding_validation.py, test_phase9_agent_audit.py
- final_test.py, final_test_fixed.py, full_pipeline_test.py
- phase5_api_test.py

---

## 6. TOTAL LINES OF CODE

| Category | Lines |
|----------|-------|
| Python code (.py) | **187,982** |
| Estimated total (all files) | ~200,000+ |

### Largest Python Files (>100KB)
| File | Size |
|------|------|
| knowledge/training_cases_v19.py | 1,511 KB |
| knowledge/icd10_engine_v19.py | 140 KB |
| knowledge/_gen_batch6.py | 131 KB |
| agents/medcode_deterministic_pipeline.py | 131 KB |
| knowledge/cpt_engine.py | 122 KB |
| surgery/integumentary/anatomy_lock_engine.py | 109 KB |
| knowledge/_gen_batch6b.py | 108 KB |

---

## 7. KEY OBSERVATIONS

1. **Massive codebase**: 776 Python files, ~188K lines of code across 83 directories
2. **Surgery module dominance**: 156 .py files (20% of all Python) with 18 subspecialty engines
3. **Knowledge bloat**: training_cases_v19.py alone is 1.5MB — single-file data dumps
4. **Root-level test sprawl**: 17 test/debug scripts scattered at root instead of in tests/
5. **14 audit report .md files** at root — legacy from previous audit phases
6. **Duplicate module purposes**: reasoning/ (26 files) + experts/ (10) + evidence_engine/ (5) overlap conceptually
7. **Large single-file engines**: medcode_deterministic_pipeline.py at 131KB needs decomposition
