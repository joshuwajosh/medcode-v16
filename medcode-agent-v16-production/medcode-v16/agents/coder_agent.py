from __future__ import annotations
"""
MedCode AI Agent -- Coder Agent (PRIMARY)
===========================================
Agent 3: Certified Professional Coder -- the core of the system.
Orchestrates semantic search -> BFS hierarchy expansion -> LLM re-ranking.
"""

import json
import logging
import re
import time
from typing import Optional

logger = logging.getLogger('medcode.coder_agent')

from core.models import (
    CodeCandidate, ClinicalNote, ExtractedClinicalData, FinalCodeSet, AgentMessage,
)
from core.llm_client import LLMClient
from core.omop_client import OMOPClient
from knowledge.prompts import CODER_AGENT_PROMPT
from knowledge.cpt_engine import build_cpt_prompt_section, get_rule_engine_scores, DELETED_CPT_2026, check_deleted_codes
from search.semantic_search import SemanticSearch
from search.bfs_traversal import BFSHierarchyTraversal
from search.code_validator import CodeValidator
from knowledge.coding_guidelines import get_s06_loc_character
from core.config import (
    MAX_SEARCH_RESULTS, BFS_EXPLORE_THRESHOLD,
    BEAM_WIDTH_BALANCED, BEAM_WIDTH_DEEP,
    BFS_MAX_DEPTH_BALANCED, BFS_MAX_DEPTH_DEEP,
    MAX_FINAL_CODES, LLM_TEMPERATURE,
)
from ml.clinical_nlp import ClinicalNLPExtractor, ClinicalFeatures


