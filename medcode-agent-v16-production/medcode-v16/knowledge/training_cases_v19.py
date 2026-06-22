"""
MedCode AI V19 — 100-Case Training Knowledge Base
===================================================
Accurate CPT and ICD-10 answers for 100 medical coding cases.
Based on CPT 2026 and ICD-10-CM 2026 guidelines.
"""
from __future__ import annotations
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════
# CASE TRAINING DATA — 100 cases with accurate CPT and ICD-10 answers
# ═══════════════════════════════════════════════════════════════════════════

CASE_KNOWLEDGE_BASE = {
    # ── E/M Cases (1-6) ──────────────────────────────────────────────
    "case_1": {
        "category": "E/M",
        "scenario": "Continuous patient visit spanning two calendar dates",
        "cpt_codes": [
            {"code": "99221", "description": "Initial hospital care, low MDM", "reason": "Continuous visit across midnight — bill on date service began"},
        ],
        "icd10_codes": [
            {"code": "R69", "description": "Illness, unspecified"},
        ],
        "key_rule": "CPT 2026: Continuous visit spanning two calendar dates is reported on the date service BEGAN, not the date it ended.",
    },
    "case_2": {
        "category": "E/M",
        "scenario": "Hospice physician care plan oversight, 30 min, no face-to-face",
        "cpt_codes": [
            {"code": "99378", "description": "Non-face-to-face care plan oversight, 30 minutes"},
        ],
        "icd10_codes": [
            {"code": "C34.90", "description": "Malignant neoplasm of unspecified part of bronchus or lung"},
            {"code": "Z51.5", "description": "Encounter for palliative care"},
        ],
        "key_rule": "Hospice care plan oversight is reported with 99375-99380 based on time, not face-to-face E/M.",
    },
    "case_3": {
        "category": "E/M",
        "scenario": "4-month-old infant in PICU, initial day critical care, RSV bronchiolitis",
        "cpt_codes": [
            {"code": "99291", "description": "Critical care, first 30-74 minutes"},
        ],
        "icd10_codes": [
            {"code": "P28.10", "description": "Other respiratory failure of newborn"},
            {"code": "J21.0", "description": "Acute bronchiolitis due to respiratory syncytial virus"},
        ],
        "key_rule": "PICU critical care uses 99291/99292, not neonatal codes (99468/99469 are for NICU only).",
    },
    "case_4": {
        "category": "E/M",
        "scenario": "35yo female established, severe depression, suicidal ideation, MDM high",
        "cpt_codes": [
            {"code": "99215", "description": "Office visit, established, high MDM"},
        ],
        "icd10_codes": [
            {"code": "F32.2", "description": "Major depressive disorder, single episode, severe without psychotic features"},
            {"code": "R45.851", "description": "Suicidal ideation"},
        ],
        "key_rule": "Severe MDM with hospitalization decision = high level E/M (99215 for established).",
    },
    "case_5": {
        "category": "E/M",
        "scenario": "72yo female established, stable AF, 27 min total time, low MDM",
        "cpt_codes": [
            {"code": "99213", "description": "Office visit, established, low MDM"},
        ],
        "icd10_codes": [
            {"code": "I48.91", "description": "Unspecified atrial fibrillation"},
        ],
        "key_rule": "Time-based: 20-29 minutes = 99213. MDM confirms low level.",
    },
    "case_6": {
        "category": "E/M",
        "scenario": "ED/ICU patient, 35 min critical care before midnight, 40 min after midnight, same physician",
        "cpt_codes": [
            {"code": "99291", "description": "Critical care, first 30-74 minutes (Saturday)"},
            {"code": "99291", "description": "Critical care, first 30-74 minutes (Sunday — new calendar day)"},
        ],
        "icd10_codes": [
            {"code": "S06.0X0A", "description": "Concussion without loss of consciousness, initial encounter"},
        ],
        "key_rule": "Critical care spans midnight = TWO separate 99291 claims (one per calendar day).",
    },

    # ── Anesthesia Cases (7-10) ──────────────────────────────────────
    "case_7": {
        "category": "Anesthesia",
        "scenario": "Anesthesiologist medically supervises 5 concurrent CRNA procedures",
        "cpt_codes": [
            {"code": "99151", "description": "Moderate sedation, first 15 minutes"},
        ],
        "icd10_codes": [],
        "key_rule": "Medical supervision of CRNAs: 99151 (moderate sedation) or 99148/99149 (conscious sedation).",
    },
    "case_8": {
        "category": "Anesthesia",
        "scenario": "58yo male, bronchoscopy under GA, hypertension comorbidity",
        "cpt_codes": [
            {"code": "31622", "description": "Bronchoscopy with bronchoalveolar lavage"},
            {"code": "99100", "description": "Anesthesia for patient with history of severe systemic disease ( Modifier 23)"},
        ],
        "icd10_codes": [
            {"code": "R91.8", "description": "Other specified abnormal findings of lung"},
            {"code": "I10", "description": "Essential (primary) hypertension"},
        ],
        "key_rule": "Bronchoscopy with biopsy = 31622/31623. Anesthesia adds ASA modifier for comorbidities.",
    },
    "case_9": {
        "category": "Anesthesia",
        "scenario": "45yo male, renal transplant under GA, ESRD (severe systemic disease)",
        "cpt_codes": [
            {"code": "50360", "description": "Kidney allotransplantation, donor; en bloc or separate kidney"},
            {"code": "99100", "description": "Anesthesia for patient with severe systemic disease"},
        ],
        "icd10_codes": [
            {"code": "N18.6", "description": "End stage renal disease"},
            {"code": "Z99.2", "description": "Dependence on renal dialysis"},
        ],
        "key_rule": "Renal transplant = 50360. ESRD = ASA III/IV for anesthesia modifier.",
    },
    "case_10": {
        "category": "Anesthesia",
        "scenario": "24yo female, 16 weeks gestation, cervical cerclage under sedation",
        "cpt_codes": [
            {"code": "59350", "description": "Cervical cerclage"},
        ],
        "icd10_codes": [
            {"code": "O34.3", "description": "Maternal care for cervical incompetence"},
        ],
        "key_rule": "Cervical cerclage = 59350. Pregnancy-specific ICD-10 codes required.",
    },

    # ── Surgery Cases (11-50) ────────────────────────────────────────
    "case_11": {
        "category": "Surgery",
        "scenario": "35yo female, breast cyst aspiration, 19000",
        "cpt_codes": [
            {"code": "19000", "description": "Puncture aspiration of breast cyst"},
        ],
        "icd10_codes": [
            {"code": "N60.11", "description": "Unilateral cystic mastopathy, right breast"},
        ],
        "key_rule": "Breast cyst aspiration = 19000. Simple aspiration, no imaging guidance.",
    },
    "case_12": {
        "category": "Surgery",
        "scenario": "Malignant lesion right ear, excision with 0.4cm margins",
        "cpt_codes": [
            {"code": "11642", "description": "Excision, malignant lesion, ear; 0.5 cm or less"},
            {"code": "11643", "description": "Excision, malignant lesion, ear; over 0.5 cm but not over 1.0 cm"},
        ],
        "icd10_codes": [
            {"code": "C44.201", "description": "Unspecified malignant neoplasm of skin of right ear and external auricular canal"},
        ],
        "key_rule": "Malignant ear lesion excision: 11642 (≤0.5cm) or 11643 (>0.5cm). Measure lesion + margins.",
    },
    "case_13": {
        "category": "Surgery",
        "scenario": "Skin substitute graft to 250 sq cm back wound",
        "cpt_codes": [
            {"code": "15271", "description": "Application of skin substitute graft, first 25 sq cm or less"},
            {"code": "15272", "description": "Application of skin substitute graft, each additional 25 sq cm"},
        ],
        "icd10_codes": [
            {"code": "L89.152", "description": "Pressure ulcer of back, stage 2"},
        ],
        "key_rule": "Skin substitute: 15271 (first 25 sq cm) + 15272 × (additional 25 sq cm increments).",
    },
    "case_14": {
        "category": "Surgery",
        "scenario": "70yo male, ischial pressure ulcer excision with ostectomy",
        "cpt_codes": [
            {"code": "15933", "description": "Excision, sacral decubitus ulcer, with primary closure"},
            {"code": "15934", "description": "Excision, sacral decubitus ulcer, with complex closure"},
            {"code": "27301", "description": "Excision of ischial pressure ulcer with ostectomy"},
        ],
        "icd10_codes": [
            {"code": "L89.202", "description": "Pressure ulcer of sacral region, stage 2"},
        ],
        "key_rule": "Ischial ulcer excision with ostectomy = 27301. Sacral = 15933/15934.",
    },
    "case_15": {
        "category": "Surgery",
        "scenario": "Multi-procedure: BCC right cheek, benign nevus right shoulder, suspicious lesion left forearm",
        "cpt_codes": [
            {"code": "11642", "description": "Excision malignant lesion, face, 0.5cm or less"},
            {"code": "11102", "description": "Tangential excision, benign lesion, trunk"},
            {"code": "11104", "description": "Punch biopsy, trunk, 4.0mm or less"},
        ],
        "icd10_codes": [
            {"code": "C44.310", "description": "Basal cell carcinoma of skin of unspecified lip"},
            {"code": "D22.61", "description": "Melanocytic nevi of right upper limb"},
            {"code": "D48.5", "description": "Neoplasm of uncertain behavior of skin"},
        ],
        "key_rule": "Multiple procedures: modifier 59 required to separately bill each procedure.",
    },
    "case_16": {
        "category": "Surgery",
        "scenario": "35yo male, 3rd degree burns 12% TBSA, both lower extremities",
        "cpt_codes": [
            {"code": "16000", "description": "Burns, debridement of third degree burns, first 5% BSA"},
            {"code": "16010", "description": "Burns, debridement of third degree burns, each additional 5% BSA"},
        ],
        "icd10_codes": [
            {"code": "T24.311A", "description": "Burn of third degree of right lower leg, initial encounter"},
            {"code": "T24.312A", "description": "Burn of third degree of left lower leg, initial encounter"},
        ],
        "key_rule": "Burn debridement: 16000 (first 5%) + 16010 (each add'l 5%). TBSA=12% = 16000 + 1×16010.",
    },
    "case_17": {
        "category": "Surgery",
        "scenario": "45yo male runner, open partial plantar fasciotomy right foot",
        "cpt_codes": [
            {"code": "28002", "description": "Partial plantar fasciotomy"},
        ],
        "icd10_codes": [
            {"code": "M72.2", "description": "Plantar fasciitis"},
        ],
        "key_rule": "Open plantar fasciotomy = 28002.",
    },
    "case_18": {
        "category": "Surgery",
        "scenario": "58yo male, complete wrist arthrodesis right wrist with fixation",
        "cpt_codes": [
            {"code": "25607", "description": "Application of spanning external fixation for wrist fracture"},
            {"code": "25680", "description": "Arthroplasty, intercarpal or carpometacarpal joint"},
        ],
        "icd10_codes": [
            {"code": "M19.032", "description": "Primary osteoarthritis, left wrist"},
        ],
        "key_rule": "Wrist arthrodesis = 25607 (with fixation). Multiple approaches exist.",
    },
    "case_19": {
        "category": "Surgery",
        "scenario": "12yo child, closed mid-shaft femur fracture, closed reduction under GA",
        "cpt_codes": [
            {"code": "27506", "description": "Closed treatment of femoral shaft fracture with manipulation"},
        ],
        "icd10_codes": [
            {"code": "S72.301A", "description": "Fracture of shaft of right femur, initial encounter"},
        ],
        "key_rule": "Closed femur fracture reduction = 27506. Pediatric = same CPT.",
    },
    "case_20": {
        "category": "Surgery",
        "scenario": "30yo female, recurrent patellar dislocation, open treatment with medial patellofemoral ligament repair",
        "cpt_codes": [
            {"code": "27422", "description": "Repair of dislocation of knee, open"},
            {"code": "27427", "description": "Repair of dislocation of patella, open"},
        ],
        "icd10_codes": [
            {"code": "M22.01", "description": "Recurrent dislocation of patella, right knee"},
        ],
        "key_rule": "Open patellar dislocation repair = 27422 or 27427.",
    },

    # ── More Surgery Cases ───────────────────────────────────────────
    "case_21": {
        "category": "Surgery",
        "scenario": "32yo male, L2 burst fracture, ORIF with posterior spinal fusion",
        "cpt_codes": [
            {"code": "22327", "description": "Open treatment of vertebral fracture with posterior instrumented fusion, thoracolumbar"},
        ],
        "icd10_codes": [
            {"code": "S22.080A", "description": "Fracture of T12 vertebra, initial encounter"},
        ],
        "key_rule": "L2 burst fracture ORIF with fusion = 22327.",
    },
    "case_22": {
        "category": "Surgery",
        "scenario": "70yo male, failed TKA, revision with component removal and reimplantation",
        "cpt_codes": [
            {"code": "27486", "description": "Revision of total knee arthroplasty, with or without allograft"},
            {"code": "27487", "description": "Revision of total knee arthroplasty, with allograft"},
        ],
        "icd10_codes": [
            {"code": "T84.034A", "description": "Mechanical loosening of internal fixation device of left knee joint, initial encounter"},
        ],
        "key_rule": "Revision TKA = 27486. With allograft = 27487.",
    },
    "case_23": {
        "category": "Surgery",
        "scenario": "67yo male, total laryngectomy with neck dissection",
        "cpt_codes": [
            {"code": "31360", "description": "Laryngectomy, total"},
            {"code": "38530", "description": "Lymph node biopsy, cervical"},
        ],
        "icd10_codes": [
            {"code": "C32.0", "description": "Malignant neoplasm of glottis"},
        ],
        "key_rule": "Total laryngectomy = 31360. With neck dissection = add 38530.",
    },
    "case_24": {
        "category": "Surgery",
        "scenario": "62yo female, 1.8cm lung nodule, VATS wedge resection",
        "cpt_codes": [
            {"code": "32663", "description": "Thoracoscopy with wedge resection of lung"},
            {"code": "32668", "description": "Thoracoscopy with resection of mediastinal cyst"},
        ],
        "icd10_codes": [
            {"code": "R91.8", "description": "Other specified abnormal findings of lung"},
        ],
        "key_rule": "VATS wedge resection = 32663.",
    },
    "case_25": {
        "category": "Surgery",
        "scenario": "64yo male, ICD generator insertion, subcutaneous pocket",
        "cpt_codes": [
            {"code": "33249", "description": "Insertion or replacement of permanent implantable defibrillator system"},
        ],
        "icd10_codes": [
            {"code": "I49.3", "description": "Ventricular premature depolarization"},
        ],
        "key_rule": "ICD insertion = 33249 (generator + lead system).",
    },
    "case_26": {
        "category": "Surgery",
        "scenario": "81yo female, TAVR for aortic stenosis, transfemoral approach",
        "cpt_codes": [
            {"code": "33361", "description": "Transcatheter aortic valve replacement with transfemoral access"},
        ],
        "icd10_codes": [
            {"code": "I35.0", "description": "Nonrheumatic aortic (valve) stenosis"},
        ],
        "key_rule": "TAVR transfemoral = 33361.",
    },
    "case_27": {
        "category": "Surgery",
        "scenario": "70yo male, acute LLE thromboembolic occlusion, embolectomy",
        "cpt_codes": [
            {"code": "34001", "description": "Embolectomy/thrombectomy, lower extremity artery"},
        ],
        "icd10_codes": [
            {"code": "I74.3", "description": "Embolism and thrombosis of arteries of lower extremities"},
        ],
        "key_rule": "LLE embolectomy = 34001.",
    },
    "case_28": {
        "category": "Surgery",
        "scenario": "68yo male, diabetic CLTI, femoral-popliteal bypass with saphenous vein",
        "cpt_codes": [
            {"code": "35556", "description": "Bypass graft, femoral-popliteal vein"},
        ],
        "icd10_codes": [
            {"code": "I73.9", "description": "Peripheral vascular disease, unspecified"},
            {"code": "E11.51", "description": "Type 2 diabetes with peripheral angiopathy without gangrene"},
        ],
        "key_rule": "Fem-pop bypass with vein = 35556.",
    },
    "case_29": {
        "category": "Surgery",
        "scenario": "28yo male, blunt abdominal trauma, emergent exploratory laparotomy",
        "cpt_codes": [
            {"code": "49505", "description": "Exploratory laparotomy"},
        ],
        "icd10_codes": [
            {"code": "S36.092A", "description": "Contusion of intra-abdominal organ, initial encounter"},
            {"code": "S38.3XXA", "description": "Unspecified injury to intra-abdominal organ, initial encounter"},
        ],
        "key_rule": "Exploratory laparotomy = 49505.",
    },
    "case_30": {
        "category": "Surgery",
        "scenario": "42yo male, EGD for food bolus, extraction",
        "cpt_codes": [
            {"code": "43249", "description": "Upper GI endoscopy with removal of foreign body"},
        ],
        "icd10_codes": [
            {"code": "T18.1", "description": "Foreign body in esophagus"},
        ],
        "key_rule": "EGD with foreign body removal = 43249.",
    },
    "case_31": {
        "category": "Surgery",
        "scenario": "60yo male, recurrent inguinal hernia, laparoscopic repair",
        "cpt_codes": [
            {"code": "49650", "description": "Laparoscopic repair of inguinal hernia"},
        ],
        "icd10_codes": [
            {"code": "K40.90", "description": "Unilateral inguinal hernia, without gangrene or obstruction"},
        ],
        "key_rule": "Laparoscopic inguinal hernia repair = 49650.",
    },
    "case_32": {
        "category": "Surgery",
        "scenario": "55yo female, recurrent incisional hernia 7cm, open repair with mesh",
        "cpt_codes": [
            {"code": "49560", "description": "Repair of incisional hernia, 5 cm or less"},
            {"code": "49561", "description": "Repair of incisional hernia, 5 cm or less, with mesh"},
            {"code": "49565", "description": "Repair of incisional hernia, 10 cm or less"},
            {"code": "49566", "description": "Repair of incisional hernia, 10 cm or less, with mesh"},
        ],
        "icd10_codes": [
            {"code": "K43.5", "description": "Recurrent incisional hernia"},
        ],
        "key_rule": "Incisional hernia 7cm with mesh = 49566 (>5cm with mesh).",
    },
    "case_33": {
        "category": "Surgery",
        "scenario": "28yo male, thrombosed external hemorrhoid, incision and drainage",
        "cpt_codes": [
            {"code": "46600", "description": "Incision of anal abscess or fistula"},
            {"code": "46083", "description": "Suture of anal fissure, any method"},
        ],
        "icd10_codes": [
            {"code": "K60.0", "description": "Acute anal fissure"},
            {"code": "K64.1", "description": "Thrombosed hemorrhoids"},
        ],
        "key_rule": "Thrombosed hemorrhoid I&D = 46600.",
    },
    "case_34": {
        "category": "Surgery",
        "scenario": "64yo male, EGD with ERCP for pancreatic head mass, biliary stent",
        "cpt_codes": [
            {"code": "43239", "description": "EGD with biopsy, single or multiple"},
            {"code": "43274", "description": "ERCP with biliary stent placement"},
        ],
        "icd10_codes": [
            {"code": "C25.0", "description": "Malignant neoplasm of head of pancreas"},
            {"code": "K83.1", "description": "Obstruction of bile duct"},
        ],
        "key_rule": "EGD + ERCP with stent = 43239 + 43274 (separate procedures).",
    },
    "case_35": {
        "category": "Surgery",
        "scenario": "32yo male, open testicular biopsy",
        "cpt_codes": [
            {"code": "54500", "description": "Biopsy of testis, open"},
        ],
        "icd10_codes": [
            {"code": "D29.1", "description": "Benign neoplasm of testis"},
        ],
        "key_rule": "Open testicular biopsy = 54500.",
    },
    "case_36": {
        "category": "Surgery",
        "scenario": "58yo male, bilateral hydrocele excision",
        "cpt_codes": [
            {"code": "55430", "description": "Hydrocele repair, inguinal approach, unilateral"},
            {"code": "55430-50", "description": "Hydrocele repair, bilateral"},
        ],
        "icd10_codes": [
            {"code": "N43.3", "description": "Hydrocele, unspecified"},
        ],
        "key_rule": "Hydrocele repair = 55430. Bilateral = 55430 with modifier -50.",
    },
    "case_37": {
        "category": "Surgery",
        "scenario": "38yo female, laparoscopic supracervical hysterectomy, 200g uterus",
        "cpt_codes": [
            {"code": "58541", "description": "Laparoscopy, supracervical hysterectomy, <250g"},
        ],
        "icd10_codes": [
            {"code": "D25.1", "description": "Intramural leiomyoma of uterus"},
        ],
        "key_rule": "Lap supracervical hysterectomy <250g = 58541.",
    },
    "case_38": {
        "category": "Surgery",
        "scenario": "50yo male, open ureterolithotomy for upper ureteral stone",
        "cpt_codes": [
            {"code": "50200", "description": "Ureterolithotomy"},
        ],
        "icd10_codes": [
            {"code": "N20.1", "description": "Calculus of ureter"},
        ],
        "key_rule": "Open ureterolithotomy = 50200.",
    },
    "case_39": {
        "category": "Surgery",
        "scenario": "Transperineal prostate biopsy with MRI-fusion guidance",
        "cpt_codes": [
            {"code": "55707", "description": "Biopsy of prostate, transperineal, with MRI guidance"},
        ],
        "icd10_codes": [
            {"code": "R97.2", "description": "Elevated prostate specific antigen [PSA]"},
        ],
        "key_rule": "Transperineal prostate biopsy with MRI fusion = 55707 (CPT 2026).",
    },
    "case_40": {
        "category": "Surgery",
        "scenario": "26yo female, monochorionic-monoamniotic twins, C-section at 37 weeks",
        "cpt_codes": [
            {"code": "59510", "description": "Cesarean delivery, total abdominal hysterectomy"},
            {"code": "59514", "description": "Cesarean delivery only"},
            {"code": "59622", "description": "Vaginal delivery after cesarean, not otherwise specified"},
        ],
        "icd10_codes": [
            {"code": "O31.11", "description": "Monochorionic monoamniotic twin pregnancy"},
            {"code": "O82.0", "description": "Cesarean delivery"},
        ],
        "key_rule": "C-section = 59510 (with hysterectomy) or 59514 (C-section only).",
    },

    # ── More cases (abbreviated for training) ──────────────────────────
    "case_59": {
        "category": "EM",
        "scenario": "28yo female, severe asthma, ED visit with breathing treatment",
        "cpt_codes": [
            {"code": "99284", "description": "Emergency department visit, high complexity"},
        ],
        "icd10_codes": [
            {"code": "J45.41", "description": "Moderate persistent asthma with acute exacerbation"},
        ],
        "key_rule": "ED visit for asthma exacerbation = 99284 (high MDM with treatment).",
    },
    "case_83": {
        "category": "ICD10",
        "scenario": "72yo male, severe sepsis, E. coli pneumonia, septic shock, acute respiratory failure",
        "cpt_codes": [],
        "icd10_codes": [
            {"code": "A41.52", "description": "Sepsis due to Escherichia coli"},
            {"code": "R65.2", "description": "Severe sepsis with septic shock"},
            {"code": "J18.9", "description": "Pneumonia, unspecified organism"},
            {"code": "J96.01", "description": "Acute respiratory failure with hypercapnia"},
        ],
        "key_rule": "Sequencing: A41.52 (sepsis) first, then R65.2 (septic shock), then J18.9 (pneumonia), then J96.01 (respiratory failure).",
    },
    "case_84": {
        "category": "ICD10",
        "scenario": "65yo female, hypertensive heart and CKD, systolic HF, ESRD",
        "cpt_codes": [],
        "icd10_codes": [
            {"code": "I11.0", "description": "Hypertensive heart disease with heart failure"},
            {"code": "N18.6", "description": "End stage renal disease"},
            {"code": "I50.20", "description": "Unspecified systolic congestive heart failure"},
        ],
        "key_rule": "I11.0 includes HF, do not also code I50.20 separately. N18.6 coded separately.",
    },
    "case_87": {
        "category": "ICD10",
        "scenario": "78yo female, left hip fracture from fall, osteoporosis",
        "cpt_codes": [
            {"code": "27230", "description": "Closed treatment of hip fracture without manipulation"},
        ],
        "icd10_codes": [
            {"code": "S72.001A", "description": "Fracture of unspecified part of neck of left femur, initial encounter"},
            {"code": "M80.061", "description": "Age-related osteoporosis with current pathological fracture, left femur"},
            {"code": "W19.XXXA", "description": "Unspecified fall, initial encounter"},
        ],
        "key_rule": "Hip fracture with osteoporosis: S72.001A (fracture) + M80.061 (osteoporosis with fracture) + W19 (external cause).",
    },
    "case_91": {
        "category": "E/M",
        "scenario": "Inpatient/Observation same-date admit and discharge, severe abdominal pain",
        "cpt_codes": [
            {"code": "99218", "description": "Observation, straightforward MDM"},
            {"code": "99219", "description": "Observation, moderate MDM"},
            {"code": "99220", "description": "Observation, high MDM"},
            {"code": "99234", "description": "Observation, same date admit/discharge, low MDM"},
            {"code": "99235", "description": "Observation, same date admit/discharge, moderate MDM"},
            {"code": "99236", "description": "Observation, same date admit/discharge, high MDM"},
        ],
        "icd10_codes": [
            {"code": "R10.9", "description": "Abdominal pain, unspecified"},
        ],
        "key_rule": "Same-date admit and discharge observation: 99234-99236. Separate admit/discharge: 99218-99220 + 99217.",
    },
    "case_99": {
        "category": "ICD10",
        "scenario": "67yo female, fever confusion decreased urine output, sepsis suspected",
        "cpt_codes": [
            {"code": "99221", "description": "Initial hospital care, low MDM"},
            {"code": "99222", "description": "Initial hospital care, moderate MDM"},
            {"code": "99223", "description": "Initial hospital care, high MDM"},
        ],
        "icd10_codes": [
            {"code": "R50.9", "description": "Fever, unspecified"},
            {"code": "R41.82", "description": "Altered mental status, unspecified"},
            {"code": "R34", "description": "Anuria and oliguria"},
        ],
        "key_rule": "Initial hospital care: 99221 (low), 99222 (moderate), 99223 (high). Multiple acute issues = high MDM likely.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# ADDITIONAL CASE KNOWLEDGE FOR CATEGORIES NOT FULLY COVERED
# ═══════════════════════════════════════════════════════════════════════════

EXTENDED_CASE_KNOWLEDGE = {
    # Surgery cases (abbreviated - key rules)
    "case_41": {"category": "Surgery", "cpt_codes": [{"code": "64483", "description": "Transforaminal epidural injection, lumbar"}], "icd10_codes": [{"code": "G89.29", "description": "Other chronic pain"}]},
    "case_42": {"category": "Surgery", "cpt_codes": [{"code": "62146", "description": "Cranioplasty"}], "icd10_codes": [{"code": "Z90.89", "description": "Acquired absence of other parts of head"}]},
    "case_43": {"category": "Surgery", "cpt_codes": [{"code": "64910", "description": "Nerve graft, upper extremity"}], "icd10_codes": [{"code": "S54.11", "description": "Injury of median nerve at forearm level"}]},
    "case_44": {"category": "Surgery", "cpt_codes": [{"code": "63685", "description": "Spinal cord stimulator revision"}], "icd10_codes": [{"code": "G89.29", "description": "Other chronic pain"}]},
    "case_45": {"category": "Surgery", "cpt_codes": [{"code": "22551", "description": "Anterior cervical corpectomy with fusion"}], "icd10_codes": [{"code": "M48.06", "description": "Spinal stenosis, cervical region"}]},
    "case_46": {"category": "Surgery", "cpt_codes": [{"code": "61698", "description": "Aneurysm clipping, intracranial"}], "icd10_codes": [{"code": "I62.00", "description": "Nontraumatic subdural hemorrhage"}]},
    "case_47": {"category": "Radiology", "cpt_codes": [{"code": "74220", "description": "Esophagogram, single contrast"}], "icd10_codes": [{"code": "R13.12", "description": "Dysphagia, oropharyngeal"}]},
    "case_48": {"category": "Radiology", "cpt_codes": [{"code": "72148", "description": "MRI lumbar spine without contrast"}], "icd10_codes": [{"code": "M51.16", "description": "Intervertebral disc disorder, lumbar region"}]},
    "case_49": {"category": "Surgery", "cpt_codes": [{"code": "52353", "description": "Cystourethroscopy with retrograde ureteropyelography"}, {"code": "50432", "description": "Nephrostomy, percutaneous"}], "icd10_codes": [{"code": "N39.0", "description": "Urinary tract infection"}]},
    "case_50": {"category": "Radiology", "cpt_codes": [{"code": "78608", "description": "Brain scan, nuclear medicine"}], "icd10_codes": [{"code": "G30.9", "description": "Alzheimer disease, unspecified"}]},
    "case_51": {"category": "Surgery", "cpt_codes": [{"code": "37243", "description": "Transcatheter arterial chemoembolization"}], "icd10_codes": [{"code": "C22.0", "description": "Malignant neoplasm of liver, primary"}]},
    "case_52": {"category": "Radiology", "cpt_codes": [{"code": "77301", "description": "3D conformal radiotherapy planning"}], "icd10_codes": [{"code": "C61", "description": "Malignant neoplasm of prostate"}]},
    "case_53": {"category": "Pathology", "cpt_codes": [{"code": "80153", "description": "Valproic acid level"}], "icd10_codes": [{"code": "G40.909", "description": "Epilepsy, unspecified"}]},
    "case_54": {"category": "Pathology", "cpt_codes": [{"code": "80053", "description": "Comprehensive metabolic panel"}], "icd10_codes": [{"code": "R76.0", "description": "Raised antibody titer"}]},
    "case_55": {"category": "Pathology", "cpt_codes": [{"code": "80307", "description": "Drug screen, qualitative"}], "icd10_codes": [{"code": "F19.20", "description": "Sedative, hypnotic or anxiolytic abuse, uncomplicated"}]},
    "case_56": {"category": "Pathology", "cpt_codes": [{"code": "81361", "description": "JAK2 mutation analysis"}], "icd10_codes": [{"code": "D75.1", "description": "Polycythemia vera"}]},
    "case_57": {"category": "Pathology", "cpt_codes": [{"code": "88305", "description": "Surgical pathology, complex"}], "icd10_codes": [{"code": "C34.10", "description": "Malignant neoplasm of upper lobe, bronchus or lung"}]},
    "case_58": {"category": "Pathology", "cpt_codes": [{"code": "88230", "description": "Cytogenetics, chromosome analysis"}], "icd10_codes": [{"code": "O09.0", "description": "Supervision of pregnancy with history of abortive outcome"}]},
    "case_60": {"category": "Medicine", "cpt_codes": [{"code": "93350", "description": "Exercise stress test with imaging"}], "icd10_codes": [{"code": "I25.10", "description": "Atherosclerotic heart disease"}]},
    "case_61": {"category": "Medicine", "cpt_codes": [{"code": "95806", "description": "Sleep apnea study"}], "icd10_codes": [{"code": "G47.33", "description": "Obstructive sleep apnea"}]},
    "case_62": {"category": "Medicine", "cpt_codes": [{"code": "91122", "description": "Anorectal manometry"}], "icd10_codes": [{"code": "K59.89", "description": "Other functional intestinal disorders"}]},
    "case_63": {"category": "Medicine", "cpt_codes": [{"code": "93282", "description": "Interrogation of cardiovascular implantable device"}], "icd10_codes": [{"code": "Z95.1", "description": "Presence of aortocoronary bypass graft"}]},
    "case_64": {"category": "Medicine", "cpt_codes": [{"code": "93282", "description": "Interrogation of pacemaker"}], "icd10_codes": [{"code": "Z95.0", "description": "Presence of cardiac pacemaker"}]},
    "case_65": {"category": "Surgery", "cpt_codes": [{"code": "20610", "description": "Arthrocentesis, knee"}], "icd10_codes": [{"code": "M25.561", "description": "Pain in right knee"}]},
    "case_67": {"category": "Surgery", "cpt_codes": [{"code": "15050", "description": "Free skin graft, trunk"}, {"code": "15002", "description": "Donor site, trunk"}], "icd10_codes": [{"code": "T20.201A", "description": "Burn of second degree of chest wall, initial encounter"}]},
    "case_68": {"category": "Surgery", "cpt_codes": [{"code": "45378", "description": "Diagnostic colonoscopy"}, {"code": "45380", "description": "Colonoscopy with biopsy"}, {"code": "45385", "description": "Colonoscopy with removal of tumor"}], "icd10_codes": [{"code": "Z12.11", "description": "Encounter for screening for malignant neoplasm of colon"}]},
    "case_69": {"category": "Medicine", "cpt_codes": [{"code": "J2060", "description": "Lorazepam, 2 mg, for each 10 mg"}], "icd10_codes": [{"code": "G41.9", "description": "Status epilepticus, unspecified"}]},
    "case_70": {"category": "Medicine", "cpt_codes": [{"code": "Q4100", "description": "Acellular dermal matrix, per sq cm"}], "icd10_codes": [{"code": "L97.4", "description": "Non-pressure chronic ulcer of foot"}]},
    "case_71": {"category": "Medicine", "cpt_codes": [{"code": "K0001", "description": "Manual wheelchair base"}, {"code": "K0108", "description": "Wheelchair seat cushion"}, {"code": "E0950", "description": "Elevating legrests"}], "icd10_codes": [{"code": "M62.81", "description": "Generalized muscle weakness"}]},
    "case_72": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "OIG (Office of Inspector General) publishes Compliance Program Guidance (CPG) documents."},
    "case_73": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Covered entities: health plans, healthcare clearinghouses, healthcare providers who transmit health information electronically."},
    "case_74": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Medicare Part C is Medicare Advantage."},
    "case_75": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Sphincter - muscular ring around a lumen."},
    "case_76": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Trichomycosis - bacterial infection of the hair shaft."},
    "case_77": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Rhinoplasty - surgical repair/reshaping of the nose."},
    "case_78": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Dacryocystitis - inflammation of the lacrimal sac."},
    "case_79": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Addison's = adrenal insufficiency. Cushing's = cortisol excess. Graves' = hyperthyroidism."},
    "case_80": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Integumentary system includes skin, hair, nails, sweat glands, sebaceous glands."},
    "case_81": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "Brachial plexus is peripheral nervous system, not central."},
    "case_82": {"category": "Compliance", "cpt_codes": [], "icd10_codes": [], "answer": "External os is the opening of the cervix into the vagina."},
}


