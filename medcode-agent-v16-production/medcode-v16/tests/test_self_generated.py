"""
MedCode AI V19 — Comprehensive Self-Generated Test Suite
=========================================================
Tests generated from medical coding knowledge to verify:
1. All folders are interconnected correctly
2. Pipeline is working properly
3. All modules are wired together
"""
import sys
sys.path.insert(0, '.')

from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15
pipeline = MedcodeDeterministicPipelineV15()

# ═══════════════════════════════════════════════════════════════════════════
# SELF-GENERATED TEST CASES — 50 cases across all specialties
# ═══════════════════════════════════════════════════════════════════════════

test_cases = [
    # ═══ E/M (10 cases) ═══════════════════════════════════════════════
    {"name": "E/M: Established office visit low MDM",
     "note": "45-year-old established patient presents for routine follow-up of hypertension. BP 138/82. Medication continued. Low complexity MDM. Total time 15 minutes.",
     "expect_cpt": ["99213"], "expect_icd": ["I10"]},

    {"name": "E/M: Established office visit moderate MDM",
     "note": "55-year-old established diabetic patient with worsening HbA1c 9.2%. New medication started. Moderate MDM with data review and prescription management.",
     "expect_cpt": ["99214"], "expect_icd": ["E11.65"]},

    {"name": "E/M: New patient comprehensive exam",
     "note": "New 30-year-old patient presents with comprehensive history and examination for multiple complaints. Moderate MDM. Detailed assessment and plan.",
     "expect_cpt": ["99204"], "expect_icd": []},

    {"name": "E/M: Hospital initial care high MDM",
     "note": "65-year-old admitted with acute MI. Critical condition requiring intensive workup. High complexity MDM. Multiple comorbidities.",
     "expect_cpt": ["99223"], "expect_icd": ["I21.0"]},

    {"name": "E/M: Hospital subsequent low MDM",
     "note": "Hospital day 3, patient stable. Review of labs, medication reconciliation. Low MDM. Routine post-op care.",
     "expect_cpt": ["99231"], "expect_icd": []},

    {"name": "E/M: ED visit high complexity",
     "note": "Emergency department visit for chest pain. ECG, troponin, IV access, medications given. High complexity ED visit.",
     "expect_cpt": ["99285"], "expect_icd": ["R07.9"]},

    {"name": "E/M: Observation admit/discharge moderate",
     "note": "Patient admitted to observation for chest pain workup. Troponin negative. Discharged same day. Moderate MDM.",
     "expect_cpt": ["99235"], "expect_icd": ["R07.9"]},

    {"name": "E/M: Critical care first hour",
     "note": "ICU patient with septic shock. Norepinephrine, intubation, central line. 45 minutes critical care time documented.",
     "expect_cpt": ["99291"], "expect_icd": ["R65.21"]},

    {"name": "E/M: Consultation moderate",
     "note": "Cardiology consultation requested for new atrial fibrillation. Comprehensive history, focused exam. Moderate MDM. Written report.",
     "expect_cpt": ["99253"], "expect_icd": ["I48.91"]},

    {"name": "E/M: Telehealth visit",
     "note": "50-year-old established patient via video telehealth for medication management of hypertension. Low MDM. 15 minutes total time.",
     "expect_cpt": ["99212"], "expect_icd": ["I10"]},

    # ═══ SURGERY (10 cases) ═══════════════════════════════════════════
    {"name": "Surgery: Laparoscopic cholecystectomy",
     "note": "45-year-old female with symptomatic cholelithiasis. Laparoscopic cholecystectomy performed with critical view of safety. No complications.",
     "expect_cpt": ["47562"], "expect_icd": ["K80.20"]},

    {"name": "Surgery: Inguinal hernia repair mesh",
     "note": "55-year-old male with right inguinal hernia. Open tension-free mesh repair performed. Direct hernia. No complications.",
     "expect_cpt": ["49560"], "expect_icd": ["K40.90"]},

    {"name": "Surgery: Total knee replacement",
     "note": "68-year-old female with severe osteoarthritis right knee. Total knee arthroplasty with cemented components. Tourniquet 90 minutes.",
     "expect_cpt": ["27447"], "expect_icd": ["M17.11"]},

    {"name": "Surgery: Carpal tunnel release",
     "note": "42-year-old female with carpal tunnel syndrome. Endoscopic carpal tunnel release. Median nerve decompressed.",
     "expect_cpt": ["64721"], "expect_icd": ["G56.00"]},

    {"name": "Surgery: Colonoscopy with polypectomy",
     "note": "60-year-old male for screening colonoscopy. 8mm sessile polyp found in sigmoid colon. Snare polypectomy performed.",
     "expect_cpt": ["45385"], "expect_icd": ["Z12.11"]},

    {"name": "Surgery: Appendectomy laparoscopic",
     "note": "22-year-old male with acute appendicitis. Laparoscopic appendectomy. Appendix inflamed, no perforation.",
     "expect_cpt": ["44970"], "expect_icd": ["K35.80"]},

    {"name": "Surgery: Rotator cuff repair arthroscopic",
     "note": "55-year-old male with supraspinatus tear. Arthroscopic rotator cuff repair. Double row technique.",
     "expect_cpt": ["29827"], "expect_icd": ["M75.11"]},

    {"name": "Surgery: Tonsillectomy",
     "note": "7-year-old with recurrent tonsillitis. Tonsillectomy performed. Bipolar dissection. No bleeding.",
     "expect_cpt": ["42820"], "expect_icd": ["J35.01"]},

    {"name": "Surgery: Cataract phacoemulsification",
     "note": "70-year-old with cataract right eye. Phacoemulsification with IOL insertion. 21D lens. No complications.",
     "expect_cpt": ["66984"], "expect_icd": ["H25.11"]},

    {"name": "Surgery: EGD with biopsy",
     "note": "55-year-old with dyspepsia. EGD performed. Erythematous esophagitis. Biopsies taken from distal esophagus.",
     "expect_cpt": ["43239"], "expect_icd": ["K21.0"]},

    # ═══ CARDIOVASCULAR (5 cases) ═══════════════════════════════════════
    {"name": "Cardio: CABG x3",
     "note": "65-year-old male with three-vessel CAD. CABG x3: LIMA to LAD, SVG to RCA, SVG to OM1. On pump, cross clamp 85 min.",
     "expect_cpt": ["33533"], "expect_icd": ["I25.10"]},

    {"name": "Cardio: Cardiac catheterization diagnostic",
     "note": "50-year-old male with chest pain. Diagnostic cardiac catheterization. LAD 40%, RCA 30%. EF 55%. No intervention.",
     "expect_cpt": ["93458"], "expect_icd": ["I25.10"]},

    {"name": "Cardio: PCI with stent",
     "note": "60-year-old male with STEMI. Primary PCI with drug-eluting stent to LAD. TIMI 3 flow achieved.",
     "expect_cpt": ["92928"], "expect_icd": ["I21.0"]},

    {"name": "Cardio: Pacemaker insertion",
     "note": "75-year-old male with sick sinus syndrome. Dual chamber pacemaker implanted. Leads in RA and RV.",
     "expect_cpt": ["33230"], "expect_icd": ["I49.5"]},

    {"name": "Cardio: TEE",
     "note": "55-year-old female for evaluation of mitral regurgitation. Transesophageal echocardiogram performed. Moderate MR confirmed.",
     "expect_cpt": ["93312"], "expect_icd": ["I34.0"]},

    # ═══ ICD-10 CODING (10 cases) ═══════════════════════════════════════
    {"name": "ICD10: Diabetes with complications",
     "note": "60-year-old female with type 2 diabetes with proliferative retinopathy and diabetic nephropathy stage 3.",
     "expect_cpt": [], "expect_icd": ["E11.319", "E11.21"]},

    {"name": "ICD10: COPD exacerbation",
     "note": "68-year-old male with COPD gold stage 3 with acute exacerbation. Purulent sputum. Started on steroids.",
     "expect_cpt": [], "expect_icd": ["J44.1"]},

    {"name": "ICD10: Heart failure",
     "note": "72-year-old female with systolic heart failure EF 30%. NYHA class III. On carvedilol, lisinopril, spironolactone.",
     "expect_cpt": [], "expect_icd": ["I50.23"]},

    {"name": "ICD10: Acute MI",
     "note": "58-year-old male with STEMI anterior wall. Troponin elevated. Catheterization shows LAD occlusion.",
     "expect_cpt": [], "expect_icd": ["I21.0"]},

    {"name": "ICD10: Stroke",
     "note": "75-year-old female with acute ischemic stroke right MCA territory. NIHSS 12. TPA administered.",
     "expect_cpt": [], "expect_icd": ["I63.51"]},

    {"name": "ICD10: Pneumonia",
     "note": "45-year-old male with community acquired pneumonia. CXR shows RLL consolidation. Sputum culture pending.",
     "expect_cpt": [], "expect_icd": ["J18.1"]},

    {"name": "ICD10: CKD stage 4",
     "note": "65-year-old male with chronic kidney disease stage 4. GFR 28. On ACE inhibitor.",
     "expect_cpt": [], "expect_icd": ["N18.4"]},

    {"name": "ICD10: Sepsis",
     "note": "70-year-old female with sepsis from UTI. Blood cultures positive E. coli. On vasopressors.",
     "expect_cpt": [], "expect_icd": ["A41.52", "R65.21"]},

    {"name": "ICD10: Hip fracture",
     "note": "80-year-old female with left femoral neck fracture after fall. Osteoporosis history.",
     "expect_cpt": [], "expect_icd": ["S72.001A", "M80.061"]},

    {"name": "ICD10: Depression",
     "note": "35-year-old female with major depressive disorder, severe, single episode. PHQ-9 score 22.",
     "expect_cpt": [], "expect_icd": ["F32.2"]},

    # ═══ PATHOLOGY/LAB (5 cases) ═══════════════════════════════════════
    {"name": "Pathology: CMP",
     "note": "Adult patient. Comprehensive metabolic panel ordered. Glucose, BUN, creatinine, electrolytes, liver enzymes.",
     "expect_cpt": ["80053"], "expect_icd": []},

    {"name": "Pathology: CBC with differential",
     "note": "Adult patient. CBC with automated differential ordered. White count, hemoglobin, hematocrit, platelets.",
     "expect_cpt": ["85025"], "expect_icd": []},

    {"name": "Pathology: HbA1c",
     "note": "Diabetic patient. Hemoglobin A1c ordered for diabetes management.",
     "expect_cpt": ["83036"], "expect_icd": ["E11.9"]},

    {"name": "Pathology: Urinalysis",
     "note": "Patient with dysuria. Urinalysis with microscopy ordered. Evaluating for UTI.",
     "expect_cpt": ["81003"], "expect_icd": ["N39.0"]},

    {"name": "Pathology: Lipid panel",
     "note": "50-year-old male for cardiovascular risk assessment. Fasting lipid panel ordered.",
     "expect_cpt": ["80061"], "expect_icd": []},

    # ═══ RADIOLOGY (5 cases) ═══════════════════════════════════════════
    {"name": "Radiology: Chest X-ray 2 views",
     "note": "65-year-old with cough and fever. Chest X-ray PA and lateral views ordered.",
     "expect_cpt": ["71046"], "expect_icd": ["J18.9"]},

    {"name": "Radiology: CT head without contrast",
     "note": "70-year-old with new onset headache. CT head without contrast ordered to rule out hemorrhage.",
     "expect_cpt": ["70450"], "expect_icd": ["R51.9"]},

    {"name": "Radiology: MRI lumbar spine",
     "note": "50-year-old with radicular leg pain. MRI lumbar spine without contrast ordered.",
     "expect_cpt": ["72148"], "expect_icd": ["M54.5"]},

    {"name": "Radiology: CT abdomen with contrast",
     "note": "45-year-old with abdominal pain. CT abdomen with IV contrast ordered to evaluate for appendicitis.",
     "expect_cpt": ["74177"], "expect_icd": ["R10.9"]},

    {"name": "Radiology: Mammogram screening",
     "note": "55-year-old female for annual screening mammogram. Bilateral screening views.",
     "expect_cpt": ["77067"], "expect_icd": []},

    # ═══ MEDICINE (5 cases) ═══════════════════════════════════════════
    {"name": "Medicine: IV antibiotics pneumonia",
     "note": "65-year-old admitted with community acquired pneumonia. IV ceftriaxone and azithromycin started.",
     "expect_cpt": ["96360"], "expect_icd": ["J18.1"]},

    {"name": "Medicine: Chemotherapy infusion",
     "note": "55-year-old with breast cancer. IV chemotherapy infusion. First hour 96413.",
     "expect_cpt": ["96413"], "expect_icd": ["C50.919"]},

    {"name": "Medicine: TTE comprehensive",
     "note": "60-year-old with heart failure. Comprehensive transthoracic echocardiogram with Doppler.",
     "expect_cpt": ["93306"], "expect_icd": ["I50.9"]},

    {"name": "Medicine: Dialysis evaluation",
     "note": "ESRD patient on hemodialysis. Nephrologist evaluates during dialysis session.",
     "expect_cpt": ["90935"], "expect_icd": ["N18.6"]},

    {"name": "Medicine: Pacemaker interrogation",
     "note": "70-year-old with pacemaker. In-person interrogation and programming of device.",
     "expect_cpt": ["93282"], "expect_icd": ["Z95.0"]},

    # ═══ KNOWLEDGE/DEFINITIONS (5 cases) ═══════════════════════════════
    {"name": "Knowledge: Sepsis definition",
     "note": "Patient meets SIRS criteria with suspected infection. Sepsis defined as life-threatening organ dysfunction.",
     "expect_cpt": [], "expect_icd": []},

    {"name": "Knowledge: E/M MDM levels",
     "note": "E/M MDM has 4 levels: Straightforward, Low, Moderate, High. Determined by problems, data, and risk.",
     "expect_cpt": [], "expect_icd": []},

    {"name": "Knowledge: NCCI edits purpose",
     "note": "NCCI edits prevent improper code bundling and promote correct coding methodologies.",
     "expect_cpt": [], "expect_icd": []},

    {"name": "Knowledge: HIPAA definition",
     "note": "HIPAA establishes national standards for healthcare transactions, PHI privacy, and insurance portability.",
     "expect_cpt": [], "expect_icd": []},

    {"name": "Knowledge: Modifier 25 usage",
     "note": "Modifier 25 indicates significant, separately identifiable E/M service on same day as procedure.",
     "expect_cpt": [], "expect_icd": []},
]


