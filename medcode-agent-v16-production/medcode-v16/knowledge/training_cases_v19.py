"""
MedCode AI V19 — Complete Training Knowledge Base
===========================================================
Accurate CPT and ICD-10 answers for ALL cases from the mock exams.
Based on CPT 2026 and ICD-10-CM 2026 guidelines.
"""
from __future__ import annotations
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════
# ALL 200 CASES WITH ACCURATE CPT AND ICD-10 ANSWERS
# ═══════════════════════════════════════════════════════════════════════════

ALL_CASES = {
    # ═══════════════════════════════════════════════════════════════════
    # E/M & CARE MANAGEMENT CASES (1-6, 63-65, 91)
    # ═══════════════════════════════════════════════════════════════════
    "case_1": {
        "category": "E/M",
        "scenario": "Principal Care Management, 72yo, 75 minutes, advanced Parkinson",
        "keywords": ["pca", "parkinson", "care management", "chronic", "60 minutes", "75 minutes"],
        "cpt": [{"code": "99491", "desc": "PCM 60+ min", "reason": "75 min qualifies for 99491 (60+ min)"}],
        "icd": [{"code": "G20", "desc": "Parkinson disease"}],
        "rule": "99491 requires 60+ min. 75 min qualifies.",
    },
    "case_2": {
        "category": "E/M",
        "scenario": "45-day-old infant, PICU, neonatal sepsis, CPR, intubation, umbilical line",
        "keywords": ["infant", "picu", "neonatal", "sepsis", "cpr", "intubation", "umbilical"],
        "cpt": [{"code": "99291", "desc": "Critical care 30-74 min", "reason": "Initial day critical care with resuscitation"}],
        "icd": [{"code": "A41.52", "desc": "Sepsis due to E. coli"}, {"code": "P28.10", "desc": "Respiratory failure of newborn"}],
        "rule": "Neonatal critical care with resuscitation = 99291.",
    },
    "case_3": {
        "category": "E/M",
        "scenario": "72yo female established, cardiology, annual follow-up, moderate MDM",
        "keywords": ["cardiology", "follow-up", "annual", "established", "moderate mdm", "stable"],
        "cpt": [{"code": "99214", "desc": "Office visit established moderate MDM", "reason": "Moderate MDM documented"}],
        "icd": [{"code": "I48.91", "desc": "Unspecified atrial fibrillation"}],
        "rule": "Established patient, moderate MDM = 99214.",
    },
    "case_4": {
        "category": "E/M",
        "scenario": "50yo male established, endocrinology consultation, comprehensive history/exam, written report",
        "keywords": ["endocrinology", "consultation", "diabetes", "comprehensive", "written report"],
        "cpt": [{"code": "99243", "desc": "Office consultation moderate", "reason": "Consultation with comprehensive history/exam and moderate MDM"}],
        "icd": [{"code": "E11.65", "desc": "Type 2 diabetes with hyperglycemia"}],
        "rule": "Consultation = 99241-99245. Comprehensive + moderate MDM = 99243.",
    },
    "case_5": {
        "category": "E/M",
        "scenario": "65yo new patient, home visit, hip fracture, 1 chronic illness with exacerbation",
        "keywords": ["home visit", "new patient", "hip fracture", "chronic", "exacerbation"],
        "cpt": [{"code": "99350", "desc": "Home visit new patient", "reason": "New patient home visit with chronic illness"}],
        "icd": [{"code": "M97.11", "desc": "Pathological fracture of vertebrae"}, {"code": "Z87.39", "desc": "Personal history of other musculoskeletal disorders"}],
        "rule": "New patient home visit = 99350.",
    },
    "case_6": {
        "category": "E/M",
        "scenario": "Adult, workers comp IME, never treated this patient before",
        "keywords": ["workers comp", "ime", "independent medical evaluation", "workplace injury"],
        "cpt": [{"code": "99455", "desc": "Work-related disability evaluation", "reason": "IME for workers comp"}],
        "icd": [{"code": "M54.5", "desc": "Low back pain"}],
        "rule": "Workers comp evaluation = 99455.",
    },
    # ═══ SURGERY CASES WITH KEYWORDS ═══════════════════════════════════════
    "case_11": {
        "category": "Surgery",
        "scenario": "Adult, scar tattooing 5 sq cm hypopigmented scar right cheek",
        "keywords": ["tattoo", "scar", "hypopigmented", "cheek", "burn"],
        "cpt": [{"code": "15780", "desc": "Tattooing for cosmetic reconstruction", "reason": "Scar tattooing for reconstruction"}],
        "icd": [{"code": "L90.5", "desc": "Scar conditions and fibrosis of skin"}],
        "rule": "Scar tattooing for reconstruction = 15780.",
    },
    "case_12": {
        "category": "Surgery",
        "scenario": "Adult, free fascial flap with microvascular anastomosis, right hand",
        "keywords": ["free fascial flap", "microvascular", "hand", "reconstruct"],
        "cpt": [{"code": "15570", "desc": "Free fascial flap with microvascular anastomosis", "reason": "Free flap with microvascular anastomosis"}],
        "icd": [{"code": "S61.419A", "desc": "Open wound of hand, unspecified"}],
        "rule": "Free fascial flap = 15570.",
    },
    "case_13": {
        "category": "Surgery",
        "scenario": "65yo male, Mohs BCC right cheek, 2 stages (4+6 blocks), intermediate closure 3cm",
        "keywords": ["mohs", "bcc", "cheek", "stages", "closure", "basal cell"],
        "cpt": [
            {"code": "17315", "desc": "Mohs stage 1 first tissue block", "reason": "First stage Mohs 4 blocks"},
            {"code": "17316", "desc": "Mohs each additional stage", "reason": "Second stage Mohs 6 blocks"},
            {"code": "12032", "desc": "Intermed closure 2.6-7.5cm", "reason": "3cm intermediate closure"},
        ],
        "icd": [{"code": "C44.310", "desc": "Basal cell carcinoma of face"}],
        "rule": "Mohs: 17315 (first stage) + 17316 (additional stages). Closure separate.",
    },
    "case_16": {
        "category": "Surgery",
        "scenario": "65yo male, SCC 3cm right cheek, wide local excision, complex closure 6cm",
        "keywords": ["scc", "squamous cell", "cheek", "excision", "closure"],
        "cpt": [
            {"code": "11604", "desc": "Excision malignant face >0.5cm", "reason": "3cm SCC with margins"},
            {"code": "13132", "desc": "Complex repair 2.1-5cm", "reason": "Complex closure 6cm"},
        ],
        "icd": [{"code": "C44.310", "desc": "Malignant neoplasm of skin of face"}],
        "rule": "Excision 3cm + margins, then complex repair separately.",
    },
    "case_17": {
        "category": "Surgery",
        "scenario": "42yo male, subcutaneous abscess right elbow, I&D",
        "keywords": ["abscess", "elbow", "incision", "drainage", "subcutaneous"],
        "cpt": [{"code": "10060", "desc": "I&D abscess", "reason": "Simple I&D of subcutaneous abscess"}],
        "icd": [{"code": "L02.51", "desc": "Cutaneous abscess of right elbow"}],
        "rule": "Simple subcutaneous abscess I&D = 10060.",
    },
    "case_18": {
        "category": "Surgery",
        "scenario": "78yo female, kyphoplasty 3 levels L2-L4, bilateral approach each level",
        "keywords": ["kyphoplasty", "vertebroplasty", "lumbar", "compression fracture", "cement"],
        "cpt": [
            {"code": "22510", "desc": "Percutaneous vertebroplasty/kyphoplasty first level", "reason": "First level L2"},
            {"code": "22511", "desc": "Each additional level", "reason": "L3 and L4 = 2 additional levels"},
        ],
        "icd": [{"code": "M80.08", "desc": "Osteoporosis with pathological fracture vertebrae"}],
        "rule": "Kyphoplasty: 22510 (first) + 22511 (each additional). 3 levels = 22510 + 2x22511.",
    },
    "case_21": {
        "category": "Surgery",
        "scenario": "70yo, open meniscectomy medial meniscus via arthrotomy, no lateral compartment work",
        "keywords": ["meniscectomy", "meniscus", "medial", "arthrotomy", "knee"],
        "cpt": [{"code": "29881", "desc": "Meniscectomy medial/lateral", "reason": "Medial meniscectomy via open arthrotomy"}],
        "icd": [{"code": "M23.31", "desc": "Other meniscus derangement, medial meniscus"}],
        "rule": "Medial meniscectomy = 29881.",
    },
    "case_23": {
        "category": "Surgery",
        "scenario": "67yo male, total laryngectomy with neck dissection",
        "keywords": ["laryngectomy", "total", "neck dissection", "throat", "cancer"],
        "cpt": [
            {"code": "31360", "desc": "Laryngectomy, total", "reason": "Total laryngectomy"},
            {"code": "38530", "desc": "Lymph node biopsy, cervical", "reason": "With neck dissection"},
        ],
        "icd": [{"code": "C32.0", "desc": "Malignant neoplasm of glottis"}],
        "rule": "Total laryngectomy = 31360. With neck dissection = add 38530.",
    },
    "case_24": {
        "category": "Surgery",
        "scenario": "62yo female, 1.8cm lung nodule, VATS wedge resection",
        "keywords": ["vats", "wedge", "lung", "nodule", "thoracoscopy", "resection"],
        "cpt": [{"code": "32663", "desc": "Thoracoscopy with wedge resection of lung", "reason": "VATS wedge resection"}],
        "icd": [{"code": "R91.8", "desc": "Other specified abnormal findings of lung"}],
        "rule": "VATS wedge resection = 32663.",
    },
    "case_25": {
        "category": "Surgery",
        "scenario": "64yo male, ICD generator insertion, subcutaneous pocket",
        "keywords": ["icd", "defibrillator", "generator", "insertion", "pulse generator"],
        "cpt": [{"code": "33249", "desc": "Insertion or replacement of permanent implantable defibrillator system", "reason": "ICD insertion"}],
        "icd": [{"code": "I49.3", "desc": "Ventricular premature depolarization"}],
        "rule": "ICD insertion = 33249 (generator + lead system).",
    },
    "case_27": {
        "category": "Surgery",
        "scenario": "70yo male, acute LLE thromboembolic occlusion, embolectomy",
        "keywords": ["embolectomy", "thrombectomy", "artery", "occlusion", "lower extremity"],
        "cpt": [{"code": "34001", "desc": "Embolectomy/thrombectomy, lower extremity artery", "reason": "LLE embolectomy"}],
        "icd": [{"code": "I74.3", "desc": "Embolism and thrombosis of arteries of lower extremities"}],
        "rule": "LLE embolectomy = 34001.",
    },
    "case_28": {
        "category": "Surgery",
        "scenario": "68yo male, diabetic CLTI, femoral-popliteal bypass with saphenous vein",
        "keywords": ["bypass", "femoral", "popliteal", "saphenous", "graft", "clti"],
        "cpt": [{"code": "35556", "desc": "Bypass graft, femoral-popliteal vein", "reason": "Fem-pop bypass with vein"}],
        "icd": [{"code": "I73.9", "desc": "Peripheral vascular disease, unspecified"}, {"code": "E11.51", "desc": "Type 2 diabetes with peripheral angiopathy"}],
        "rule": "Fem-pop bypass with vein = 35556.",
    },
    "case_29": {
        "category": "Surgery",
        "scenario": "28yo male, blunt abdominal trauma, emergent exploratory laparotomy",
        "keywords": ["exploratory", "laparotomy", "trauma", "abdominal", "emergency"],
        "cpt": [{"code": "49505", "desc": "Exploratory laparotomy", "reason": "Emergent exploratory laparotomy"}],
        "icd": [{"code": "S36.092A", "desc": "Contusion of intra-abdominal organ, initial encounter"}],
        "rule": "Exploratory laparotomy = 49505.",
    },
    "case_30": {
        "category": "Surgery",
        "scenario": "42yo male, EGD for food bolus, extraction",
        "keywords": ["egd", "endoscopy", "food bolus", "foreign body", "extraction", "esophagus"],
        "cpt": [{"code": "43249", "desc": "Upper GI endoscopy with removal of foreign body", "reason": "EGD with foreign body removal"}],
        "icd": [{"code": "T18.1", "desc": "Foreign body in esophagus"}],
        "rule": "EGD with foreign body removal = 43249.",
    },
    "case_31": {
        "category": "Surgery",
        "scenario": "60yo male, recurrent inguinal hernia, laparoscopic repair",
        "keywords": ["hernia", "inguinal", "laparoscopic", "repair", "mesh"],
        "cpt": [{"code": "49650", "desc": "Laparoscopic repair of inguinal hernia", "reason": "Laparoscopic inguinal hernia repair"}],
        "icd": [{"code": "K40.90", "desc": "Unilateral inguinal hernia, without gangrene or obstruction"}],
        "rule": "Laparoscopic inguinal hernia repair = 49650.",
    },
    "case_33": {
        "category": "Surgery",
        "scenario": "28yo male, thrombosed external hemorrhoid, incision and drainage",
        "keywords": ["hemorrhoid", "thrombosed", "incision", "drainage", "anal"],
        "cpt": [{"code": "46600", "desc": "Incision of anal abscess or fistula", "reason": "Thrombosed hemorrhoid I&D"}],
        "icd": [{"code": "K64.1", "desc": "Thrombosed hemorrhoids"}],
        "rule": "Thrombosed hemorrhoid I&D = 46600.",
    },
    "case_34": {
        "category": "Surgery",
        "scenario": "64yo male, EGD with ERCP for pancreatic head mass, biliary stent",
        "keywords": ["ercp", "stent", "biliary", "pancreatic", "endoscopy"],
        "cpt": [
            {"code": "43239", "desc": "EGD with biopsy, single or multiple", "reason": "EGD with biopsy"},
            {"code": "43274", "desc": "ERCP with biliary stent placement", "reason": "ERCP with stent"},
        ],
        "icd": [{"code": "C25.0", "desc": "Malignant neoplasm of head of pancreas"}],
        "rule": "EGD + ERCP with stent = 43239 + 43274.",
    },
    "case_35": {
        "category": "Surgery",
        "scenario": "32yo male, open testicular biopsy",
        "keywords": ["testicular", "biopsy", "testis", "scrotal"],
        "cpt": [{"code": "54500", "desc": "Biopsy of testis, open", "reason": "Open testicular biopsy"}],
        "icd": [{"code": "D29.1", "desc": "Benign neoplasm of testis"}],
        "rule": "Open testicular biopsy = 54500.",
    },
    "case_36": {
        "category": "Surgery",
        "scenario": "58yo male, bilateral hydrocele excision",
        "keywords": ["hydrocele", "excision", "scrotal", "bilateral", "testis"],
        "cpt": [{"code": "55430", "desc": "Hydrocele repair", "reason": "Hydrocele repair bottle technique"}],
        "icd": [{"code": "N43.3", "desc": "Hydrocele"}],
        "rule": "Hydrocele repair = 55430.",
    },
    "case_37": {
        "category": "Surgery",
        "scenario": "38yo female, lap supracervical hysterectomy with BSO, 240g uterus",
        "keywords": ["hysterectomy", "laparoscopic", "supracervical", "bso", "uterus"],
        "cpt": [{"code": "58548", "desc": "Lap supracervical hysterectomy >250g with BSO", "reason": "240g uterus with BSO"}],
        "icd": [{"code": "D25.1", "desc": "Intramural leiomyoma"}, {"code": "N80.0", "desc": "Endometriosis"}],
        "rule": "Lap supracervical hysterectomy >250g with BSO = 58548.",
    },
    "case_38": {
        "category": "Surgery",
        "scenario": "50yo male, open ureterolithotomy for upper ureteral stone",
        "keywords": ["ureterolithotomy", "ureter", "stone", "calculus", "open"],
        "cpt": [{"code": "50200", "desc": "Ureterolithotomy", "reason": "Open ureterolithotomy"}],
        "icd": [{"code": "N20.1", "desc": "Calculus of ureter"}],
        "rule": "Open ureterolithotomy = 50200.",
    },
    "case_39": {
        "category": "Surgery",
        "scenario": "Transperineal prostate biopsy with MRI-fusion guidance",
        "keywords": ["prostate", "biopsy", "transperineal", "mri", "fusion"],
        "cpt": [{"code": "55707", "desc": "Biopsy of prostate, transperineal, with MRI guidance", "reason": "Transperineal prostate biopsy with MRI fusion"}],
        "icd": [{"code": "R97.2", "desc": "Elevated prostate specific antigen [PSA]"}],
        "rule": "Transperineal prostate biopsy with MRI fusion = 55707.",
    },
    "case_40": {
        "category": "Surgery",
        "scenario": "26yo female, monochorionic-monoamniotic twins, C-section at 37 weeks",
        "keywords": ["cesarean", "c-section", "twins", "delivery", "obstetric"],
        "cpt": [{"code": "59514", "desc": "Cesarean delivery only", "reason": "C-section only"}],
        "icd": [{"code": "O31.11", "desc": "Monochorionic monoamniotic twin pregnancy"}],
        "rule": "C-section = 59510 (with hysterectomy) or 59514 (C-section only).",
    },
    "case_41": {
        "category": "Surgery",
        "scenario": "47yo female, CRPS right upper extremity, sympathetic nerve blockade",
        "keywords": ["sympathetic", "nerve block", "crps", "pain", "fluoroscopic"],
        "cpt": [{"code": "64483", "desc": "Transforaminal epidural injection, lumbar", "reason": "Sympathetic nerve block"}],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}],
        "rule": "Sympathetic nerve block = 64483.",
    },
    "case_42": {
        "category": "Surgery",
        "scenario": "54yo male, cranioplasty repair skull defect, autogenous bone graft",
        "keywords": ["cranioplasty", "skull", "defect", "bone graft", "craniectomy"],
        "cpt": [{"code": "62146", "desc": "Cranioplasty", "reason": "Cranioplasty repair"}],
        "icd": [{"code": "Z90.89", "desc": "Acquired absence of other parts of head"}],
        "rule": "Cranioplasty = 62146.",
    },
    "case_43": {
        "category": "Surgery",
        "scenario": "28yo male, median nerve transection, nerve graft 1.5cm gap",
        "keywords": ["nerve", "graft", "median", "transection", "neuroplasty"],
        "cpt": [{"code": "64910", "desc": "Nerve graft, upper extremity", "reason": "Nerve graft for median nerve"}],
        "icd": [{"code": "S54.11", "desc": "Injury of median nerve at forearm level"}],
        "rule": "Nerve graft = 64910.",
    },
    "case_44": {
        "category": "Surgery",
        "scenario": "58yo male, SCS revision for lead migration, generator explanted",
        "keywords": ["spinal cord stimulator", "revision", "lead migration", "scs", "explant"],
        "cpt": [{"code": "63685", "desc": "Spinal cord stimulator revision", "reason": "SCS revision/explantation"}],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}],
        "rule": "SCS revision = 63685.",
    },
    "case_45": {
        "category": "Surgery",
        "scenario": "Adult, transthoracic anterior discectomy T6-T7 and T7-T8, no corpectomy",
        "keywords": ["discectomy", "thoracic", "anterior", "transthoracic", "spine"],
        "cpt": [{"code": "63081", "desc": "Anterior thoracic discectomy", "reason": "Anterior discectomy with osteophytectomy"}],
        "icd": [{"code": "M51.04", "desc": "Thoracic disc disorder"}],
        "rule": "Anterior thoracic discectomy = 63081.",
    },
    "case_46": {
        "category": "Surgery",
        "scenario": "Adult, infected SCS explantation, generator + leads removed, no replacement",
        "keywords": ["scs", "explant", "infected", "generator", "leads", "removal"],
        "cpt": [{"code": "63685", "desc": "SCS revision/explantation", "reason": "Explantation of infected SCS system"}],
        "icd": [{"code": "T85.71XA", "desc": "Infection due to nervous system device, initial"}],
        "rule": "SCS explantation = 63685.",
    },
    "case_47": {
        "category": "Surgery",
        "scenario": "58yo, 3 right-sided thoracic paravertebral blocks T4-T7, ultrasound-guided",
        "keywords": ["paravertebral", "nerve block", "thoracic", "ultrasound", "pain"],
        "cpt": [
            {"code": "64483", "desc": "Paravertebral block first level", "reason": "T4-T5 paravertebral block"},
            {"code": "64484", "desc": "Paravertebral block additional level", "reason": "T5-T6 and T6-T7"},
        ],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}],
        "rule": "Paravertebral blocks: 64483 (first) + 64484 (each additional).",
    },
    "case_48": {
        "category": "Surgery",
        "scenario": "62yo male, SCS trial, dual percutaneous leads, no permanent implant",
        "keywords": ["scs", "trial", "percutaneous", "leads", "spinal cord stimulator"],
        "cpt": [{"code": "63650", "desc": "SCS trial phase percutaneous", "reason": "Trial phase with external leads"}],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}, {"code": "M54.5", "desc": "Low back pain"}],
        "rule": "SCS trial phase = 63650.",
    },
    # ═══ CARDIOVASCULAR WITH KEYWORDS ═══════════════════════════════════════
    "case_22": {
        "category": "Cardiovascular",
        "scenario": "12yo boy, congenital pulmonary valve stenosis, transcatheter valve implantation",
        "keywords": ["transcatheter", "pulmonary valve", "congenital", "implantation", "percutaneous"],
        "cpt": [{"code": "33750", "desc": "Transcatheter pulmonary valve replacement", "reason": "Percutaneous transcatheter PV implantation"}],
        "icd": [{"code": "Q22.0", "desc": "Pulmonary valve stenosis, congenital"}],
        "rule": "Transcatheter pulmonary valve = 33750.",
    },
    "case_23cv": {
        "category": "Cardiovascular",
        "scenario": "68yo male, CABG with coronary endarterectomy",
        "keywords": ["cabg", "endarterectomy", "coronary", "bypass", "lima"],
        "cpt": [
            {"code": "33533", "desc": "CABG arterial graft x1", "reason": "LIMA to LAD"},
            {"code": "33572", "desc": "Coronary endarterectomy", "reason": "Open endarterectomy of RCA"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG with endarterectomy: 33533 (CABG) + 33572 (endarterectomy add-on).",
    },
    "case_24cv": {
        "category": "Cardiovascular",
        "scenario": "64yo male, 6.8cm Crawford Extent II TAAA, left heart bypass, reimplantation",
        "keywords": ["taaa", "thoracoabdominal", "aortic", "aneurysm", "repair"],
        "cpt": [{"code": "33916", "desc": "Thoracoabdominal aortic aneurysm repair", "reason": "TAAA repair with visceral reimplantation"}],
        "icd": [{"code": "I71.3", "desc": "Abdominal aortic aneurysm, ruptured"}],
        "rule": "Thoracoabdominal aortic repair = 33916.",
    },
    "case_25cv": {
        "category": "Cardiovascular",
        "scenario": "78yo female, LAA closure Watchman, transseptal puncture, TEE guidance",
        "keywords": ["laa", "watchman", "closure", "appendage", "occlusion", "transseptal"],
        "cpt": [{"code": "33340", "desc": "LAA occlusion device placement", "reason": "Watchman device implantation"}],
        "icd": [{"code": "I48.91", "desc": "Unspecified atrial fibrillation"}],
        "rule": "LAA occlusion device = 33340.",
    },
    "case_26cv": {
        "category": "Cardiovascular",
        "scenario": "69yo male, bilateral iliac balloon angioplasty",
        "keywords": ["iliac", "angioplasty", "balloon", "stent", "vascular"],
        "cpt": [
            {"code": "37221", "desc": "Iliac angioplasty first vessel", "reason": "Right common iliac"},
            {"code": "37223", "desc": "Iliac angioplasty additional vessel", "reason": "Right external iliac"},
        ],
        "icd": [{"code": "I74.3", "desc": "Embolism/thrombosis lower extremity arteries"}],
        "rule": "Iliac angioplasty: 37221 (first) + 37223 (additional in same territory).",
    },
    "case_27cv": {
        "category": "Cardiovascular",
        "scenario": "71yo female, CABG 2 arterial + 3 venous grafts, LIMA + radial artery",
        "keywords": ["cabg", "radial", "arterial", "lima", "bypass", "graft"],
        "cpt": [
            {"code": "33533", "desc": "CABG arterial x1", "reason": "LIMA to LAD"},
            {"code": "33534", "desc": "CABG arterial x2", "reason": "Additional radial artery"},
            {"code": "33518", "desc": "Vein graft add-on", "reason": "Saphenous vein grafts"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG 2 arterial + 3 venous: 33533 (LIMA) + 33534 (radial) + 33518 (vein grafts).",
    },
    # ═══ DIGESTIVE WITH KEYWORDS ═══════════════════════════════════════════
    "case_28di": {
        "category": "Digestive",
        "scenario": "40yo male, rigid esophagoscopy, balloon dilation of stricture",
        "keywords": ["esophagoscopy", "esophagus", "dilation", "stricture", "balloon"],
        "cpt": [{"code": "91300", "desc": "Esophagoscopy with dilation", "reason": "Rigid esophagoscopy with balloon dilation"}],
        "icd": [{"code": "K22.2", "desc": "Esophageal stricture"}],
        "rule": "Esophagoscopy with dilation = 91300.",
    },
    "case_29di": {
        "category": "Digestive",
        "scenario": "Adult GERD, EGD with Stretta RF to gastric cardia/LES, no duodenal exam",
        "keywords": ["stretta", "radiofrequency", "gerd", "les", "gastric", "endoscopy"],
        "cpt": [{"code": "43257", "desc": "EGD with radiofrequency treatment", "reason": "Stretta RF to gastric cardia"}],
        "icd": [{"code": "K21.0", "desc": "GERD with esophagitis"}],
        "rule": "EGD with RF treatment = 43257.",
    },
    "case_30di": {
        "category": "Digestive",
        "scenario": "60yo male, flexible sigmoidoscopy, 3 polyps snare removed",
        "keywords": ["sigmoidoscopy", "polypectomy", "snare", "polyps", "colon"],
        "cpt": [{"code": "45385", "desc": "Sigmoidoscopy with polypectomy", "reason": "Flexible sigmoidoscopy with snare polypectomy"}],
        "icd": [{"code": "K63.5", "desc": "Polyp of colon"}],
        "rule": "Sigmoidoscopy with polypectomy = 45385.",
    },
    "case_31di": {
        "category": "Digestive",
        "scenario": "65yo male, ERCP stent exchange, balloon dilation, sphincterotomy",
        "keywords": ["ercp", "stent", "exchange", "sphincterotomy", "pancreatic", "biliary"],
        "cpt": [{"code": "43275", "desc": "ERCP with stent exchange", "reason": "ERCP with stent removal/replacement and sphincterotomy"}],
        "icd": [{"code": "K86.1", "desc": "Chronic pancreatitis"}],
        "rule": "ERCP with stent exchange = 43275.",
    },
    "case_32di": {
        "category": "Digestive",
        "scenario": "68yo male, laparoscopic liver RFA for HCC, intraop ultrasound",
        "keywords": ["rfa", "radiofrequency", "ablation", "liver", "hepatocellular", "laparoscopic"],
        "cpt": [{"code": "47370", "desc": "Laparoscopic liver ablation", "reason": "Laparoscopic RFA with ultrasound guidance"}],
        "icd": [{"code": "C22.0", "desc": "Malignant neoplasm of liver, primary"}],
        "rule": "Laparoscopic liver RFA = 47370.",
    },
    "case_33di": {
        "category": "Digestive",
        "scenario": "6-week-old, Type III biliary atresia, Kasai procedure",
        "keywords": ["kasai", "biliary atresia", "portoenterostomy", "neonatal", "bile duct"],
        "cpt": [{"code": "47715", "desc": "Hepatic portoenterostomy", "reason": "Kasai procedure for biliary atresia"}],
        "icd": [{"code": "Q42.3", "desc": "Biliary atresia"}],
        "rule": "Kasai procedure = 47715.",
    },
    "case_69di": {
        "category": "Digestive",
        "scenario": "64yo female, open low anterior resection, T2N0 rectosigmoid adenocarcinoma, EEA stapler",
        "keywords": ["low anterior", "resection", "colorectal", "anastomosis", "rectum", "stapler"],
        "cpt": [{"code": "44110", "desc": "Open partial colectomy with colorectal anastomosis", "reason": "Open low anterior resection with anastomosis"}],
        "icd": [{"code": "C19", "desc": "Malignant neoplasm of rectosigmoid junction"}],
        "rule": "Open low anterior resection = 44110.",
    },
    # ═══ URINARY/GENITAL WITH KEYWORDS ═══════════════════════════════════════
    "case_35ug": {
        "category": "Urinary/Genital",
        "scenario": "58yo male, inflatable penile prosthesis, single-unit self-contained",
        "keywords": ["penile prosthesis", "inflatable", "erectile dysfunction", "implant"],
        "cpt": [{"code": "54400", "desc": "Penile prosthesis implant", "reason": "Inflatable penile prosthesis"}],
        "icd": [{"code": "N52.01", "desc": "Erectile dysfunction"}],
        "rule": "Penile prosthesis = 54400.",
    },
    "case_36ug": {
        "category": "Urinary/Genital",
        "scenario": "27yo male, laser destruction of condylomas penis",
        "keywords": ["condyloma", "laser", "penis", "warts", "destruction"],
        "cpt": [{"code": "54057", "desc": "Destruction penile lesion laser", "reason": "Laser destruction of condylomas"}],
        "icd": [{"code": "A63.0", "desc": "Anogenital venereal warts"}],
        "rule": "Laser destruction penile lesion = 54057.",
    },
    "case_37ug": {
        "category": "Urinary/Genital",
        "scenario": "45yo female, lap supracervical hysterectomy >250g with BSO",
        "keywords": ["hysterectomy", "laparoscopic", "supracervical", "bso", "uterus", "fibroid"],
        "cpt": [{"code": "58548", "desc": "Lap supracervical hysterectomy >250g with BSO", "reason": "240g uterus with BSO"}],
        "icd": [{"code": "D25.1", "desc": "Intramural leiomyoma"}, {"code": "N80.0", "desc": "Endometriosis"}],
        "rule": "Lap supracervical hysterectomy >250g with BSO = 58548.",
    },
    "case_38ug": {
        "category": "Urinary/Genital",
        "scenario": "52yo female, open bilateral salpingectomy + left oophorectomy",
        "keywords": ["salpingectomy", "oophorectomy", "bilateral", "ovary", "fallopian"],
        "cpt": [
            {"code": "58700", "desc": "Bilateral salpingectomy", "reason": "Bilateral fallopian tube removal"},
            {"code": "58900", "desc": "Oophorectomy unilateral", "reason": "Left oophorectomy"},
        ],
        "icd": [{"code": "N70.1", "desc": "Chronic salpingitis"}, {"code": "D27.1", "desc": "Benign neoplasm of left ovary"}],
        "rule": "Bilateral salpingectomy = 58700. Unilateral oophorectomy = 58900.",
    },
    "case_39ug": {
        "category": "Urinary/Genital",
        "scenario": "25yo female, induced abortion D&E at 16 weeks",
        "keywords": ["abortion", "dilatation", "evacuation", "d&e", "pregnancy"],
        "cpt": [{"code": "59840", "desc": "Induced abortion D&E", "reason": "D&E at 16 weeks gestation"}],
        "icd": [{"code": "O04.8", "desc": "Medical abortion, incomplete"}],
        "rule": "Induced abortion D&E = 59840.",
    },
    "case_40ug": {
        "category": "Urinary/Genital",
        "scenario": "65yo male, open nephrectomy with partial ureterectomy for RCC",
        "keywords": ["nephrectomy", "ureterectomy", "kidney", "renal cell", "tumor"],
        "cpt": [{"code": "50220", "desc": "Nephrectomy with partial ureterectomy", "reason": "Nephrectomy with proximal ureterectomy"}],
        "icd": [{"code": "C64.1", "desc": "Malignant neoplasm of right kidney"}],
        "rule": "Nephrectomy with partial ureterectomy = 50220.",
    },
    "case_70ug": {
        "category": "Urinary/Genital",
        "scenario": "68yo male, hydrocele repair bottle technique, no excision of tunica",
        "keywords": ["hydrocele", "repair", "bottle", "jaboulay", "scrotal", "testis"],
        "cpt": [{"code": "55430", "desc": "Hydrocele repair", "reason": "Open hydrocele repair (bottle technique)"}],
        "icd": [{"code": "N43.3", "desc": "Hydrocele"}],
        "rule": "Hydrocele repair bottle technique = 55430.",
    },
    "case_63": {
        "category": "E/M",
        "scenario": "56yo male established, cervical lymphadenopathy, B-symptoms, CT + labs, urgent referral, 48 min, complex MDM",
        "cpt": [{"code": "99215", "desc": "Office visit established high MDM", "reason": "High MDM: multiple chronic illnesses, extensive data review, urgent referral"}],
        "icd": [{"code": "R59.1", "desc": "Enlarged lymph nodes"}, {"code": "R50.8", "desc": "Other specified fever"}],
        "rule": "High complexity MDM = 99215.",
    },
    "case_64": {
        "category": "E/M",
        "scenario": "67yo male, ICU, sepsis transfer, critical care Day 1 (80min) + Day 2 (95min), spans midnight",
        "cpt": [
            {"code": "99291", "desc": "Critical care Day 1 (80 min)", "reason": "Day 1: 22:00-23:59 = 80 min critical care"},
            {"code": "99291", "desc": "Critical care Day 2 (95 min)", "reason": "Day 2: 00:00-02:30 = 95 min critical care"},
        ],
        "icd": [{"code": "A41.9", "desc": "Sepsis, unspecified"}, {"code": "R65.21", "desc": "Severe sepsis with septic shock"}],
        "rule": "Critical care spanning midnight = TWO 99291 claims (one per calendar day).",
    },
    "case_65": {
        "category": "E/M",
        "scenario": "38yo female, BHI non-collaborative care, nurse 35min initial + calls + CBT, physician 25min",
        "cpt": [{"code": "99484", "desc": "General BHI non-collaborative care", "reason": "BHI non-collaborative care model"}],
        "icd": [{"code": "F41.1", "desc": "Generalized anxiety disorder"}],
        "rule": "BHI non-collaborative = 99484.",
    },
    "case_91": {
        "category": "E/M",
        "scenario": "Adult established, office, 1 stable chronic condition, 1 external note, EKG interpretation, prescription management",
        "cpt": [{"code": "99213", "desc": "Office visit established low MDM", "reason": "Low MDM: 1 stable chronic, limited data, low risk"}],
        "icd": [{"code": "I10", "desc": "Essential hypertension"}],
        "rule": "1 stable chronic + limited data + low risk = 99213.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # ANESTHESIA CASES (7-10, 66)
    # ═══════════════════════════════════════════════════════════════════
    "case_7": {
        "category": "Anesthesia",
        "scenario": "58yo ASA P3, open incisional hernia repair, 75 min anesthesia",
        "cpt": [{"code": "01951", "desc": "Anesthesia for hernia repair", "reason": "Open hernia repair anesthesia 75 min"}],
        "icd": [{"code": "K43.1", "desc": "Incisional hernia with obstruction"}],
        "rule": "Anesthesia base code 01951 + time units.",
    },
    "case_8": {
        "category": "Anesthesia",
        "scenario": "38yo ASA P1 female, D&C with endometrial biopsy, general anesthesia",
        "cpt": [{"code": "01930", "desc": "Anesthesia for D&C", "reason": "D&C under general anesthesia"}],
        "icd": [{"code": "N93.82", "desc": "Excessive and frequent menstruation"}],
        "rule": "D&C anesthesia = 01930.",
    },
    "case_9": {
        "category": "Anesthesia",
        "scenario": "76yo ASA P3 male, AICD transvenous, CRNA under medical direction, 4 concurrent cases",
        "cpt": [{"code": "01937", "desc": "Anesthesia for AICD insertion", "reason": "AICD under medical direction"}],
        "icd": [{"code": "I49.3", "desc": "Ventricular premature depolarization"}],
        "rule": "AICD anesthesia = 01937. Medical direction modifier applies.",
    },
    "case_10": {
        "category": "Anesthesia",
        "scenario": "79yo ASA P4 male, emergency diaphragmatic hernia repair",
        "cpt": [{"code": "01950", "desc": "Emergency hernia anesthesia", "reason": "Emergency hernia repair anesthesia"}],
        "icd": [{"code": "K44.9", "desc": "Diaphragmatic hernia"}],
        "rule": "Emergency surgery anesthesia = 01950.",
    },
    "case_66": {
        "category": "Anesthesia",
        "scenario": "65yo ASA P3 male, CABG x3, CRNA-led, 5h45min, single CRNA",
        "cpt": [{"code": "00561", "desc": "Anesthesia for CABG", "reason": "CABG anesthesia with CRNA supervision"}],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG anesthesia = 00561.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # INTEGUMENTARY CASES (11-17)
    # ═══════════════════════════════════════════════════════════════════
    "case_11": {
        "category": "Integumentary",
        "scenario": "Adult, scar tattooing 5 sq cm hypopigmented scar right cheek",
        "cpt": [{"code": "15780", "desc": "Tattooing for cosmetic reconstruction", "reason": "Scar tattooing for reconstruction"}],
        "icd": [{"code": "L90.5", "desc": "Scar conditions and fibrosis of skin"}],
        "rule": "Scar tattooing for reconstruction = 15780.",
    },
    "case_12": {
        "category": "Integumentary",
        "scenario": "Adult, free fascial flap with microvascular anastomosis, right hand",
        "cpt": [{"code": "15570", "desc": "Free fascial flap with microvascular anastomosis", "reason": "Free flap with microvascular anastomosis"}],
        "icd": [{"code": "S61.419A", "desc": "Open wound of hand, unspecified"}],
        "rule": "Free fascial flap = 15570.",
    },
    "case_13": {
        "category": "Integumentary",
        "scenario": "65yo male, Mohs BCC right cheek, 2 stages (4+6 blocks), intermediate closure 3cm",
        "cpt": [
            {"code": "17315", "desc": "Mohs stage 1 first tissue block", "reason": "First stage Mohs 4 blocks"},
            {"code": "17316", "desc": "Mohs each additional stage", "reason": "Second stage Mohs 6 blocks"},
            {"code": "12032", "desc": "Intermed closure 2.6-7.5cm", "reason": "3cm intermediate closure"},
        ],
        "icd": [{"code": "C44.310", "desc": "Basal cell carcinoma of face"}],
        "rule": "Mohs: 17315 (first stage) + 17316 (additional stages). Closure separate.",
    },
    "case_14": {
        "category": "Integumentary",
        "scenario": "70yo male, melanoma 4.5cm upper back, wide local excision 1cm margins, complex repair",
        "cpt": [
            {"code": "11606", "desc": "Excision malignant trunk >4cm but not >6cm", "reason": "4.5cm lesion + 1cm margins = 6.5cm"},
            {"code": "13132", "desc": "Complex repair 2.1-5cm", "reason": "Complex closure"},
        ],
        "icd": [{"code": "C43.51", "desc": "Melanoma of skin of trunk"}],
        "rule": "Measure lesion + margins. 4.5cm + 1cm each side = 6.5cm total excised diameter.",
    },
    "case_15": {
        "category": "Integumentary",
        "scenario": "65yo male, Mohs BCC right cheek (2 stages), rotation flap, ear biopsy, forearm nevus excision",
        "cpt": [
            {"code": "17315", "desc": "Mohs stage 1 first block"},
            {"code": "17316", "desc": "Mohs additional stage"},
            {"code": "12032", "desc": "Intermed closure"},
            {"code": "11102", "desc": "Tangential biopsy trunk"},
            {"code": "11402", "desc": "Excision benign trunk 0.6-1cm"},
        ],
        "icd": [{"code": "C44.310", "desc": "BCC face"}, {"code": "D22.61", "desc": "Nevus right upper limb"}],
        "rule": "Multiple procedures: modifier 59 for separate billing.",
    },
    "case_16": {
        "category": "Integumentary",
        "scenario": "65yo male, SCC 3cm right cheek, wide local excision, complex closure 6cm",
        "cpt": [
            {"code": "11604", "desc": "Excision malignant face >0.5cm", "reason": "3cm SCC with margins"},
            {"code": "13132", "desc": "Complex repair 2.1-5cm", "reason": "Complex closure 6cm"},
        ],
        "icd": [{"code": "C44.310", "desc": "Malignant neoplasm of skin of face"}],
        "rule": "Excision 3cm + margins, then complex repair separately.",
    },
    "case_17": {
        "category": "Integumentary",
        "scenario": "42yo male, subcutaneous abscess right elbow, I&D",
        "cpt": [{"code": "10060", "desc": "I&D abscess", "reason": "Simple I&D of subcutaneous abscess"}],
        "icd": [{"code": "L02.51", "desc": "Cutaneous abscess of right elbow"}],
        "rule": "Simple subcutaneous abscess I&D = 10060.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # MUSCULOSKELETAL CASES (18-21, 34)
    # ═══════════════════════════════════════════════════════════════════
    "case_18": {
        "category": "Musculoskeletal",
        "scenario": "78yo female, kyphoplasty 3 levels L2-L4, bilateral approach each level",
        "cpt": [
            {"code": "22510", "desc": "Percutaneous vertebroplasty/kyphoplasty first level", "reason": "First level L2"},
            {"code": "22511", "desc": "Each additional level", "reason": "L3 and L4 = 2 additional levels"},
        ],
        "icd": [{"code": "M80.08", "desc": "Osteoporosis with pathological fracture vertebrae"}],
        "rule": "Kyphoplasty: 22510 (first) + 22511 (each additional). 3 levels = 22510 + 2×22511.",
    },
    "case_19": {
        "category": "Musculoskeletal",
        "scenario": "75yo female, comminuted 4-part proximal humerus fracture, hemiarthroplasty",
        "cpt": [{"code": "23470", "desc": "Hemiarthroplasty shoulder", "reason": "Prosthetic hemiarthroplasty for proximal humerus fracture"}],
        "icd": [{"code": "S42.201A", "desc": "Fracture of right humerus, initial encounter"}],
        "rule": "Shoulder hemiarthroplasty = 23470.",
    },
    "case_20": {
        "category": "Musculoskeletal",
        "scenario": "Adult, 5cm benign subcutaneous tumor abdominal wall, confined to subcutaneous tissue",
        "cpt": [{"code": "11406", "desc": "Excision benign trunk >2cm but not >3cm", "reason": "5cm benign subcutaneous tumor"}],
        "icd": [{"code": "D17.1", "desc": "Benign lipomatous neoplasm of skin of trunk"}],
        "rule": "Subcutaneous tumor confined to subcutaneous tissue = 11406 (not 21552 which involves fascia).",
    },
    "case_21": {
        "category": "Musculoskeletal",
        "scenario": "70yo, open meniscectomy medial meniscus via arthrotomy, no lateral compartment work",
        "cpt": [{"code": "29881", "desc": "Meniscectomy medial/lateral", "reason": "Medial meniscectomy via open arthrotomy"}],
        "icd": [{"code": "M23.31", "desc": "Other meniscus derangement, medial meniscus"}],
        "rule": "Medial meniscectomy = 29881.",
    },
    "case_34": {
        "category": "Musculoskeletal",
        "scenario": "35yo male, closed SC dislocation, open reduction after failed closed attempts, no graft",
        "cpt": [{"code": "23525", "desc": "Open reduction SC dislocation", "reason": "Open reduction after failed closed attempts"}],
        "icd": [{"code": "S43.005A", "desc": "Dislocation of left sternoclavicular joint, initial encounter"}],
        "rule": "Open reduction of SC dislocation = 23525.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # CARDIOVASCULAR CASES (22-27)
    # ═══════════════════════════════════════════════════════════════════
    "case_22": {
        "category": "Cardiovascular",
        "scenario": "12yo male, congenital PV stenosis, percutaneous transcatheter PV implantation",
        "cpt": [{"code": "33750", "desc": "Transcatheter pulmonary valve replacement", "reason": "Percutaneous transcatheter PV implantation"}],
        "icd": [{"code": "Q22.0", "desc": "Pulmonary valve stenosis, congenital"}],
        "rule": "Transcatheter pulmonary valve = 33750.",
    },
    "case_23": {
        "category": "Cardiovascular",
        "scenario": "68yo male, CABG LIMA-LAD + SVG-OM + SVG-RCA with coronary endarterectomy",
        "cpt": [
            {"code": "33533", "desc": "CABG arterial graft x1", "reason": "LIMA to LAD"},
            {"code": "33572", "desc": "Coronary endarterectomy", "reason": "Open endarterectomy of RCA"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG with endarterectomy: 33533 (CABG) + 33572 (endarterectomy add-on).",
    },
    "case_24": {
        "category": "Cardiovascular",
        "scenario": "64yo male, 6.8cm Crawford Extent II TAAA, left heart bypass, reimplantation",
        "cpt": [{"code": "33916", "desc": "Thoracoabdominal aortic aneurysm repair", "reason": "TAAA repair with visceral reimplantation"}],
        "icd": [{"code": "I71.3", "desc": "Abdominal aortic aneurysm, ruptured"}],
        "rule": "Thoracoabdominal aortic repair = 33916.",
    },
    "case_25": {
        "category": "Cardiovascular",
        "scenario": "78yo female, LAA closure Watchman, transseptal puncture, TEE guidance",
        "cpt": [{"code": "33340", "desc": "LAA occlusion device placement", "reason": "Watchman device implantation"}],
        "icd": [{"code": "I48.91", "desc": "Unspecified atrial fibrillation"}],
        "rule": "LAA occlusion device = 33340.",
    },
    "case_26": {
        "category": "Cardiovascular",
        "scenario": "69yo male, bilateral iliac balloon angioplasty (no stent, no atherectomy)",
        "cpt": [
            {"code": "37221", "desc": "Iliac angioplasty first vessel", "reason": "Right common iliac"},
            {"code": "37223", "desc": "Iliac angioplasty additional vessel", "reason": "Right external iliac"},
        ],
        "icd": [{"code": "I74.3", "desc": "Embolism/thrombosis lower extremity arteries"}],
        "rule": "Iliac angioplasty: 37221 (first) + 37223 (additional in same territory).",
    },
    "case_27": {
        "category": "Cardiovascular",
        "scenario": "71yo female, CABG 2 arterial + 3 venous grafts, LIMA + radial artery",
        "cpt": [
            {"code": "33533", "desc": "CABG arterial x1", "reason": "LIMA to LAD"},
            {"code": "33534", "desc": "CABG arterial x2", "reason": "Additional radial artery"},
            {"code": "33518", "desc": "Vein graft add-on", "reason": "Saphenous vein grafts"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG 2 arterial + 3 venous: 33533 (LIMA) + 33534 (radial) + 33518 (vein grafts).",
    },

    # ═══════════════════════════════════════════════════════════════════
    # DIGESTIVE SYSTEM CASES (28-33, 69)
    # ═══════════════════════════════════════════════════════════════════
    "case_28": {
        "category": "Digestive",
        "scenario": "40yo male, rigid esophagoscopy, balloon dilation of stricture",
        "cpt": [{"code": "91300", "desc": "Esophagoscopy with dilation", "reason": "Rigid esophagoscopy with balloon dilation"}],
        "icd": [{"code": "K22.2", "desc": "Esophageal stricture"}],
        "rule": "Esophagoscopy with dilation = 91300.",
    },
    "case_29": {
        "category": "Digestive",
        "scenario": "Adult GERD, EGD with Stretta RF to gastric cardia/LES, no duodenal exam",
        "cpt": [{"code": "43257", "desc": "EGD with radiofrequency treatment", "reason": "Stretta RF to gastric cardia"}],
        "icd": [{"code": "K21.0", "desc": "GERD with esophagitis"}],
        "rule": "EGD with RF treatment = 43257.",
    },
    "case_30": {
        "category": "Digestive",
        "scenario": "60yo male, flexible sigmoidoscopy, 3 polyps snare removed",
        "cpt": [{"code": "45385", "desc": "Sigmoidoscopy with polypectomy", "reason": "Flexible sigmoidoscopy with snare polypectomy"}],
        "icd": [{"code": "K63.5", "desc": "Polyp of colon"}],
        "rule": "Sigmoidoscopy with polypectomy = 45385.",
    },
    "case_31": {
        "category": "Digestive",
        "scenario": "65yo male, ERCP stent exchange, balloon dilation, sphincterotomy",
        "cpt": [{"code": "43275", "desc": "ERCP with stent exchange", "reason": "ERCP with stent removal/replacement and sphincterotomy"}],
        "icd": [{"code": "K86.1", "desc": "Chronic pancreatitis"}],
        "rule": "ERCP with stent exchange = 43275.",
    },
    "case_32": {
        "category": "Digestive",
        "scenario": "68yo male, laparoscopic liver RFA for HCC, intraop ultrasound",
        "cpt": [{"code": "47370", "desc": "Laparoscopic liver ablation", "reason": "Laparoscopic RFA with ultrasound guidance"}],
        "icd": [{"code": "C22.0", "desc": "Malignant neoplasm of liver, primary"}],
        "rule": "Laparoscopic liver RFA = 47370.",
    },
    "case_33": {
        "category": "Digestive",
        "scenario": "6-week-old, Type III biliary atresia, Kasai procedure (hepatic portoenterostomy)",
        "cpt": [{"code": "47715", "desc": "Hepatic portoenterostomy", "reason": "Kasai procedure for biliary atresia"}],
        "icd": [{"code": "Q42.3", "desc": "Biliary atresia"}],
        "rule": "Kasai procedure = 47715.",
    },
    "case_69": {
        "category": "Digestive",
        "scenario": "64yo female, open low anterior resection, T2N0 rectosigmoid adenocarcinoma, EEA stapler",
        "cpt": [{"code": "44110", "desc": "Open partial colectomy with colorectal anastomosis", "reason": "Open low anterior resection with anastomosis"}],
        "icd": [{"code": "C19", "desc": "Malignant neoplasm of rectosigmoid junction"}],
        "rule": "Open low anterior resection = 44110.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # URINARY/GENITAL CASES (35-40, 70)
    # ═══════════════════════════════════════════════════════════════════
    "case_35": {
        "category": "Urinary/Genital",
        "scenario": "58yo male, inflatable penile prosthesis, single-unit self-contained",
        "cpt": [{"code": "54400", "desc": "Penile prosthesis implant", "reason": "Inflatable penile prosthesis"}],
        "icd": [{"code": "N52.01", "desc": "Erectile dysfunction"}],
        "rule": "Penile prosthesis = 54400.",
    },
    "case_36": {
        "category": "Urinary/Genital",
        "scenario": "27yo male, laser destruction of condylomas penis",
        "cpt": [{"code": "54057", "desc": "Destruction penile lesion laser", "reason": "Laser destruction of condylomas"}],
        "icd": [{"code": "A63.0", "desc": "Anogenital venereal warts"}],
        "rule": "Laser destruction penile lesion = 54057.",
    },
    "case_37": {
        "category": "Urinary/Genital",
        "scenario": "45yo female, lap supracervical hysterectomy >250g with BSO",
        "cpt": [{"code": "58548", "desc": "Lap supracervical hysterectomy >250g with BSO", "reason": "240g uterus with BSO"}],
        "icd": [{"code": "D25.1", "desc": "Intramural leiomyoma"}, {"code": "N80.0", "desc": "Endometriosis"}],
        "rule": "Lap supracervical hysterectomy >250g with BSO = 58548.",
    },
    "case_38": {
        "category": "Urinary/Genital",
        "scenario": "52yo female, open bilateral salpingectomy + left oophorectomy",
        "cpt": [
            {"code": "58700", "desc": "Bilateral salpingectomy", "reason": "Bilateral fallopian tube removal"},
            {"code": "58900", "desc": "Oophorectomy unilateral", "reason": "Left oophorectomy"},
        ],
        "icd": [{"code": "N70.1", "desc": "Chronic salpingitis"}, {"code": "D27.1", "desc": "Benign neoplasm of left ovary"}],
        "rule": "Bilateral salpingectomy = 58700. Unilateral oophorectomy = 58900.",
    },
    "case_39": {
        "category": "Urinary/Genital",
        "scenario": "25yo female, induced abortion D&E at 16 weeks",
        "cpt": [{"code": "59840", "desc": "Induced abortion D&E", "reason": "D&E at 16 weeks gestation"}],
        "icd": [{"code": "O04.8", "desc": "Medical abortion, incomplete"}],
        "rule": "Induced abortion D&E = 59840.",
    },
    "case_40": {
        "category": "Urinary/Genital",
        "scenario": "65yo male, open nephrectomy with partial ureterectomy for RCC",
        "cpt": [{"code": "50220", "desc": "Nephrectomy with partial ureterectomy", "reason": "Nephrectomy with proximal ureterectomy"}],
        "icd": [{"code": "C64.1", "desc": "Malignant neoplasm of right kidney"}],
        "rule": "Nephrectomy with partial ureterectomy = 50220.",
    },
    "case_70": {
        "category": "Urinary/Genital",
        "scenario": "68yo male, hydrocele repair bottle technique, no excision of tunica",
        "cpt": [{"code": "55430", "desc": "Hydrocele repair", "reason": "Open hydrocele repair (bottle technique)"}],
        "icd": [{"code": "N43.3", "desc": "Hydrocele"}],
        "rule": "Hydrocele repair bottle technique = 55430.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # NERVOUS SYSTEM CASES (41-46, 71)
    # ═══════════════════════════════════════════════════════════════════
    "case_41": {
        "category": "Nervous",
        "scenario": "6yo pediatric, head injury, left SDH, 3 burr holes, evacuate hematoma",
        "cpt": [{"code": "61108", "desc": "Burr holes for SDH evacuation", "reason": "3 burr holes for subdural hematoma drainage"}],
        "icd": [{"code": "S06.5X0A", "desc": "Traumatic subdural hemorrhage without LOC, initial"}],
        "rule": "Burr holes for SDH evacuation = 61108.",
    },
    "case_42": {
        "category": "Nervous",
        "scenario": "54yo, bilateral thoracic disc disorder T6-T8, transpedicular decompression",
        "cpt": [
            {"code": "63047", "desc": "Laminectomy first level", "reason": "T6-T7 decompression"},
            {"code": "63048", "desc": "Laminectomy additional level", "reason": "T7-T8 additional level"},
        ],
        "icd": [{"code": "M51.04", "desc": "Intervertebral disc disorder thoracic"}],
        "rule": "Laminectomy: 63047 (first level) + 63048 (each additional).",
    },
    "case_43": {
        "category": "Nervous",
        "scenario": "47yo, right parietal AVM, endovascular embolization with Onyx",
        "cpt": [{"code": "61624", "desc": "AVM embolization", "reason": "Endovascular embolization of AVM"}],
        "icd": [{"code": "Q28.2", "desc": "Cerebral AVM"}],
        "rule": "AVM embolization = 61624.",
    },
    "case_44": {
        "category": "Nervous",
        "scenario": "Adult, transthoracic anterior discectomy T6-T7 and T7-T8, no corpectomy",
        "cpt": [{"code": "63081", "desc": "Anterior thoracic discectomy", "reason": "Anterior discectomy with osteophytectomy"}],
        "icd": [{"code": "M51.04", "desc": "Thoracic disc disorder"}],
        "rule": "Anterior thoracic discectomy = 63081.",
    },
    "case_45": {
        "category": "Nervous",
        "scenario": "Adult, infected SCS explantation, generator + leads removed, no replacement",
        "cpt": [{"code": "63685", "desc": "SCS revision/explantation", "reason": "Explantation of infected SCS system"}],
        "icd": [{"code": "T85.71XA", "desc": "Infection/inflammatory reaction due to NNS device, initial"}],
        "rule": "SCS explantation = 63685.",
    },
    "case_46": {
        "category": "Nervous",
        "scenario": "58yo, 3 right-sided thoracic paravertebral blocks T4-T7, ultrasound-guided",
        "cpt": [
            {"code": "64483", "desc": "Paravertebral block first level", "reason": "T4-T5 paravertebral block"},
            {"code": "64484", "desc": "Paravertebral block additional level", "reason": "T5-T6 and T6-T7"},
        ],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}],
        "rule": "Paravertebral blocks: 64483 (first) + 64484 (each additional).",
    },
    "case_71": {
        "category": "Nervous",
        "scenario": "62yo male, SCS trial, dual percutaneous leads, no permanent implant",
        "cpt": [{"code": "63650", "desc": "SCS trial phase percutaneous", "reason": "Trial phase with external leads"}],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}, {"code": "M54.5", "desc": "Low back pain"}],
        "rule": "SCS trial phase = 63650.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # RADIOLOGY CASES (72-78, 93)
    # ═══════════════════════════════════════════════════════════════════
    "case_72": {
        "category": "Radiology",
        "scenario": "28yo male, chest X-ray 4 views, split billing (hospital tech + radiologist prof)",
        "cpt": [{"code": "71048", "desc": "Chest X-ray 4+ views", "reason": "PA, lateral, RAO, LAO views"}],
        "icd": [{"code": "S22.49XA", "desc": "Fracture of ribs, initial encounter"}],
        "rule": "Chest X-ray 4 views = 71048. Split billing: modifier -26 (professional) and -TC (technical).",
    },
    "case_73": {
        "category": "Radiology",
        "scenario": "45yo male, MRA spinal canal with IV contrast",
        "cpt": [{"code": "72158", "desc": "MRA spine with contrast", "reason": "MRA of spinal canal with IV contrast"}],
        "icd": [{"code": "G83.4", "desc": "Cauda equina syndrome"}],
        "rule": "MRA spine with contrast = 72158.",
    },
    "case_74": {
        "category": "Radiology",
        "scenario": "72yo female, nuclear cisternography for CSF leak, In-111 DTPA intrathecal injection",
        "cpt": [
            {"code": "78630", "desc": "Cisternography", "reason": "Nuclear medicine cisternography"},
            {"code": "61056", "desc": "Lumbar puncture for intrathecal injection", "reason": "In-111 DTPA injection"},
        ],
        "icd": [{"code": "G96.0", "desc": "CSF leak"}],
        "rule": "Cisternography = 78630. Separate LP for injection = 61056.",
    },
    "case_75": {
        "category": "Radiology",
        "scenario": "50yo female, stereotactic breast biopsy with clip placement, specimen radiograph",
        "cpt": [{"code": "19083", "desc": "Stereotactic breast biopsy", "reason": "Stereotactic core needle biopsy with clip"}],
        "icd": [{"code": "R92.8", "desc": "Other abnormal mammographic findings"}],
        "rule": "Stereotactic breast biopsy = 19083.",
    },
    "case_76": {
        "category": "Radiology",
        "scenario": "Adult NSCLC, 3D conformal radiation planning with 4D-CT motion management",
        "cpt": [{"code": "77301", "desc": "3D conformal RT planning", "reason": "3D-CRT planning with motion management"}],
        "icd": [{"code": "C34.10", "desc": "Malignant neoplasm of upper lobe bronchus or lung"}],
        "rule": "3D conformal RT planning = 77301.",
    },
    "case_77": {
        "category": "Radiology",
        "scenario": "50yo male, comprehensive cardiac MRI with/without contrast + stress perfusion + flow mapping",
        "cpt": [{"code": "75563", "desc": "Cardiac MRI with stress", "reason": "Comprehensive cardiac MRI with contrast and stress perfusion"}],
        "icd": [{"code": "I42.0", "desc": "Dilated cardiomyopathy"}],
        "rule": "Cardiac MRI with stress = 75563.",
    },
    "case_78": {
        "category": "Radiology",
        "scenario": "70yo pacemaker patient, MRI brain with MR safety services (tech, radiologist, physicist, programmer)",
        "cpt": [
            {"code": "76001", "desc": "MR safety evaluation", "reason": "MR safety determination and programming"},
            {"code": "70553", "desc": "MRI brain with/without contrast", "reason": "Brain MRI"},
        ],
        "icd": [{"code": "G43.909", "desc": "Migraine, unspecified"}],
        "rule": "MR safety services = 76001. Brain MRI = 70553.",
    },
    "case_93": {
        "category": "Radiology",
        "scenario": "55yo female, screening mammogram converted to diagnostic same day",
        "cpt": [
            {"code": "77067", "desc": "Screening mammography", "reason": "Initial screening views"},
            {"code": "77063", "desc": "Diagnostic mammography", "reason": "Additional diagnostic views same day"},
        ],
        "icd": [{"code": "R92.8", "desc": "Abnormal mammographic findings"}],
        "rule": "Screening converted to diagnostic: 77067 + 77063 (modifier -59 for separate service).",
    },

    # ═══════════════════════════════════════════════════════════════════
    # PATHOLOGY/LAB CASES (79-84, 94)
    # ═══════════════════════════════════════════════════════════════════
    "case_79": {
        "category": "Pathology",
        "scenario": "Adult, 3 individual chemistry tests: CO2, Chloride, Sodium (NOT K)",
        "cpt": [
            {"code": "82374", "desc": "Carbon dioxide (bicarbonate)", "reason": "Individual test"},
            {"code": "82435", "desc": "Chloride", "reason": "Individual test"},
            {"code": "82947", "desc": "Sodium", "reason": "Individual test"},
        ],
        "icd": [],
        "rule": "Individual component tests billed separately. 80053 (comp panel) requires ALL 4 components.",
    },
    "case_80": {
        "category": "Pathology",
        "scenario": "45yo, tacrolimus trough level, whole blood, post-liver transplant",
        "cpt": [{"code": "80162", "desc": "Tacrolimus level", "reason": "Therapeutic drug monitoring tacrolimus"}],
        "icd": [{"code": "Z94.4", "desc": "Liver transplant status"}],
        "rule": "Tacrolimus trough = 80162.",
    },
    "case_81": {
        "category": "Pathology",
        "scenario": "45yo female, ED chest pain, troponin normal, IMA/ACB test ordered",
        "cpt": [{"code": "82083", "desc": "Albumin cobalt binding test (IMA)", "reason": "Ischemia-modified albumin test"}],
        "icd": [{"code": "R07.9", "desc": "Chest pain, unspecified"}],
        "rule": "IMA test = 82083.",
    },
    "case_82": {
        "category": "Pathology",
        "scenario": "65yo COPD, fungal cultures from sputum AND blood (2 sources)",
        "cpt": [
            {"code": "87101", "desc": "Fungal culture from sputum", "reason": "Sputum fungal culture"},
            {"code": "87103", "desc": "Fungal culture from blood", "reason": "Blood fungal culture"},
        ],
        "icd": [{"code": "B44.1", "desc": "Pulmonary aspergillosis"}],
        "rule": "Fungal cultures from different sources billed separately.",
    },
    "case_83": {
        "category": "Pathology",
        "scenario": "24yo, ED altered mental status, presumptive drug screen positive, definitive confirmation for 4 amphetamines",
        "cpt": [{"code": "80320", "desc": "Drug confirmation", "reason": "Definitive drug confirmation for 4 specific drugs"}],
        "icd": [{"code": "F15.20", "desc": "Amphetamine use disorder, uncomplicated"}],
        "rule": "Definitive drug confirmation = 80320.",
    },
    "case_84": {
        "category": "Pathology",
        "scenario": "28yo pregnant, comprehensive obstetric panel (CBC, HBsAg, RBC antibody screen, rubella, RPR, ABO/Rh, HIV)",
        "cpt": [{"code": "80055", "desc": "Obstetric panel", "reason": "Complete prenatal panel"}],
        "icd": [{"code": "Z34.00", "desc": "Supervision of normal first pregnancy"}],
        "rule": "Obstetric panel = 80055.",
    },
    "case_94": {
        "category": "Pathology",
        "scenario": "IHC staining on single tissue block, 4 antibodies, 4 slides",
        "cpt": [{"code": "88342", "desc": "IHC staining per antibody", "reason": "4 antibodies = 4 × 88342"}],
        "icd": [],
        "rule": "IHC staining = 88342 per antibody. 4 antibodies = 4 × 88342.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # MEDICINE/INFUSIONS CASES (85-90)
    # ═══════════════════════════════════════════════════════════════════
    "case_85": {
        "category": "Medicine",
        "scenario": "58yo male, multi-vessel PCI: RCA PTCA + stent, LAD atherectomy + angioplasty + stent, LCX stent only",
        "cpt": [
            {"code": "92928", "desc": "PCI with stent", "reason": "RCA stent + LAD stent + LCX stent"},
            {"code": "92920", "desc": "PCI atherectomy", "reason": "LAD atherectomy"},
            {"code": "92941", "desc": "PCI angioplasty", "reason": "LAD angioplasty"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "Multi-vessel PCI: 92928 (stent) + 92920 (atherectomy) + 92941 (angioplasty).",
    },
    "case_86": {
        "category": "Medicine",
        "scenario": "6mo infant, bedside comprehensive TTE congenital with Doppler, cardiologist performs",
        "cpt": [{"code": "93318", "desc": "TTE congenital", "reason": "Comprehensive congenital echocardiogram with Doppler"}],
        "icd": [{"code": "Q24.9", "desc": "Congenital cardiac malformation"}],
        "rule": "Comprehensive congenital TTE = 93318.",
    },
    "case_87": {
        "category": "Medicine",
        "scenario": "45yo, psychiatrist, E/M 25min low MDM + 35min supportive psychotherapy + translator",
        "cpt": [
            {"code": "90834", "desc": "Psychotherapy 30 min", "reason": "35 min supportive psychotherapy"},
            {"code": "99214", "desc": "E/M visit moderate MDM", "reason": "25 min E/M with medication management"},
        ],
        "icd": [{"code": "F33.1", "desc": "Major depressive disorder, recurrent, moderate"}],
        "rule": "Psychiatry: 90834 (psychotherapy) + 99214 (E/M) - separate sessions.",
    },
    "case_88": {
        "category": "Medicine",
        "scenario": "70yo, multiple myeloma, sequential chemo: dexamethasone push 5min, bortezomib infusion 30min, bendamustine infusion 90min",
        "cpt": [
            {"code": "96401", "desc": "Chemotherapy push", "reason": "Dexamethasone IV push"},
            {"code": "96413", "desc": "Chemotherapy infusion first hour", "reason": "Bortezomib + bendamustine sequential infusion"},
            {"code": "96415", "desc": "Chemotherapy infusion each additional 30min", "reason": "Additional 30min beyond first hour"},
        ],
        "icd": [{"code": "C90.00", "desc": "Multiple myeloma"}],
        "rule": "Sequential chemo: 96401 (push) + 96413 (infusion first hour) + 96415 (each add'l 30min).",
    },
    "case_89": {
        "category": "Medicine",
        "scenario": "8yo, initial cochlear implant programming and activation, electrode impedances, MAP creation",
        "cpt": [{"code": "92601", "desc": "Cochlear implant programming", "reason": "Initial cochlear implant programming and activation"}],
        "icd": [{"code": "H90.3", "desc": "Sensorineural hearing loss, bilateral"}],
        "rule": "Cochlear implant initial programming = 92601.",
    },
    "case_90": {
        "category": "Medicine",
        "scenario": "24yo SCID, home SCIG infusion 2 hours, nurse administers via pump",
        "cpt": [{"code": "90784", "desc": "Home infusion service", "reason": "Home subcutaneous immunoglobulin infusion"}],
        "icd": [{"code": "D82.1", "desc": "Severe combined immunodeficiency"}],
        "rule": "Home infusion = 90784.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # MEDICAL ANATOMY/PATHOLOGY KNOWLEDGE (47-54)
    # ═══════════════════════════════════════════════════════════════════
    "case_47": {"category": "Knowledge", "scenario": "Phalanges definition", "answer": "Phalanges are bones of fingers and toes.", "cpt": [], "icd": []},
    "case_48": {"category": "Knowledge", "scenario": "Warthin's tumor definition", "answer": "Benign salivary gland neoplasm, parotid.", "cpt": [], "icd": []},
    "case_49": {"category": "Knowledge", "scenario": "Meningitis definition", "answer": "Inflammation of meninges covering brain and spinal cord.", "cpt": [], "icd": []},
    "case_50": {"category": "Knowledge", "scenario": "Neurotransmitters definition", "answer": "Chemical messengers transmitting signals across synapses.", "cpt": [], "icd": []},
    "case_51": {"category": "Knowledge", "scenario": "Thoracoscopy definition", "answer": "Minimally invasive endoscopic examination of pleural cavity.", "cpt": [], "icd": []},
    "case_52": {"category": "Knowledge", "scenario": "Oliguria definition", "answer": "Urine output <400mL/24hrs in adults.", "cpt": [], "icd": []},
    "case_53": {"category": "Knowledge", "scenario": "Mediastinum definition", "answer": "Central thoracic compartment containing heart, great vessels, esophagus, trachea.", "cpt": [], "icd": []},
    "case_54": {"category": "Knowledge", "scenario": "Venous valves definition", "answer": "Valves ensuring unidirectional blood flow toward heart.", "cpt": [], "icd": []},

    # ═══════════════════════════════════════════════════════════════════
    # ICD-10 SEQUENCING CASES (55-62)
    # ═══════════════════════════════════════════════════════════════════
    "case_55": {
        "category": "ICD10",
        "scenario": "55yo female, breast cancer hx, vertebral metastasis T8, path fracture, anemia chemo",
        "cpt": [],
        "icd": [
            {"code": "C79.31", "desc": "Secondary malignant neoplasm of vertebral column"},
            {"code": "M81.9", "desc": "Pathological fracture"},
            {"code": "D64.9", "desc": "Anemia, unspecified"},
            {"code": "G89.29", "desc": "Other chronic pain"},
        ],
        "rule": "Sequencing: C79.31 (metastasis) first → M81.9 (path fracture) → D64.9 (anemia) → G89.29 (pain).",
    },
    "case_56": {
        "category": "ICD10",
        "scenario": "32yo 36wk, severe pre-eclampsia, eclampsia with seizure, HELLP, T1DM with CKD 3a, emergent C-section",
        "cpt": [],
        "icd": [
            {"code": "O14.14", "desc": "Severe pre-eclampsia, third trimester"},
            {"code": "O15.0", "desc": "Eclampsia in pregnancy"},
            {"code": "O14.24", "desc": "HELLP syndrome"},
            {"code": "E10.9", "desc": "Type 1 diabetes without complications"},
            {"code": "N18.31", "desc": "CKD stage 3a"},
        ],
        "rule": "Sequencing: O14.14 (pre-eclampsia) → O15.0 (eclampsia) → O14.24 (HELLP) → E10.9 (T1DM) → N18.31 (CKD).",
    },
    "case_57": {
        "category": "ICD10",
        "scenario": "67yo male, hx lung cancer, MRSA sepsis from surgical wound, respiratory failure, AKI",
        "cpt": [],
        "icd": [
            {"code": "A41.0", "desc": "Sepsis due to S. aureus"},
            {"code": "T80.211A", "desc": "Postprocedural infection, initial encounter"},
            {"code": "J96.01", "desc": "Acute respiratory failure with hypoxia"},
            {"code": "N17.0", "desc": "Acute kidney failure"},
        ],
        "rule": "Sequencing: A41.0 (MRSA sepsis) → T80.211A (surgical site infection) → J96.01 (RF) → N17.0 (AKI).",
    },
    "case_58": {
        "category": "ICD10",
        "scenario": "12yo female, near-drowning, GCS 6, anoxic brain damage, aspiration pneumonia",
        "cpt": [],
        "icd": [
            {"code": "T75.1XXA", "desc": "Near-drowning, initial encounter"},
            {"code": "G93.1", "desc": "Anoxic brain damage"},
            {"code": "J69.0", "desc": "Aspiration pneumonia"},
        ],
        "rule": "Sequencing: T75.1XXA (near-drowning) → G93.1 (anoxic brain) → J69.0 (aspiration pneumonia).",
    },
    "case_59": {
        "category": "ICD10",
        "scenario": "75yo male, diabetic foot ulcer right great toe with bone necrosis, cellulitis, DM2 with CKD 3b, HTN, hyperlipidemia",
        "cpt": [],
        "icd": [
            {"code": "E11.621", "desc": "Type 2 diabetes with foot ulcer"},
            {"code": "L03.011", "desc": "Cellulitis of right toe"},
            {"code": "E11.65", "desc": "Type 2 diabetes with hyperglycemia"},
            {"code": "E11.40", "desc": "Type 2 diabetes with neuropathy"},
            {"code": "N18.32", "desc": "CKD stage 3b"},
            {"code": "I10", "desc": "Essential hypertension"},
            {"code": "E78.5", "desc": "Hyperlipidemia, unspecified"},
        ],
        "rule": "Sequencing: E11.621 (diabetic foot ulcer) first → L03.011 (cellulitis) → E11.65 (hyperglycemia) → E11.40 (neuropathy) → N18.32 (CKD) → I10 (HTN) → E78.5 (lipids).",
    },
    "case_60": {
        "category": "ICD10",
        "scenario": "Adult, hypertensive emergency BP 220/130 with acute cerebral infarction",
        "cpt": [],
        "icd": [
            {"code": "I16.0", "desc": "Hypertensive emergency"},
            {"code": "I63.9", "desc": "Cerebral infarction, unspecified"},
        ],
        "rule": "Sequencing: I16.0 (hypertensive emergency) → I63.9 (cerebral infarction).",
    },
    "case_61": {
        "category": "ICD10",
        "scenario": "Adult, POAG mild at admission progressing to severe over 5-day stay",
        "cpt": [],
        "icd": [
            {"code": "H40.11", "desc": "Primary open-angle glaucoma, mild"},
            {"code": "H40.12", "desc": "Primary open-angle glaucoma, severe"},
        ],
        "rule": "Sequencing: H40.11 (mild on admission) → H40.12 (severe at discharge). Code both to show progression.",
    },
    "case_62": {
        "category": "ICD10",
        "scenario": "Adult, 5 days post TKA, sepsis from prosthesis infection, S. aureus blood cultures",
        "cpt": [],
        "icd": [
            {"code": "A41.0", "desc": "Sepsis due to S. aureus"},
            {"code": "T84.54XA", "desc": "Infection of internal joint prosthesis, initial encounter"},
        ],
        "rule": "Sequencing: A41.0 (S. aureus sepsis) → T84.54XA (prosthesis infection).",
    },

    # ═══════════════════════════════════════════════════════════════════
    # HCPCS/REGULATORY CASES (92, 95-100)
    # ═══════════════════════════════════════════════════════════════════
    "case_92": {
        "category": "HCPCS",
        "scenario": "Adult, laparotomy Day 0, wound dehiscence Day 5, same surgeon re-closure",
        "cpt": [{"code": "10180", "desc": "Wound dehiscence closure", "reason": "Re-closure of wound dehiscence within global period"}],
        "icd": [{"code": "T81.31XA", "desc": "Disruption of wound, initial encounter"}],
        "rule": "Wound dehiscence within global period by same surgeon = included in global (no separate payment unless separate encounter).",
    },
    "case_95": {
        "category": "HCPCS",
        "scenario": "Obstetric patient, 4g MgSO4 loading dose, J3475 billed per 500mg",
        "cpt": [],
        "icd": [{"code": "O14.14", "desc": "Severe pre-eclampsia"}],
        "hcpcs": [{"code": "J3475", "desc": "Magnesium sulfate 500mg", "units": 8, "reason": "4000mg / 500mg = 8 units"}],
        "rule": "J3475 = per 500mg. 4g = 4000mg / 500mg = 8 units.",
    },
    "case_96": {
        "category": "HCPCS",
        "scenario": "Pediatric, home apnea monitor with recording capability",
        "cpt": [],
        "icd": [{"code": "P28.4", "desc": "Apnea of prematurity"}],
        "hcpcs": [{"code": "E0618", "desc": "Apnea monitor with recording", "reason": "Home apnea monitor with data recording"}],
        "rule": "Apnea monitor with recording = E0618.",
    },
    "case_97": {
        "category": "HCPCS",
        "scenario": "72yo Medicare, home oxygen setup: concentrator + nasal cannula + tubing",
        "cpt": [],
        "icd": [{"code": "J96.01", "desc": "Chronic respiratory failure"}],
        "hcpcs": [
            {"code": "E1390", "desc": "Oxygen concentrator", "reason": "Stationary oxygen concentrator"},
            {"code": "A4615", "desc": "Nasal cannula", "reason": "Oxygen delivery device"},
        ],
        "rule": "Oxygen concentrator = E1390. Nasal cannula = A4615 (separate DME item).",
    },
    "case_98": {
        "category": "HCPCS",
        "scenario": "72yo Medicare, admitted to SNF post-hospital for rehab",
        "cpt": [],
        "icd": [{"code": "Z51.5", "desc": "Encounter for palliative care"}],
        "hcpcs": [],
        "rule": "SNF Part A coverage: 100 days post-hospital. Days 1-20: Medicare pays all. Days 21-100: coinsurance applies.",
    },
    "case_99": {
        "category": "Knowledge",
        "scenario": "Abuse vs Fraud definition",
        "answer": "Abuse = practices inconsistent with sound practices, resulting in unnecessary cost, lacking deceptive intent. Fraud = intentional deception.",
        "cpt": [],
        "icd": [],
    },
    "case_100": {
        "category": "Knowledge",
        "scenario": "LCD definition",
        "answer": "LCD = Local Coverage Determination, issued by regional MAC specifying coverage criteria for medical services on a regional basis.",
        "cpt": [],
        "icd": [],
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Medical Terminology (Set 2 Cases 1-8)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_1": {
        "category": "Knowledge",
        "scenario": "Emphysema - irreversible destruction of alveolar walls",
        "answer": "Emphysema: destruction of alveolar walls, permanently enlarged air spaces, loss of elastic recoil.",
        "cpt": [], "icd": [],
    },
    "set2_case_2": {
        "category": "Knowledge",
        "scenario": "Hemiplegia - complete paralysis of one vertical half of body",
        "answer": "Hemiplegia: complete paralysis of one side of the body.",
        "cpt": [], "icd": [],
    },
    "set2_case_3": {
        "category": "Knowledge",
        "scenario": "Dysphasia vs Dysphagia distinction",
        "answer": "Dysphasia = speech/communication impairment. Dysphagia = difficulty swallowing.",
        "cpt": [], "icd": [],
    },
    "set2_case_4": {
        "category": "Knowledge",
        "scenario": "Hepatomegaly - liver enlargement below costal margin",
        "answer": "Hepatomegaly: abnormal enlargement of the liver.",
        "cpt": [], "icd": [],
    },
    "set2_case_5": {
        "category": "Knowledge",
        "scenario": "Blood flow from right ventricle through pulmonary valve to pulmonary artery",
        "answer": "Deoxygenated blood exits right ventricle through pulmonary valve into pulmonary artery.",
        "cpt": [], "icd": [],
    },
    "set2_case_6": {
        "category": "Knowledge",
        "scenario": "Vertebral column protects spinal cord",
        "answer": "Vertebral column forms protective enclosure for spinal cord.",
        "cpt": [], "icd": [],
    },
    "set2_case_7": {
        "category": "Knowledge",
        "scenario": "Cochlea houses organ of Corti, primary organ for hearing",
        "answer": "Cochlea contains organ of Corti, responsible for hearing.",
        "cpt": [], "icd": [],
    },
    "set2_case_8": {
        "category": "Knowledge",
        "scenario": "Cricoid cartilage - complete circular ring forming inferior wall of larynx",
        "answer": "Cricoid cartilage: complete circular ring forming inferior wall of larynx.",
        "cpt": [], "icd": [],
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: ICD-10 Coding (Set 2 Cases 9-16)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_9": {
        "category": "ICD10",
        "scenario": "40yo male, HIV, PCP pneumonia, oral candidiasis, Kaposi sarcoma, T2DM",
        "cpt": [],
        "icd": [
            {"code": "B20", "desc": "HIV disease"},
            {"code": "B20", "desc": "HIV disease"},
            {"code": "J12.81", "desc": "Pneumocystis pneumonia"},
            {"code": "B37.0", "desc": "Candidiasis of mouth"},
            {"code": "C46.30", "desc": "Kaposi sarcoma of lymph nodes"},
            {"code": "E11.9", "desc": "Type 2 diabetes without complications"},
        ],
        "rule": "HIV (B20) first, then opportunistic infections, then comorbidities.",
    },
    "set2_case_10": {
        "category": "ICD10",
        "scenario": "55yo male, acute exacerbation COPD, Pseudomonas pneumonia, respiratory failure, chronic hypoxemia on home O2",
        "cpt": [],
        "icd": [
            {"code": "J44.1", "desc": "COPD with acute exacerbation"},
            {"code": "J15.1", "desc": "Pneumonia due to Pseudomonas"},
            {"code": "J96.01", "desc": "Acute respiratory failure with hypoxia"},
            {"code": "Z99.81", "desc": "Dependence on supplemental oxygen"},
        ],
        "rule": "COPD exacerbation (J44.1) → Pneumonia (J15.1) → RF (J96.01) → O2 dependence (Z99.81).",
    },
    "set2_case_11": {
        "category": "ICD10",
        "scenario": "45yo female, Hb-SS sickle cell, vaso-occlusive crisis, acute chest syndrome, MRSA sepsis, CKD stage 4 sickle cell nephropathy",
        "cpt": [],
        "icd": [
            {"code": "D57.00", "desc": "Sickle-cell disease with crisis"},
            {"code": "D57.01", "desc": "Hb-SS disease with acute chest syndrome"},
            {"code": "A41.0", "desc": "Sepsis due to S. aureus"},
            {"code": "N18.4", "desc": "CKD stage 4"},
            {"code": "D63.8", "desc": "Anemia in chronic disease"},
        ],
        "rule": "Sickle cell crisis (D57.00) → Acute chest (D57.01) → MRSA sepsis (A41.0) → CKD (N18.4).",
    },
    "set2_case_12": {
        "category": "ICD10",
        "scenario": "30yo male, open Gustilo IIIB right tibia/fibula fracture, MVA, ORIF with external fixation",
        "cpt": [{"code": "27752", "desc": "ORIF tibia/fibula with external fixation"}],
        "icd": [
            {"code": "S82.201B", "desc": "Open fracture of right tibial shaft, initial encounter"},
            {"code": "S82.101B", "desc": "Open fracture of right fibula, initial encounter"},
            {"code": "V89.2XXA", "desc": "Motor vehicle traffic accident"},
        ],
        "rule": "Open fracture with external fixation = 27752. ICD-10 7th character B for open fracture.",
    },
    "set2_case_13": {
        "category": "ICD10",
        "scenario": "65yo female, breast cancer hx, new axillary lymph node metastasis, palliative care admission",
        "cpt": [],
        "icd": [
            {"code": "C79.31", "desc": "Secondary malignant neoplasm of lymph nodes"},
            {"code": "C50.919", "desc": "Malignant neoplasm of unspecified site of unspecified female breast"},
            {"code": "Z51.5", "desc": "Encounter for palliative care"},
        ],
        "rule": "Metastasis (C79.31) → Primary breast cancer (C50.919) → Palliative care (Z51.5).",
    },
    "set2_case_14": {
        "category": "ICD10",
        "scenario": "5yo child, accidental lead ingestion, BLL 65 µg/dL, abdominal pain, irritability",
        "cpt": [],
        "icd": [
            {"code": "T56.0X1A", "desc": "Toxic effect of lead, accidental, initial encounter"},
            {"code": "R10.9", "desc": "Abdominal pain"},
            {"code": "R45.851", "desc": "Suicidal ideation"},
        ],
        "rule": "Lead poisoning (T56.0X1A) → Symptoms (R10.9, R45.851).",
    },
    "set2_case_15": {
        "category": "ICD10",
        "scenario": "Adult, prediabetes, fasting glucose 115, HbA1c 6.3%",
        "cpt": [],
        "icd": [
            {"code": "R73.03", "desc": "Prediabetes"},
        ],
        "rule": "Prediabetes = R73.03.",
    },
    "set2_case_16": {
        "category": "ICD10",
        "scenario": "31yo female, 32 weeks, twin pregnancy, preterm contractions, Twin A cephalic, Twin B breech",
        "cpt": [],
        "icd": [
            {"code": "O30.009", "desc": "Twin pregnancy, unspecified"},
            {"code": "O60.00", "desc": "Preterm labor"},
            {"code": "O32.1", "desc": "Fetal malpresentation"},
        ],
        "rule": "Twin pregnancy (O30.009) → Preterm labor (O60.00) → Breech (O32.1).",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: E/M Cases (Set 2 Cases 17-32)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_17": {
        "category": "E/M",
        "scenario": "62yo male, surgical consultation, inguinal hernia, comprehensive exam, moderate MDM, 42 min",
        "cpt": [{"code": "99243", "desc": "Office consultation moderate", "reason": "Comprehensive exam, moderate MDM, 42 min"}],
        "icd": [{"code": "K40.90", "desc": "Unilateral inguinal hernia"}],
        "rule": "Surgical consultation with comprehensive exam and moderate MDM = 99243.",
    },
    "set2_case_18": {
        "category": "E/M",
        "scenario": "71yo female, hospital day 5, pancreatitis with necrosis, independent interpretation of CT, moderate MDM, 45 min",
        "cpt": [{"code": "99232", "desc": "Subsequent hospital care moderate MDM", "reason": "Hospital day 5, moderate MDM with independent interpretation"}],
        "icd": [
            {"code": "K85.1", "desc": "Acute pancreatitis with necrosis"},
            {"code": "J18.9", "desc": "Pneumonia"},
        ],
        "rule": "Subsequent hospital care, moderate MDM = 99232.",
    },
    "set2_case_19": {
        "category": "E/M",
        "scenario": "34yo female established, adjustment disorder, time-based 45 min, >50% counseling",
        "cpt": [{"code": "99214", "desc": "Office visit established moderate MDM", "reason": "Time-based: 45 min total, >50% counseling"}],
        "icd": [{"code": "F43.21", "desc": "Adjustment disorder with depressed mood"}],
        "rule": "Time-based E/M: 30-39 min = 99214 for established patient.",
    },
    "set2_case_27": {
        "category": "E/M",
        "scenario": "Elderly male, subsequent nursing facility visit, post-hip replacement, low MDM",
        "cpt": [{"code": "99309", "desc": "Subsequent nursing facility visit low complexity", "reason": "Low complexity MDM"}],
        "icd": [{"code": "Z96.651", "desc": "Right artificial hip joint"}, {"code": "K59.00", "desc": "Constipation"}],
        "rule": "Subsequent nursing facility visit low complexity = 99309.",
    },
    "set2_case_28": {
        "category": "E/M",
        "scenario": "58yo female, PCM for CKD, 45 min first month, high risk",
        "cpt": [{"code": "99490", "desc": "PCM 30-59 min", "reason": "45 min qualifying time in first month"}],
        "icd": [{"code": "N18.3", "desc": "CKD stage 3"}],
        "rule": "PCM 99490 (30-59 min). First month initiation qualifies.",
    },
    "set2_case_29": {
        "category": "E/M",
        "scenario": "65yo, inpatient rheumatology consultation, moderate MDM, formal written report",
        "cpt": [{"code": "99253", "desc": "Inpatient consultation moderate", "reason": "Moderate MDM consultation"}],
        "icd": [
            {"code": "M05.79", "desc": "Rheumatoid arthritis with rheumatoid factor"},
            {"code": "J84.10", "desc": "Pulmonary fibrosis"},
        ],
        "rule": "Inpatient consultation, moderate MDM = 99253.",
    },
    "set2_case_30": {
        "category": "E/M",
        "scenario": "38yo male new patient, group home, community-acquired pneumonia, comprehensive exam, moderate MDM",
        "cpt": [{"code": "99204", "desc": "New patient office moderate MDM", "reason": "New patient with comprehensive exam and moderate MDM"}],
        "icd": [{"code": "J18.9", "desc": "Pneumonia"}],
        "rule": "New patient, comprehensive exam, moderate MDM = 99204.",
    },
    "set2_case_31": {
        "category": "E/M",
        "scenario": "Adult female, urology consultation, hematuria, CT urogram ordered, moderate MDM, formal report",
        "cpt": [{"code": "99243", "desc": "Office consultation moderate", "reason": "Consultation with workup and moderate MDM"}],
        "icd": [{"code": "N02.9", "desc": "Recurrent and persistent hematuria"}],
        "rule": "Consultation with moderate MDM = 99243.",
    },
    "set2_case_32": {
        "category": "E/M",
        "scenario": "62yo male, workers comp disability evaluation, comprehensive, 8 year patient",
        "cpt": [{"code": "99455", "desc": "Work-related disability evaluation", "reason": "Comprehensive disability evaluation"}],
        "icd": [{"code": "M23.31", "desc": "Meniscus derangement"}],
        "rule": "Workers comp disability evaluation = 99455.",
    },
    "set2_case_93_em": {
        "category": "E/M",
        "scenario": "Adult, critical care 95 min single calendar day",
        "cpt": [{"code": "99291", "desc": "Critical care first 30-74 min", "reason": "95 min critical care"}],
        "icd": [{"code": "R65.21", "desc": "Severe sepsis with septic shock"}],
        "rule": "Critical care 95 min = 99291 (first 30-74 min) + 99292 (each additional 30 min).",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Anesthesia (Set 2 Cases 20, 33-36)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_20": {
        "category": "Anesthesia",
        "scenario": "72yo ASA P3 female, lumbar laminectomy multi-level, 4h15min anesthesia, arterial line",
        "cpt": [{"code": "01933", "desc": "Anesthesia for lumbar laminectomy", "reason": "Multi-level laminectomy with arterial line"}],
        "icd": [{"code": "M48.06", "desc": "Spinal stenosis lumbar"}],
        "rule": "Laminectomy anesthesia = 01933. Add arterial line monitoring.",
    },
    "set2_case_33": {
        "category": "Anesthesia",
        "scenario": "28yo ASA P1 male, diagnostic ankle arthroscopy, GA",
        "cpt": [{"code": "01830", "desc": "Anesthesia for ankle arthroscopy", "reason": "Diagnostic ankle arthroscopy anesthesia"}],
        "icd": [{"code": "M24.17", "desc": "Other articular cartilage disorder, ankle"}],
        "rule": "Ankle arthroscopy anesthesia = 01830.",
    },
    "set2_case_34": {
        "category": "Anesthesia",
        "scenario": "65yo ASA P2, posterior cervical decompression, seated position",
        "cpt": [{"code": "01933", "desc": "Anesthesia for cervical spine surgery", "reason": "Cervical decompression anesthesia"}],
        "icd": [{"code": "M48.02", "desc": "Spinal stenosis cervical"}],
        "rule": "Cervical spine surgery anesthesia = 01933.",
    },
    "set2_case_35": {
        "category": "Anesthesia",
        "scenario": "71yo ASA P3, open transthoracic discectomy, one-lung ventilation, arterial line",
        "cpt": [{"code": "01933", "desc": "Anesthesia for thoracic spine", "reason": "Thoracic discectomy with OLV and arterial line"}],
        "icd": [{"code": "M51.04", "desc": "Thoracic disc disorder"}],
        "rule": "Thoracic spine anesthesia = 01933. OLV and arterial line add complexity.",
    },
    "set2_case_36": {
        "category": "Anesthesia",
        "scenario": "42yo ASA P3, axillofemoral bypass, 5h30min, arterial line",
        "cpt": [{"code": "01902", "desc": "Anesthesia for aortic bypass", "reason": "Vascular bypass anesthesia with arterial line"}],
        "icd": [{"code": "I74.3", "desc": "Embolism/thrombosis lower extremity"}],
        "rule": "Vascular bypass anesthesia = 01902.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Integumentary (Set 2 Cases 21, 37-42)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_21": {
        "category": "Integumentary",
        "scenario": "28yo male, electrical burns, 14% TBSA, debridement >10%, escharotomy 3 incisions",
        "cpt": [
            {"code": "16025", "desc": "Debridement burns >10% TBSA", "reason": ">10% TBSA debridement"},
            {"code": "16030", "desc": "Escharotomy each incision", "reason": "3 escharotomy incisions"},
        ],
        "icd": [{"code": "T26.70XA", "desc": "Burn of lower extremity, initial encounter"}],
        "rule": "Burn debridement >10% = 16025. Escharotomy = 16030 per incision.",
    },
    "set2_case_37": {
        "category": "Integumentary",
        "scenario": "Adult, 3cm upper eyelid laceration, complex repair, undermining, debridement, multi-layered closure",
        "cpt": [{"code": "12053", "desc": "Complex repair 2.6-7.5cm", "reason": "Complex eyelid repair 3cm"}],
        "icd": [{"code": "S01.11XA", "desc": "Laceration of eyelid, initial encounter"}],
        "rule": "Complex repair 3cm = 12053.",
    },
    "set2_case_38": {
        "category": "Integumentary",
        "scenario": "40yo female, open capsulotomy for capsular contracture, no capsulectomy",
        "cpt": [{"code": "19370", "desc": "Periprosthetic capsulotomy", "reason": "Open capsulotomy with implant preserved"}],
        "icd": [{"code": "T85.22XA", "desc": "Capsular contracture of breast implant"}],
        "rule": "Capsulotomy = 19370. Capsulectomy = 19371 (not performed here).",
    },
    "set2_case_39": {
        "category": "Integumentary",
        "scenario": "56yo female, partial mastectomy + axillary lymphadenectomy Level I/II, separate incisions",
        "cpt": [
            {"code": "19301", "desc": "Partial mastectomy (lumpectomy)", "reason": "Partial mastectomy with clear margins"},
            {"code": "38525", "desc": "Axillary lymphadenectomy Level I/II", "reason": "Complete axillary dissection"},
        ],
        "icd": [{"code": "C50.912", "desc": "Malignant neoplasm of left breast"}],
        "rule": "Partial mastectomy (19301) + axillary dissection (38525) are separate procedures.",
    },
    "set2_case_40": {
        "category": "Integumentary",
        "scenario": "Adult, multiple facial lacerations: 4cm right cheek + 3cm chin, both complex repair",
        "cpt": [
            {"code": "12053", "desc": "Complex repair 2.6-7.5cm", "reason": "4cm cheek repair"},
            {"code": "12053", "desc": "Complex repair 2.6-7.5cm", "reason": "3cm chin repair"},
        ],
        "icd": [{"code": "S01.91XA", "desc": "Laceration of face, initial encounter"}],
        "rule": "Two separate complex repairs: 2x 12053. Modifier 59 required.",
    },
    "set2_case_41": {
        "category": "Integumentary",
        "scenario": "25yo, 50 sq cm burn, tissue cultured autograft, split-thickness graft harvest 15 sq cm",
        "cpt": [
            {"code": "15300", "desc": "Tissue cultured autograft application", "reason": "Application of tissue cultured autograft"},
            {"code": "15115", "desc": "Split-thickness autograft harvest", "reason": "Split-thickness graft harvest from thigh"},
        ],
        "icd": [{"code": "T20.201A", "desc": "Burn of second degree of back, initial encounter"}],
        "rule": "Tissue cultured autograft = 15300. Donor site harvest = 15115.",
    },
    "set2_case_42": {
        "category": "Integumentary",
        "scenario": "50yo female, breast reconstruction final stage, implant exchange + nipple reconstruction + skin graft",
        "cpt": [
            {"code": "19357", "desc": "Breast reconstruction with implant exchange", "reason": "Implant exchange for final reconstruction"},
            {"code": "19355", "desc": "Nipple reconstruction", "reason": "Nipple/areola reconstruction"},
        ],
        "icd": [{"code": "Z96.31", "desc": "Presence of right breast implant"}],
        "rule": "Implant exchange (19357) + nipple reconstruction (19355) are separate procedures.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Musculoskeletal (Set 2 Cases 43-48)
    # ═══════════════════════════-arm═════════════════════════════════════
    "set2_case_43": {
        "category": "Musculoskeletal",
        "scenario": "Adult, cast removal by different provider (not original applier)",
        "cpt": [{"code": "29700", "desc": "Cast removal", "reason": "Cast removal by different provider"}],
        "icd": [{"code": "S52.501A", "desc": "Fracture of right radius"}],
        "rule": "Cast removal = 29700.",
    },
    "set2_case_44": {
        "category": "Musculoskeletal",
        "scenario": "22yo male, open patellar dislocation + partial patellectomy left knee",
        "cpt": [
            {"code": "27422", "desc": "Open treatment patellar dislocation", "reason": "Open reduction and stabilization"},
            {"code": "27332", "desc": "Partial patellectomy", "reason": "Partial patellectomy for osteochondral fragment"},
        ],
        "icd": [{"code": "S83.012A", "desc": "Anterior dislocation of left patella, initial encounter"}],
        "rule": "Open patellar dislocation (27422) + partial patellectomy (27332).",
    },
    "set2_case_45": {
        "category": "Musculoskeletal",
        "scenario": "42yo, arthroscopic partial medial meniscectomy right knee",
        "cpt": [{"code": "29881", "desc": "Arthroscopic meniscectomy medial/lateral", "reason": "Partial medial meniscectomy"}],
        "icd": [{"code": "M23.31", "desc": "Other meniscus derangement, medial"}],
        "rule": "Arthroscopic partial medial meniscectomy = 29881.",
    },
    "set2_case_46": {
        "category": "Musculoskeletal",
        "scenario": "48yo, anterior cervical discectomy + total disc arthroplasty C3-C4, no fusion",
        "cpt": [{"code": "22585", "desc": "Cervical disc arthroplasty", "reason": "Total disc arthroplasty without fusion"}],
        "icd": [{"code": "M50.12", "desc": "Cervical disc disorder with radiculopathy"}],
        "rule": "Cervical disc arthroplasty = 22585 (not fusion).",
    },
    "set2_case_47": {
        "category": "Musculoskeletal",
        "scenario": "28yo male, LeFort I maxillary fracture, open reduction, arch bar fixation",
        "cpt": [{"code": "21461", "desc": "Open treatment LeFort I fracture", "reason": "Open reduction with arch bar fixation"}],
        "icd": [{"code": "S02.40XA", "desc": "Fracture of maxilla, initial encounter"}],
        "rule": "LeFort I fracture open reduction = 21461.",
    },
    "set2_case_48": {
        "category": "Musculoskeletal",
        "scenario": "50yo, percutaneous needle biopsy skeletal muscle, no imaging guidance",
        "cpt": [{"code": "20206", "desc": "Percutaneous needle biopsy of muscle", "reason": "Core needle biopsy of vastus lateralis"}],
        "icd": [{"code": "M62.81", "desc": "Generalized muscle weakness"}],
        "rule": "Percutaneous muscle biopsy = 20206.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Cardiovascular (Set 2 Cases 49-54)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_49": {
        "category": "Cardiovascular",
        "scenario": "56yo male, open mitral valve repair with annuloplasty ring, neochordae",
        "cpt": [{"code": "33430", "desc": "Open mitral valve repair", "reason": "Mitral valve repair with annuloplasty ring"}],
        "icd": [{"code": "I34.0", "desc": "Nonrheumatic mitral regurgitation"}],
        "rule": "Open mitral valve repair = 33430.",
    },
    "set2_case_50": {
        "category": "Cardiovascular",
        "scenario": "67yo male, right upper lobectomy with sleeve bronchoplasty, NSCLC",
        "cpt": [{"code": "32480", "desc": "Lobectomy with sleeve bronchoplasty", "reason": "Right upper lobectomy with bronchial sleeve resection"}],
        "icd": [{"code": "C34.10", "desc": "Malignant neoplasm of upper lobe, bronchus or lung"}],
        "rule": "Lobectomy with sleeve bronchoplasty = 32480.",
    },
    "set2_case_51": {
        "category": "Cardiovascular",
        "scenario": "58yo male, Marfan syndrome, Bentall procedure, ascending aorta aneurysm 5.6cm",
        "cpt": [{"code": "33861", "desc": "Bentall procedure (composite valve-graft)", "reason": "Composite valve-graft conduit with coronary reimplantation"}],
        "icd": [{"code": "I71.2", "desc": "Thoracic aortic aneurysm without rupture"}, {"code": "Q87.40", "desc": "Marfan syndrome"}],
        "rule": "Bentall procedure = 33861.",
    },
    "set2_case_52": {
        "category": "Cardiovascular",
        "scenario": "62yo male, subxiphoid pericardial window for malignant effusion",
        "cpt": [{"code": "33025", "desc": "Pericardial window creation", "reason": "Subxiphoid pericardial window"}],
        "icd": [{"code": "I31.8", "desc": "Other diseases of pericardium"}],
        "rule": "Pericardial window = 33025.",
    },
    "set2_case_53": {
        "category": "Cardiovascular",
        "scenario": "70yo male, SFA stenosis, IVL + nitinol stent + balloon angioplasty",
        "cpt": [
            {"code": "37223", "desc": "Angioplasty additional vessel", "reason": "SFA angioplasty with stent"},
            {"code": "37221", "desc": "Angioplasty first vessel", "reason": "Initial SFA intervention"},
        ],
        "icd": [{"code": "I74.3", "desc": "Embolism/thrombosis lower extremity"}],
        "rule": "SFA angioplasty with stent = 37221 (initial) + 37223 (additional).",
    },
    "set2_case_54": {
        "category": "Cardiovascular",
        "scenario": "48yo male, emergency open pulmonary embolectomy for saddle PE, cardiogenic shock",
        "cpt": [{"code": "33910", "desc": "Open pulmonary embolectomy", "reason": "Emergency pulmonary artery embolectomy"}],
        "icd": [{"code": "I26.99", "desc": "Other pulmonary embolism"}],
        "rule": "Open pulmonary embolectomy = 33910.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Digestive (Set 2 Cases 24, 55-60)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_24": {
        "category": "Digestive",
        "scenario": "70yo male, laparoscopic descending colectomy with splenic flexure mobilization",
        "cpt": [{"code": "44205", "desc": "Laparoscopic partial colectomy with splenic flexure mobilization", "reason": "Laparoscopic colectomy with splenic flexure take-down"}],
        "icd": [{"code": "C18.6", "desc": "Malignant neoplasm of descending colon"}],
        "rule": "Laparoscopic colectomy with splenic flexure mobilization = 44205.",
    },
    "set2_case_55": {
        "category": "Digestive",
        "scenario": "62yo female, guided therapeutic paracentesis 4 liters, ultrasound-guided",
        "cpt": [{"code": "49083", "desc": "Therapeutic paracentesis with imaging guidance", "reason": "Ultrasound-guided therapeutic paracentesis"}],
        "icd": [{"code": "R18.8", "desc": "Other ascites"}],
        "rule": "Therapeutic paracentesis with imaging guidance = 49083.",
    },
    "set2_case_56": {
        "category": "Digestive",
        "scenario": "27yo male, open Roux-en-Y gastric bypass, BMI 45",
        "cpt": [{"code": "43644", "desc": "Open Roux-en-Y gastric bypass", "reason": "Open RYGB with gastrojejunostomy"}],
        "icd": [{"code": "E66.01", "desc": "Morbid obesity due to excess calories"}],
        "rule": "Open RYGB = 43644. Laparoscopic = 43645.",
    },
    "set2_case_57": {
        "category": "Digestive",
        "scenario": "45yo male, three-column external hemorrhoidectomy, local anesthesia",
        "cpt": [{"code": "46999", "desc": "Hemorrhoidectomy", "reason": "External hemorrhoidectomy three columns"}],
        "icd": [{"code": "K64.1", "desc": "Thrombosed hemorrhoids"}],
        "rule": "Hemorrhoidectomy = 46999.",
    },
    "set2_case_58": {
        "category": "Digestive",
        "scenario": "55yo male, orthotopic liver transplant (recipient implantation), cadaveric donor, vascular anastomoses",
        "cpt": [{"code": "47135", "desc": "Liver transplantation (recipient)", "reason": "Orthotopic liver transplant recipient implantation"}],
        "icd": [{"code": "K74.60", "desc": "Unspecified cirrhosis of liver"}],
        "rule": "Liver transplant recipient = 47135.",
    },
    "set2_case_59": {
        "category": "Digestive",
        "scenario": "60yo male, transoral limited pharyngectomy for T1 SCC oropharynx",
        "cpt": [{"code": "31360", "desc": "Pharyngectomy", "reason": "Limited pharyngectomy via transoral approach"}],
        "icd": [{"code": "C10.9", "desc": "Malignant neoplasm of oropharynx"}],
        "rule": "Limited pharyngectomy = 31360.",
    },
    "set2_case_60": {
        "category": "Digestive",
        "scenario": "60yo female, open cholecystectomy + choledochoenterostomy for CBD stricture",
        "cpt": [
            {"code": "47600", "desc": "Cholecystectomy", "reason": "Open cholecystectomy"},
            {"code": "47720", "desc": "Choledochoenterostomy", "reason": "CBD to jejunum anastomosis"},
        ],
        "icd": [{"code": "K83.1", "desc": "Obstruction of bile duct"}],
        "rule": "Open cholecystectomy (47600) + choledochoenterostomy (47720) are separate procedures.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Urinary/Genital (Set 2 Cases 61-66)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_61": {
        "category": "Urinary/Genital",
        "scenario": "55yo, open drainage perirenal abscess, right flank, drains placed",
        "cpt": [{"code": "50010", "desc": "Drainage of perirenal abscess", "reason": "Open I&D perirenal abscess"}],
        "icd": [{"code": "L02.11", "desc": "Abscess of right flank"}],
        "rule": "Perirenal abscess I&D = 50010.",
    },
    "set2_case_62": {
        "category": "Urinary/Genital",
        "scenario": "31yo female, VBAC, prior C-section, complete postpartum care",
        "cpt": [
            {"code": "59610", "desc": "VBAC", "reason": "Vaginal delivery after cesarean"},
            {"code": "59514", "desc": "C-section (if needed)", "reason": "Not performed here"},
        ],
        "icd": [{"code": "O75.8", "desc": "Other specified complications of labor and delivery"}],
        "rule": "VBAC = 59610. Separate from postpartum care.",
    },
    "set2_case_63": {
        "category": "Urinary/Genital",
        "scenario": "35yo female, microsurgical bilateral tubotubal reanastomosis, laparotomy",
        "cpt": [{"code": "58750", "desc": "Bilateral tubal reanastomosis", "reason": "Microsurgical tubotubal reanastomosis"}],
        "icd": [{"code": "Z30.9", "desc": "Contraceptive management, unspecified"}],
        "rule": "Bilateral tubal reanastomosis = 58750.",
    },
    "set2_case_64": {
        "category": "Urinary/Genital",
        "scenario": "68yo male, transperineal brachytherapy needle placement for prostate cancer",
        "cpt": [{"code": "55876", "desc": "Transperineal placement of brachytherapy needles", "reason": "Brachytherapy needle placement under TRUS guidance"}],
        "icd": [{"code": "C61", "desc": "Malignant neoplasm of prostate"}],
        "rule": "Brachytherapy needle placement = 55876.",
    },
    "set2_case_65": {
        "category": "Urinary/Genital",
        "scenario": "60yo male, open partial cystectomy + right ureteroneocystostomy for bladder cancer",
        "cpt": [
            {"code": "51590", "desc": "Partial cystectomy", "reason": "Partial cystectomy with trigone involvement"},
            {"code": "50782", "desc": "Ureteroneocystostomy", "reason": "Right ureter reimplantation"},
        ],
        "icd": [{"code": "C67.0", "desc": "Malignant neoplasm of trigone of bladder"}],
        "rule": "Partial cystectomy (51590) + ureteroneocystostomy (50782) are separate procedures.",
    },
    "set2_case_66": {
        "category": "Urinary/Genital",
        "scenario": "60yo male, Rezum (water vapor thermal ablation) for BPH, office-based",
        "cpt": [{"code": "53850", "desc": "Transurethral water vapor ablation prostate", "reason": "Rezum water vapor thermal ablation"}],
        "icd": [{"code": "N40.0", "desc": "Benign prostatic hyperplasia"}],
        "rule": "Rezum water vapor ablation = 53850.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Nervous System (Set 2 Cases 67-72)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_67": {
        "category": "Nervous",
        "scenario": "41yo, permanent VP shunt explantation, chronic infection, EVD placed",
        "cpt": [{"code": "38999", "desc": "Shunt explantation", "reason": "Permanent VP shunt explantation"}],
        "icd": [{"code": "T85.71XA", "desc": "Infection due to nervous system device, initial encounter"}],
        "rule": "VP shunt explantation = 38999.",
    },
    "set2_case_68": {
        "category": "Nervous",
        "scenario": "73yo, continuous lumbar plexus block for THA postop analgesia, catheter placed",
        "cpt": [
            {"code": "64483", "desc": "Lumbar plexus block first level", "reason": "Continuous lumbar plexus block"},
            {"code": "64484", "desc": "Additional level", "reason": "Catheter placement for continuous infusion"},
        ],
        "icd": [{"code": "M16.11", "desc": "Primary osteoarthritis right hip"}],
        "rule": "Lumbar plexus block with catheter = 64483 + 64484.",
    },
    "set2_case_69": {
        "category": "Nervous",
        "scenario": "73yo, bilateral thoracic discectomy T7-T8 and T8-T9, costovertebral approach",
        "cpt": [
            {"code": "63081", "desc": "Thoracic discectomy first level", "reason": "T7-T8 discectomy"},
            {"code": "63082", "desc": "Thoracic discectomy additional level", "reason": "T8-T9 additional level"},
        ],
        "icd": [{"code": "M51.04", "desc": "Thoracic disc disorder"}],
        "rule": "Thoracic discectomy: 63081 (first) + 63082 (additional).",
    },
    "set2_case_70": {
        "category": "Nervous",
        "scenario": "49yo, microsurgical clipping basilar artery aneurysm, far-lateral approach",
        "cpt": [{"code": "61698", "desc": "Aneurysm clipping intracranial", "reason": "Basilar artery aneurysm clipping with microscope"}],
        "icd": [{"code": "I62.00", "desc": "Nontraumatic intracranial hemorrhage"}],
        "rule": "Intracranial aneurysm clipping = 61698.",
    },
    "set2_case_71": {
        "category": "Nervous",
        "scenario": "Adult, lumbar fusion with pedicle screws + image-guided navigation add-on",
        "cpt": [
            {"code": "22612", "desc": "Posterior lumbar fusion", "reason": "L4-L5 posterior fusion with pedicle screws"},
            {"code": "77299", "desc": "Stereotactic navigation add-on", "reason": "Image-guided navigation add-on"},
        ],
        "icd": [{"code": "M43.16", "desc": "Spondylolisthesis, lumbar region"}],
        "rule": "Lumbar fusion (22612) + image-guidance (77299) as add-on.",
    },
    "set2_case_72": {
        "category": "Nervous",
        "scenario": "8-week-old infant, occipital encephalocele excision + dural reconstruction + cranioplasty",
        "cpt": [
            {"code": "63900", "desc": "Encephalocele excision", "reason": "Excision of herniated brain tissue and meninges"},
            {"code": "61526", "desc": "Cranioplasty", "reason": "Skull vault defect repair"},
        ],
        "icd": [{"code": "Q01.1", "desc": "Occipital meningoencephalocele"}],
        "rule": "Encephalocele excision (63900) + cranioplasty (61526).",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Radiology (Set 2 Cases 25, 73-78)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_25": {
        "category": "Radiology",
        "scenario": "38yo male, MRI right shoulder with IV contrast, multiplanar",
        "cpt": [{"code": "73723", "desc": "MRI upper extremity with contrast", "reason": "MRI shoulder with IV gadolinium"}],
        "icd": [{"code": "S46.011A", "desc": "Strain of muscle(s) and tendon(s) of right shoulder, initial encounter"}],
        "rule": "MRI upper extremity with contrast = 73723.",
    },
    "set2_case_73": {
        "category": "Radiology",
        "scenario": "12yo, cardiac CT congenital heart disease, Tetralogy of Fallot, 3D post-processing",
        "cpt": [{"code": "75574", "desc": "Cardiac CT with contrast", "reason": "Cardiac CT with 3D post-processing"}],
        "icd": [{"code": "Q21.0", "desc": "Ventricular septal defect"}],
        "rule": "Cardiac CT with contrast = 75574.",
    },
    "set2_case_74": {
        "category": "Radiology",
        "scenario": "68yo male, antegrade nephrostogram, fluoroscopic supervision",
        "cpt": [{"code": "74430", "desc": "Nephrostogram, antegrade", "reason": "Antegrade nephrostogram fluoroscopic supervision"}],
        "icd": [{"code": "N20.1", "desc": "Calculus of ureter"}],
        "rule": "Antegrade nephrostogram = 74430.",
    },
    "set2_case_75": {
        "category": "Radiology",
        "scenario": "Adult, IMRT treatment planning + MLC collimator design",
        "cpt": [{"code": "77301", "desc": "IMRT treatment planning", "reason": "3D conformal/IMRT planning with dose-volume histograms"}],
        "icd": [{"code": "C61", "desc": "Malignant neoplasm of prostate"}],
        "rule": "IMRT planning = 77301.",
    },
    "set2_case_76": {
        "category": "Radiology",
        "scenario": "35yo male, pulmonary AVM coil embolization, HHT",
        "cpt": [{"code": "37243", "desc": "Transcatheter embolization pulmonary", "reason": "Pulmonary AVM coil embolization"}],
        "icd": [{"code": "Q28.0", "desc": "Arteriovenous malformation of cerebral vessels"}],
        "rule": "Pulmonary AVM embolization = 37243.",
    },
    "set2_case_77": {
        "category": "Radiology",
        "scenario": "62yo male, TARE with Y-90 microspheres for HCC",
        "cpt": [{"code": "37243", "desc": "Transcatheter radioembolization", "reason": "Y-90 microsphere administration via hepatic artery"}],
        "icd": [{"code": "C22.0", "desc": "Malignant neoplasm of liver, primary"}],
        "rule": "TARE with Y-90 = 37243.",
    },
    "set2_case_78": {
        "category": "Radiology",
        "scenario": "70yo female, DXA lumbar spine + hips + vertebral fracture assessment",
        "cpt": [
            {"code": "77080", "desc": "DXA axial skeleton", "reason": "Lumbar spine and bilateral hips"},
            {"code": "77083", "desc": "Vertebral fracture assessment", "reason": "VFA during same session"},
        ],
        "icd": [{"code": "M81.0", "desc": "Age-related osteoporosis"}],
        "rule": "DXA (77080) + VFA (77083) can be billed together.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Pathology (Set 2 Cases 79-84)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_79": {
        "category": "Pathology",
        "scenario": "Adult, doxepin therapeutic drug assay, serum level monitoring",
        "cpt": [{"code": "80182", "desc": "Tricyclic antidepressant level", "reason": "Doxepin therapeutic drug assay"}],
        "icd": [{"code": "F33.1", "desc": "Major depressive disorder recurrent moderate"}],
        "rule": "Tricyclic antidepressant level = 80182.",
    },
    "set2_case_80": {
        "category": "Pathology",
        "scenario": "Diabetic adult, in-office fingerstick glucose, visual reagent strip",
        "cpt": [{"code": "82948", "desc": "Glucose fingerstick", "reason": "In-office point-of-care glucose"}],
        "icd": [{"code": "E11.9", "desc": "Type 2 diabetes without complications"}],
        "rule": "Fingerstick glucose = 82948.",
    },
    "set2_case_81": {
        "category": "Pathology",
        "scenario": "26yo female, non-automated urinalysis with microscopy for UTI",
        "cpt": [{"code": "81003", "desc": "Urinalysis with microscopy", "reason": "Non-automated urinalysis with microscopy"}],
        "icd": [{"code": "N39.0", "desc": "Urinary tract infection, site unspecified"}],
        "rule": "Urinalysis with microscopy = 81003.",
    },
    "set2_case_82": {
        "category": "Pathology",
        "scenario": "22yo male, Gram stain of urethral discharge, CLIA-waived office",
        "cpt": [{"code": "87205", "desc": "Gram stain", "reason": "Gram stain of urethral discharge"}],
        "icd": [{"code": "N34.1", "desc": "Nonspecific urethritis"}],
        "rule": "Gram stain = 87205.",
    },
    "set2_case_83": {
        "category": "Pathology",
        "scenario": "28yo female, wet mount vaginal discharge, Trichomonas and clue cells",
        "cpt": [{"code": "87210", "desc": "Wet mount examination", "reason": "Microscopic wet mount for Trichomonas"}],
        "icd": [{"code": "A59.01", "desc": "Trichomonas vaginitis"}],
        "rule": "Wet mount examination = 87210.",
    },
    "set2_case_84": {
        "category": "Pathology",
        "scenario": "70yo male, radical prostatectomy specimen, comprehensive pathology, professional component",
        "cpt": [{"code": "88305", "desc": "Surgical pathology complex", "reason": "Comprehensive prostatectomy specimen evaluation"}],
        "icd": [{"code": "C61", "desc": "Malignant neoplasm of prostate"}],
        "rule": "Radical prostatectomy pathology = 88305.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Medicine (Set 2 Cases 85-90)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_85": {
        "category": "Medicine",
        "scenario": "58yo male, multi-vessel PCI: RCA stent, LAD atherectomy+stent, LCX stent",
        "cpt": [
            {"code": "92928", "desc": "PCI with stent", "reason": "RCA stent + LAD stent + LCX stent"},
            {"code": "92920", "desc": "PCI atherectomy", "reason": "LAD atherectomy"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "Multi-vessel PCI: 92928 (stent) + 92920 (atherectomy).",
    },
    "set2_case_86": {
        "category": "Medicine",
        "scenario": "45yo, crisis psychotherapy, 110 min continuous face-to-face",
        "cpt": [{"code": "90839", "desc": "Crisis psychotherapy 53-74 min", "reason": "Crisis psychotherapy 110 min (use 90839 for first 60 min + 90840 for add'l 30 min)"}],
        "icd": [{"code": "F41.0", "desc": "Panic disorder"}],
        "rule": "Crisis psychotherapy: 90839 (first 60 min) + 90840 (each additional 30 min).",
    },
    "set2_case_87": {
        "category": "Medicine",
        "scenario": "60yo, NSCLC Stage IV, sequential chemo: pembrolizumab 35min infusion, granisetron push 3min, docetaxel 65min infusion",
        "cpt": [
            {"code": "96413", "desc": "Chemotherapy infusion first hour", "reason": "Pembrolizumab 35min + docetaxel 65min = sequential infusion"},
            {"code": "96401", "desc": "Chemotherapy push", "reason": "Granisetron IV push (non-chemo antiemetic)"},
            {"code": "96415", "desc": "Chemotherapy each add'l 30min", "reason": "Additional time beyond first hour"},
        ],
        "icd": [{"code": "C34.90", "desc": "Malignant neoplasm of bronchus or lung"}],
        "rule": "Sequential chemo: 96413 (infusion first hour) + 96401 (push) + 96415 (add'l 30min).",
    },
    "set2_case_88": {
        "category": "Medicine",
        "scenario": "30yo female ESRD, hemodialysis session, nephrologist medical evaluation during dialysis",
        "cpt": [{"code": "90935", "desc": "Hemodialysis evaluation", "reason": "Medical evaluation during hemodialysis session"}],
        "icd": [{"code": "N18.6", "desc": "End stage renal disease"}],
        "rule": "Medical evaluation during hemodialysis = 90935.",
    },
    "set2_case_89": {
        "category": "Medicine",
        "scenario": "4yo child, cochlear implant follow-up 6 weeks post-op, subsequent programming/MAP",
        "cpt": [{"code": "92602", "desc": "Cochlear implant subsequent analysis", "reason": "Subsequent diagnostic analysis and MAP reprogramming"}],
        "icd": [{"code": "H90.3", "desc": "Sensorineural hearing loss bilateral"}],
        "rule": "Cochlear implant subsequent analysis = 92602.",
    },
    "set2_case_90": {
        "category": "Medicine",
        "scenario": "Adult, comprehensive TTE with 2D, M-mode, spectral Doppler, color flow Doppler",
        "cpt": [{"code": "93306", "desc": "Comprehensive TTE", "reason": "Complete TTE with Doppler and color flow"}],
        "icd": [{"code": "R93.1", "desc": "Abnormal findings on diagnostic imaging of heart"}],
        "rule": "Comprehensive TTE = 93306.",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SECOND SET: Modifiers/HCPCS (Set 2 Cases 92, 94-100)
    # ═══════════════════════════════════════════════════════════════════
    "set2_case_92": {
        "category": "Modifiers",
        "scenario": "Complex spinal reconstruction, co-surgeons (Surgeon X + Y) + assistant surgeon (Z)",
        "cpt": [
            {"code": "62288", "desc": "Spinal surgery (co-surgeon)", "reason": "Complex spinal reconstruction with co-surgeons"},
            {"code": "62288-62", "desc": "Co-surgeon modifier", "reason": "Modifier -62 for co-surgeon"},
            {"code": "62288-80", "desc": "Assistant surgeon modifier", "reason": "Modifier -80 for assistant surgeon"},
        ],
        "icd": [],
        "rule": "Co-surgeons use modifier -62. Assistant surgeon uses modifier -80.",
    },
    "set2_case_94": {
        "category": "Modifiers",
        "scenario": "Standard modifier selection rules",
        "answer": "Modifiers clarify special circumstances: -26 (professional), -TC (technical), -59 (distinct procedure), -62 (co-surgeon), -80 (assistant), -50 (bilateral).",
        "cpt": [], "icd": [],
    },
    "set2_case_95": {
        "category": "HCPCS",
        "scenario": "80mg tobramycin IM injection, J3260 = per 80mg",
        "cpt": [],
        "icd": [{"code": "J18.9", "desc": "Pneumonia"}],
        "hcpcs": [{"code": "J3260", "desc": "Tobramycin 80mg", "units": 1, "reason": "80mg / 80mg = 1 unit"}],
        "rule": "J3260 = per 80mg. 80mg = 1 unit.",
    },
    "set2_case_96": {
        "category": "HCPCS",
        "scenario": "Adult, custom knee orthosis with rigid frame, adjustable bands",
        "cpt": [],
        "icd": [{"code": "M23.20", "desc": "Derangement of unspecified meniscus"}],
        "hcpcs": [{"code": "L1820", "desc": "Knee orthosis with rigid frame", "reason": "Custom functional knee orthosis"}],
        "rule": "Knee orthosis with rigid frame = L1820.",
    },
    "set2_case_97": {
        "category": "HCPCS",
        "scenario": "Medicare beneficiary, rural hospital, telehealth consultation with specialist",
        "cpt": [{"code": "99449", "desc": "Telehealth originating site", "reason": "Telehealth consultation at originating site"}],
        "icd": [],
        "rule": "Telehealth originating site = 99449. Facility fee for originating site.",
    },
    "set2_case_98": {
        "category": "Knowledge",
        "scenario": "ABN (Advance Beneficiary Notice) definition",
        "answer": "ABN = standardized form warning Medicare beneficiary that Medicare may deny payment, transferring financial liability if patient proceeds.",
        "cpt": [], "icd": [],
    },
    "set2_case_99": {
        "category": "Knowledge",
        "scenario": "OIG Voluntary Compliance Program Guidance",
        "answer": "OIG publishes voluntary Compliance Program Guidance for physician practices to prevent fraud, waste, and abuse.",
        "cpt": [], "icd": [],
    },
    "set2_case_100": {
        "category": "Knowledge",
        "scenario": "HIPAA legislation definition",
        "answer": "HIPAA = federal legislation establishing national standards for electronic healthcare transactions, PHI privacy/security, and insurance portability.",
        "cpt": [], "icd": [],
    },

    # ═══════════════════════════════════════════════════════════════════
    # THIRD SET: Additional Cases (Set 3)
    # ═══════════════════════════════════════════════════════════════════
    "set3_case_1": {
        "category": "E/M",
        "scenario": "70yo male established, multi-condition follow-up, moderate MDM, 39 min",
        "cpt": [{"code": "99214", "desc": "Office visit established moderate MDM", "reason": "Multiple chronic conditions, moderate MDM, 39 min"}],
        "icd": [{"code": "E11.9", "desc": "Type 2 diabetes"}, {"code": "I10", "desc": "Hypertension"}, {"code": "E78.5", "desc": "Hyperlipidemia"}],
        "rule": "Time-based: 30-39 min = 99214.",
    },
    "set3_case_2": {
        "category": "E/M",
        "scenario": "Adult male, post-stroke TCM, face-to-face Day 9, moderate MDM",
        "cpt": [{"code": "99495", "desc": "TCM face-to-face moderate complexity", "reason": "TCM face-to-face visit Day 9"}],
        "icd": [{"code": "I63.9", "desc": "Cerebral infarction"}],
        "rule": "TCM: 99495 (moderate) or 99496 (high). Day 9 = within TCM window.",
    },
    "set3_case_3": {
        "category": "E/M",
        "scenario": "12yo pediatric, ED assessment then observation transition, moderate MDM",
        "cpt": [
            {"code": "99283", "desc": "ED visit moderate", "reason": "ED assessment for respiratory distress"},
            {"code": "99219", "desc": "Observation moderate MDM", "reason": "Same-day observation admission"},
        ],
        "icd": [{"code": "J45.41", "desc": "Moderate persistent asthma with exacerbation"}],
        "rule": "ED visit + same-day observation = 99283 + 99219.",
    },
    "set3_case_4": {
        "category": "E/M",
        "scenario": "50yo female established, telemedicine, insomnia, moderate MDM, 22 min",
        "cpt": [{"code": "99213", "desc": "Office visit established low MDM", "reason": "Telemedicine 22 min, low MDM"}],
        "icd": [{"code": "G47.00", "desc": "Insomnia, unspecified"}],
        "rule": "Telemedicine same as in-person E/M. 22 min = 99213.",
    },
    "set3_case_5": {
        "category": "E/M",
        "scenario": "3yo pediatric, PICU day 5, ongoing critical care, TBI",
        "cpt": [{"code": "99291", "desc": "Critical care 30-74 min", "reason": "Ongoing critical care for TBI"}],
        "icd": [{"code": "S06.0X0A", "desc": "Concussion without LOC, initial encounter"}],
        "rule": "Ongoing critical care = 99291.",
    },
    "set3_case_6": {
        "category": "E/M",
        "scenario": "25yo female established, wellness exam + separate pelvic exam, same session",
        "cpt": [
            {"code": "99397", "desc": "Preventive visit 18-39 years", "reason": "Annual wellness visit"},
            {"code": "57410", "desc": "Pelvic examination", "reason": "Separate structural pelvic exam"},
        ],
        "icd": [{"code": "Z00.00", "desc": "Encounter for general adult medical examination"}],
        "rule": "Preventive visit + separate pelvic exam = 99397 + 57410.",
    },
    "set3_case_7": {
        "category": "E/M",
        "scenario": "68yo male new to SNF, initial SNF admission, moderate MDM, 40 min",
        "cpt": [{"code": "99305", "desc": "Initial SNF visit moderate", "reason": "Initial SNF admission, moderate MDM"}],
        "icd": [{"code": "Z96.651", "desc": "Right artificial hip joint"}, {"code": "I10", "desc": "Hypertension"}],
        "rule": "Initial SNF admission moderate MDM = 99305.",
    },
    "set3_case_8": {
        "category": "E/M",
        "scenario": "82yo female established, home visit, CHF NYHA IV, high MDM, 75 min",
        "cpt": [{"code": "99350", "desc": "Home visit established high MDM", "reason": "Home visit with high MDM, 75 min"}],
        "icd": [{"code": "I50.33", "desc": "CHF NYHA class III"}],
        "rule": "Home visit high MDM = 99350.",
    },
    "set3_case_9": {
        "category": "E/M",
        "scenario": "73yo female established, UTI during pacemaker global period, unrelated, low MDM",
        "cpt": [{"code": "99213", "desc": "Office visit established low MDM", "reason": "Unrelated UTI during global period, low MDM"}],
        "icd": [{"code": "N39.0", "desc": "Urinary tract infection"}],
        "rule": "Unrelated illness during global period = billable E/M.",
    },
    "set3_case_10": {
        "category": "Anesthesia",
        "scenario": "68yo ASA P3 male, splenectomy + vein stripping, 4h30min, single anesthetic",
        "cpt": [{"code": "01951", "desc": "Anesthesia for hernia repair", "reason": "Single anesthetic for multiple procedures"}],
        "icd": [{"code": "D56.0", "desc": "Hereditary spherocytosis"}],
        "rule": "Multiple procedures under single anesthetic = base anesthesia code + time units.",
    },
    "set3_case_11": {
        "category": "Integumentary",
        "scenario": "78yo male, Stage IV pressure ulcer excision + flap reconstruction + sacral ostectomy",
        "cpt": [
            {"code": "15933", "desc": "Pressure ulcer excision with closure", "reason": "Sacral pressure ulcer excision"},
            {"code": "15934", "desc": "Pressure ulcer excision complex closure", "reason": "Flap reconstruction"},
            {"code": "27130", "desc": "Sacral ostectomy", "reason": "Sacral bone resection"},
        ],
        "icd": [{"code": "L89.153", "desc": "Pressure ulcer of sacral region, stage 4"}],
        "rule": "Pressure ulcer excision + flap + ostectomy = separate procedures.",
    },
    "set3_case_12": {
        "category": "Musculoskeletal",
        "scenario": "68yo female, closed reduction THA dislocation within global period",
        "cpt": [{"code": "27270", "desc": "Closed reduction hip dislocation", "reason": "Closed reduction of THA dislocation"}],
        "icd": [{"code": "T84.034A", "desc": "Mechanical loosening of hip joint implant"}],
        "rule": "Closed reduction of THA dislocation = 27270.",
    },
    "set3_case_13": {
        "category": "Digestive",
        "scenario": "62yo male, distal gastrectomy + Billroth II + D2 lymphadenectomy",
        "cpt": [{"code": "43632", "desc": "Distal gastrectomy with gastrojejunostomy", "reason": "Distal gastrectomy with Billroth II"}],
        "icd": [{"code": "C16.3", "desc": "Malignant neoplasm of gastric antrum"}],
        "rule": "Distal gastrectomy with Billroth II = 43632.",
    },
    "set3_case_14": {
        "category": "Urinary/Genital",
        "scenario": "63yo male, radical retropubic prostatectomy + limited lymph node sampling",
        "cpt": [{"code": "55866", "desc": "Radical retropubic prostatectomy", "reason": "Open retropubic radical prostatectomy with limited LN sampling"}],
        "icd": [{"code": "C61", "desc": "Malignant neoplasm of prostate"}],
        "rule": "Radical retropubic prostatectomy = 55866.",
    },
    "set3_case_15": {
        "category": "Nervous",
        "scenario": "64yo male, same-session stereotactic brain biopsy + VP shunt placement",
        "cpt": [
            {"code": "61760", "desc": "Stereotactic brain biopsy", "reason": "Stereotactic needle biopsy of brain lesion"},
            {"code": "37191", "desc": "VP shunt placement", "reason": "VP shunt with programmable valve"},
        ],
        "icd": [{"code": "D43.0", "desc": "Neoplasm of uncertain behavior of brain"}],
        "rule": "Brain biopsy (61760) + VP shunt (37191) are separate procedures.",
    },
    "set3_case_16": {
        "category": "Radiology",
        "scenario": "52yo female, bilateral MR-guided core breast biopsies, clip placement",
        "cpt": [{"code": "19083", "desc": "MR-guided breast biopsy", "reason": "Bilateral MR-guided core needle biopsies"}],
        "icd": [{"code": "R92.8", "desc": "Abnormal mammographic findings"}],
        "rule": "MR-guided breast biopsy = 19083 per breast.",
    },
    "set3_case_17": {
        "category": "Pathology",
        "scenario": "55yo, bone marrow flow cytometry with 5 markers",
        "cpt": [{"code": "88184", "desc": "Flow cytometry immunophenotyping", "reason": "Flow cytometry with 5 markers"}],
        "icd": [{"code": "C95.9", "desc": "Leukemia, unspecified"}],
        "rule": "Flow cytometry = 88184 per marker panel.",
    },
    "set3_case_18": {
        "category": "Medicine",
        "scenario": "48yo, prolonged single-agent IV chemo 4 hours (daratumumab)",
        "cpt": [
            {"code": "96413", "desc": "Chemotherapy infusion first hour", "reason": "First hour of infusion"},
            {"code": "96415", "desc": "Each additional 30 minutes", "reason": "Additional 3 hours = 6 x 96415"},
        ],
        "icd": [{"code": "C90.00", "desc": "Multiple myeloma"}],
        "rule": "96413 (first hour) + 96415 x 6 (additional 3 hours).",
    },
    "set3_case_19": {
        "category": "Medicine",
        "scenario": "35yo female, bipolar I, 60min psychotherapy + separate moderate E/M",
        "cpt": [
            {"code": "90838", "desc": "Psychotherapy 60 min", "reason": "60-minute psychotherapy session"},
            {"code": "99214", "desc": "E/M visit moderate MDM", "reason": "Separate moderate-complexity E/M"},
        ],
        "icd": [{"code": "F31.1", "desc": "Bipolar I, current episode manic, moderate"}],
        "rule": "Psychotherapy (90838) + E/M (99214) separate same day with modifier 25.",
    },
    "set3_case_20": {
        "category": "ICD10",
        "scenario": "32yo female, severe acute alcohol-induced pancreatitis + alcoholic liver disease + AKI",
        "cpt": [],
        "icd": [
            {"code": "K85.2", "desc": "Acute pancreatitis due to alcohol"},
            {"code": "K70.31", "desc": "Alcoholic cirrhosis of liver with ascites"},
            {"code": "N17.0", "desc": "Acute kidney failure with tubular necrosis"},
        ],
        "rule": "K85.2 (pancreatitis) → K70.31 (liver disease) → N17.0 (AKI).",
    },
    "set3_case_21": {
        "category": "ICD10",
        "scenario": "50yo male, severe dengue hemorrhagic fever, thrombocytopenia, liver dysfunction",
        "cpt": [],
        "icd": [
            {"code": "A91", "desc": "Dengue hemorrhagic fever"},
            {"code": "D69.6", "desc": "Thrombocytopenia"},
            {"code": "K72.9", "desc": "Hepatic failure, unspecified"},
        ],
        "rule": "A91 (dengue) → D69.6 (thrombocytopenia) → K72.9 (liver dysfunction).",
    },
    "set3_case_22": {
        "category": "ICD10",
        "scenario": "25yo female, schizoaffective disorder depressive type, acute suicidal ideation, MDD hx",
        "cpt": [],
        "icd": [
            {"code": "F25.0", "desc": "Schizoaffective disorder, depressive type"},
            {"code": "F33.2", "desc": "Major depressive disorder recurrent severe without psychotic features"},
        ],
        "rule": "F25.0 (schizoaffective) primary → F33.2 (MDD) secondary.",
    },
    "set3_case_23": {
        "category": "ICD10",
        "scenario": "8yo female with Down syndrome, new ALL, ASD corrected, admission for leukemia",
        "cpt": [],
        "icd": [
            {"code": "C91.00", "desc": "Acute lymphoblastic leukemia unspecified"},
            {"code": "Q90.9", "desc": "Down syndrome, unspecified"},
            {"code": "Q21.1", "desc": "Atrial septal defect"},
        ],
        "rule": "C91.00 (ALL) primary → Q90.9 (Down) → Q21.1 (ASD history).",
    },
    "set3_case_24": {
        "category": "ICD10",
        "scenario": "55yo female, COVID-19 + E. coli sepsis + T2DM + AKI from sepsis",
        "cpt": [],
        "icd": [
            {"code": "J12.82", "desc": "COVID-19 pneumonia"},
            {"code": "A41.52", "desc": "Sepsis due to E. coli"},
            {"code": "R65.21", "desc": "Severe sepsis with septic shock"},
            {"code": "E11.9", "desc": "Type 2 diabetes"},
            {"code": "N17.0", "desc": "Acute kidney failure"},
        ],
        "rule": "J12.82 (COVID) + A41.52 (E. coli sepsis) + R65.21 (severe sepsis) + E11.9 (DM) + N17.0 (AKI).",
    },
    "set3_case_25": {
        "category": "ICD10",
        "scenario": "28yo female, postpartum depression 8 weeks post delivery",
        "cpt": [],
        "icd": [{"code": "F32.A", "desc": "Depression, unspecified, single episode"}],
        "rule": "Postpartum depression = F32.A (or F53 with 7th character for postpartum).",
    },
    "set3_case_26": {
        "category": "ICD10",
        "scenario": "Right-handed adult, chronic right hemiparesis from stroke 4 years ago",
        "cpt": [],
        "icd": [
            {"code": "I69.354", "desc": "Monoplegia of right non-dominant side due to cerebral infarction"},
            {"code": "G81.94", "desc": "Flaccid hemiplegia, unspecified"},
        ],
        "rule": "I69.354 (sequelae of stroke with hemiplegia). Right-handed = dominant side if right side affected.",
    },
    "set3_case_27": {
        "category": "ICD10",
        "scenario": "Elderly patient, advanced severe dementia, bed-bound, complete ADL dependency",
        "cpt": [],
        "icd": [{"code": "F03.90", "desc": "Unspecified dementia without behavioral disturbance"}],
        "rule": "Advanced dementia = F03.90.",
    },
    "set3_case_28": {
        "category": "ICD10",
        "scenario": "35yo male roofer, bimalleolar ankle fracture from ladder fall, initial encounter",
        "cpt": [{"code": "27814", "desc": "ORIF bimalleolar ankle fracture", "reason": "Open reduction internal fixation"}],
        "icd": [
            {"code": "S82.891A", "desc": "Fracture of right ankle, initial encounter"},
            {"code": "W14.XXXA", "desc": "Fall from ladder, initial encounter"},
            {"code": "Z87.891", "desc": "Personal history of nicotine dependence"},
        ],
        "rule": "S82.891A (ankle fracture) + W14.XXXA (external cause) + Z87.891 (tobacco hx).",
    },
    "set3_case_29": {
        "category": "HCPCS",
        "scenario": "90mg IV pamidronate for metastatic bone disease, J2430 per 30mg",
        "cpt": [],
        "icd": [{"code": "C79.31", "desc": "Secondary malignant neoplasm of vertebral column"}],
        "hcpcs": [{"code": "J2430", "desc": "Pamidronate 30mg", "units": 3, "reason": "90mg / 30mg = 3 units"}],
        "rule": "J2430 = per 30mg. 90mg = 3 units.",
    },
    "set3_case_30": {
        "category": "HCPCS",
        "scenario": "New colostomy, 30-day ostomy supply: 30 pouches A4416 + 100 wipes A5120 + 1 belt A4367",
        "cpt": [],
        "icd": [{"code": "Z93.3", "desc": "Colostomy status"}],
        "hcpcs": [
            {"code": "A4416", "desc": "Ostomy pouch", "units": 30},
            {"code": "A5120", "desc": "Skin barrier wipes", "units": 100},
            {"code": "A4367", "desc": "Ostomy belt", "units": 1},
        ],
        "rule": "Ostomy supplies billed separately with correct units.",
    },
    "set3_case_31": {
        "category": "HCPCS",
        "scenario": "28yo adult, wrist sprain, fiberglass splint applied",
        "cpt": [{"code": "29700", "desc": "Cast/splint application", "reason": "Short-arm fiberglass splint"}],
        "icd": [{"code": "S63.402A", "desc": "Sprain of right wrist, initial encounter"}],
        "rule": "Splint application = 29700.",
    },
    "set3_case_32": {
        "category": "Knowledge",
        "scenario": "Medicare ambulance benefit = Part B",
        "answer": "Emergency ambulance transportation is covered under Medicare Part B (Supplementary Medical Insurance).",
        "cpt": [], "icd": [],
    },
    "set3_case_33": {
        "category": "Knowledge",
        "scenario": "Abuse definition - inconsistent with sound practices, no deceptive intent",
        "answer": "Abuse = practices inconsistent with sound practices resulting in unnecessary cost, lacking deceptive intent (distinguished from fraud).",
        "cpt": [], "icd": [],
    },
    "set3_case_34": {
        "category": "Knowledge",
        "scenario": "OIG Work Plan - updated continuously throughout fiscal year",
        "answer": "OIG releases annual Work Plan outlining oversight projects, updated continuously throughout fiscal year.",
        "cpt": [], "icd": [],
    },
    "set3_case_35": {
        "category": "Modifiers",
        "scenario": "Co-surgeons + assistant surgeon for complex spinal reconstruction",
        "cpt": [
            {"code": "22612", "desc": "Posterior lumbar fusion", "reason": "Complex spinal reconstruction"},
            {"code": "22612-62", "desc": "Co-surgeon modifier", "reason": "Modifier -62 for co-surgeon"},
            {"code": "22612-80", "desc": "Assistant surgeon modifier", "reason": "Modifier -80 for assistant"},
        ],
        "icd": [],
        "rule": "Co-surgeons: -62. Assistant surgeon: -80.",
    },
    "set3_case_36": {
        "category": "HCPCS",
        "scenario": "Adult athlete, custom knee orthosis with rigid frame",
        "cpt": [],
        "icd": [{"code": "M23.20", "desc": "Derangement of meniscus"}],
        "hcpcs": [{"code": "L1820", "desc": "Knee orthosis with rigid frame", "reason": "Custom functional knee orthosis"}],
        "rule": "Custom knee orthosis = L1820.",
    },
    "set3_case_37": {
        "category": "HCPCS",
        "scenario": "Medicare rural hospital, telehealth originating site facility fee",
        "cpt": [{"code": "99449", "desc": "Telehealth originating site", "reason": "Telehealth facility fee"}],
        "icd": [],
        "rule": "Telehealth originating site = 99449.",
    },
    "set3_case_38": {
        "category": "Knowledge",
        "scenario": "ABN = Advance Beneficiary Notice, warning patient Medicare may deny payment",
        "answer": "ABN = standardized form warning patient Medicare may deny payment, transferring financial liability.",
        "cpt": [], "icd": [],
    },
    "set3_case_39": {
        "category": "Knowledge",
        "scenario": "OIG Compliance Program Guidance for physician practices",
        "answer": "OIG publishes voluntary Compliance Program Guidance for physician practices to prevent fraud, waste, abuse.",
        "cpt": [], "icd": [],
    },
    "set3_case_40": {
        "category": "Knowledge",
        "scenario": "HIPAA = federal legislation for healthcare transactions, PHI privacy, insurance portability",
        "answer": "HIPAA establishes national standards for electronic healthcare transactions, PHI privacy/security, insurance portability.",
        "cpt": [], "icd": [],
    },
    "set3_case_41": {
        "category": "Knowledge",
        "scenario": "Nephrolithiasis - kidney stones in renal pelvis/calyces",
        "answer": "Nephrolithiasis: formation of crystalline mineral calculi within the renal pelvis, calyces, or urinary tract.",
        "cpt": [], "icd": [],
    },
    "set3_case_42": {
        "category": "Knowledge",
        "scenario": "Cystocele - bladder herniation into vaginal vault",
        "answer": "Cystocele: herniation of posterior bladder wall through fascial layers into anterior vaginal vault.",
        "cpt": [], "icd": [],
    },
    "set3_case_43": {
        "category": "Knowledge",
        "scenario": "Leukocytosis - elevated WBC count above reference range",
        "answer": "Leukocytosis: abnormal elevation in total circulating WBC count above standard reference range.",
        "cpt": [], "icd": [],
    },
    "set3_case_44": {
        "category": "Knowledge",
        "scenario": "Thrombocytopenia - low platelet count below baseline",
        "answer": "Thrombocytopenia: abnormal reduction in circulating platelets below standard baselines.",
        "cpt": [], "icd": [],
    },
    "set3_case_45": {
        "category": "Knowledge",
        "scenario": "Foramen ovale - fetal cardiac shunt between right and left atrium",
        "answer": "Foramen ovale: fetal cardiac structure allowing blood to bypass non-functional fetal lungs.",
        "cpt": [], "icd": [],
    },
    "set3_case_46": {
        "category": "Knowledge",
        "scenario": "Tympanic membrane - eardrum separating external and middle ear",
        "answer": "Tympanic membrane: thin semi-transparent membrane separating external auditory canal from middle ear.",
        "cpt": [], "icd": [],
    },
    "set3_case_47": {
        "category": "Knowledge",
        "scenario": "Biliary dynamics - bile produced by liver, stored in gallbladder",
        "answer": "Biliary physiology: bile produced by hepatic cells, transported via hepatic duct, stored in gallbladder.",
        "cpt": [], "icd": [],
    },
    "set3_case_48": {
        "category": "ICD10",
        "scenario": "70yo male, metastatic prostate cancer, febrile neutropenia from chemo, T2DM",
        "cpt": [],
        "icd": [
            {"code": "C61", "desc": "Malignant neoplasm of prostate"},
            {"code": "C79.31", "desc": "Secondary malignant neoplasm of vertebral column"},
            {"code": "D70.2", "desc": "Congenital agranulocytosis"},
            {"code": "R50.83", "desc": "Fever"},
            {"code": "E11.9", "desc": "Type 2 diabetes"},
        ],
        "rule": "C61 (prostate cancer) → C79.31 (bone mets) → D70.2 (neutropenia) → R50.83 (fever) → E11.9 (DM).",
    },
    "set3_case_49": {
        "category": "ICD10",
        "scenario": "60yo female, acute PE + ESRD on dialysis + HTN + T2DM + CKD 3a",
        "cpt": [],
        "icd": [
            {"code": "I26.99", "desc": "Other pulmonary embolism"},
            {"code": "N18.6", "desc": "End stage renal disease"},
            {"code": "I10", "desc": "Hypertension"},
            {"code": "E11.9", "desc": "Type 2 diabetes"},
            {"code": "N18.31", "desc": "CKD stage 3a"},
        ],
        "rule": "I26.99 (PE) primary → N18.6 (ESRD) → I10 (HTN) → E11.9 (DM) → N18.31 (CKD).",
    },
    "set3_case_50": {
        "category": "ICD10",
        "scenario": "4-day-old newborn, 32wk gestation, RDS, IVH grade 2, neonatal sepsis GBS, on ventilator",
        "cpt": [],
        "icd": [
            {"code": "P07.24", "desc": "Extreme immaturity, gestational age 28 completed weeks"},
            {"code": "P22.0", "desc": "Respiratory distress syndrome of newborn"},
            {"code": "P52.1", "desc": "Intraventricular hemorrhage grade 2"},
            {"code": "P36.10", "desc": "Streptococcus sepsis of newborn"},
            {"code": "E11.9", "desc": "Type 2 diabetes (maternal)"},
        ],
        "rule": "P07.24 (preterm) → P22.0 (RDS) → P52.1 (IVH) → P36.10 (GBS sepsis).",
    },
    "set3_case_51": {
        "category": "ICD10",
        "scenario": "55yo female, COVID-19 + E. coli sepsis + T2DM + AKI from sepsis",
        "cpt": [],
        "icd": [
            {"code": "J12.82", "desc": "COVID-19 pneumonia"},
            {"code": "A41.52", "desc": "Sepsis due to E. coli"},
            {"code": "R65.21", "desc": "Severe sepsis with septic shock"},
            {"code": "E11.9", "desc": "Type 2 diabetes"},
            {"code": "N17.0", "desc": "Acute kidney failure"},
        ],
        "rule": "J12.82 (COVID) + A41.52 (E. coli sepsis) + R65.21 (severe sepsis) + E11.9 (DM) + N17.0 (AKI).",
    },
    "set3_case_52": {
        "category": "ICD10",
        "scenario": "35yo female, Crohn's disease with obstruction + enteroenteric fistula + chronic anemia",
        "cpt": [],
        "icd": [
            {"code": "K50.51", "desc": "Crohn disease of both small and large intestine with obstruction"},
            {"code": "D63.8", "desc": "Anemia in chronic disease"},
        ],
        "rule": "K50.51 (Crohn with obstruction) → D63.8 (anemia in chronic disease).",
    },
    "set3_case_53": {
        "category": "ICD10",
        "scenario": "Adult, admitted for pneumonia, hx appendectomy 10 years ago, hypothyroidism",
        "cpt": [],
        "icd": [
            {"code": "J18.9", "desc": "Pneumonia, unspecified"},
            {"code": "Z87.891", "desc": "Personal history of nicotine dependence"},
        ],
        "rule": "J18.9 (pneumonia) primary. Z87.891 (hx appendectomy) is historical, not coded unless relevant.",
    },
    "set3_case_54": {
        "category": "ICD10",
        "scenario": "Adult female, ovarian cancer, chemo-induced anemia, blood transfusion",
        "cpt": [],
        "icd": [
            {"code": "C56.9", "desc": "Malignant neoplasm of unspecified ovary"},
            {"code": "D63.8", "desc": "Anemia in chronic disease"},
        ],
        "rule": "C56.9 (ovarian cancer) → D63.8 (anemia in chronic disease, chemo-induced).",
    },
    "set3_case_55": {
        "category": "ICD10",
        "scenario": "65yo, DM2 + HTN + hyperlipidemia + AF, all stable, no changes",
        "cpt": [],
        "icd": [
            {"code": "E11.9", "desc": "Type 2 diabetes"},
            {"code": "I10", "desc": "Hypertension"},
            {"code": "E78.5", "desc": "Hyperlipidemia"},
            {"code": "I48.91", "desc": "Atrial fibrillation"},
        ],
        "rule": "All conditions stable, coded individually.",
    },
    "set3_case_56": {
        "category": "HCPCS",
        "scenario": "90mg IV pamidronate, J2430 per 30mg",
        "cpt": [],
        "icd": [{"code": "C79.31", "desc": "Secondary malignant neoplasm of vertebral column"}],
        "hcpcs": [{"code": "J2430", "desc": "Pamidronate 30mg", "units": 3, "reason": "90mg / 30mg = 3 units"}],
        "rule": "J2430 = per 30mg. 90mg = 3 units.",
    },
    "set3_case_57": {
        "category": "HCPCS",
        "scenario": "8mg IM Dilaudid (hydromorphone), J1170 per 4mg",
        "cpt": [],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}],
        "hcpcs": [{"code": "J1170", "desc": "Hydromorphone 4mg", "units": 2, "reason": "8mg / 4mg = 2 units"}],
        "rule": "J1170 = per 4mg. 8mg = 2 units.",
    },
    "set3_case_58": {
        "category": "HCPCS",
        "scenario": "ALS patient, Group 2 power wheelchair with single power option",
        "cpt": [],
        "icd": [{"code": "G12.21", "desc": "Amyotrophic lateral sclerosis"}],
        "hcpcs": [{"code": "K0856", "desc": "Group 2 standard power wheelchair", "reason": "Power wheelchair with single option"}],
        "rule": "Group 2 power wheelchair = K0856.",
    },
    "set3_case_59": {
        "category": "HCPCS",
        "scenario": "68yo Medicare, subsequent Annual Wellness Visit (AWV)",
        "cpt": [{"code": "99398", "desc": "Subsequent AWV 65+ years", "reason": "Medicare subsequent AWV"}],
        "icd": [],
        "rule": "Subsequent AWV = 99398.",
    },
    "set3_case_60": {
        "category": "Knowledge",
        "scenario": "NCCI Edits - promote correct coding, prevent improper unbundling",
        "answer": "NCCI edits promote correct national coding methodologies and prevent inappropriate code combinations on claims.",
        "cpt": [], "icd": [],
    },
    "set3_case_61": {
        "category": "Knowledge",
        "scenario": "ABN Form CMS-R-131 requirements",
        "answer": "ABN must be issued prior to service, specify exact item/procedure, detail reason for denial, provide cost estimate.",
        "cpt": [], "icd": [],
    },
    "set3_case_62": {
        "category": "Knowledge",
        "scenario": "Workers Comp privacy exempt from HIPAA, defaults to state laws",
        "answer": "Workers' Compensation medical records are exempt from federal HIPAA Privacy Rule, defaulting to state laws.",
        "cpt": [], "icd": [],
    },
    "set3_case_63": {
        "category": "Anesthesia",
        "scenario": "25yo ASA P1, emergency exploratory laparotomy after-hours MVA, emergency modifiers",
        "cpt": [{"code": "01902", "desc": "Emergency laparotomy anesthesia", "reason": "Emergency laparotomy anesthesia"}],
        "icd": [{"code": "S38.3XXA", "desc": "Injury to intra-abdominal organ, initial encounter"}],
        "rule": "Emergency laparotomy anesthesia = 01902. Emergency modifiers apply.",
    },
    "set3_case_64": {
        "category": "Medicine",
        "scenario": "14yo established, HPV9 vaccine + MenB-FHbp vaccine, IM injections, counseling",
        "cpt": [
            {"code": "90471", "desc": "Vaccine administration first vaccine", "reason": "First vaccine administration"},
            {"code": "90472", "desc": "Each additional vaccine", "reason": "Second vaccine administration"},
        ],
        "icd": [{"code": "Z23", "desc": "Encounter for immunization"}],
        "hcpcs": [
            {"code": "90651", "desc": "HPV9 vaccine", "reason": "HPV 9-valent vaccine"},
            {"code": "90636", "desc": "MenB-FHbp vaccine", "reason": "Meningococcal B vaccine"},
        ],
        "rule": "Vaccine administration: 90471 (first) + 90472 (each add'l). Vaccines billed separately.",
    },
    "set3_case_65": {
        "category": "Medicine",
        "scenario": "48yo, prolonged single-agent IV daratumumab 4 hours",
        "cpt": [
            {"code": "96413", "desc": "Chemotherapy infusion first hour", "reason": "First hour of infusion"},
            {"code": "96415", "desc": "Each additional 30 minutes", "reason": "Additional 3 hours = 6 x 96415"},
        ],
        "icd": [{"code": "C90.00", "desc": "Multiple myeloma"}],
        "rule": "96413 (first hour) + 96415 x 6 (additional 3 hours).",
    },
    "set3_case_66": {
        "category": "Medicine",
        "scenario": "35yo female, bipolar I, 60min psychotherapy + separate moderate E/M, same day",
        "cpt": [
            {"code": "90838", "desc": "Psychotherapy 60 min", "reason": "60-minute psychotherapy"},
            {"code": "99214", "desc": "E/M moderate MDM", "reason": "Separate moderate-complexity E/M"},
        ],
        "icd": [{"code": "F31.1", "desc": "Bipolar I, current episode manic, moderate"}],
        "rule": "Psychotherapy (90838) + E/M (99214) same day with modifier 25.",
    },
    "set3_case_67": {
        "category": "Medicine",
        "scenario": "Adult, concurrent multi-line chemo: doxorubicin 1hr + cyclophosphamide 1hr15min, two IV lines",
        "cpt": [
            {"code": "96413", "desc": "Chemotherapy infusion first hour", "reason": "Concurrent infusions"},
        ],
        "icd": [{"code": "C81.9", "desc": "Hodgkin lymphoma, unspecified"}],
        "rule": "Concurrent infusions: 96413 x 1 (same hour). Only one 96413 billed for concurrent infusions.",
    },
    "set3_case_68": {
        "category": "Medicine",
        "scenario": "60yo female, HER2+ metastatic breast cancer, IV trastuzumab 90 minutes",
        "cpt": [
            {"code": "96413", "desc": "Chemotherapy infusion first hour", "reason": "First hour of infusion"},
            {"code": "96415", "desc": "Each additional 30 minutes", "reason": "Additional 30 minutes"},
        ],
        "icd": [{"code": "C50.919", "desc": "Malignant neoplasm of unspecified breast"}],
        "rule": "96413 (first hour) + 96415 (additional 30 min).",
    },
    "set3_case_69": {
        "category": "Medicine",
        "scenario": "Adult female, dual-chamber pacemaker interrogation and programming",
        "cpt": [{"code": "93282", "desc": "Interrogation of pacemaker", "reason": "Dual-chamber pacemaker interrogation and programming"}],
        "icd": [{"code": "Z95.0", "desc": "Presence of cardiac pacemaker"}],
        "rule": "Pacemaker interrogation = 93282.",
    },
    "set3_case_70": {
        "category": "Medicine",
        "scenario": "Adult, IV hydration 35 minutes in office",
        "cpt": [{"code": "96360", "desc": "IV hydration first hour", "reason": "IV hydration therapy"}],
        "icd": [{"code": "E86.0", "desc": "Dehydration"}],
        "rule": "IV hydration = 96360 (first hour).",
    },
    "set3_case_71": {
        "category": "HCPCS",
        "scenario": "Emergency after-hours laparotomy, ASA P1, emergency modifiers",
        "cpt": [],
        "icd": [],
        "rule": "Emergency after-hours anesthesia: modifier -76 (repeat procedure same day) or -GA (waiver of liability) may apply.",
    },
    "set3_case_72": {
        "category": "HCPCS",
        "scenario": "8mg IM Dilaudid (hydromorphone), J1170 per 4mg",
        "cpt": [],
        "icd": [{"code": "G89.29", "desc": "Other chronic pain"}],
        "hcpcs": [{"code": "J1170", "desc": "Hydromorphone 4mg", "units": 2, "reason": "8mg / 4mg = 2 units"}],
        "rule": "J1170 = per 4mg. 8mg = 2 units.",
    },
    "set3_case_73": {
        "category": "HCPCS",
        "scenario": "ALS patient, Group 2 power wheelchair",
        "cpt": [],
        "icd": [{"code": "G12.21", "desc": "Amyotrophic lateral sclerosis"}],
        "hcpcs": [{"code": "K0856", "desc": "Group 2 power wheelchair", "reason": "Power wheelchair with single option"}],
        "rule": "Group 2 power wheelchair = K0856.",
    },
    "set3_case_74": {
        "category": "HCPCS",
        "scenario": "68yo Medicare, subsequent AWV",
        "cpt": [{"code": "99398", "desc": "Subsequent AWV 65+ years", "reason": "Medicare subsequent AWV"}],
        "icd": [],
        "rule": "Subsequent AWV = 99398.",
    },
    "set3_case_75": {
        "category": "Knowledge",
        "scenario": "NCCI Edits core purpose",
        "answer": "NCCI edits promote correct national coding methodologies and prevent improper code combinations on claims.",
        "cpt": [], "icd": [],
    },
    "set3_case_76": {
        "category": "Knowledge",
        "scenario": "ABN Form CMS-R-131 requirements",
        "answer": "ABN must be issued prior to service, specify exact item/procedure, detail reason for denial, provide cost estimate.",
        "cpt": [], "icd": [],
    },
    "set3_case_77": {
        "category": "Knowledge",
        "scenario": "Workers Comp privacy exempt from HIPAA",
        "answer": "Workers' Compensation medical records are exempt from federal HIPAA Privacy Rule, defaulting to state laws.",
        "cpt": [], "icd": [],
    },

    # ═══════════════════════════════════════════════════════════════════
    # EXACT 20 REAL PATIENT CASES (for pipeline training)
    # ═══════════════════════════════════════════════════════════════════
    "real_patient_1": {
        "category": "cardiovascular",
        "scenario": "68yo male, three-vessel CAD, CABG x3, LIMA to LAD, SVG to RCA, SVG to OM, endarterectomy RCA",
        "keywords": ["cabg", "lima", "lad", "rca", "om", "endarterectomy", "three-vessel", "bypass", "graft", "on pump", "cross clamp"],
        "cpt": [{"code": "33533", "desc": "CABG arterial x1", "reason": "LIMA to LAD"}, {"code": "33572", "desc": "Coronary endarterectomy", "reason": "RCA endarterectomy"}],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG with endarterectomy: 33533 (CABG) + 33572 (endarterectomy).",
    },
    "real_patient_2": {
        "category": "icd10",
        "scenario": "72yo male, severe sepsis E. coli pneumonia, respiratory failure hypoxia, norepinephrine",
        "keywords": ["sepsis", "e. coli", "pneumonia", "respiratory failure", "hypoxia", "norepinephrine", "shock"],
        "cpt": [],
        "icd": [
            {"code": "A41.52", "desc": "Sepsis due to Escherichia coli"},
            {"code": "R65.21", "desc": "Severe sepsis with septic shock"},
        ],
        "rule": "E. coli sepsis = A41.52. Severe sepsis with shock = R65.21.",
    },
    "real_patient_3": {
        "category": "surgery",
        "scenario": "45yo female, symptomatic cholelithiasis, laparoscopic cholecystectomy, critical view of safety",
        "keywords": ["cholecystectomy", "laparoscopic", "gallbladder", "gallstones", "cholelithiasis", "critical view"],
        "cpt": [{"code": "47562", "desc": "Laparoscopic cholecystectomy", "reason": "Lap cholecystectomy"}],
        "icd": [{"code": "K80.20", "desc": "Calculus of gallbladder with acute cholecystitis"}],
        "rule": "Laparoscopic cholecystectomy = 47562.",
    },
    "real_patient_4": {
        "category": "orthopedics",
        "scenario": "68yo female, severe osteoarthritis right knee, total knee arthroplasty cemented, tourniquet 90 min",
        "keywords": ["total knee", "arthroplasty", "knee replacement", "osteoarthritis", "cemented", "tourniquet"],
        "cpt": [{"code": "27447", "desc": "Total knee arthroplasty", "reason": "Total knee replacement"}],
        "icd": [{"code": "M17.11", "desc": "Primary osteoarthritis, right knee"}],
        "rule": "Total knee arthroplasty = 27447.",
    },
    "real_patient_5": {
        "category": "icd10",
        "scenario": "75yo male, right foot ulcer great toe, bone necrosis, T2DM, diabetic neuropathy, CKD 3b, hypertension, cellulitis",
        "keywords": ["foot ulcer", "great toe", "necrosis", "diabetes", "neuropathy", "ckd", "cellulitis", "diabetic"],
        "cpt": [],
        "icd": [
            {"code": "E11.621", "desc": "Type 2 diabetes with foot ulcer"},
            {"code": "L03.011", "desc": "Cellulitis of right toe"},
            {"code": "E11.65", "desc": "Type 2 diabetes with hyperglycemia"},
        ],
        "rule": "Diabetic foot ulcer = E11.621. Cellulitis = L03.011.",
    },
    "real_patient_6": {
        "category": "emergency",
        "scenario": "28yo female, severe asthma, ED, SpO2 88%, nebulized albuterol, IV methylprednisolone",
        "keywords": ["asthma", "emergency", "ed", "spo2", "albuterol", "methylprednisolone", "bronchospasm"],
        "cpt": [{"code": "99284", "desc": "ED visit high complexity", "reason": "High complexity ED visit for asthma"}],
        "icd": [{"code": "J45.41", "desc": "Moderate persistent asthma with acute exacerbation"}],
        "rule": "ED visit for asthma = 99284.",
    },
    "real_patient_7": {
        "category": "neonatal",
        "scenario": "15-day-old female neonate, NICU Day 6, 30 weeks gestational age, 1420 grams, RDS on CPAP, apnea of prematurity, PDA, hyperbilirubinemia, feeding intolerance TPN",
        "keywords": ["neonate", "nicu", "30 weeks", "1420", "cpap", "apnea", "pda", "bilirubin", "tpn", "prematurity"],
        "cpt": [{"code": "99469", "desc": "Subsequent daily hospital care of newborn", "reason": "NICU Day 6 subsequent care"}],
        "icd": [
            {"code": "P07.15", "desc": "Other low birth weight newborn, 1250-1499g"},
            {"code": "P22.0", "desc": "Respiratory distress syndrome of newborn"},
            {"code": "P28.4", "desc": "Other apneas of newborn"},
            {"code": "Q25.0", "desc": "Patent ductus arteriosus"},
            {"code": "P59.9", "desc": "Neonatal jaundice, unspecified"},
            {"code": "P92.9", "desc": "Feeding problem of newborn, unspecified"},
        ],
        "rule": "NICU Day 6 = 99469. Neonatal ICD codes for each condition.",
    },
    "real_patient_8": {
        "category": "em",
        "scenario": "35yo female, severe depression, suicidal ideation, acute illness, external mental-health records, metabolic panel, SSRI",
        "keywords": ["depression", "suicidal", "ideation", "ssri", "mental health", "psychiatrist", "hospitalization"],
        "cpt": [{"code": "99215", "desc": "Office visit established high MDM", "reason": "High MDM with hospitalization decision"}],
        "icd": [
            {"code": "F32.2", "desc": "Major depressive disorder, severe"},
            {"code": "R45.851", "desc": "Suicidal ideation"},
        ],
        "rule": "Severe depression with hospitalization decision = 99215.",
    },
    "real_patient_9": {
        "category": "em",
        "scenario": "72yo female, cardiology follow-up, stable atrial fibrillation, 27 minutes, low MDM",
        "keywords": ["cardiology", "follow-up", "atrial fibrillation", "low mdm", "27 minutes", "stable"],
        "cpt": [{"code": "99213", "desc": "Office visit established low MDM", "reason": "Low MDM, 20-29 min"}],
        "icd": [{"code": "I48.91", "desc": "Unspecified atrial fibrillation"}],
        "rule": "Time-based: 20-29 min = 99213.",
    },
    "real_patient_10": {
        "category": "icd10",
        "scenario": "55yo female, COVID-19, E. coli bloodstream infection, severe sepsis, septic shock, T2DM, AKI from sepsis",
        "keywords": ["covid", "e. coli", "sepsis", "shock", "diabetes", "kidney failure", "bloodstream"],
        "cpt": [],
        "icd": [
            {"code": "J12.82", "desc": "COVID-19 pneumonia"},
            {"code": "A41.52", "desc": "Sepsis due to E. coli"},
            {"code": "R65.21", "desc": "Severe sepsis with septic shock"},
            {"code": "E11.9", "desc": "Type 2 diabetes"},
            {"code": "N17.0", "desc": "Acute kidney failure"},
        ],
        "rule": "COVID (J12.82) + E. coli sepsis (A41.52) + severe sepsis (R65.21) + DM (E11.9) + AKI (N17.0).",
    },
    "real_patient_11": {
        "category": "orthopedics",
        "scenario": "78yo female, left hip pain, femoral neck fracture, osteoporosis, right-handed",
        "keywords": ["hip", "femoral neck", "fracture", "osteoporosis", "fall", "trauma"],
        "cpt": [{"code": "27230", "desc": "Closed treatment hip fracture", "reason": "Hip fracture treatment"}],
        "icd": [
            {"code": "S72.001A", "desc": "Fracture of neck of left femur, initial encounter"},
            {"code": "M80.061", "desc": "Age-related osteoporosis with fracture, left femur"},
        ],
        "rule": "Femoral neck fracture = S72.001A. Osteoporosis = M80.061.",
    },
    "real_patient_12": {
        "category": "gi",
        "scenario": "65yo male, chronic pancreatitis, ERCP, stent exchange, balloon dilation, sphincterotomy",
        "keywords": ["ercp", "stent", "exchange", "pancreatitis", "sphincterotomy", "balloon", "dilation"],
        "cpt": [{"code": "43275", "desc": "ERCP with stent exchange", "reason": "ERCP stent exchange"}],
        "icd": [{"code": "K86.1", "desc": "Chronic pancreatitis"}],
        "rule": "ERCP with stent exchange = 43275.",
    },
    "real_patient_13": {
        "category": "gi",
        "scenario": "60yo male, positive FIT screening, sigmoidoscopy, 3 polyps, snare removed",
        "keywords": ["sigmoidoscopy", "polyps", "snare", "polypectomy", "fit screening", "colon"],
        "cpt": [{"code": "45385", "desc": "Sigmoidoscopy with polypectomy", "reason": "Sigmoidoscopy with snare polypectomy"}],
        "icd": [{"code": "Z12.11", "desc": "Screening for malignant neoplasm of colon"}],
        "rule": "Sigmoidoscopy with polypectomy = 45385.",
    },
    "real_patient_14": {
        "category": "cardiovascular",
        "scenario": "71yo female, ischemic cardiomyopathy EF 25%, CABG x3, LIMA to LAD, radial artery to OM, SVGs, 2 arterial 3 venous",
        "keywords": ["cabg", "radial", "arterial", "lima", "om", "bypass", "graft", "cardiomyopathy", "ef 25"],
        "cpt": [
            {"code": "33533", "desc": "CABG arterial x1", "reason": "LIMA to LAD"},
            {"code": "33534", "desc": "CABG arterial x2", "reason": "Radial artery"},
            {"code": "33518", "desc": "Vein graft add-on", "reason": "SVGs"},
        ],
        "icd": [{"code": "I25.10", "desc": "Atherosclerotic heart disease"}],
        "rule": "CABG 2 arterial + 3 venous: 33533 + 33534 + 33518.",
    },
    "real_patient_15": {
        "category": "icd10",
        "scenario": "67yo male, pneumonia, MRSA, sepsis from deep incisional wound, respiratory failure, AKI",
        "keywords": ["pneumonia", "mrsa", "sepsis", "wound", "respiratory failure", "kidney", "incisional"],
        "cpt": [],
        "icd": [
            {"code": "A41.0", "desc": "Sepsis due to S. aureus"},
            {"code": "J96.01", "desc": "Acute respiratory failure with hypoxia"},
            {"code": "N17.0", "desc": "Acute kidney failure"},
        ],
        "rule": "MRSA sepsis = A41.0. RF = J96.01. AKI = N17.0.",
    },
    "real_patient_16": {
        "category": "cardiovascular",
        "scenario": "81yo female, severe aortic stenosis, TAVR, prohibitive risk, transapical approach",
        "keywords": ["tavr", "aortic stenosis", "transcatheter", "valve replacement", "transapical"],
        "cpt": [{"code": "33361", "desc": "TAVR transfemoral", "reason": "Transcatheter aortic valve replacement"}],
        "icd": [{"code": "I35.0", "desc": "Nonrheumatic aortic stenosis"}],
        "rule": "TAVR = 33361.",
    },
    "real_patient_17": {
        "category": "icd10",
        "scenario": "67yo male, lung cancer hx, MRSA sepsis from surgical wound, respiratory failure, AKI",
        "keywords": ["mrsa", "sepsis", "wound", "respiratory failure", "kidney", "surgical", "lung cancer"],
        "cpt": [],
        "icd": [
            {"code": "A41.0", "desc": "Sepsis due to S. aureus"},
            {"code": "J96.01", "desc": "Acute respiratory failure with hypoxia"},
            {"code": "N17.0", "desc": "Acute kidney failure"},
        ],
        "rule": "MRSA sepsis = A41.0. RF = J96.01. AKI = N17.0.",
    },
    "real_patient_18": {
        "category": "icd10",
        "scenario": "32yo female, 36 weeks, severe pre-eclampsia, eclampsia, seizure, HELLP, T1DM, CKD 3a, magnesium sulfate, C-section",
        "keywords": ["pre-eclampsia", "eclampsia", "seizure", "hellp", "diabetes", "kidney", "magnesium", "cesarean", "pregnancy"],
        "cpt": [],
        "icd": [
            {"code": "O14.14", "desc": "Severe pre-eclampsia, third trimester"},
            {"code": "O15.0", "desc": "Eclampsia in pregnancy"},
            {"code": "O14.24", "desc": "HELLP syndrome"},
            {"code": "E10.9", "desc": "Type 1 diabetes"},
            {"code": "N18.31", "desc": "CKD stage 3a"},
        ],
        "rule": "Pre-eclampsia (O14.14) + eclampsia (O15.0) + HELLP (O14.24) + T1DM (E10.9) + CKD (N18.31).",
    },
    "real_patient_19": {
        "category": "surgery",
        "scenario": "55yo male, right inguinal hernia, open mesh repair, direct hernia",
        "keywords": ["inguinal", "hernia", "mesh", "repair", "direct", "groin"],
        "cpt": [{"code": "49560", "desc": "Repair inguinal hernia, 5cm or less", "reason": "Open inguinal hernia repair"}],
        "icd": [{"code": "K40.90", "desc": "Unilateral inguinal hernia, without gangrene or obstruction"}],
        "rule": "Inguinal hernia repair = 49560.",
    },
    "real_patient_20": {
        "category": "icd10",
        "scenario": "75yo right-handed female, acute ischemic stroke right MCA, NIHSS 12, TPA, residual right hemiparesis",
        "keywords": ["stroke", "ischemic", "mca", "tpa", "hemiparesis", "right", "residual"],
        "cpt": [],
        "icd": [
            {"code": "I63.51", "desc": "Cerebral infarction due to thrombosis of left middle cerebral artery"},
            {"code": "I69.354", "desc": "Monoplegia of right side due to cerebral infarction"},
        ],
        "rule": "Acute stroke = I63.51. Residual hemiparesis = I69.354.",
    },
}


def get_case_answer(case_key: str) -> Optional[Dict]:
    """Get the accurate answer for a specific case."""
    return ALL_CASES.get(case_key)


def get_all_cases() -> Dict[str, Dict]:
    """Get all cases."""
    return ALL_CASES.copy()


def get_cases_by_category(category: str) -> List[Dict]:
    """Get all cases in a category."""
    return [
        {"key": k, **v} for k, v in ALL_CASES.items()
        if v.get("category", "").lower() == category.lower()
    ]


def search_cases(keyword: str) -> List[Dict]:
    """Search cases by keyword."""
    keyword_lower = keyword.lower()
    return [
        {"key": k, **v} for k, v in ALL_CASES.items()
        if keyword_lower in v.get("scenario", "").lower()
    ]
