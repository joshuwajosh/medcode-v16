"""
Tests for Clinical Note Parser — 20 clinical note scenarios.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.clinical_note_parser import ClinicalNoteParser


TEST_CASES = [
    {
        "name": "Office visit - established patient with CAD",
        "note": """Chief Complaint: Chest pain
History: 65yo male, established patient, presents for follow-up of coronary artery disease.
Currently on aspirin 81mg, statin, beta-blocker. Blood pressure 138/82.
Assessment: Coronary artery disease, stable angina. Hypertension.
Plan: Continue current medications. Follow up in 3 months.""",
        "expected_cpt": ["99213"],
        "expected_icd": ["I25.10", "I10"],
    },
    {
        "name": "ED visit - chest pain",
        "note": """Emergency Department Note
Patient is a 52yo female presenting with acute chest pain, onset 2 hours ago.
ECG: ST elevation in leads II, III, aVF. Troponin elevated at 2.4.
Assessment: Acute ST elevation myocardial infarction.
Plan: Activate cath lab. Start heparin and aspirin.""",
        "expected_cpt": ["99283", "99284", "99285"],
        "expected_icd": ["I21.3", "I21.9"],
    },
    {
        "name": "Operative report - laparoscopic cholecystectomy",
        "note": """OPERATIVE REPORT
Procedure: Laparoscopic cholecystectomy
Diagnosis: Cholelithiasis with chronic cholecystitis
Indication: Symptomatic gallstones, ultrasound confirmed.
Findings: Multiple stones in gallbladder. No common bile duct dilation.
Technique: Four trocar technique. Critical view of safety achieved.
Gallbladder dissected and removed from liver bed.
Specimen sent to pathology.""",
        "expected_cpt": ["47562"],
        "expected_icd": ["K80.20"],
    },
    {
        "name": "Hospital admission - pneumonia",
        "note": """Admission Note
Patient is a 78yo male admitted for community-acquired pneumonia.
Vitals: Temp 101.8F, HR 95, BP 110/70, O2 sat 91% on room air.
Chest X-ray: Right lower lobe consolidation.
Assessment: Pneumonia, right lower lobe. COPD. Hypertension.
Plan: Start IV antibiotics. Supplemental oxygen.""",
        "expected_cpt": ["99221", "99222", "99223"],
        "expected_icd": ["J18.9", "J44.1", "I10"],
    },
    {
        "name": "Operative report - CABG x3",
        "note": """OPERATIVE REPORT
Procedure: Coronary artery bypass graft x3
Technique: LIMA to LAD, SVG to RCA, SVG to OM1
Cross-clamp time: 85 minutes. Pump time: 120 minutes.
Diagnosis: Severe triple vessel coronary artery disease.""",
        "expected_cpt": ["33533"],
        "expected_icd": ["I25.10"],
    },
    {
        "name": "Office visit - diabetes management",
        "note": """Office Visit Note