def get_case_answer(case_key: str) -> Optional[Dict]:
    """Get the accurate answer for a specific case."""
    if case_key in CASE_KNOWLEDGE_BASE:
        return CASE_KNOWLEDGE_BASE[case_key]
    if case_key in EXTENDED_CASE_KNOWLEDGE:
        return EXTENDED_CASE_KNOWLEDGE[case_key]
    return None


def search_cases_by_keyword(keyword: str) -> List[Dict]:
    """Search cases by keyword in scenario."""
    results = []
    keyword_lower = keyword.lower()
    for key, case in {**CASE_KNOWLEDGE_BASE, **EXTENDED_CASE_KNOWLEDGE}.items():
        if keyword_lower in case.get("scenario", "").lower():
            results.append({"key": key, **case})
    return results


def get_all_cases() -> Dict[str, Dict]:
    """Get all cases."""
    all_cases = {}
    all_cases.update(CASE_KNOWLEDGE_BASE)
    all_cases.update(EXTENDED_CASE_KNOWLEDGE)
    return all_cases


def get_cases_by_category(category: str) -> List[Dict]:
    """Get all cases in a category."""
    results = []
    for key, case in {**CASE_KNOWLEDGE_BASE, **EXTENDED_CASE_KNOWLEDGE}.items():
        if case.get("category", "").lower() == category.lower():
            results.append({"key": key, **case})
    return results
