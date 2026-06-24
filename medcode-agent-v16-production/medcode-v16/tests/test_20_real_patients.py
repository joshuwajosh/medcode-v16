"""
MedCode AI V19 — Full Pipeline Test with 20 Real Patient Cases
===============================================================
Real-world clinical scenarios with expected CPT and ICD-10 codes.
"""
import sys
import json
import time
sys.path.insert(0, '.')

from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15
pipeline = MedcodeDeterministicPipelineV15()

# ═══════════════════════════════════════════════════════════════════════════
# 20 REAL PATIENT CASES WITH EXPECTED CODES
# ═══════════════════════════════════════════════════════════════════════════

PATIENT_CASES = [
    {
        "id": 1,
        "name": "CABG x3 with Endarterectomy",
        "note": """68-year-old male with three-vessel coronary artery disease and diffusely diseased right coronary artery.
Under cardiopulmonary bypass via median sternotomy, surgeon performs LIMA-to-LAD anastomosis,
SVG to obtuse marginal artery, and SVG to RCA with open coronary endarterectomy of the RCA.
Saphenous vein harvested endoscopically from left thigh.""",
        "expected_cpt": ["33533", "33572"],
        "expected_icd": ["I25.10"],
        "category": "cardiovascular",
    },
    {
        "id": 2,
        "name": "Severe Sepsis with E. coli",
        "note": """72-year-old male admitted with severe sepsis and septic shock secondary to E. coli pneumonia.
Patient rapidly develops acute respiratory failure with hypoxia. On norepinephrine. Blood cultures positive for E. coli.""",
        "expected_cpt": [],
        "expected_icd": ["A41.52", "R65.21"],
        "category": "icd10",
    },
    {
        "id": 3,
        "name": "Laparoscopic Cholecystectomy",
        "note": """45-year-old female with symptomatic cholelithiasis. Laparoscopic cholecystectomy performed.
Critical view of safety achieved. No cholangiography. Three 5mm trocars used. Gallbladder removed in endocatch bag.""",
        "expected_cpt": ["47562"],
        "expected_icd": ["K80.20"],
        "category": "surgery",
    },
    {
        "id": 4,
        "name": "Total Knee Replacement",
        "note": """68-year-old female with severe osteoarthritis right knee. Total knee arthroplasty with cemented components.
Varus deformity corrected. Tourniquet 90 minutes. Patient ambulating POD1.""",
        "expected_cpt": ["27447"],
        "expected_icd": ["M17.11"],
        "category": "orthopedics",
    },
    {
        "id": 5,
        "name": "Diabetic Foot Ulcer with Cellulitis",
        "note": """75-year-old male admitted for severe right foot ulcer on great toe with bone necrosis.
History of insulin-dependent Type 2 diabetes, diabetic neuropathy, CKD stage 3b, hypertension.
Developed secondary cellulitis of right foot.""",
        "expected_cpt": [],
        "expected_icd": ["E11.621", "L03.011", "E11.65"],
        "category": "icd10",
    },
    {
        "id": 6,
        "name": "Emergency Department Asthma",
        "note": """28-year-old female presenting to ED with severe asthma exacerbation and acute respiratory distress.
SpO2 88% on room air. Administered continuous nebulized albuterol and IV methylprednisolone.
Multiple breathing treatments given.""",
        "expected_cpt": ["99284"],
        "expected_icd": ["J45.41"],
        "category": "emergency",
    },
    {
        "id": 7,
        "name": "Neonatal Critical Care NICU Day 6",
        "note": """15-day-old female neonate in NICU at 30 weeks gestational age, 1420 grams.
Born via emergency C-section for placental abruption. NICU Day 6.
RDS on CPAP, apnea of prematurity on caffeine, PDA medically managed.
Indirect hyperbilirubinemia resolving with phototherapy.
Feeding intolerance on TPN with trophic feeds.""",
        "expected_cpt": ["99469"],
        "expected_icd": ["P07.15", "P22.0", "P28.4", "Q25.0", "P59.9", "P92.9"],
        "category": "neonatal",
    },
    {
        "id": 8,
        "name": "Severe Depression with Suicidal Ideation",
        "note": """35-year-old female established patient with severe depression and suicidal ideation.
One acute illness with systemic symptoms. External mental-health records reviewed.
Metabolic panel ordered. Critical decision regarding hospitalization evaluated.
SSRI therapy initiated after discussion with on-call psychiatrist.""",
        "expected_cpt": ["99215"],
        "expected_icd": ["F32.2", "R45.851"],
        "category": "em",
    },
    {
        "id": 9,
        "name": "Atrial Fibrillation Follow-up",
        "note": """72-year-old female established patient at cardiology clinic.
Follow-up of stable atrial fibrillation. Total time 27 minutes including chart review 5 min,
face-to-face 15 min, prescription review 4 min, documentation 3 min.
Low level of MDM documented.""",
        "expected_cpt": ["99213"],
        "expected_icd": ["I48.91"],
        "category": "em",
    },
    {
        "id": 10,
        "name": "COVID-19 with E. coli Sepsis",
        "note": """55-year-old female admitted to ICU with confirmed COVID-19 infection.
Concurrent E. coli bloodstream infection causing severe sepsis and septic shock.
History of insulin-dependent Type 2 diabetes. Develops acute kidney failure from E. coli sepsis.""",
        "expected_cpt": [],
        "expected_icd": ["J12.82", "A41.52", "R65.21"],
        "category": "icd10",
    },
    {
        "id": 11,
        "name": "Hip Fracture with Osteoporosis",
        "note": """78-year-old female with left hip pain following minor trauma.
ED evaluation reveals femoral neck fracture due to age-related osteoporosis.
Right-handed patient.""",
        "expected_cpt": ["27230"],
        "expected_icd": ["S72.001A", "M80.061"],
        "category": "orthopedics",
    },
    {
        "id": 12,
        "name": "ERCP with Stent Exchange",
        "note": """65-year-old male with chronic pancreatitis presents for routine stent exchange.
ERCP performed, existing pancreatic duct stent removed with snare.
Balloon dilation of pancreatic duct. New pancreatic duct stent deployed.
Small sphincterotomy performed.""",
        "expected_cpt": ["43275"],
        "expected_icd": ["K86.1"],
        "category": "gi",
    },
    {
        "id": 13,
        "name": "Colonoscopy with Polypectomy",
        "note": """60-year-old male following positive FIT screening.
Flexible sigmoidoscopy performed. Three polyps found in sigmoid colon.
All three removed with snare technique.""",
        "expected_cpt": ["45385"],
        "expected_icd": ["Z12.11"],
        "category": "gi",
    },
    {
        "id": 14,
        "name": "CABG x3 with Radial Artery",
        "note": """71-year-old female with severe ischemic cardiomyopathy, EF 25%.
CABG x3: LIMA to LAD, radial artery to OM, SVG to RCA, SVG to PDA, SVG to diagonal.
Two arterial grafts, three venous grafts.""",
        "expected_cpt": ["33533", "33534", "33518"],
        "expected_icd": ["I25.10"],
        "category": "cardiovascular",
    },
    {
        "id": 15,
        "name": "Pneumonia with Sepsis",
        "note": """67-year-old male admitted with pneumonia. Sputum cultures confirm MRSA.
Severe sepsis secondary to MRSA infection from deep incisional wound infection.
Develops acute respiratory failure and acute kidney failure.""",
        "expected_cpt": [],
        "expected_icd": ["A41.0", "R65.21"],
        "category": "icd10",
    },
    {
        "id": 16,
        "name": "TAVR for Aortic Stenosis",
        "note": """81-year-old female with severe symptomatic aortic stenosis.
Prohibitive risk for transfemoral access due to severe peripheral arterial disease.
Transcatheter aortic valve replacement via transapical approach.""",
        "expected_cpt": ["33361"],
        "expected_icd": ["I35.0"],
        "category": "cardiovascular",
    },
    {
        "id": 17,
        "name": "Sepsis with MRSA from Surgical Wound",
        "note": """67-year-old male with history of lung cancer treated with lobectomy 4 years ago.
Admitted with acute systemic sepsis secondary to MRSA infection from recent revision surgery.
Develops acute respiratory failure with severe hypoxia and acute kidney failure.""",
        "expected_cpt": [],
        "expected_icd": ["A41.0", "J96.01"],
        "category": "icd10",
    },
    {
        "id": 18,
        "name": "Pre-eclampsia with HELLP",
        "note": """32-year-old female at 36 weeks gestation with severe pre-eclampsia and eclampsia.
Witnessed generalized seizure. HELLP syndrome with elevated liver enzymes and platelets 78,000.
History of Type 1 diabetes with CKD stage 3a.
Eclampsia stabilized with magnesium sulfate. Emergency C-section performed.""",
        "expected_cpt": [],
        "expected_icd": ["O14.14", "O15.0", "O14.24"],
        "category": "icd10",
    },
    {
        "id": 19,
        "name": "Inguinal Hernia Repair",
        "note": """55-year-old male with right inguinal hernia. Open tension-free mesh repair.
Direct hernia. No complications. Discharged same day.""",
        "expected_cpt": ["49560"],
        "expected_icd": ["K40.90"],
        "category": "surgery",
    },
    {
        "id": 20,
        "name": "Stroke with Hemiparesis",
        "note": """75-year-old right-handed female with acute ischemic stroke right MCA territory.
NIHSS 12. TPA administered within window. Residual right hemiparesis.
Chronic residuals documented.""",
        "expected_cpt": [],
        "expected_icd": ["I63.51", "I69.354"],
        "category": "icd10",
    },
]


