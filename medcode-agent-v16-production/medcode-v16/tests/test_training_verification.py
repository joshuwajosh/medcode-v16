"""
Test Training Cases — Verify V19 Training Knowledge Base
"""
import sys
sys.path.insert(0, '.')

from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15
pipeline = MedcodeDeterministicPipelineV15()

test_cases = [
    {
        "name": "Case 3: PICU Infant RSV",
        "note": "4-month-old infant admitted to PICU with severe RSV bronchiolitis requiring mechanical ventilation. Pediatric intensivist provides initial-day comprehensive critical care management.",
        "expected_cpt": ["99291"],
        "expected_icd": ["J21.0"],
    },
    {
        "name": "Case 4: Severe Depression",
        "note": "35-year-old female established patient at family medicine clinic. Severe depression and suicidal ideation. One acute illness with systemic symptoms. External mental-health records reviewed. Metabolic panel ordered. Critical decision regarding hospitalization evaluated. SSRI therapy initiated.",
        "expected_cpt": ["99215"],
        "expected_icd": ["F32.2"],
    },
    {
        "name": "Case 5: AF Follow-up",
        "note": "72-year-old female established patient at cardiology clinic. Follow-up of stable atrial fibrillation. Total time spent on date of encounter is 27 minutes including chart review 5 min, face-to-face 15 min, prescription review 4 min, documentation 3 min. Low level of MDM documented.",
        "expected_cpt": ["99213"],
        "expected_icd": ["I48.91"],
    },
    {
        "name": "Case 83: Sepsis E.coli",
        "note": "72-year-old male admitted with severe sepsis and septic shock secondary to E. coli pneumonia. Patient rapidly develops acute respiratory failure with hypoxia.",
        "expected_cpt": [],
        "expected_icd": ["A41.52", "R65.2"],
    },
    {
        "name": "Case 87: Hip Fracture",
        "note": "78-year-old female with left hip pain following minor trauma. Emergency department evaluation reveals hip fracture due to age-related osteoporosis.",
        "expected_cpt": ["27230"],
        "expected_icd": ["S72.001A", "M80.061"],
    },
    {
        "name": "Case 1: Continuous Visit",
        "note": "Hospital inpatient. A continuous patient visit and evaluation spans the transition of two calendar dates. The visit started at 11:30 PM and continued past midnight.",
        "expected_cpt": ["99221"],
        "expected_icd": ["R69"],
    },
    {
        "name": "Case 84: Hypertensive Heart CKD",
        "note": "65-year-old female admitted with hypertensive heart and chronic kidney disease. Manifestations include acute on chronic systolic heart failure alongside end-stage renal disease requiring dialysis.",
        "expected_cpt": [],
        "expected_icd": ["I11.0", "N18.6"],
    },
    {
        "name": "Case 59: Asthma ED",
        "note": "28-year-old female presenting to emergency department with severe asthma and acute respiratory distress. Provider administers continuous positive airway pressure and breathing treatments.",
        "expected_cpt": ["99284"],
        "expected_icd": ["J45.41"],
    },
]

print("=" * 80)
print("  MedCode AI V19 — Training Case Verification")
print("=" * 80)

passed = 0
failed = 0

for i, case in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"  TEST {i}: {case['name']}")
    print(f"{'='*80}")
    
    result = pipeline.run(note_text=case["note"], note_id=f"test-{i}")
    
    cpt_codes = [c.get("code", "") for c in result.cpt_codes]
    icd_codes = [c.get("code", "") for c in result.icd10_codes]
    
    # Check CPT
    cpt_match = any(ec in cpt_codes for ec in case["expected_cpt"]) if case["expected_cpt"] else True
    
    # Check ICD
    icd_match = any(ei in icd_codes for ei in case["expected_icd"]) if case["expected_icd"] else True
    
    status = "PASS" if (cpt_match and icd_match) else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
    
    print(f"  Status: {status}")
    print(f"  CPT Generated:    {', '.join(cpt_codes[:5]) if cpt_codes else '(none)'}")
    print(f"  CPT Expected:     {', '.join(case['expected_cpt']) if case['expected_cpt'] else '(none)'}")
    print(f"  ICD Generated:    {', '.join(icd_codes[:5]) if icd_codes else '(none)'}")
    print(f"  ICD Expected:     {', '.join(case['expected_icd']) if case['expected_icd'] else '(none)'}")

print(f"\n{'='*80}")
print(f"  RESULTS: {passed}/{passed+failed} passed ({passed/(passed+failed)*100:.0f}%)")
print(f"{'='*80}")
