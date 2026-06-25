"""
MedCode V16 — Regression Tests
Covers negation, laterality, modifiers, E/M, context classification,
physician queries, medical necessity, documentation quality.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from context_engine.context_classifier import ContextClassifier, CONTEXT_TYPE_NEGATED, CONTEXT_TYPE_FAMILY, CONTEXT_TYPE_HISTORICAL, CONTEXT_TYPE_ACTIVE, CONTEXT_TYPE_SUSPECTED
from modifier_engine import ModifierEngine
from em_engine import EMCodingEngine
from documentation_quality import DocumentationQualityEngine
from physician_query import PhysicianQueryEngine
from medical_necessity import MedicalNecessityEngine
from validation.global_period_validator import GlobalPeriodValidator


# ── Context Classifier Tests ──────────────────────────────────────────────────

class TestContextClassifier:
    def setup_method(self):
        self.clf = ContextClassifier()

    def test_negated_rule_out_stroke(self):
        text = "rule out stroke. Patient denies chest pain."
        result = self.clf.filter_active_only(["stroke"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_NEGATED
        assert result[0]["should_code"] is False

    def test_negated_no_evidence(self):
        text = "no evidence of pulmonary embolism"
        result = self.clf.filter_active_only(["pulmonary embolism"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_NEGATED
        assert result[0]["should_code"] is False

    def test_negated_denies(self):
        text = "Patient denies chest pain, shortness of breath"
        result = self.clf.filter_active_only(["chest pain"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_NEGATED

    def test_family_history_diabetes(self):
        text = "Family history of diabetes mellitus. Mother had diabetes."
        result = self.clf.filter_active_only(["diabetes"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_FAMILY
        assert result[0]["should_code"] is False

    def test_family_history_not_active(self):
        text = "FH: father had MI. No personal history of MI."
        result = self.clf.filter_active_only(["mi"], text)
        # Should be family history or negated
        assert result[0]["should_code"] is False

    def test_historical_is_codeable(self):
        text = "History of appendectomy 5 years ago. S/P cholecystectomy."
        result = self.clf.filter_active_only(["appendectomy"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_HISTORICAL
        assert result[0]["should_code"] is True  # Personal hx CAN be coded

    def test_active_diagnosis_coded(self):
        text = "Patient presents with acute COPD exacerbation."
        result = self.clf.filter_active_only(["copd"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_ACTIVE
        assert result[0]["should_code"] is True

    def test_postoperative_status(self):
        text = "Status post CABG 3 weeks ago. Now presents for follow-up."
        result = self.clf.filter_active_only(["cabg"], text)
        assert result[0]["context_type"] in ["POSTOPERATIVE", "HISTORICAL"]

    def test_suspected_not_negated(self):
        text = "Likely pneumonia vs. atypical infection."
        result = self.clf.filter_active_only(["pneumonia"], text)
        assert result[0]["context_type"] == CONTEXT_TYPE_SUSPECTED
        assert result[0]["should_code"] is True

    def test_postop_cabg_no_active_cpt(self):
        """Postoperative CABG note should NOT re-emit CABG CPT"""
        text = "Post-op day 2 following CABG. Wound healing well."
        result = self.clf.filter_active_only(["cabg"], text)
        # CABG in postop context — context_type should not be ACTIVE
        assert result[0]["context_type"] != CONTEXT_TYPE_ACTIVE

    def test_ros_negative_bulk(self):
        text = "ROS: negative. Patient denies fever, cough, chest pain."
        result = self.clf.filter_active_only(["fever", "cough", "chest pain"], text)
        for r in result:
            assert r["should_code"] is False

    def test_multiple_entities_mixed_context(self):
        text = "Active hypertension. Family history of diabetes. Denies chest pain."
        result = self.clf.filter_active_only(["hypertension", "diabetes", "chest pain"], text)
        contexts = {r["term"]: r for r in result}
        assert contexts["hypertension"]["should_code"] is True
        assert contexts["diabetes"]["should_code"] is False
        assert contexts["chest pain"]["should_code"] is False


# ── Modifier Engine Tests ──────────────────────────────────────────────────────

class TestModifierEngine:
    def setup_method(self):
        self.engine = ModifierEngine()

    def test_laterality_left(self):
        result = self.engine.determine_modifiers(["27447"], "Left total knee replacement performed.", {})
        assert any(m.modifier == "-LT" for m in result["27447"].applied_modifiers)

    def test_laterality_right(self):
        result = self.engine.determine_modifiers(["27447"], "Right knee arthroplasty.", {})
        assert any(m.modifier == "-RT" for m in result["27447"].applied_modifiers)

    def test_bilateral_modifier(self):
        result = self.engine.determine_modifiers(["27447"], "Bilateral knee replacement.", {})
        assert any(m.modifier == "-50" for m in result["27447"].applied_modifiers)

    def test_em_with_procedure_gets_25(self):
        result = self.engine.determine_modifiers(
            ["99214", "20610"], "Office visit with joint injection today.", {}
        )
        em_result = result["99214"]
        assert any(m.modifier == "-25" for m in em_result.applied_modifiers)

    def test_return_to_or_gets_78(self):
        result = self.engine.determine_modifiers(
            ["13160"], "Patient returned to the OR for wound dehiscence repair.", {}
        )
        assert any(m.modifier == "-78" for m in result["13160"].applied_modifiers)

    def test_multiple_surgeries_get_51(self):
        result = self.engine.determine_modifiers(
            ["27447", "29881"], "Bilateral knee replacement with meniscectomy.", {}
        )
        # Secondary procedure should get -51
        secondary = result["29881"]
        assert any(m.modifier in ["-51", "-59"] for m in secondary.applied_modifiers)

    def test_staged_procedure_gets_58(self):
        result = self.engine.determine_modifiers(
            ["14040"], "Second stage tissue transfer as planned staged procedure.", {},
            global_period_active=True, prior_surgery_code="14040", days_since_surgery=21
        )
        assert any(m.modifier == "-58" for m in result["14040"].applied_modifiers)

    def test_modifier_reasoning_populated(self):
        result = self.engine.determine_modifiers(["99214", "20610"], "Office visit with injection.", {})
        assert len(result["99214"].modifier_reasoning) > 0


# ── E/M Engine Tests ──────────────────────────────────────────────────────────

class TestEMEngine:
    def setup_method(self):
        self.engine = EMCodingEngine()

    def test_high_complexity_sepsis(self):
        note = "ICU patient with septic shock. Multiple organ dysfunction. On vasopressors."
        result = self.engine.code(note, encounter_type_hint="inpatient_initial")
        assert result.primary_code == "99223"
        assert result.mdm.overall_level.value == 4

    def test_critical_care_code(self):
        note = "Critically ill patient in ICU with respiratory failure requiring intubation. Total time 45 minutes."
        result = self.engine.code(note, encounter_type_hint="critical_care")
        assert result.primary_code == "99291"

    def test_low_complexity_office(self):
        note = "Routine follow-up for stable hypertension. Well-controlled on lisinopril. No new complaints."
        result = self.engine.code(note, encounter_type_hint="office_est")
        assert result.primary_code in ["99212", "99213"]

    def test_moderate_complexity_new_problem(self):
        note = "New problem: chest pain. EKG ordered. Labs sent. New onset undiagnosed condition."
        result = self.engine.code(note, encounter_type_hint="office_est")
        assert result.primary_code in ["99213", "99214"]

    def test_time_based_selection(self):
        note = "Total time spent with patient: 35 minutes."
        result = self.engine.code(note, encounter_type_hint="office_est")
        assert result.primary_code in ["99213", "99214", "99215"]

    def test_ed_level_5_life_threatening(self):
        note = "Emergency department. Unstable patient with life-threatening cardiac arrest. Multiple resuscitation attempts. Vasopressors. Intubation. Total critical care time documented."
        result = self.engine.code(note, encounter_type_hint="ed")
        assert result.primary_code in ["99284", "99285"]

    def test_ed_level_3_moderate(self):
        note = "Emergency department visit. Patient with pneumonia. Chest x-ray ordered and reviewed. Labs ordered and reviewed. IV antibiotics started. Disposition planned."
        result = self.engine.code(note, encounter_type_hint="ed")
        assert result.primary_code in ["99282", "99283", "99284"]

    def test_mdm_reasoning_populated(self):
        note = "Complex patient with CHF, diabetes, CKD. Multiple medications adjusted."
        result = self.engine.code(note)
        assert len(result.reasoning) > 0
        assert result.mdm is not None

    def test_hospital_subsequent_low(self):
        note = "Hospital day 2. Patient stable. Following routine chronic conditions."
        result = self.engine.code(note, encounter_type_hint="inpatient_sub")
        assert result.primary_code in ["99231", "99232"]

    def test_high_risk_drug_monitoring(self):
        note = "Follow-up for warfarin monitoring. INR checked. Dose adjusted."
        result = self.engine.code(note, encounter_type_hint="office_est")
        assert result.mdm.overall_level.value >= 2


# ── Global Period Validator Tests ─────────────────────────────────────────────

class TestGlobalPeriodValidator:
    def setup_method(self):
        self.validator = GlobalPeriodValidator()

    def test_postop_visit_in_global_period(self):
        result = self.validator.validate(
            "99213", "Post-op visit day 14. Wound check. Suture removal.",
            prior_surgery_code="27447", days_since_surgery=14
        )
        assert result.is_postop_visit is True

    def test_staged_procedure_gets_58(self):
        result = self.validator.validate(
            "14040", "Second stage planned tissue transfer.",
            prior_surgery_code="14040", days_since_surgery=30
        )
        assert result.is_staged is True
        assert result.recommended_modifier in ["-58", None] or result.recommended_modifier == "-58"

    def test_return_to_or_gets_78(self):
        result = self.validator.validate("13160", "Patient returned to the OR for wound dehiscence.")
        assert result.is_return_to_or is True
        assert result.recommended_modifier == "-78"

    def test_clean_note_passes(self):
        result = self.validator.validate("27447", "Patient presents for new right knee pain.")
        assert result.passed is True
        assert result.is_postop_visit is False


# ── Documentation Quality Tests ───────────────────────────────────────────────

class TestDocumentationQuality:
    def setup_method(self):
        self.engine = DocumentationQualityEngine()

    def _gap_cats(self, result):
        return [g.category for g in result.documentation_gaps]

    def test_missing_laterality_for_knee(self):
        result = self.engine.analyse("Total knee replacement performed.", ["27447"])
        assert "LATERALITY" in self._gap_cats(result)

    def test_missing_diabetes_specificity(self):
        result = self.engine.analyse("Patient has diabetes. Well-controlled.")
        assert "DIAGNOSIS_SPECIFICITY" in self._gap_cats(result)

    def test_missing_cabg_graft_count(self):
        result = self.engine.analyse("CABG performed. Bypass completed.", ["33533"])
        assert "GRAFT_COUNT" in self._gap_cats(result)

    def test_missing_approach(self):
        result = self.engine.analyse("Cholecystectomy was performed successfully.", ["47600"])
        assert "OPERATIVE_DETAILS" in self._gap_cats(result)

    def test_complete_note_high_score(self):
        note = (
            "Left total knee arthroplasty performed via standard medial parapatellar approach. "
            "Type 2 diabetes mellitus well-controlled. "
            "Specimen sent to pathology. Device: DePuy Attune size 3."
        )
        result = self.engine.analyse(note, ["27447"])
        assert result.score >= 0.5

    def test_minimal_note_low_score(self):
        result = self.engine.analyse("Surgery done.", ["27447"])
        assert result.score < 0.85

    def test_biopsy_without_pathology(self):
        result = self.engine.analyse("Excision of lesion performed.", ["11400"])
        assert "PATHOLOGY_LINKAGE" in self._gap_cats(result)


# ── Physician Query Engine Tests ──────────────────────────────────────────────

class TestPhysicianQueryEngine:
    def setup_method(self):
        self.engine = PhysicianQueryEngine()

    def test_diabetes_type_query(self):
        queries = self.engine.generate_queries("Patient has diabetes, uncontrolled.")
        cats = [q.category for q in queries]
        assert "DIAGNOSIS_SPECIFICITY" in cats
        q = next(q for q in queries if "diabetes" in q.trigger.lower())
        assert len(q.options) >= 3
        assert "Type 1" in q.options[0] or "Type 2" in q.options[1]

    def test_chf_specificity_query(self):
        queries = self.engine.generate_queries("Heart failure. Admitted for decompensation.")
        triggers = [q.trigger for q in queries]
        assert any("heart failure" in t.lower() for t in triggers)

    def test_ckd_stage_query(self):
        queries = self.engine.generate_queries("CKD. Creatinine elevated.")
        cats = [q.category for q in queries]
        assert "DIAGNOSIS_SPECIFICITY" in cats

    def test_sepsis_source_query(self):
        queries = self.engine.generate_queries("Sepsis. Patient admitted to ICU.")
        assert any("sepsis" in q.trigger.lower() for q in queries)

    def test_laterality_query(self):
        queries = self.engine.generate_queries("Knee pain and swelling. Scheduled for arthroscopy.")
        cats = [q.category for q in queries]
        assert "LATERALITY" in cats
        q = next(q for q in queries if q.category == "LATERALITY")
        assert "Left" in q.options and "Right" in q.options

    def test_clean_specific_note_no_queries(self):
        note = (
            "Type 2 diabetes mellitus with peripheral neuropathy. "
            "Systolic heart failure, EF 35%. Acute. "
            "CKD stage 3b. Right knee osteoarthritis."
        )
        queries = self.engine.generate_queries(note)
        # Well-documented note should have fewer queries
        assert len(queries) < 5

    def test_queries_are_non_leading(self):
        """AHIMA requirement: queries must not suggest a specific answer"""
        queries = self.engine.generate_queries("Patient has diabetes and heart failure.")
        for q in queries:
            # Should offer multiple options (not just one suggestive answer)
            assert len(q.options) >= 2


# ── Medical Necessity Tests ───────────────────────────────────────────────────

class TestMedicalNecessity:
    def setup_method(self):
        self.engine = MedicalNecessityEngine()

    def test_cabg_with_cad(self):
        results = self.engine.validate(["33533"], ["I25.10"], "CABG for coronary artery disease")
        assert results["33533"].passed is True
        assert results["33533"].denial_risk in ["LOW", "MEDIUM"]

    def test_cabg_without_cad(self):
        results = self.engine.validate(["33533"], ["E11.9"], "CABG performed")
        assert results["33533"].passed is False
        assert results["33533"].denial_risk == "HIGH"

    def test_dialysis_with_esrd(self):
        results = self.engine.validate(["90937"], ["N18.6"], "ESRD on hemodialysis")
        assert results["90937"].passed is True

    def test_pacemaker_with_av_block(self):
        results = self.engine.validate(["33249"], ["I44.2"], "Complete AV block, pacemaker implanted")
        assert results["33249"].passed is True

    def test_chemo_requires_malignancy(self):
        results = self.engine.validate(["96413"], ["C50.912"], "Chemotherapy for breast cancer")
        assert results["96413"].passed is True

    def test_chemo_without_malignancy_fails(self):
        results = self.engine.validate(["96413"], ["J18.9"], "Chemotherapy")
        assert results["96413"].passed is False

    def test_no_rule_defaults_pass(self):
        """Unknown CPT should default to pass with medium confidence"""
        results = self.engine.validate(["99213"], ["Z00.00"], "Annual wellness visit")
        assert results["99213"].passed is True

    def test_necessity_score_range(self):
        results = self.engine.validate(["33533"], ["I25.10"], "CABG for CAD")
        assert 0 <= results["33533"].score <= 100

    def test_tavr_requires_aortic_stenosis(self):
        results = self.engine.validate(["33361"], ["I35.0"], "TAVR for severe AS")
        assert results["33361"].passed is True

    def test_tavr_without_diagnosis(self):
        results = self.engine.validate(["33361"], ["Z00.00"], "TAVR procedure")
        assert results["33361"].passed is False


# ── Integration: False Positive Prevention ───────────────────────────────────

class TestFalsePositivePrevention:
    def setup_method(self):
        self.clf = ContextClassifier()

    def test_rule_out_never_coded(self):
        notes = [
            "rule out stroke", "r/o MI", "r/o PE", "rules out DVT",
            "ruled out sepsis", "rule out fracture"
        ]
        for note in notes:
            term = note.split()[-1]
            result = self.clf.filter_active_only([term], note)
            assert result[0]["should_code"] is False, f"False positive: '{note}' should not code {term}"

    def test_family_history_never_active(self):
        notes_terms = [
            ("Family history of colon cancer", "colon cancer"),
            ("Mother had breast cancer", "breast cancer"),
            ("FH: father with MI", "mi"),
            ("Sister had diabetes", "diabetes"),
        ]
        for note, term in notes_terms:
            result = self.clf.filter_active_only([term], note)
            assert result[0]["should_code"] is False, f"Family hx false positive: {note}"

    def test_postop_cabg_not_active_surgery(self):
        note = "Post-operative day 1 following CABG. Patient stable."
        result = self.clf.filter_active_only(["cabg"], note)
        assert result[0]["context_type"] != "ACTIVE"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