Patient is a 55yo female with type 2 diabetes mellitus, presents for routine follow-up.
HbA1c 7.2%. Fasting glucose 142. On metformin 1000mg BID.
Assessment: Type 2 diabetes mellitus, suboptimally controlled. Hypertension. Hyperlipidemia.
Plan: Increase metformin to 1500mg BID. Recheck HbA1c in 3 months.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["E11.9", "E11.65", "I10"],
    },
    {
        "name": "Total knee replacement",
        "note": """OPERATIVE REPORT
Procedure: Right total knee arthroplasty
Diagnosis: Severe osteoarthritis right knee
Approach: Medial parapatellar arthrotomy
Implant: Zimmer Persona cruciate-retaining
Tibial component cemented. Femoral component cemented. Patella resurfaced.""",
        "expected_cpt": ["27447"],
        "expected_icd": ["M17.11", "M19.90"],
    },
    {
        "name": "Colonoscopy with polypectomy",
        "note": """PROCEDURE NOTE
Procedure: Colonoscopy with polypectomy
Indication: Screening colonoscopy, family history of colon cancer.
Findings: Two polyps in sigmoid colon removed with cold snare.
Pathology sent. Cecum reached. Withdrawal time 12 minutes.
Diagnosis: Colonic polyps. Family history of colon cancer.""",
        "expected_cpt": ["45385"],
        "expected_icd": ["Z12.11", "Z80.0", "D12.6"],
    },
    {
        "name": "Inguinal hernia repair",
        "note": """OPERATIVE REPORT
Procedure: Right inguinal hernia repair
Technique: Lichtenstein tension-free mesh repair
Diagnosis: Right indirect inguinal hernia
Hernia sac reduced. Mesh secured with sutures.""",
        "expected_cpt": ["44950", "49560"],
        "expected_icd": ["K40.91", "K40.90", "K40.9"],
    },
    {
        "name": "Stroke admission",
        "note": """Admission Note
Patient is a 72yo male admitted with acute ischemic stroke.
CT head: No hemorrhage. CTA: Left MCA occlusion.
NIHSS score: 14. Onset: 3 hours ago.
Assessment: Acute ischemic stroke, left MCA territory. Atrial fibrillation. Hypertension. Diabetes.
Plan: Start tPA. Admit to neuro step-down unit.""",
        "expected_cpt": ["99221", "99222", "99223"],
        "expected_icd": ["I63.9", "I63.51", "I48.91", "I10", "E11.9"],
    },
    {
        "name": "Inpatient progress note - heart failure",
        "note": """Progress Note - Day 2
Patient is a 68yo female with acute decompensated heart failure.
Current: BNP 1850. Weight 198 lbs (up 12 lbs from dry weight).
Jugular venous distension. Bilateral lower extremity edema.
Assessment: Acute decompensated heart failure, systolic. CKD stage 3. Diabetes.
Plan: Increase diuresis. Daily weights. Restrict fluids.""",
        "expected_cpt": ["99231", "99232", "99233"],
        "expected_icd": ["I50.23", "I50.9", "N18.3", "N18.9", "E11.9"],
    },
    {
        "name": "Pediatric well-child visit",
        "note": """Well Child Visit
Patient: 4-year-old male
Vitals: Weight 35 lbs (50th percentile), Height 38 inches (45th percentile).
Development: Age-appropriate milestones. Speaks in full sentences.
Immunizations: Up to date.
Assessment: Healthy 4-year-old male.
Plan: Continue routine immunizations. Return in 1 year.""",
        "expected_cpt": ["99394", "99213"],
        "expected_icd": ["Z00.121", "Z00.12"],
    },
    {
        "name": "Knee MRI",
        "note": """Radiology Report
Procedure: MRI right knee without contrast
Clinical indication: Knee pain, possible meniscal tear
Findings: Medial meniscus posterior horn tear. Mild medial compartment osteoarthritis.
No ligament tear. Small joint effusion.
Impression: Medial meniscus tear. Early osteoarthritis.""",
        "expected_cpt": ["73721"],
        "expected_icd": ["M23.31", "M17.11", "M19.90"],
    },
    {
        "name": "Upper endoscopy with biopsy",
        "note": """PROCEDURE NOTE
Procedure: Esophagogastroduodenoscopy with biopsy
Indication: Dyspepsia, H. pylori testing
Findings: Erythematous gastritis. Biopsies taken from antrum for H. pylori.
No Barrett esophagus. Duodenum normal.
Diagnosis: Gastritis.""",
        "expected_cpt": ["43239"],
        "expected_icd": ["K29.70"],
    },
    {
        "name": "Atrial fibrillation ablation",
        "note": """OPERATIVE REPORT
Procedure: Pulmonary vein isolation with radiofrequency ablation
Indication: Drug-refractory atrial fibrillation
Findings: Pulmonary vein isolation confirmed. No complications.
Diagnosis: Paroxysmal atrial fibrillation.""",
        "expected_cpt": ["93656"],
        "expected_icd": ["I48.0", "I48.91"],
    },
    {
        "name": "Carpal tunnel release",
        "note": """OPERATIVE REPORT
Procedure: Right carpal tunnel release
Technique: Open release of transverse carpal ligament
Diagnosis: Carpal tunnel syndrome, right
Findings: Median nerve compressed. Ligament divided. Nerve decompressed.""",
        "expected_cpt": ["64721"],
        "expected_icd": ["G56.0"],
    },
    {
        "name": "Appendectomy",
        "note": """OPERATIVE REPORT
Procedure: Laparoscopic appendectomy
Diagnosis: Acute appendicitis
Findings: Non-perforated appendix with appendicolith.
Technique: Three-trocar technique. Appendix base stapled. Removed through port site.""",
        "expected_cpt": ["44970"],
        "expected_icd": ["K35.80"],
    },
    {
        "name": "Echocardiogram",
        "note": """Echocardiogram Report
Procedure: Complete transthoracic echocardiogram
Indication: Shortness of breath, possible heart failure
Findings: LVEF 35%. Mild MR. LV dilation 6.2cm. No pericardial effusion.
Impression: Reduced ejection fraction. Dilated cardiomyopathy. Mild mitral regurgitation.""",
        "expected_cpt": ["93306"],
        "expected_icd": ["I50.20", "I42.9", "I34.0"],
    },
    {
        "name": "Asthma exacerbation - ED",
        "note": """Emergency Department Note
Patient is a 28yo female with history of asthma presenting with acute asthma exacerbation.
Wheezing bilaterally. O2 sat 94% on room air. Peak flow 200 L/min (50% predicted).
Assessment: Moderate asthma exacerbation.
Plan: Nebulized albuterol x3, IV methylprednisolone. Reassess after treatments.""",
        "expected_cpt": ["99283", "99284", "99285"],
        "expected_icd": ["J45.41", "J45.901", "J45.40"],
    },
    {
        "name": "Hip fracture - surgical",
        "note": """OPERATIVE REPORT
Procedure: Open reduction and internal fixation right hip fracture
Diagnosis: Displaced right femoral neck fracture
Technique: Lateral approach. Three cannulated screws placed.
Fracture reduced anatomically. Hardware position confirmed with fluoroscopy.""",
        "expected_cpt": ["27230"],
        "expected_icd": ["S72.001A", "S72.009A"],
    },
]


def run_tests():
    parser = ClinicalNoteParser()
    passed = 0
    total = len(TEST_CASES)

    print("=" * 80)
    print("  Clinical Note Parser Test Suite: 20 Scenarios")
    print("=" * 80)

    for i, case in enumerate(TEST_CASES, 1):
        result = parser.parse(case["note"])

        cpt_found = [c["code"] for c in result.get("cpt_codes", [])]
        icd_found = [c["code"] for c in result.get("icd_codes", [])]

        cpt_match = any(c in cpt_found for c in case["expected_cpt"]) if case["expected_cpt"] else True
        icd_match = any(c in icd_found for c in case["expected_icd"]) if case["expected_icd"] else True

        overall = cpt_match and icd_match
        if overall:
            passed += 1

        status = "PASS" if overall else "FAIL"
        print(f"  {status} [{i:2d}/{total}] {case['name'][:45]:<45} | "
              f"CPT: {','.join(cpt_found[:3]):<15} | ICD: {','.join(icd_found[:3]):<15}")

    print("\n" + "=" * 80)
    print(f"  RESULTS: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print("=" * 80)
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