def run_test(index, case):
    """Run a single test case."""
    result = pipeline.run(note_text=case["note"], note_id=f"selftest-{index}")

    cpt_codes = [c.get("code", "") for c in result.cpt_codes]
    icd_codes = [c.get("code", "") for c in result.icd10_codes]

    # Check CPT match (any expected CPT in generated)
    cpt_ok = True
    if case["expect_cpt"]:
        cpt_ok = any(ec in cpt_codes for ec in case["expect_cpt"])

    # Check ICD match (all expected ICD in generated)
    icd_ok = True
    if case["expect_icd"]:
        icd_ok = all(ei in icd_codes for ei in case["expect_icd"])

    passed = cpt_ok and icd_ok
    return {
        "name": case["name"],
        "passed": passed,
        "cpt_generated": cpt_codes[:3],
        "cpt_expected": case["expect_cpt"],
        "icd_generated": icd_codes[:3],
        "icd_expected": case["expect_icd"],
    }


def main():
    print("=" * 80)
    print("  MedCode AI V19 — Self-Generated Comprehensive Test Suite")
    print("=" * 80)
    print("  Running {} test cases...".format(len(test_cases)))
    print()

    results = []
    passed = 0
    failed = 0

    for i, case in enumerate(test_cases, 1):
        result = run_test(i, case)
        results.append(result)

        if result["passed"]:
            passed += 1
            icon = "PASS"
        else:
            failed += 1
            icon = "FAIL"

        cpt_str = ",".join(result["cpt_generated"][:2]) if result["cpt_generated"] else "-"
        icd_str = ",".join(result["icd_generated"][:2]) if result["icd_generated"] else "-"

        print("  {:4s} [{:2d}/{:2d}] {:45s} | CPT:{:15s} | ICD:{:15s}".format(
            icon, i, len(test_cases), result["name"][:45], cpt_str[:15], icd_str[:15]))

    # Summary
    print()
    print("=" * 80)
    print("  SUMMARY: {}/{} passed ({:.0f}%)".format(passed, len(test_cases), passed/len(test_cases)*100))
    print("=" * 80)

    # Category breakdown
    categories = {}
    for r in results:
        cat = r["name"].split(":")[0]
        categories.setdefault(cat, {"passed": 0, "total": 0})
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    print()
    print("  BY CATEGORY:")
    for cat, stats in sorted(categories.items()):
        rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        bar = "#" * int(rate / 5) + "." * (20 - int(rate / 5))
        print("  {:20s} | {}/{} | {} | {:.0f}%".format(
            cat, stats["passed"], stats["total"], bar, rate))

    return passed, failed


if __name__ == "__main__":
    passed, failed = main()
    sys.exit(0 if failed == 0 else 1)
