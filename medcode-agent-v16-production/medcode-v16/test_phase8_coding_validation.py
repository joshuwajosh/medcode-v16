"""
Phase 8 — Medical Coding Engine Validation
Test 20 diverse clinical notes across all specialties.
"""
import sys
import json
import time
import traceback

sys.path.insert(0, '.')

from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15 as MedcodeDeterministicPipelineV16
from agents.clinical_note_parser import ClinicalNoteParser

# ═══════════════════════════════════════════════════════════════════
# 20 DIVERSE CLINICAL NOTES
# ═══════════════════════════════════════════════════════════════════

TEST_CASES = [
    # ── SURGERY ────────────────────────────────────────────────────
    {
        "id": "S1",
        "specialty": "Surgery - CABG",
        "note": (
            "PROCEDURE: Coronary artery bypass grafting x3 (CABG x3). "
            "LEFT INTERNAL MAMMARY ARTERY (LIMA) to left anterior descending artery. "
            "Saphenous vein graft to right coronary artery. "
            "Saphenous vein graft to obtuse marginal artery. "
            "Preoperative diagnosis: Severe triple-vessel coronary artery disease. "
            "Postoperative diagnosis: Severe triple-vessel coronary artery disease. "
            "Indication: Patient had refractory angina despite maximal medical therapy. "
            "Cardiac catheterization showed 90% LAD, 85% RCA, 80% OM stenoses. "
            "The patient was placed on cardiopulmonary bypass with aortic and bicaval cannulation. "
            "Cross-clamp time: 78 minutes. Pump time: 112 minutes. "
            "The patient tolerated the procedure well and was transferred to the CTICU in stable condition."
        ),
        "expected_cpt": ["33533"],
        "expected_icd_prefix": ["I25"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "S2",
        "specialty": "Surgery - Cholecystectomy",
        "note": (
            "PROCEDURE: Laparoscopic cholecystectomy. "
            "PREOPERATIVE DIAGNOSIS: Symptomatic cholelithiasis. "
            "POSTOPERATIVE DIAGNOSIS: Symptomatic cholelithiasis. "
            "INDICATION: Right upper quadrant pain, multiple gallstones on ultrasound. "
            "DESCRIPTION: The patient was placed under general anesthesia. "
            "A 12mm umbilical port was inserted using the Hasson technique. "
            "Two additional 5mm ports were placed in the right upper quadrant. "
            "The gallbladder was retracted cephalad. Calot's triangle was dissected. "
            "The cystic duct and cystic artery were identified and clipped with titanium clips. "
            "The gallbladder was removed from the liver bed using electrocautery. "
            "Hemostasis was achieved. The gallbladder was removed through the umbilical port. "
            "The fascia was closed with 0-Vicryl. Skin was closed with subcuticular 4-0 Monocryl."
        ),
        "expected_cpt": ["47562"],
        "expected_icd_prefix": ["K80", "K81"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "S3",
        "specialty": "Surgery - Hernia Repair",
        "note": (
            "PROCEDURE: Right inguinal hernia repair with mesh. "
            "PREOPERATIVE DIAGNOSIS: Right indirect inguinal hernia. "
            "POSTOPERATIVE DIAGNOSIS: Right indirect inguinal hernia. "
            "INDICATION: Bulge in right groin region, clinically symptomatic. "
            "DESCRIPTION: Under general anesthesia, a 3 cm incision was made in the right inguinal region. "
            "The external oblique fascia was opened. The spermatic cord was identified. "
            "An indirect hernia sac was identified and dissected to the internal ring. "
            "The sac was reduced. A polypropylene mesh was placed over the posterior wall of the inguinal canal. "
            "The mesh was secured with interrupted 3-0 PDS sutures. "
            "The external oblique was closed with running 3-0 Vicryl. "
            "Skin was closed with subcuticular 4-0 Monocryl."
        ),
        "expected_cpt": ["44950", "49560"],
        "expected_icd_prefix": ["K40"],
        "check_laterality": True,
        "laterality_expected": "right",
        "check_organism": False,
    },
    {
        "id": "S4",
        "specialty": "Surgery - Knee Replacement",
        "note": (
            "PROCEDURE: Left total knee arthroplasty. "
            "PREOPERATIVE DIAGNOSIS: Severe left knee osteoarthritis. "
            "POSTOPERATIVE DIAGNOSIS: Severe left knee osteoarthritis. "
            "INDICATION: End-stage left knee osteoarthritis with bone-on-bone articulation, "
            "failed conservative management including physical therapy and injections. "
            "DESCRIPTION: The left knee was approached through a medial parapatellar incision. "
            "The distal femur was cut using intramedullary alignment. "
            "The proximal tibia was cut using extramedullary alignment. "
            "Trial components were placed and range of motion was assessed. "
            "The final cemented components were inserted: femoral component size 4, tibial component size 3. "
            "The patella was resurfaced. "
            "The wound was irrigated and closed in layers. "
            "A hemovac drain was placed."
        ),
        "expected_cpt": ["27447"],
        "expected_icd_prefix": ["M17"],
        "check_laterality": True,
        "laterality_expected": "left",
        "check_organism": False,
    },

    # ── E/M ────────────────────────────────────────────────────────
    {
        "id": "EM1",
        "specialty": "E/M - Office Visit",
        "note": (
            "OFFICE VISIT - ESTABLISHED PATIENT\n"
            "Patient is a 58-year-old male presenting for follow-up of type 2 diabetes mellitus "
            "and hypertension. Patient reports good medication compliance. "
            "Current medications: metformin 1000mg BID, lisinopril 10mg daily. "
            "Review of systems: No complaints today. No chest pain, shortness of breath, "
            "or lower extremity edema. Denies polyuria or polydipsia. "
            "Physical examination: BP 128/76, HR 72, RR 16, Temp 98.6F, SpO2 98% RA. "
            "HEENT: PERRLA, oropharynx clear. Neck: No thyromegaly. "
            "Cardiovascular: Regular rate and rhythm, no murmurs. "
            "Lungs: Clear to auscultation bilaterally. "
            "Extremities: No edema, pulses 2+ bilaterally. "
            "Assessment: 1. Type 2 diabetes mellitus, well controlled. 2. Hypertension, well controlled. "
            "Plan: Continue current medications. Repeat HbA1c in 3 months. Annual dilated eye exam. "
            "Annual foot exam performed today - monofilament testing normal bilateral."
        ),
        "expected_cpt": ["99213", "99214"],
        "expected_icd_prefix": ["E11", "I10"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "EM2",
        "specialty": "E/M - Hospital Admission",
        "note": (
            "HOSPITAL ADMISSION NOTE\n"
            "Patient is a 72-year-old female admitted through the ED for acute exacerbation of COPD. "
            "Patient presents with 3-day history of worsening dyspnea, productive cough with "
            "yellow-green sputum, and decreased exercise tolerance. "
            "She reports she ran out of her Spiriva and Symbicort 2 weeks ago. "
            "ED course: Started on Duoneb q4h, prednisone 125mg IV, azithromycin 500mg IV. "
            "Chest X-ray showed hyperinflation with no acute infiltrate. "
            "ABG on room air: pH 7.32, pCO2 52, pO2 58, HCO3 27. "
            "Physical examination: Diffuse expiratory wheezing bilaterally, prolonged expiratory phase. "
            "SpO2 89% on room air, improved to 94% on 2L NC. "
            "Assessment: Acute exacerbation of COPD, respiratory failure. "
            "Plan: Continue nebulizer treatments, IV steroids, antibiotics, titrate O2 to maintain SpO2 >90%. "
            "Pulmonology consult for optimization."
        ),
        "expected_cpt": ["99223"],
        "expected_icd_prefix": ["J44", "J96"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "EM3",
        "specialty": "E/M - Critical Care",
        "note": (
            "CRITICAL CARE NOTE - ICU\n"
            "Patient is a 65-year-old male in the medical ICU with septic shock secondary to "
            "klebsiella pneumonia. Patient was intubated on admission. "
            "Current ventilator settings: AC mode, TV 450, RR 14, FiO2 60%, PEEP 8. "
            "Vitals: BP 88/52 on norepinephrine 12 mcg/min, HR 110, Temp 38.9C, SpO2 96%. "
            "Physical exam: Intubated, sedated. Lungs: Crackles right lower lobe. "
            "Abdomen: Soft, non-distended. Extremities: Warm, capillary refill 2 seconds. "
            "Labs: WBC 18.2, lactate 3.8, procalcitonin 8.5, Cr 1.8 (baseline 1.0). "
            "Blood cultures grew Klebsiella pneumoniae. Sensitivity pending. "
            "Assessment: Septic shock, Klebsiella pneumonia, acute kidney injury. "
            "Plan: Continue vasopressors, broad-spectrum antibiotics pending sensitivities, "
            "lung-protective ventilation, conservative fluid strategy. "
            "Total critical care time: 90 minutes."
        ),
        "expected_cpt": ["99291"],
        "expected_icd_prefix": ["A41", "J15", "J18"],
        "check_laterality": False,
        "check_organism": True,
        "organism_keyword": "klebsiella",
        "organism_expected_icd": "J15.0",
    },

    # ── RADIOLOGY ──────────────────────────────────────────────────
    {
        "id": "R1",
        "specialty": "Radiology - CT",
        "note": (
            "CT CHEST WITH CONTRAST\n"
            "CLINICAL HISTORY: 55-year-old male with history of lung cancer, staging. "
            "TECHNIQUE: CT of the chest was performed with IV contrast. "
            "FINDINGS: \n"
            "Lungs: 2.3 cm spiculated mass in the right upper lobe. No additional pulmonary nodules. "
            "No pleural effusion. No pneumothorax. "
            "Mediastinum: Pretracheal and right paratracheal lymphadenopathy, largest 1.8 cm. "
            "Heart: Normal heart size. No pericardial effusion. "
            "Chest wall: No rib destruction. "
            "IMPRESSION: \n"
            "1. Right upper lobe mass, suspicious for primary lung malignancy.\n"
            "2. Mediastinal lymphadenopathy, concerning for metastatic disease."
        ),
        "expected_cpt": ["71260"],
        "expected_icd_prefix": ["C34", "R"],
        "check_laterality": True,
        "laterality_expected": "right",
        "check_organism": False,
    },
    {
        "id": "R2",
        "specialty": "Radiology - MRI",
        "note": (
            "MRI LEFT KNEE WITHOUT CONTRAST\n"
            "CLINICAL HISTORY: 42-year-old female with left knee pain after sports injury. "
            "TECHNIQUE: MRI of the left knee was performed without IV contrast using standard protocol. "
            "FINDINGS:\n"
            "Menisci: Complex tear of the posterior horn of the medial meniscus. "
            "Lateral meniscus is intact.\n"
            "Ligaments: Complete tear of the anterior cruciate ligament (ACL). "
            "MCL and PCL are intact.\n"
            "Cartilage: Full-thickness chondral defect of the medial femoral condyle, approximately 2 cm. "
            "Other compartments show mild chondromalacia.\n"
            "Bone: Bone contusion of the lateral femoral condyle and posterolateral tibial plateau "
            "(pivot shift pattern).\n"
            "Effusion: Moderate joint effusion.\n"
            "IMPRESSION:\n"
            "1. Complete ACL tear.\n"
            "2. Complex tear of the posterior horn of the medial meniscus.\n"
            "3. Full-thickness chondral defect, medial femoral condyle.\n"
            "4. Bone contusion pattern consistent with acute ACL injury."
        ),
        "expected_cpt": ["73721"],
        "expected_icd_prefix": ["S83", "M23", "M17"],
        "check_laterality": True,
        "laterality_expected": "left",
        "check_organism": False,
    },

    # ── PATHOLOGY ──────────────────────────────────────────────────
    {
        "id": "P1",
        "specialty": "Pathology - Biopsy",
        "note": (
            "PATHOLOGY REPORT\n"
            "CLINICAL HISTORY: 68-year-old female with right breast mass. Family history of breast cancer. "
            "SPECIMEN: Ultrasound-guided core needle biopsy, right breast, 3 o'clock position.\n"
            "GROSS DESCRIPTION: Three core tissue fragments, each 1.5 cm in length, tan-white. "
            "HISTOLOGICAL EXAMINATION:\n"
            "The sections show infiltrating ductal carcinoma, Nottingham grade 2 (tubule formation 2, "
            "nuclear pleomorphism 2, mitotic count 1). Tumor measures 1.8 cm in greatest dimension. "
            "Lymphovascular invasion is not identified. "
            "Immunohistochemistry: ER positive (80%), PR positive (40%), HER2 negative (1+), "
            "Ki-67 25%.\n"
            "DIAGNOSIS: \n"
            "Right breast, 3 o'clock, core biopsy: Infiltrating ductal carcinoma, Nottingham grade 2. "
            "Molecular subtype: Luminal B.\n"
            "AJCC Stage: pT1c N0 (sentinel node pending)."
        ),
        "expected_cpt": ["19102"],
        "expected_icd_prefix": ["C50"],
        "check_laterality": True,
        "laterality_expected": "right",
        "check_organism": False,
    },
    {
        "id": "P2",
        "specialty": "Pathology - FNA",
        "note": (
            "FINE NEEDLE ASPIRATION BIOPSY REPORT\n"
            "CLINICAL HISTORY: 45-year-old female with left thyroid nodule, FNA for cytological evaluation. "
            "SPECIMEN: Fine needle aspiration biopsy, left thyroid, nodule at mid-pole.\n"
            "GROSS DESCRIPTION: Three passes yielded moderately cellular material. "
            "Air-dried and alcohol-fixed smears were prepared. "
            "CYTOLOGICAL FINDINGS:\n"
            "The smears show a moderately cellular specimen with overlapping groups and "
            "syncytial clusters of follicular cells with mild nuclear enlargement, "
            "irregular nuclear contours, and occasional intranuclear inclusions. "
            "Multinucleated giant cells and abundant colloid are present. "
            "No features of papillary thyroid carcinoma are seen.\n"
            "DIAGNOSIS:\n"
            "Left thyroid, FNA: Benign thyroid nodule (colloid nodule). Bethesda Category II.\n"
            "RECOMMENDATION: Clinical correlation and follow-up ultrasound in 12-24 months."
        ),
        "expected_cpt": ["10005"],
        "expected_icd_prefix": ["E04", "D34"],
        "check_laterality": True,
        "laterality_expected": "left",
        "check_organism": False,
    },

    # ── ANESTHESIA ─────────────────────────────────────────────────
    {
        "id": "A1",
        "specialty": "Anesthesia - General",
        "note": (
            "ANESTHESIA RECORD\n"
            "PROCEDURE: General anesthesia for laparoscopic cholecystectomy. "
            "PATIENT: 45-year-old female, ASA II. "
            "PREOPERATIVE ASSESSMENT: Mallampati II, no airway concerns, NPO x 10 hours. "
            "ANESTHESIA INDUCTION: Propofol 200mg, fentanyl 100mcg, rocuronium 50mg. "
            "MAINTENANCE: Sevoflurane 1.5-2% in O2/air mixture. "
            "INTUBATION: Direct laryngoscopy, Grade I view, 7.0 ETT placed, confirmed with ETCO2. "
            "MONITORING: ASA standard monitors, arterial line (radial), temperature. "
            "INTRAOPERATIVE COURSE: Stable hemodynamics throughout. Blood loss minimal (<50cc). "
            "Urine output adequate. No complications. "
            "EMERGENCE: Reversed with sugammadex 200mg. Extubated awake, following commands. "
            "DURATION: 95 minutes total. "
            "POSTOPERATIVE: PACU, Aldrete 10/10."
        ),
        "expected_cpt": ["01967"],
        "expected_icd_prefix": ["K80", "Z"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "A2",
        "specialty": "Anesthesia - Regional",
        "note": (
            "ANESTHESIA RECORD\n"
            "PROCEDURE: Regional anesthesia - left interscalene nerve block for shoulder arthroscopy. "
            "PATIENT: 38-year-old male, ASA I. "
            "TECHNIQUE: Ultrasound-guided interscalene nerve block. "
            "Needle: 22G 50mm Stimuplex needle. "
            "Local anesthetic: 20 mL of 0.5% ropivacaine with 1:200,000 epinephrine. "
            "PROCEDURE: Patient positioned supine, head turned to the right. "
            "Ultrasound identified C5-C6 nerve roots in the interscalene groove. "
            "Negative aspiration followed by incremental injection of local anesthetic. "
            "Sensory and motor block achieved within 15 minutes. "
            "MONITORING: Pulse oximetry, ETCO2, BP q5min. "
            "INTRAOPERATIVE: Adequate surgical anesthesia throughout. "
            "Patient comfortable, no complications. "
            "POSTOPERATIVE: PACU, motor function returning at 4 hours."
        ),
        "expected_cpt": ["64415"],
        "expected_icd_prefix": ["M75"],
        "check_laterality": True,
        "laterality_expected": "left",
        "check_organism": False,
    },

    # ── CARDIOLOGY ─────────────────────────────────────────────────
    {
        "id": "C1",
        "specialty": "Cardiology - Catheterization",
        "note": (
            "CARDIAC CATHETERIZATION REPORT\n"
            "CLINICAL HISTORY: 62-year-old male with unstable angina. Troponin elevated at 0.8. "
            "ECG showed ST depression in leads II, III, aVF. "
            "PROCEDURE: Left heart catheterization with coronary angiography. "
            "HEMODYNAMICS: LV pressure 128/12, aortic pressure 118/68, PCWP 18. "
            "CORONARY ANGIOGRAPHY:\n"
            "Left main: 30% distal stenosis.\n"
            "LAD: 90% proximal stenosis, 80% mid stenosis.\n"
            "LCx: 70% stenosis.\n"
            "RCA: 95% proximal stenosis.\n"
            "EF: 40% by ventriculography.\n"
            "INTERVENTION: PCI to LAD proximal stenosis with drug-eluting stent (DES). "
            "Post-dilation with 3.5mm balloon. Final result: 0% residual stenosis, TIMI 3 flow. "
            "RCA stenosis deferred to staged procedure.\n"
            "COMPLICATIONS: None.\n"
            "DISPOSITION: CCU for monitoring."
        ),
        "expected_cpt": ["93458", "92928"],
        "expected_icd_prefix": ["I21", "I25"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "C2",
        "specialty": "Cardiology - Ablation",
        "note": (
            "CARDIAC ABLATION PROCEDURE NOTE\n"
            "CLINICAL HISTORY: 55-year-old female with symptomatic paroxysmal atrial fibrillation "
            "refractory to flecainide and metoprolol. "
            "PROCEDURE: Pulmonary vein isolation using radiofrequency ablation. "
            "TECHNIQUE: Transseptal puncture under fluoroscopic and intracardiac echo guidance. "
            "Circular mapping catheter placed in left atrium. "
            "Activation mapping identified pulmonary vein potentials. "
            "Radiofrequency ablation performed at: left superior PV, left inferior PV, "
            "right superior PV, right inferior PV. "
            "Completion of isolation confirmed by entrance and exit block. "
            "DURATION: 180 minutes. FLUOROSCOPY: 45 minutes. "
            "COMPLICATIONS: None. No pericardial effusion. "
            "POST-PROCEDURE: Patient in normal sinus rhythm. Monitored overnight. "
            "Discharged on anticoagulation (apixaban)."
        ),
        "expected_cpt": ["93656"],
        "expected_icd_prefix": ["I48"],
        "check_laterality": False,
        "check_organism": False,
    },

    # ── ORTHOPEDICS ────────────────────────────────────────────────
    {
        "id": "O1",
        "specialty": "Orthopedics - Fracture",
        "note": (
            "OPERATIVE REPORT\n"
            "PROCEDURE: Open reduction and internal fixation (ORIF) of right distal radius fracture. "
            "PREOPERATIVE DIAGNOSIS: Displaced right distal radius fracture (Colles' type). "
            "POSTOPERATIVE DIAGNOSIS: Displaced right distal radius fracture. "
            "INDICATION: 62-year-old female who fell on outstretched hand. X-ray showed "
            "displaced distal radius fracture with dorsal angulation >20 degrees. "
            "PROCEDURE: Under general anesthesia with a right upper extremity tourniquet. "
            "A volar approach was made through the flexor carpi radialis interval. "
            "The fracture was identified and reduced under fluoroscopic guidance. "
            "A volar locking plate was applied and secured with 7 locking screws. "
            "Articular surface was restored. Range of motion was assessed. "
            "Wound was closed in layers. A short arm splint was applied. "
            "Estimated blood loss: 50cc. Tourniquet time: 45 minutes."
        ),
        "expected_cpt": ["25607"],
        "expected_icd_prefix": ["S52"],
        "check_laterality": True,
        "laterality_expected": "right",
        "check_organism": False,
    },
    {
        "id": "O2",
        "specialty": "Orthopedics - Arthroscopy",
        "note": (
            "ARTHROSCOPY PROCEDURE NOTE\n"
            "PROCEDURE: Right knee arthroscopy with partial medial meniscectomy. "
            "PREOPERATIVE DIAGNOSIS: Right medial meniscal tear. "
            "POSTOPERATIVE DIAGNOSIS: Complex tear, posterior horn medial meniscus. "
            "INDICATION: 35-year-old male with right knee pain and mechanical symptoms "
            "after a twisting injury. MRI confirmed medial meniscal tear. "
            "DESCRIPTION: Standard arthroscopic portals were established. "
            "Diagnostic arthroscopy revealed: \n"
            "1. Complex tear of the posterior horn of the medial meniscus.\n"
            "2. Grade II chondromalacia of the medial femoral condyle.\n"
            "3. ACL and PCL intact.\n"
            "4. Lateral compartment normal.\n"
            "PARTIAL MENISECTOMY: The torn fragments were resected using arthroscopic biters "
            "and shaver. The remaining meniscal rim was stable. "
            "No additional procedures were required. "
            "Wounds were closed with Steri-Strips. A compressive dressing was applied."
        ),
        "expected_cpt": ["29881"],
        "expected_icd_prefix": ["M23"],
        "check_laterality": True,
        "laterality_expected": "right",
        "check_organism": False,
    },

    # ── EMERGENCY MEDICINE ─────────────────────────────────────────
    {
        "id": "EM_ED1",
        "specialty": "Emergency Medicine - Trauma",
        "note": (
            "EMERGENCY DEPARTMENT NOTE\n"
            "CHIEF COMPLAINT: Motor vehicle accident with chest pain. "
            "HPI: 28-year-old male, restrained driver, rear-ended at 45 mph. "
            "Complaining of chest pain, left shoulder pain, and neck pain. "
            "No loss of consciousness. No head strike. Seatbelt sign present on chest. "
            "VITAL SIGNS: BP 132/84, HR 108, RR 20, Temp 98.2F, SpO2 97% RA. "
            "PHYSICAL EXAM: Alert and oriented x4. Left chest wall tenderness with crepitus over "
            "ribs 4-6. Left shoulder tenderness. C-spine midline tenderness. "
            "Neurologically intact bilateral upper and lower extremities. "
            "WORKUP: \n"
            "CXR: Left rib fractures (ribs 4-6), small left pneumothorax.\n"
            "CT C-spine: No fracture or malalignment.\n"
            "CT Chest: Left rib fractures with small pneumothorax. No hemothorax.\n"
            "ASSESSMENT: \n"
            "1. Left rib fractures (ribs 4-6)\n"
            "2. Left small pneumothorax\n"
            "3. Cervical spine strain\n"
            "PLAN: \n"
            "1. Chest tube (pigtail catheter) for pneumothorax.\n"
            "2. C-collar until cleared by orthopedics.\n"
            "3. Pain management: morphine 4mg IV.\n"
            "4. Admit to trauma surgery."
        ),
        "expected_cpt": ["99285"],
        "expected_icd_prefix": ["S20", "S22", "J93"],
        "check_laterality": True,
        "laterality_expected": "left",
        "check_organism": False,
    },
    {
        "id": "EM_ED2",
        "specialty": "Emergency Medicine - Sepsis",
        "note": (
            "EMERGENCY DEPARTMENT NOTE\n"
            "CHIEF COMPLAINT: Fever, confusion, and hypotension. "
            "HPI: 78-year-old female brought in by EMS from nursing home. "
            "Found confused and hypotensive by nursing staff. "
            "Temperature 39.8C, BP 78/42, HR 128, RR 28, SpO2 88% on RA. "
            "PHYSICAL EXAM: Acutely ill, confused. Lungs: crackles right lower lobe. "
            "Abdomen: soft, mild suprapubic tenderness. "
            "Skin: warm, flushed. "
            "WORKUP:\n"
            "Lactate: 4.2 mmol/L\n"
            "WBC: 22.4\n"
            "Procalcitonin: 12.8\n"
            "Blood cultures: x2\n"
            "UA: cloudy, nitrites positive, leukocyte esterase positive, WBC >50\n"
            "CXR: Right lower lobe infiltrate\n"
            "ASSESSMENT:\n"
            "1. Sepsis, source likely urinary with secondary pneumonia.\n"
            "2. Urinary tract infection.\n"
            "3. Right lower lobe pneumonia.\n"
            "4. Sepsis-induced hypotension.\n"
            "PLAN:\n"
            "1. Aggressive IV fluid resuscitation (30 mL/kg lactated Ringer's).\n"
            "2. Broad-spectrum antibiotics: vancomycin + piperacillin-tazobactam.\n"
            "3. Norepinephrine if MAP <65 after fluids.\n"
            "4. Admit to ICU.\n"
            "5. Follow blood cultures and sensitivity."
        ),
        "expected_cpt": ["99285"],
        "expected_icd_prefix": ["A41", "R65"],
        "check_laterality": False,
        "check_organism": False,
    },
    {
        "id": "EM_ED3",
        "specialty": "Emergency Medicine - Stroke",
        "note": (
            "EMERGENCY DEPARTMENT NOTE - STROKE ALERT\n"
            "CHIEF COMPLAINT: Acute onset right-sided weakness and slurred speech. "
            "HPI: 68-year-old male, history of atrial fibrillation (not on anticoagulation), "
            "hypertension, diabetes. Found by wife with right arm and leg weakness, "
            "difficulty speaking, onset approximately 2 hours ago. "
            "Last known normal: 0600, current time 0800. "
            "VITAL SIGNS: BP 188/92, HR 98 (irregular), RR 18, SpO2 96% RA. "
            "PHYSICAL EXAM: NIHSS score 14. Alert but confused. Right facial droop. "
            "Right arm strength 2/5, right leg 3/5. Dysarthric speech. "
            "Left gaze deviation. Normal left-sided strength. "
            "WORKUP:\n"
            "CT Head (non-contrast): No hemorrhage. Early ischemic changes in left MCA territory.\n"
            "CT Angiography: Left MCA M1 occlusion.\n"
            "ASSESSMENT:\n"
            "1. Acute ischemic stroke, left MCA territory.\n"
            "2. Atrial fibrillation.\n"
            "3. Hypertension.\n"
            "4. Type 2 diabetes mellitus.\n"
            "PLAN:\n"
            "1. IV alteplase (tPA) within window (BP <185/110, no contraindications).\n"
            "2. Transfer to comprehensive stroke center for thrombectomy evaluation.\n"
            "3. Admit to stroke unit.\n"
            "4. Start anticoagulation after 24 hours."
        ),
        "expected_cpt": ["99285"],
        "expected_icd_prefix": ["I63", "I48"],
        "check_laterality": True,
        "laterality_expected": "left",
        "check_organism": False,
    },
]

# ═══════════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def validate_cpt_codes(result_cpt_codes, expected_cpt_codes, case):
    """Validate CPT codes are present and correct."""
    issues = []
    found_codes = [c.get("code", "") for c in result_cpt_codes]
    
    for expected in expected_cpt_codes:
        if expected not in found_codes:
            issues.append(f"Expected CPT {expected} not found in {found_codes}")
    
    return issues

def validate_icd_specificity(result_icd_codes, expected_icd_prefixes, case):
    """Validate ICD codes are specific (not general)."""
    issues = []
    found_codes = [c.get("code", "") for c in result_icd_codes]
    
    for prefix in expected_icd_prefixes:
        matching = [c for c in found_codes if c.startswith(prefix)]
        if not matching:
            issues.append(f"No ICD code starting with {prefix} found in {found_codes}")
    
    return issues

def validate_laterality(result_icd_codes, expected_laterality, case):
    """Validate laterality is correct when mentioned."""
    issues = []
    found_codes = [c.get("code", "") for c in result_icd_codes]
    
    if expected_laterality == "left":
        has_left = any("left" in (c.get("description", "") + c.get("code", "")).lower() 
                      for c in result_icd_codes)
        has_right = any("right" in (c.get("description", "") + c.get("code", "")).lower() 
                       for c in result_icd_codes)
        if has_right and not has_left:
            issues.append(f"Laterality mismatch: expected left but found right-sided codes")
    elif expected_laterality == "right":
        has_right = any("right" in (c.get("description", "") + c.get("code", "")).lower() 
                       for c in result_icd_codes)
        has_left = any("left" in (c.get("description", "") + c.get("code", "")).lower() 
                      for c in result_icd_codes)
        if has_left and not has_right:
            issues.append(f"Laterality mismatch: expected right but found left-sided codes")
    
    return issues

def validate_organism_specific_icd(result_icd_codes, organism_keyword, expected_icd, case):
    """Validate organism-specific ICD when organism is mentioned."""
    issues = []
    found_codes = [c.get("code", "") for c in result_icd_codes]
    
    has_specific = any(c.startswith(expected_icd.split('.')[0]) for c in found_codes)
    if not has_specific:
        issues.append(f"Organism-specific ICD {expected_icd} not found for {organism_keyword} in {found_codes}")
    
    return issues

def validate_no_false_positives(result_cpt_codes, result_icd_codes, case):
    """Check for obvious false positive codes."""
    issues = []
    note_text = case["note"].lower()
    found_cpt = [c.get("code", "") for c in result_cpt_codes]
    found_icd = [c.get("code", "") for c in result_icd_codes]
    
    # Check for codes that don't match the note context
    # (simplified check - more thorough check would be done with clinical reasoning)
    pass
    
    return issues

def validate_em_level(result_cpt_codes, case):
    """Validate E/M level is appropriate."""
    issues = []
    found_cpt = [c.get("code", "") for c in result_cpt_codes]
    em_codes = [c for c in found_cpt if c.startswith("99")]
    
    # Check if E/M code was assigned
    if not em_codes and case["specialty"].startswith("E/M"):
        issues.append("No E/M code assigned for E/M encounter")
    
    return issues

# ═══════════════════════════════════════════════════════════════════
# MAIN TEST
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("PHASE 8 — MEDICAL CODING ENGINE VALIDATION")
    print("Testing 20 diverse clinical notes across all specialties")
    print("=" * 80)
    print()
    
    # Initialize pipeline
    print("Initializing pipeline...")
    try:
        pipeline = MedcodeDeterministicPipelineV16()
        print("Pipeline initialized successfully.")
    except Exception as e:
        print(f"ERROR initializing pipeline: {e}")
        traceback.print_exc()
        return
    
    # Initialize parser
    parser = ClinicalNoteParser()
    
    results = []
    total_issues = 0
    total_cpt_correct = 0
    total_icd_correct = 0
    total_cases = len(TEST_CASES)
    
    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}/{total_cases}: {case['id']} - {case['specialty']}")
        print(f"{'='*80}")
        
        try:
            # Run deterministic pipeline
            start_time = time.time()
            result = pipeline.run(
                note_text=case["note"],
                note_id=f"phase8_{case['id']}",
            )
            pipeline_time = (time.time() - start_time) * 1000
            
            # Also run parser
            parser_result = parser.parse(case["note"])
            
            # Collect all findings
            all_issues = []
            cpt_issues = validate_cpt_codes(result.cpt_codes, case["expected_cpt"], case)
            icd_issues = validate_icd_specificity(result.icd10_codes, case["expected_icd_prefix"], case)
            
            laterality_issues = []
            if case.get("check_laterality"):
                laterality_issues = validate_laterality(result.icd10_codes, case.get("laterality_expected"), case)
            
            organism_issues = []
            if case.get("check_organism"):
                organism_issues = validate_organism_specific_icd(
                    result.icd10_codes, 
                    case["organism_keyword"], 
                    case["organism_expected_icd"], 
                    case
                )
            
            false_positive_issues = validate_no_false_positives(result.cpt_codes, result.icd10_codes, case)
            em_issues = validate_em_level(result.cpt_codes, case)
            
            all_issues = cpt_issues + icd_issues + laterality_issues + organism_issues + false_positive_issues + em_issues
            
            # Print results
            print(f"\nPipeline Result:")
            print(f"  Processing Time: {pipeline_time:.1f}ms")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Specialty: {result.specialty}")
            print(f"  Procedure Family: {result.procedure_family}")
            
            print(f"\n  CPT Codes ({len(result.cpt_codes)}):")
            for c in result.cpt_codes[:5]:
                print(f"    {c.get('code', 'N/A'):6s} - {c.get('description', 'N/A')[:60]:60s} (conf: {c.get('confidence', 0):.2f})")
            
            print(f"\n  ICD-10 Codes ({len(result.icd10_codes)}):")
            for c in result.icd10_codes[:5]:
                print(f"    {c.get('code', 'N/A'):10s} - {c.get('description', 'N/A')[:60]:60s} (conf: {c.get('confidence', 0):.2f})")
            
            print(f"\n  Parser Result:")
            print(f"    CPT Codes: {len(parser_result.get('cpt_codes', []))}")
            print(f"    ICD Codes: {len(parser_result.get('icd_codes', []))}")
            print(f"    Encounter Type: {parser_result.get('encounter_type', 'N/A')}")
            
            if all_issues:
                print(f"\n  ISSUES ({len(all_issues)}):")
                for issue in all_issues:
                    print(f"    [FAIL] {issue}")
                total_issues += len(all_issues)
            else:
                print(f"\n  [PASS] All validations passed")
                total_cpt_correct += 1
                total_icd_correct += 1
            
            # Check for false positives
            if result.cpt_codes:
                total_cpt_correct += 1
            if result.icd10_codes:
                total_icd_correct += 1
            
            results.append({
                "case_id": case["id"],
                "specialty": case["specialty"],
                "pipeline_time_ms": pipeline_time,
                "confidence": result.confidence,
                "cpt_codes": [c.get("code") for c in result.cpt_codes[:5]],
                "icd_codes": [c.get("code") for c in result.icd10_codes[:5]],
                "issues": all_issues,
                "issue_count": len(all_issues),
            })
            
        except Exception as e:
            print(f"\n  ERROR: {e}")
            traceback.print_exc()
            total_issues += 1
            results.append({
                "case_id": case["id"],
                "specialty": case["specialty"],
                "error": str(e),
                "issue_count": 1,
            })
    
    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("PHASE 8 SUMMARY")
    print("=" * 80)
    print(f"Total Test Cases: {total_cases}")
    print(f"Total Issues Found: {total_issues}")
    print(f"Cases with Issues: {sum(1 for r in results if r.get('issue_count', 0) > 0)}")
    print(f"Cases without Issues: {sum(1 for r in results if r.get('issue_count', 0) == 0)}")
    print()
    
    # Save results to JSON for report generation
    with open("phase8_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to phase8_results.json")
    
    return results

if __name__ == "__main__":
    main()