def run_case(case):
    """Run a single case through the pipeline."""
    start = time.time()
    result = pipeline.run(
        note_text=case["note"],
        note_id="patient-{}".format(case["id"]),
    )
    elapsed = time.time() - start

    cpt_generated = [c.get("code", "") for c in result.cpt_codes]
    icd_generated = [c.get("code", "") for c in result.icd10_codes]

    # STRICT matching: ALL expected CPT codes must be present
    cpt_missing = [ec for ec in case["expected_cpt"] if ec not in cpt_generated] if case["expected_cpt"] else []
    cpt_match = len(cpt_missing) == 0

    # STRICT matching: ALL expected ICD codes must be present
    icd_missing = [ei for ei in case["expected_icd"] if ei not in icd_generated] if case["expected_icd"] else []
    icd_match = len(icd_missing) == 0

    overall_pass = cpt_match and icd_match

    return {
        "id": case["id"],
        "name": case["name"],
        "category": case["category"],
        "passed": overall_pass,
        "cpt_generated": cpt_generated[:5],
        "cpt_expected": case["expected_cpt"],
        "cpt_match": cpt_match,
        "cpt_missing": cpt_missing,
        "icd_generated": icd_generated[:5],
        "icd_expected": case["expected_icd"],
        "icd_match": icd_match,
        "icd_missing": icd_missing,
        "confidence": result.confidence,
        "processing_ms": result.processing_time_ms,
        "elapsed_s": round(elapsed, 2),
    }


