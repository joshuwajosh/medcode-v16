# ADR-001: Pipeline Architecture

## Status
Accepted

## Date
2025-01-15

## Context

MedCode AI processes clinical notes through a deterministic coding pipeline that extracts CPT and ICD-10 codes. The pipeline has grown from a simple encoder into a 1700+ line orchestrator with 20+ stages, deep specialty engines, training case matching, and multiple validation layers.

Key architectural decisions were needed for:
- How to organize a pipeline that has grown through additive development
- How to maintain backward compatibility while improving maintainability
- How to handle failures at individual stages without losing partial results

## Decision

### Pipeline Decomposition

The pipeline is decomposed into three layers:

1. **`agents/pipeline_utils.py`** — Module-level keyword lookup tables and pure helper functions (organism detection, laterality enforcement, ICD/CPT deduplication, clinical relevance filtering). These are stateless functions that operate on data and are independently testable.

2. **`agents/medcode_deterministic_pipeline.py`** — Main orchestrator class `MedcodeDeterministicPipelineV15` (aliased as V16) that owns engine instances and coordinates the 17-stage `run()` method. This remains the single entry point.

3. **Engine classes** — Each engine (ICD, CPT, validation, etc.) lives in its own module under the appropriate domain directory.

### Stage Execution Pattern

Each pipeline stage follows a consistent pattern:
```python
try:
    stage_result = self._engine.process(...)
    result.field = stage_result
    _trace("STAGE_NAME", "completed", {"summary": ...})
except Exception as e:
    result.field = {"error": str(e)}
    _trace("STAGE_NAME", "error", {"error": str(e)})
```

This ensures:
- No single stage failure kills the entire pipeline
- Errors are captured with full context in the audit trace
- Downstream stages receive degraded but valid data

### Backward Compatibility

The pipeline class uses multiple aliases:
```python
MedcodeDeterministicPipelineV16 = MedcodeDeterministicPipelineV15
MedCodeDeterministicPipeline = MedcodeDeterministicPipelineV15
```

All existing API routes and imports continue to work unchanged.

## Consequences

**Positive:**
- Pipeline file reduced from 2423 to ~1700 lines
- Keyword tables and helper functions are independently testable
- Stage failures are isolated and logged with context
- New engines can be added by extending `__init__` and adding stages

**Negative:**
- Two files to maintain instead of one (pipeline_utils + pipeline)
- Import graph is slightly more complex
- Training case matching logic remains in the orchestrator (too entangled with local variables to extract cleanly)

## Alternatives Considered

1. **Full stage extraction** — Each stage as a separate function in `pipeline_stages.py`. Rejected because stages share local state (cpt_candidates, icd_candidates) and extraction would require passing 10+ mutable parameters.

2. **Async pipeline** — Run stages concurrently where possible. Deferred because the current synchronous design is simpler and the bottleneck is I/O (LLM calls), not CPU.
