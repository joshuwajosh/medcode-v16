"""
Test Training Cases — Verify V19 Training Knowledge Base
"""
import sys
sys.path.insert(0, '.')

from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15
pipeline = MedcodeDeterministicPipelineV15()

test_cases = [
    {
        "name": "Case 1: Principal Care Management",
        "note": "Principal Care Management services for advanced Parkinson's disease. 75 minutes of qualifying time including ongoing monitoring, medication adjustment, and care coordination with neurology team and home health services.",
        "expected_cpt": ["99491"],
        "expected_icd": ["G20"],
    },
    {
        "name": "Case 2: Neonatal Critical Care",
        "note": "45-day-old infant admitted to PICU with severe neonatal bacterial sepsis and secondary respiratory failure. Active resuscitation CPR, emergency intubation, umbilical venous catheter. Stabilized and admitted to PICU.",
        "expected_cpt": ["99291"],
        "expected_icd": ["A41.52", "P28.10"],
    },
    {
        "name": "Case 3: Outpatient Cardiology Follow-up",
        "note": "72-year-old female established patient at cardiology clinic. Routine annual follow-up. Cardiologist performs focused evaluation, reviews lab workup and imaging. Cardiac medication regimen stable. Moderate MDM.",
        "expected_cpt": ["99214"],
        "expected_icd": ["I48.91"],
    },
    {
        "name": "Case 4: Office Endocrinology Consultation",
        "note": "50-year-old male established type 2 diabetes referred to endocrinologist for office consultation regarding glycemic control. Comprehensive history, comprehensive physical examination. Adjusts insulin regimen. Written report to referring physician.",
        "expected_cpt": ["99243"],
        "expected_icd": ["E11.65"],
    },
    {
        "name": "Case 5: Home Visit for Mobility Limitations",
        "note": "65-year-old new patient. Primary care physician performs home visit due to severe mobility limitations following recent hip fracture. Detailed evaluation, care plan with home health referral and new prescriptions.",
        "expected_cpt": ["99350"],
        "expected_icd": ["M97.11"],
    },
    {
        "name": "Case 6: Independent Medical Evaluation",
        "note": "Adult sent to primary care clinic by employer's workers' compensation carrier for independent medical evaluation following workplace injury. Evaluating physician has never treated this patient before. Comprehensive evaluation.",
        "expected_cpt": ["99455"],
        "expected_icd": ["M54.5"],
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
    icd_match = all(ei in icd_codes for ei in case["expected_icd"]) if case["expected_icd"] else True
    
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