def main():
    print("=" * 90)
    print("  MedCode AI V19 — Full Pipeline Test: 20 Real Patient Cases")
    print("=" * 90)
    print()

    results = []
    total_pass = 0
    total_fail = 0
    total_cpt_match = 0
    total_icd_match = 0
    total_confidence = 0
    total_time = 0

    for i, case in enumerate(PATIENT_CASES, 1):
        result = run_case(case)
        results.append(result)

        if result["passed"]:
            total_pass += 1
        else:
            total_fail += 1

        if result["cpt_match"]:
            total_cpt_match += 1
        if result["icd_match"]:
            total_icd_match += 1

        total_confidence += result["confidence"]
        total_time += result["elapsed_s"]

        # Print result
        status = "PASS" if result["passed"] else "FAIL"
        cpt = ",".join(result["cpt_generated"][:3]) if result["cpt_generated"] else "-"
        icd = ",".join(result["icd_generated"][:3]) if result["icd_generated"] else "-"
        exp_cpt = ",".join(result["cpt_expected"]) if result["cpt_expected"] else "-"
        exp_icd = ",".join(result["icd_expected"]) if result["icd_expected"] else "-"

        print("  {:4s} [{:2d}/20] {:30s} | CPT:{:12s} -> {:12s} | ICD:{:12s} -> {:12s} | conf:{:.2f} | {:.1f}s".format(
            status, i, result["name"][:30],
            exp_cpt[:12], cpt[:12],
            exp_icd[:12], icd[:12],
            result["confidence"],
            result["elapsed_s"]))

        if not result["passed"]:
            if result["cpt_missing"]:
                print("         CPT MISSING: {}".format(", ".join(result["cpt_missing"])))
            if result["icd_missing"]:
                print("         ICD MISSING: {}".format(", ".join(result["icd_missing"])))
            print("         Generated CPT: {}".format(",".join(result["cpt_generated"][:5]) or "(none)"))
            print("         Generated ICD: {}".format(",".join(result["icd_generated"][:8]) or "(none)"))

    # Summary
    print()
    print("=" * 90)
    print("  ACCURACY SUMMARY")
    print("=" * 90)
    print()
    print("  Overall Accuracy:     {}/{} ({:.1f}%)".format(total_pass, total_pass + total_fail, total_pass/(total_pass + total_fail)*100))
    print("  CPT Accuracy:         {}/{} ({:.1f}%)".format(total_cpt_match, total_pass + total_fail, total_cpt_match/(total_pass + total_fail)*100))
    print("  ICD-10 Accuracy:      {}/{} ({:.1f}%)".format(total_icd_match, total_pass + total_fail, total_icd_match/(total_pass + total_fail)*100))
    print("  Average Confidence:   {:.2f}".format(total_confidence / len(PATIENT_CASES)))
    print("  Total Processing Time: {:.1f}s".format(total_time))
    print("  Average per Case:     {:.1f}s".format(total_time / len(PATIENT_CASES)))
    print()

    # Category breakdown
    print("  BY CATEGORY:")
    print("  " + "-" * 60)
    for cat in ["cardiovascular", "surgery", "icd10", "em", "orthopedics", "gi", "neonatal", "emergency"]:
        cat_results = [r for r in results if r["category"] == cat]
        if cat_results:
            passed = sum(1 for r in cat_results if r["passed"])
            total = len(cat_results)
            rate = passed / total * 100
            bar = "#" * int(rate / 5) + "." * (20 - int(rate / 5))
            print("  {:15s} | {}/{} | {} | {:.0f}%".format(cat, passed, total, bar, rate))

    print()
    print("=" * 90)

    # Save detailed results
    with open("test_results_20_real.json", "w") as f:
        json.dump({
            "summary": {
                "total_cases": len(PATIENT_CASES),
                "passed": total_pass,
                "failed": total_fail,
                "overall_accuracy": round(total_pass / (total_pass + total_fail) * 100, 1),
                "cpt_accuracy": round(total_cpt_match / (total_pass + total_fail) * 100, 1),
                "icd_accuracy": round(total_icd_match / (total_pass + total_fail) * 100, 1),
                "avg_confidence": round(total_confidence / len(PATIENT_CASES), 2),
                "total_time_s": round(total_time, 1),
                "avg_time_per_case_s": round(total_time / len(PATIENT_CASES), 1),
            },
            "results": results,
        }, f, indent=2)

    print("  Detailed results saved to test_results_20_real.json")
    print("=" * 90)


if __name__ == "__main__":
    main()