class CoderAgent:
    """
    Certified Professional Coder (CPC) Agent.
    
    Pipeline:
    1. Build search queries from clinical data
    2. Semantic search -> seed candidates
    3. BFS hierarchy expansion (balanced/deep modes)
    4. LLM batch re-ranking
    5. Compliance validation
    6. Final code set assembly
    """

    def __init__(
        self,
        omop_client: OMOPClient,
        llm_client: LLMClient,
    ):
        self.omop = omop_client
        self.llm = llm_client
        self.searcher = SemanticSearch(omop_client)
        self.bfs = BFSHierarchyTraversal(omop_client, llm_client)
        self.validator = CodeValidator()
        self.nlp = ClinicalNLPExtractor()  # ML layer

    async def code(
        self,
        clinical_data: ExtractedClinicalData,
        clinical_note: ClinicalNote = None,
        mode: str = "balanced",
        vocabulary_ids: list[str] = None,
    ) -> FinalCodeSet:
        """
        Run the full coding pipeline on extracted clinical data.
        
        Args:
            clinical_data: Structured clinical data from Physician Agent
            clinical_note: Original clinical note (for audit trail)
            mode: 'quick', 'balanced', or 'deep'
            vocabulary_ids: Vocabularies to search (default: ICD10CM + CPT)
            
        Returns:
            FinalCodeSet with primary, secondary, and procedure codes
        """
        start_time = time.time()
        session_id = f"session_{int(start_time)}"
        
        if vocabulary_ids is None:
            vocabulary_ids = ["ICD10CM", "CPT"]

        raw_note = clinical_note.raw_text if clinical_note else clinical_data.clinical_summary

        audit = []
        audit.append({"step": "begin", "mode": mode, "time": time.time()})

        # ── ML FEATURE EXTRACTION (new in v5) ────────────────────────────
        # Run NLP feature extraction BEFORE semantic search to pre-filter candidates
        logger.info("Step 0: ML NLP feature extraction...")
        ml_features = self.nlp.extract(raw_note)
        audit.append({
            "step": "ml_feature_extraction",
            "encounter_category": ml_features.encounter_category,
            "extraction_confidence": ml_features.extraction_confidence,
            "top_ml_codes": list(ml_features.code_priors.keys())[:8],
            "conditions_found": [e.text for e in ml_features.conditions if not e.negated],
            "drugs_found": [e.text for e in ml_features.drugs],
        })
        logger.debug("Category: %s (conf=%s)", ml_features.encounter_category, ml_features.extraction_confidence)
        logger.debug("ML top codes: %s", list(ml_features.code_priors.keys())[:5])

        # Inject ML-predicted codes directly into candidate pool as guaranteed seeds
        ml_seed_candidates: list[CodeCandidate] = []
        from search.icd10_database import search_with_vocabulary
        for code, prior_score in ml_features.code_priors.items():
            if prior_score > 0.5:
                # Search for this specific code in local DB
                try:
                    results = search_with_vocabulary(code, vocabulary_ids or ["ICD10CM", "CPT"], 3)
                    for r in results:
                        if r.get("concept_code") == code:
                            vocab = r.get("vocabulary_id", "ICD10CM")
                            ml_seed_candidates.append(CodeCandidate(
                                code=code,
                                name=r.get("concept_name", code),
                                vocabulary=vocab,
                                similarity_score=min(0.99, prior_score + 0.1),
                            ))
                            break
                    else:
                        # Code not in DB, add with name from ML maps
                        from ml.clinical_nlp import _CONDITION_MAP, _DRUG_MAP, _PROCEDURE_MAP
                        name = code
                        for mp in [_CONDITION_MAP, _DRUG_MAP, _PROCEDURE_MAP]:
                            for term, codes in mp.items():
                                for c, n, _ in codes:
                                    if c == code:
                                        name = n
                                        break
                        vocab = "CPT" if (len(code) == 5 and code.isdigit()) else (
                            "HCPCS" if code.startswith("J") else "ICD10CM"
                        )
                        ml_seed_candidates.append(CodeCandidate(
                            code=code,
                            name=name,
                            vocabulary=vocab,
                            similarity_score=min(0.99, prior_score + 0.1),
                        ))
                except Exception:
                    pass

        if ml_seed_candidates:
            logger.info("ML seeds injected: %s", [c.code for c in ml_seed_candidates])
            audit.append({
                "step": "ml_seeds_injected",
                "codes": [c.code for c in ml_seed_candidates],
            })

        # Step 1: Semantic search
        logger.info("Step 1: Semantic search (%s mode)...", mode)
        seed_candidates = self.searcher.search_for_clinical_data(
            clinical_data=clinical_data,
            vocabulary_ids=vocabulary_ids,
            limit=MAX_SEARCH_RESULTS,
        )

        # ── MERGE ML seeds with semantic search results ───────────────────
        # ML seeds guaranteed to appear; semantic search supplements them.
        # ML hard-exclude cross-category hallucinations from OMOP results.
        merged_by_code: dict[str, CodeCandidate] = {}

        # First add ML seeds (highest priority)
        for c in ml_seed_candidates:
            merged_by_code[c.code] = c

        # Then add semantic search results, skip ML-excluded codes
        for c in seed_candidates:
            should_exclude, reason = self.nlp.should_exclude_code(ml_features, c.code)
            if should_exclude:
                logger.info("[ML Filter] Excluded %s: %s", c.code, reason)
                audit.append({"step": "ml_excluded", "code": c.code, "reason": reason})
                continue
            if c.code not in merged_by_code:
                merged_by_code[c.code] = c
            else:
                # Boost existing ML seed score slightly if semantic search also finds it
                merged_by_code[c.code].similarity_score = min(
                    0.99, merged_by_code[c.code].similarity_score + 0.05
                )

        seed_candidates = list(merged_by_code.values())

        audit.append({
            "step": "semantic_search",
            "candidates_found": len(seed_candidates),
            "candidates": [c.code for c in seed_candidates[:8]],
        })

        # Step 2: BFS hierarchy expansion (skip in quick mode)
        if mode in ("balanced", "deep"):
            logger.info("Step 2: BFS hierarchy expansion (%s)...", mode)
            seed_dicts = [
                {"code": c.code, "name": c.name, "vocabulary": c.vocabulary, "score": c.similarity_score}
                for c in seed_candidates
            ]
            expanded = await self.bfs.expand(seed_dicts, clinical_data.clinical_summary, mode=mode)
            all_candidates = expanded if expanded else seed_candidates
            audit.append({
                "step": "bfs_expansion",
                "total_candidates": len(all_candidates),
            })
        else:
            all_candidates = seed_candidates
            audit.append({
                "step": "skip_bfs",
                "reason": "quick_mode",
            })

        if not all_candidates:
            audit.append({"step": "no_candidates", "time": time.time()})
            return FinalCodeSet(
                session_id=session_id,
                clinical_note=raw_note,
                processing_time_s=time.time() - start_time,
                agent_mode=mode,
                audit_trail=audit,
                needs_human_review=True,
                review_reasons=["No candidate codes found"],
            )

        # Step 3: LLM batch re-ranking
        logger.info("Step 3: LLM re-ranking %d candidates...", len(all_candidates))
        ranked = self._llm_rerank(all_candidates, raw_note, mode, ml_features)
        audit.append({
            "step": "llm_rerank",
            "candidates_ranked": len(ranked),
        })

        # Step 3.5: CPT 2026 deprecation check
        all_candidate_codes = [c.code.replace('.', '') for c in ranked]
        deprecation_warnings = check_deleted_codes(all_candidate_codes)
        # Pre-initialize validation_warnings here (before Step 6 may overwrite)
        validation_warnings: list[str] = []
        if deprecation_warnings:
            for dw in deprecation_warnings:
                validation_warnings.append(dw["warning"])
                logger.warning("[DEPRECATED] %s: %s", dw['code'], dw['warning'])
            audit.append({
                "step": "cpt2026_deprecation_check",
                "deprecated_codes_found": [dw["code"] for dw in deprecation_warnings],
                "warnings": [dw["warning"] for dw in deprecation_warnings],
            })

        # Step 4: Filter and sort
        threshold = 50 if mode == "quick" else 40
        good_codes = [c for c in ranked if c.llm_score >= threshold][:MAX_FINAL_CODES]

        if not good_codes:
            # Relax threshold - take top codes
            good_codes = ranked[:MAX_FINAL_CODES]

        # Ensure at least one diagnosis (non-procedure) code is included
        has_dx = any(c.vocabulary not in ("CPT", "HCPCS", "ICD10PCS") for c in good_codes)
        if not has_dx:
            for c in ranked:
                if c.vocabulary not in ("CPT", "HCPCS", "ICD10PCS"):
                    good_codes.append(c)
                    break

        # Step 5: Sort by severity/priority
        sorted_codes = self.validator.sort_by_severity(good_codes)

        # Step 6: Validate each code
        validations = self.validator.validate_batch(sorted_codes)
        for code, result in validations.items():
            if not result.valid:
                validation_warnings.extend(result.errors)
            if result.warnings:
                validation_warnings.extend(result.warnings)

        # Check Excludes1 conflicts
        code_list = [c.code for c in sorted_codes]
        conflicts = self.validator.check_excludes1_conflicts(code_list)
        if conflicts:
            for c1, c2, reason in conflicts:
                validation_warnings.append(f"{reason}: {c1} & {c2}")

        # Step 7: Separate primary vs secondary
        # CRITICAL: W/X/Y/V codes are External Cause codes — NEVER primary diagnosis
        EXTERNAL_CAUSE_PREFIXES = ('W', 'X', 'Y', 'V')

        primary_dx = None
        secondary_dx = []
        procedures = []

        for c in sorted_codes:
            if c.vocabulary in ("CPT", "HCPCS", "ICD10PCS"):
                procedures.append(c)
            elif c.code and c.code[0].upper() in EXTERNAL_CAUSE_PREFIXES:
                # External cause code — always secondary/additional, never primary
                secondary_dx.append(c)
            elif primary_dx is None:
                primary_dx = c
            else:
                secondary_dx.append(c)

        # If primary_dx was set to a W/X/Y code somehow, demote it
        if primary_dx and primary_dx.code and primary_dx.code[0].upper() in EXTERNAL_CAUSE_PREFIXES:
            secondary_dx.insert(0, primary_dx)
            primary_dx = None

        # SECONDARY DX DISCIPLINE: Remove low-confidence secondary codes (score < 60)
        # that appear to be filler/padding rather than documented conditions.
        # Vague catch-all codes (M79.89, R69, Z87.xx) need score >= 70 to survive.
        VAGUE_SECONDARY_CODES = {'M79.89', 'M79.3', 'R69', 'M79.9', 'R53.83', 'Z87.39', 'Z87.9'}
        secondary_dx = [
            c for c in secondary_dx
            if c.llm_score >= 60 or  # keep if reasonably confident
               (c.llm_score >= 45 and c.code not in VAGUE_SECONDARY_CODES)  # stricter for vague codes
        ]

        # Fallback: if no primary diagnosis was found, pick the highest-scoring
        # non-procedure, non-external-cause code from sorted_codes
        if primary_dx is None:
            for c in sorted_codes:
                if (c.vocabulary not in ("CPT", "HCPCS", "ICD10PCS") and
                        c.code and c.code[0].upper() not in EXTERNAL_CAUSE_PREFIXES):
                    primary_dx = c
                    # Remove from secondary_dx if it was added there
                    secondary_dx = [x for x in secondary_dx if x.code != c.code]
                    break

        # Step 8: Calculate overall confidence
        all_scores = [c.llm_score for c in sorted_codes]
        confidence = sum(all_scores) / len(all_scores) if all_scores else 0

        # Determine human review need
        needs_review = confidence < 50 or len(validation_warnings) > 3
        human_review_reasons = []
        if confidence < 50:
            human_review_reasons.append(f"Low overall confidence ({confidence:.0f}/100)")
        if len(validation_warnings) > 3:
            human_review_reasons.append(f"{len(validation_warnings)} validation warnings")
        if conflicts:
            human_review_reasons.append(f"{len(conflicts)} Excludes1 conflicts found")
        if deprecation_warnings:
            needs_review = True
            human_review_reasons.append(
                f"CPT 2026 deprecated codes detected: {', '.join(dw['code'] for dw in deprecation_warnings)}"
            )

        # ===== S06 LOC (Loss of Consciousness) Correction =====
        # Auto-correct 6th character for S06 intracranial injury codes
        # based on whether the clinical text mentions loss of consciousness.
        # Operates on CodeCandidate.code string attribute.
        if raw_note:
            clinical_text_lower = raw_note.lower()
            if primary_dx and hasattr(primary_dx, 'code'):
                code_str = primary_dx.code.replace('.', '')
                if code_str.startswith('S06') and len(code_str) >= 6:
                    if code_str[5] in ('1', '5', '9'):
                        correct_6th = get_s06_loc_character(clinical_text_lower)
                        if correct_6th != code_str[5]:
                            chars = list(code_str)
                            chars[5] = correct_6th
                            new_code = ''.join(chars)
                            new_code_fmt = new_code[:3] + '.' + new_code[3:]
                            old_code = primary_dx.code
                            primary_dx.code = new_code_fmt
                            logger.debug("S06 LOC fix: %s -> %s (primary)", old_code, new_code_fmt)
            if secondary_dx:
                for candidate in secondary_dx:
                    if hasattr(candidate, 'code'):
                        code_str = candidate.code.replace('.', '')
                        if code_str.startswith('S06') and len(code_str) >= 6:
                            if code_str[5] in ('1', '5', '9'):
                                correct_6th = get_s06_loc_character(clinical_text_lower)
                                if correct_6th != code_str[5]:
                                    chars = list(code_str)
                                    chars[5] = correct_6th
                                    new_code = ''.join(chars)
                                    new_code_fmt = new_code[:3] + '.' + new_code[3:]
                            old_code = candidate.code
                            candidate.code = new_code_fmt
                            logger.debug("S06 LOC fix: %s -> %s (secondary)", old_code, new_code_fmt)
 
        processing_time = time.time() - start_time

        result = FinalCodeSet(
            session_id=session_id,
            clinical_note=raw_note,
            primary_dx=primary_dx,
            secondary_dx=secondary_dx,
            procedures=procedures,
            confidence_overall=round(confidence, 1),
            needs_human_review=needs_review,
            review_reasons=human_review_reasons,
            audit_trail=audit,
            processing_time_s=round(processing_time, 2),
            agent_mode=mode,
        )

        logger.info("Done: %s (confidence=%.0f, %d secondary, %.1fs)",
                     primary_dx.code if primary_dx else 'NONE',
                     confidence, len(secondary_dx), processing_time)

        return result

    def _llm_rerank(
        self,
        candidates: list[CodeCandidate],
        clinical_context: str,
        mode: str,
        ml_features: ClinicalFeatures = None,
    ) -> list[CodeCandidate]:
        """
        Batch re-rank code candidates using the LLM.
        Scores each 0-100 and adds reasoning.
        """
        if not candidates:
            return []

        # Build the code list for the prompt
        code_list = "\n".join([
            f"{i+1}. {c.code} -- {c.name}" for i, c in enumerate(candidates)
        ])

        # Detect encounter type to prevent cross-category hallucination
        ctx_lower = clinical_context.lower()
        is_skin = any(kw in ctx_lower for kw in [
            'keloid', 'sebaceous', 'skin lesion', 'excision', 'lipoma',
            'melanoma', 'nevus', 'wart', 'keratosis', 'intralesional',
        ])
        is_operative = any(kw in ctx_lower for kw in [
            'operative', 'postoperative', 'surgeon', 'anesthesia', 'prolene', 'excised',
        ])
        is_cardiac = any(kw in ctx_lower for kw in ['stemi', 'myocardial infarction', 'troponin'])
        is_pe = 'pulmonary embolism' in ctx_lower

        system_prompt = CODER_AGENT_PROMPT

        extra = ""
        if is_skin and not is_cardiac and not is_pe:
            extra = ("CRITICAL: SKIN/DERMATOLOGY encounter. "
                     "DO NOT score pulmonary (I26.x), cardiac (I21.x), or respiratory (J18.x) codes above 5 "
                     "unless explicitly documented. Primary MUST be skin code "
                     "(L91.0 keloid, D23.x benign neoplasm, C44.x malignant, L72.x cyst).\n")
        if is_operative:
            extra += ("OPERATIVE NOTE: Primary Dx = condition surgically treated, NOT pain. "
                      "M54.x scores 0 for skin lesion excision.\n")

        # Detect observation status encounter
        is_observation = any(kw in ctx_lower for kw in [
            'observation status', 'observation that same day', 'obs status',
            'observation care', 'admitted for observation',
        ])
        obs_rule = ""
        if is_observation:
            obs_rule = ("OBSERVATION STATUS RULE: This is an observation encounter. "
                        "Score 99234/99235/99236 (same-day obs admit+discharge) or "
                        "99218/99219/99220 (initial obs) highly if documented. "
                        "Low MDM comprehensive exam = 99234.\n")
            extra += obs_rule

        # Detect drug injection encounters for drug code accuracy
        is_kenalog = any(kw in ctx_lower for kw in ['kenalog', 'triamcinolone', 'intralesional'])
        is_depomedrol = any(kw in ctx_lower for kw in ['depo-medrol', 'methylprednisolone acetate'])
        lesion_count_over7 = any(kw in ctx_lower for kw in [
            'more than 7', 'more than 8', '8 lesion', '8+ lesion', 'multiple lesion',
            '>7 lesion', '>8 lesion', 'more than seven', 'more than eight',
        ])
        lesion_count_under7 = any(kw in ctx_lower for kw in [
            'one lesion', 'two lesion', 'three lesion', 'four lesion', 'five lesion',
            'six lesion', 'seven lesion', '1 lesion', '2 lesion', '3 lesion',
        ])
        drug_rule = ""
        if is_kenalog:
            drug_rule = (
                "DRUG RULE — TRIAMCINOLONE/KENALOG DETECTED:\n"
                "J3301 = Injection triamcinolone acetonide NOT elsewhere classified, 10mg — CORRECT for Kenalog.\n"
                "J1094 = Dexamethasone acetate — COMPLETELY WRONG DRUG, score 0-5 for Kenalog encounters.\n"
                "J1100 = Dexamethasone sodium phosphate — also WRONG for Kenalog, score 0-5.\n"
                "CPT 11900 = intralesional injection up to 7 lesions; 11901 = MORE than 7 lesions.\n"
                + ("Since note states 8+ lesions → 11901 scores higher than 11900.\n" if lesion_count_over7 else "")
                + "M79.89 as secondary Dx: score 0-10 — L91.0 alone is complete for keloid scar; "
                  "do NOT add vague soft tissue codes unless a SEPARATE condition is documented.\n"
            )
            extra += drug_rule
        if is_depomedrol:
            extra += ("DRUG RULE — METHYLPREDNISOLONE ACETATE DETECTED: "
                      "J1020=20mg, J1030=40mg, J1040=80mg. Score by documented dose.\n")

        # ── CPT RULE ENGINE: deterministic scores (overrides LLM on known rules) ──
        all_codes = [c.code for c in candidates]
        rule_scores = get_rule_engine_scores(clinical_context, all_codes)
        cpt_rules_section = build_cpt_prompt_section(clinical_context, all_codes)

        prompt = f"""You are a CPC with 20+ years of experience. Rate medical codes against the clinical note below.

UNIVERSAL MANDATORY RULES (override all other scoring):
1. W/X/Y/V codes (External Cause codes): score 0 as PRIMARY diagnosis role; OK as secondary/additional.
2. Principal Dx = the CONDITION treated (S-code for injuries, L-code for skin, etc.), NOT mechanism.
3. DRUG CODE ACCURACY: J-codes are drug-specific. J1094 = dexamethasone ONLY. Never use for triamcinolone.
   Kenalog/triamcinolone = J3301. Wrong drug J-code scores 0.
4. SECONDARY DX DISCIPLINE: Only add secondary codes for separately documented conditions.
   Do NOT pad with vague codes (M79.89, R69, Z87.39) when the primary code is already complete.
5. If note mentions observation status, score E/M observation codes (99234-99236) highly.
6. Score codes for conditions NOT documented in the note as 0-15 maximum.
{extra}
CLINICAL CONTEXT:
{clinical_context[:700]}

CODES TO EVALUATE:
{code_list}

SCORING: 85-100=exact documented match; 70-84=correct category; 50-69=partial; 30-49=marginal; 0-29=not documented or wrong role.
W/X/Y/V codes as primary: ALWAYS score 0. As additional/secondary: score by documentation.
CPT: 85-100 only if procedure explicitly performed; 0-29 if not in note.

{cpt_rules_section}
Return ONLY JSON array:
[{{"code": "E11.9", "score": 87, "is_billable": true, "reasoning": "..."}}]"""

        try:
            raw = self.llm.call_llm(system_prompt, prompt, max_tokens=2000)
            if raw:
                scored = self._parse_llm_scores(raw, candidates)
                if scored:
                    # ── MERGE: Rule engine scores override LLM on deterministic rules ──
                    # Rule engine has priority (70%) when it fires on a known rule.
                    # LLM score used fully when rule engine didn't trigger.
                    for c in scored:
                        if c.code in rule_scores:
                            rm = rule_scores[c.code]
                            if rm.rule_triggered not in ("keyword_match", "unknown"):
                                # Deterministic rule fired → weighted merge (rule wins)
                                llm_s = c.llm_score or 0
                                rule_s = rm.score
                                merged = round(0.30 * llm_s + 0.70 * rule_s)
                                c.reasoning = (f"[Rule: {rm.reason}] [LLM: {c.reasoning or ''}]")
                                c.llm_score = min(100, max(0, merged))
                            else:
                                # No deterministic rule → LLM score unchanged
                                pass
                    # ── ML Score Adjustment (v5 new) ──
                    # Apply ML-derived adjustments on top of LLM + rule engine
                    if ml_features:
                        for c in scored:
                            ml_adj, ml_reason = self.nlp.get_ml_score_adjustments(ml_features, c.code)
                            if ml_adj != 0.0:
                                old_score = c.llm_score
                                c.llm_score = max(0, min(100, int(c.llm_score + ml_adj)))
                                if abs(ml_adj) >= 10:
                                    c.reasoning = f"{c.reasoning} | {ml_reason}"
                            logger.debug("[ML] %s: %d -> %d (%s)", c.code, old_score, c.llm_score, ml_reason)
                    return scored
        except Exception as e:
            logger.error("LLM rerank error: %s", e)

        # Fallback: use similarity scores
        for c in candidates:
            c.llm_score = int(c.similarity_score * 100)
            c.reasoning = "Fallback: used semantic similarity score"
        return sorted(candidates, key=lambda c: c.llm_score, reverse=True)

    def _parse_llm_scores(
        self,
        raw: str,
        candidates: list[CodeCandidate],
    ) -> list[CodeCandidate]:
        """
        Parse LLM scoring response into CodeCandidate objects.
        Handles JSON arrays, markdown-wrapped JSON, and partial results.
        """
        cleaned = raw.strip()
        
        # Strip markdown code blocks
        if "```" in cleaned:
            for part in cleaned.split("```"):
                stripped = part.strip()
                if stripped.startswith("[") or stripped.startswith("{"):
                    cleaned = stripped
                    break

        # Try to find and parse JSON array
        array_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if array_match:
            try:
                data = json.loads(array_match.group())
                if isinstance(data, list):
                    return self._apply_scores(data, candidates)
            except (json.JSONDecodeError, ValueError):
                pass

        # Clean trailing commas and retry
        cleaned2 = re.sub(r',\s*([}\}\]])', r'\1', cleaned)
        try:
            data = json.loads(cleaned2)
            if isinstance(data, list):
                return self._apply_scores(data, candidates)
            if isinstance(data, dict) and "results" in data:
                return self._apply_scores(data["results"], candidates)
        except (json.JSONDecodeError, ValueError):
            pass

        # Extra data handling
        try:
            decoder = json.JSONDecoder()
            data, idx = decoder.raw_decode(cleaned)
            if isinstance(data, list):
                return self._apply_scores(data, candidates)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        # Fallback: use similarity scores
        logger.warning("JSON parse failed -- using similarity fallback")
        for c in candidates:
            c.llm_score = int(c.similarity_score * 100)
            c.reasoning = "Fallback: score from semantic similarity"
        return sorted(candidates, key=lambda c: c.llm_score, reverse=True)

    def _apply_scores(
        self,
        scored_list: list[dict],
        candidates: list[CodeCandidate],
    ) -> list[CodeCandidate]:
        """Apply LLM scores back to CodeCandidate objects."""
        score_map = {}
        for item in scored_list:
            code = item.get("code", "").strip()
            if code:
                score_map[code] = {
                    "score": max(0, min(100, int(item.get("score", 0)))),
                    "billable": bool(item.get("is_billable", False)),
                    "reasoning": str(item.get("reasoning", "")),
                }

        for c in candidates:
            if c.code in score_map:
                c.llm_score = score_map[c.code]["score"]
                c.is_billable = score_map[c.code]["billable"]
                c.reasoning = score_map[c.code]["reasoning"]
            else:
                # Code wasn't in LLM response -- low score
                c.llm_score = max(0, c.llm_score - 20)
                c.reasoning = "Not evaluated by LLM -- default low score"

        return sorted(candidates, key=lambda c: c.llm_score, reverse=True)



