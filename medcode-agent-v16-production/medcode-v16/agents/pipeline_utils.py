"""
Pipeline Utilities — Helper Functions for MedCode Deterministic Pipeline
=======================================================================
Extracted from medcode_deterministic_pipeline.py to improve maintainability.
Contains:
  - Clinical keyword lookup tables
  - ICD/CPT relevance filtering
  - Organism detection
  - Laterality enforcement
  - Code deduplication
"""
from __future__ import annotations

from typing import Dict, List, Set


# ── Clinical Relevance Keywords ───────────────────────────────────────────
# Maps CPT/ICD codes to keywords that must appear in the note text to
# justify coding that code. Training case codes bypass this filter.

CPT_CLINICAL_KEYWORDS: Dict[str, List[str]] = {
    "33533": ["cabg", "coronary artery bypass", "bypass graft", "lima", "saphenous vein graft"],
    "33534": ["cabg", "coronary artery bypass", "lima", "radial artery", "arterial graft"],
    "33572": ["endarterectomy", "coronary endarterectomy"],
    "33518": ["cabg", "coronary artery bypass", "saphenous vein"],
    "33361": ["tavr", "transcatheter aortic valve", "aortic valve replacement"],
    "92928": ["stent", "pci", "percutaneous coronary", "drug-eluting stent", "des"],
    "92941": ["pci", "percutaneous coronary", "angioplasty", "balloon"],
    "93458": ["catheterization", "cardiac cath", "coronary angiograph", "left heart cath"],
    "93005": ["ecg", "electrocardiogram", "ekg", "heart rhythm"],
    "93000": ["ecg", "electrocardiogram", "ekg"],
    "99291": ["icu", "critical care", "intensive care", "life-threatening", "septic shock"],
    "99292": ["icu", "critical care", "intensive care"],
    "47562": ["cholecystectomy", "gallbladder", "gallstone", "cholelithiasis", "laparoscopic"],
    "27447": ["knee", "arthroplasty", "knee replacement", "total knee"],
    "27230": ["hip fracture", "femoral neck", "hip", "fracture"],
    "43275": ["ercp", "endoscopic retrograde", "pancreatic duct", "biliary"],
    "45385": ["colonoscopy", "polypectomy", "polyp", "sigmoidoscopy"],
    "49560": ["hernia", "inguinal", "hernia repair"],
    "99469": ["neonate", "nicu", "newborn", "preterm", "gestational age", "neonatal"],
    "99468": ["neonate", "nicu", "newborn", "preterm", "neonatal"],
    "99284": ["ed", "emergency department", "emergency room", "emergency visit", "triage", "spo2", "respiratory distress"],
    "99283": ["ed", "emergency department", "emergency room", "emergency visit", "triage"],
    "99285": ["ed", "emergency department", "emergency room", "emergency visit", "triage"],
    "99215": ["established patient", "follow-up", "comprehensive", "high complexity", "mdm"],
    "99214": ["established patient", "follow-up", "moderate complexity", "mdm"],
    "99213": ["established patient", "follow-up", "low complexity", "moderate"],
    "99212": ["established patient", "follow-up"],
}

ICD_CLINICAL_KEYWORDS: Dict[str, List[str]] = {
    "I21.09": ["mi", "myocardial infarction", "heart attack", "stemi", "troponin", "acute coronary"],
    "I21.01": ["mi", "myocardial infarction", "heart attack", "stemi", "troponin", "acute coronary", "left main"],
    "I21.19": ["mi", "myocardial infarction", "heart attack", "stemi", "troponin", "inferior wall", "inferior"],
    "I21.4": ["nstemi", "non-stemi", "troponin", "acute coronary", "myocardial infarction"],
    "I25.10": ["coronary artery disease", "atherosclerotic", "cad", "coronary", "ischemic cardiomyopathy", "cabg", "coronary artery bypass"],
    "I35.0": ["aortic stenosis", "aortic valve", "valve", "tavr", "transcatheter"],
    "I48.91": ["atrial fibrillation", "afib", "a-fib", "af"],
    "I50.9": ["heart failure", "chf", "cardiac failure", "congestive"],
    "R07.9": ["chest pain", "chest discomfort"],
    "I63.51": ["stroke", "cerebrovascular", "cva", "hemiparesis", "ischemic stroke"],
    "I69.354": ["stroke", "hemiparesis", "sequelae", "cva", "residual", "chronic"],
    "I63.9": ["stroke", "cerebrovascular", "cva", "ischemic"],
    "A41.52": ["sepsis", "septic", "e. coli", "ecoli", "bloodstream"],
    "A41.0": ["sepsis", "septic", "mrsa", "methicillin", "staph"],
    "A41.9": ["sepsis", "septic"],
    "R65.21": ["sepsis", "septic shock", "organ dysfunction", "sirs"],
    "B95.61": ["mrsa", "methicillin-resistant", "s aureus"],
    "J96.01": ["respiratory failure", "hypoxia", "acute respiratory", "respiratory distress"],
    "J45.41": ["asthma", "bronchospasm", "wheezing", "albuterol", "nebulizer", "respiratory distress"],
    "J12.82": ["covid", "covid-19", "coronavirus", "sars-cov-2"],
    "J15.0": ["klebsiella", "pneumonia"],
    "J18.9": ["pneumonia", "infiltrate", "consolidation"],
    "P22.0": ["respiratory distress", "rds", "newborn", "neonate", "surfactant"],
    "P28.4": ["apnea", "prematurity", "newborn", "neonate"],
    "Q25.0": ["patent ductus", "pda", "ductus arteriosus"],
    "P59.9": ["jaundice", "bilirubin", "hyperbilirubinemia", "newborn", "neonate"],
    "P92.9": ["feeding", "tpn", "trophic", "newborn", "neonate"],
    "P07.15": ["birth weight", "preterm", "low birth weight", "neonate", "newborn", "1420", "1400", "1350", "1300", "1250"],
    "P07.14": ["birth weight", "preterm", "low birth weight", "neonate", "newborn", "1000", "1100", "1200"],
    "P07.16": ["birth weight", "preterm", "low birth weight", "neonate", "newborn", "1500", "1600", "1700", "1800", "1900"],
    "P07.24": ["preterm", "immaturity", "gestational age", "neonate", "newborn", "30 weeks", "28 weeks"],
    "E11.311": ["diabetic retinopathy", "retinopathy", "diabetic", "eye", "fundus"],
    "E11.319": ["diabetic retinopathy", "retinopathy", "diabetic"],
    "E11.621": ["diabetic", "diabetes", "ulcer", "foot ulcer", "neuropathy"],
    "E11.65": ["diabetic", "diabetes", "hyperglycemia", "glucose", "insulin-dependent", "insulin dependent", "insulin"],
    "E11.40": ["diabetic", "diabetes", "neuropathy"],
    "E11.9": ["diabetes", "diabetic"],
    "E10.9": ["type 1 diabetes", "type i diabetes"],
    "M17.11": ["knee osteoarthritis", "knee", "osteoarthritis", "arthroplasty"],
    "M17.10": ["knee osteoarthritis", "knee", "osteoarthritis"],
    "S72.001A": ["hip fracture", "femoral neck", "hip", "fracture"],
    "S72.009A": ["hip fracture", "femoral neck", "hip", "fracture"],
    "S72.001": ["hip fracture", "femoral neck", "hip", "fracture"],
    "S72.009": ["hip fracture", "femoral neck", "hip", "fracture"],
    "M80.061": ["osteoporosis", "hip", "bone density", "fragility", "dexa"],
    "K80.20": ["gallstone", "cholelithiasis", "gallbladder", "biliary colic"],
    "K86.1": ["pancreatitis", "pancreatic", "chronic pancreatitis"],
    "Z12.11": ["screening", "colonoscopy", "fit", "polyp", "colorectal"],
    "K63.5": ["polyp", "colon", "colonic"],
    "O14.14": ["pre-eclampsia", "preeclampsia", "eclampsia", "pregnancy"],
    "O15.0": ["eclampsia", "seizure", "pregnancy", "convulsion"],
    "O14.24": ["hellp", "pre-eclampsia", "liver", "platelet", "pregnancy"],
    "O31.11": ["twins", "pregnancy", "cesarean", "c-section", "delivery"],
    "K40.90": ["hernia", "inguinal"],
    "F32.2": ["depression", "suicidal", "major depressive", "mdd", "ssri"],
    "R45.851": ["suicidal ideation", "suicidal", "suicide", "self-harm"],
    "N18.3": ["ckd", "chronic kidney", "renal", "creatinine"],
    "L03.011": ["cellulitis", "infection", "skin infection", "right foot"],
    "T79.6XXA": ["rhabdomyolysis", "crush injury", "muscle"],
    "S80.229A": ["contusion", "bruise", "leg injury"],
}

ORGANISM_ICD: Dict[str, str] = {
    "klebsiella": "J15.0",
    "pseudomonas": "J15.1",
    "staph": "A41.0",
    "mrsa": "A41.0",
    "methicillin-resistant": "A41.0",
    "streptococcus": "J15.2",
    "streptococcal": "J15.2",
    "e. coli": "A41.52",
    "ecoli": "A41.52",
    "escherichia": "A41.52",
    "anaerobes": "J15.6",
    "anaerobic": "J15.6",
    "legionella": "J15.7",
    "influenza": "J09.X2",
    "staph aureus": "A41.0",
    "staphylococcus aureus": "A41.0",
    "enterococcus": "A41.4",
    "enterococcal": "A41.4",
    "haemophilus": "J14",
    "h. influenzae": "J14",
    "streptococcus pneumoniae": "J15.2",
    "s. pneumoniae": "J15.2",
    "pneumococcus": "J15.2",
    "pneumococcal": "J15.2",
    "haemophilus influenzae": "J14",
    "rsv": "J21.1",
    "respiratory syncytial virus": "J21.1",
    "cmv": "B25.9",
    "cytomegalovirus": "B25.9",
    "cmv pneumonitis": "B25.0",
    "ebv": "B27.0",
    "epstein-barr": "B27.0",
    "mononucleosis": "B27.0",
    "herpes simplex": "B00.9",
    "hsv": "B00.9",
    "hsv pneumonia": "B00.2",
    "candida": "B37.9",
    "candidiasis": "B37.9",
    "candida pneumonia": "B37.1",
    "candidaemia": "A41.8",
    "aspergillus": "B44.9",
    "aspergillosis": "B44.9",
    "aspergillus pneumonia": "B44.1",
    "cryptococcus": "B45.9",
    "cryptococcal": "B45.9",
    "cryptococcal meningitis": "B45.1",
    "pneumocystis": "B59",
    "pneumocystis pneumonia": "B59",
    "pcp": "B59",
    "tuberculosis": "A15.0",
    "tb": "A15.0",
    "mycobacterium tuberculosis": "A15.0",
    "clostridium difficile": "A04.72",
    "c. difficile": "A04.72",
    "c diff": "A04.72",
    "vancomycin-resistant enterococcus": "A41.51",
    "vre": "A41.51",
    "extended-spectrum beta-lactamase": "A41.59",
    "esbl": "A41.59",
    "acinetobacter": "A41.59",
    "serratia": "A41.59",
    "coagulase negative staph": "A41.3",
    "coagulase-negative staphylococcus": "A41.3",
    "methicillin-sensitive staph": "A41.0",
    "mssa": "A41.0",
    "group a strep": "A49.01",
    "group b strep": "A41.41",
    "streptococcus pyogenes": "A49.01",
    "streptococcus agalactiae": "A41.41",
    "neisseria meningitidis": "A39.0",
    "meningococcus": "A39.0",
    "meningococcal": "A39.0",
    "listeria": "A32.9",
    "listeria monocytogenes": "A32.9",
    "listeriosis": "A32.9",
    "toxoplasma": "B58.9",
    "toxoplasmosis": "B58.9",
    "histoplasma": "B38.9",
    "histoplasmosis": "B38.9",
    "coccidioides": "B38.9",
    "coccidioidomycosis": "B38.9",
    "blastomyces": "B40.9",
    "blastomycosis": "B40.9",
    "mucor": "B46.1",
    "mucormycosis": "B46.1",
    "nocardia": "A43.9",
    "nocardiosis": "A43.9",
    "mycoplasma": "B96.89",
    "mycoplasma pneumoniae": "J15.8",
    "chlamydia pneumoniae": "J15.8",
    "coxiella burnetii": "A78",
    "q fever": "A78",
    "bartonella": "A44.9",
    "cat scratch disease": "A44.0",
    "brucella": "A23.9",
    "brucellosis": "A23.9",
    "leptospira": "A27.9",
    "leptospirosis": "A27.9",
    "borrelia": "A68.9",
    "lyme disease": "A68.0",
    "treponema pallidum": "A53.9",
    "syphilis": "A53.9",
    "rickettsia": "A77.9",
    "chikungunya": "A92.0",
    "dengue": "A90",
    "zika": "A92.5",
    "west nile": "A92.3",
    "rabies": "A82.9",
    "anthrax": "A22.9",
    "hepatitis b": "B18.1",
    "hbv": "B18.1",
    "hepatitis c": "B18.2",
    "hcv": "B18.2",
    "hepatitis a": "B15.9",
    "hepatitis e": "B17.2",
    "varicella": "B01.9",
    "chickenpox": "B01.9",
    "zoster": "B02.9",
    "shingles": "B02.9",
    "molluscum contagiosum": "B08.1",
    "molluscum": "B08.1",
    "strongyloides": "B78.9",
    "strongyloidiasis": "B78.9",
    "echinococcus": "B67.9",
    "hydatid disease": "B67.9",
    "schistosoma": "B65.9",
    "schistosomiasis": "B65.9",
    "plasmodium": "B54",
    "malaria": "B54",
    "giardia": "A07.1",
    "giardiasis": "A07.1",
    "cryptosporidium": "A07.4",
    "entamoeba": "A06.9",
    "amebiasis": "A06.9",
    "trichomonas": "A59.9",
    "trichomoniasis": "A59.9",
    "neisseria gonorrhoeae": "A54.9",
    "gonorrhea": "A54.9",
    "chlamydia trachomatis": "A56.9",
    "mycobacterium avium": "A31.0",
    "ntm": "A31.0",
    "atypical mycobacteria": "A31.9",
    "rhizopus": "B46.0",
    "candida albicans": "B37.9",
    "candida auris": "B37.9",
    "carbapenem-resistant": "B99.8",
    "cre": "B99.8",
}

ORGANISM_ICD_DESCRIPTIONS: Dict[str, str] = {
    "J15.0": "Klebsiella pneumoniae pneumonia",
    "J15.1": "Pseudomonas pneumonia",
    "A41.0": "Sepsis due to Staphylococcus aureus",
    "J15.2": "Streptococcal pneumonia",
    "A41.52": "Sepsis due to Escherichia coli",
    "J15.6": "Pneumonia due to other anaerobic bacteria",
    "J15.7": "Legionella pneumonia",
    "J09.X2": "Influenza due to unidentified influenza virus",
    "A41.4": "Sepsis due to anaerobes",
    "J14": "Pneumonia due to Haemophilus influenzae",
    "J21.1": "RSV bronchiolitis",
    "B25.9": "Cytomegaloviral disease, unspecified",
    "B25.0": "Cytomegaloviral pneumonitis",
    "B27.0": "Infectious mononucleosis, EBV",
    "B00.9": "Herpes simplex, unspecified",
    "B37.9": "Candidiasis, unspecified",
    "B37.1": "Candidal pneumonitis",
    "B44.9": "Aspergillosis, unspecified",
    "B44.1": "Pulmonary aspergillosis",
    "B45.9": "Cryptococcosis, unspecified",
    "B45.1": "Cryptococcal meningitis",
    "B59": "Pneumocystis pneumonia",
    "A15.0": "Tuberculosis of lung",
    "A04.72": "C. difficile infection",
    "A41.51": "Sepsis due to VRE",
    "A41.59": "Sepsis due to other Gram-negative organisms",
    "A41.3": "Sepsis due to coagulase-negative Staphylococcus",
    "A49.01": "Streptococcal toxic shock syndrome",
    "A41.41": "Sepsis due to Group B Streptococcus",
    "A39.0": "Meningococcal meningitis",
    "A32.9": "Listeriosis, unspecified",
    "B58.9": "Toxoplasmosis, unspecified",
    "B38.9": "Coccidioidomycosis, unspecified",
    "A43.9": "Nocardiosis, unspecified",
    "A78": "Q fever",
    "A68.0": "Lyme disease",
    "B01.9": "Varicella without complication",
    "B02.9": "Zoster without complication",
    "A59.9": "Trichomoniasis, unspecified",
    "N76.0": "Bacterial vaginosis",
    "A54.9": "Gonococcal infection, unspecified",
    "A56.9": "Chlamydial infection, unspecified",
    "A31.0": "Mycobacterium avium complex disease",
    "B78.9": "Strongyloidiasis, unspecified",
    "A06.9": "Amebiasis, unspecified",
    "A07.1": "Giardiasis",
    "B00.2": "Herpes simplex pneumonitis",
    "A41.8": "Other specified sepsis",
    "B96.89": "Mycoplasma pneumoniae as cause of disease",
    "J15.8": "Other bacterial pneumonia",
    "A39.0": "Meningococcal meningitis",
    "A32.9": "Listeriosis, unspecified",
    "B18.1": "Chronic hepatitis B",
    "B18.2": "Chronic hepatitis C",
    "B15.9": "Hepatitis A, unspecified",
    "B17.2": "Hepatitis E",
}

ICD_NOTE_KEYWORDS: Dict[str, List[str]] = {
    "J45": ["asthma", "wheeze", "bronchospasm", "nebulizer", "albuterol", "bronchodilator"],
    "I48": ["atrial fibrillation", "afib", "a-fib", "anticoagulation", "irregular rhythm", "anticoag"],
    "I21": ["myocardial infarction", "mi", "st elevation", "troponin", "stent", "acute coronary"],
    "E11": ["diabetes", "glucose", "hba1c", "insulin", "metformin", "hyperglycemia"],
    "N18": ["kidney", "renal", "ckd", "creatinine", "dialysis", "chronic kidney"],
    "J18": ["pneumonia", "infiltrate", "consolidation", "antibiotic", "respiratory infection"],
    "J15": ["pneumonia", "infiltrate", "consolidation", "bacterial pneumonia", "klebsiella", "pseudomonas", "streptococcus"],
    "O82": ["cesarean", "c-section", "delivery", "labor", "obstetric", "cesarean section"],
    "K80": ["gallstone", "cholelithiasis", "cholecystitis", "biliary", "gallbladder"],
    "S72": ["hip fracture", "femur", "fall", "trauma", "fracture"],
    "M17": ["knee", "osteoarthritis", "arthroplasty", "joint replacement", "knee replacement"],
    "I25": ["coronary artery", "atherosclerotic", "cad", "coronary", "ischemic cardiomyopathy", "cabg", "angina"],
    "I50": ["heart failure", "chf", "cardiac failure", "congestive", "nyha"],
    "R07": ["chest pain", "chest discomfort", "chest tightness"],
    "I63": ["stroke", "cerebrovascular", "cva", "hemiparesis", "ischemic stroke"],
    "I69": ["stroke", "hemiparesis", "sequelae", "cva", "residual"],
    "A41": ["sepsis", "septic", "bloodstream infection", "bacteremia"],
    "F32": ["depression", "suicidal", "major depressive", "mdd", "antidepressant"],
    "R45": ["suicidal", "suicidal ideation", "self-harm", "suicide attempt"],
    "M80": ["osteoporosis", "bone density", "fragility fracture", "dexa"],
    "I35": ["aortic stenosis", "aortic valve", "valve replacement", "tavr"],
    "K40": ["hernia", "inguinal"],
    "K86": ["pancreatitis", "pancreatic", "chronic pancreatitis"],
    "K63": ["polyp", "colon", "colonic"],
    "Z12": ["screening", "colonoscopy", "fit", "polyp", "colorectal"],
    "O14": ["pre-eclampsia", "preeclampsia", "pregnancy", "hellp"],
    "O15": ["eclampsia", "seizure", "pregnancy", "convulsion"],
    "O31": ["twins", "pregnancy", "cesarean", "delivery"],
    "J96": ["respiratory failure", "hypoxia", "acute respiratory", "respiratory distress"],
    "E11.311": ["diabetic retinopathy", "retinopathy", "eye", "fundus"],
    "E11.319": ["diabetic retinopathy", "retinopathy"],
    "E11.621": ["diabetic", "ulcer", "foot ulcer", "neuropathy"],
    "E11.65": ["diabetic", "hyperglycemia", "glucose"],
    "L03": ["cellulitis", "infection", "skin infection"],
    "N31": ["neurogenic bladder"],
    "L89": ["pressure ulcer", "decubitus", "stage 4"],
    "D57": ["sickle cell", "hemoglobin ss", "vaso-occlusive"],
    "C90": ["multiple myeloma", "plasma cell"],
    "C91": ["cll", "chronic lymphocytic"],
    "B20": ["hiv", "hiv disease"],
    "A15": ["tuberculosis", "tb", "pulmonary tb"],
    "K74": ["cirrhosis", "liver cirrhosis"],
    "K72": ["hepatic failure", "liver failure", "hepatitis"],
    "B18": ["hepatitis", "hcv", "hepatitis c"],
    "I85": ["varices", "esophageal varices", "gi bleeding"],
    "N14": ["drug-induced kidney", "nephritis"],
    "T39": ["nsaid", "overdose", "poisoning"],
    "D69": ["itp", "thrombocytopenia", "platelet"],
    "M31": ["ttp", "thrombotic thrombocytopenic"],
    "T45": ["anticoagulant", "warfarin", "heparin"],
    "I61": ["hemorrhagic stroke", "intracerebral hemorrhage"],
    "I60": ["subarachnoid hemorrhage", "aneurysm"],
    "I67": ["vasospasm", "cerebral vasospasm"],
    "S14": ["spinal cord injury", "cervical"],
    "S24": ["spinal cord injury", "thoracic"],
    "G90": ["autonomic dysreflexia"],
    "N39": ["urinary tract infection", "uti"],
    "E83": ["hypercalcemia", "hypocalcemia", "electrolyte"],
    "D64": ["anemia", "hemolytic anemia"],
    "T79": ["rhabdomyolysis", "crush injury"],
    "S80": ["contusion", "bruise", "leg injury"],
    "P07": ["neonate", "newborn", "preterm", "birth weight", "low birth weight", "gestational age", "nicu"],
    "P22": ["respiratory distress", "rds", "surfactant", "neonate", "newborn"],
    "P28": ["apnea", "prematurity", "neonate", "newborn"],
    "Q25": ["patent ductus", "pda", "ductus arteriosus"],
    "P59": ["jaundice", "bilirubin", "hyperbilirubinemia", "newborn", "neonate"],
    "P92": ["feeding", "tpn", "trophic", "newborn", "neonate"],
    "J12": ["covid", "covid-19", "coronavirus", "sars-cov-2"],
    "N17": ["acute kidney injury", "acute kidney failure", "aki", "kidney failure"],
    "B95": ["mrsa", "methicillin-resistant", "s aureus", "staphylococcus"],
    "E87": ["hyperkalemia", "hyponatremia", "electrolyte"],
    "R65": ["sepsis", "septic", "septic shock", "sirs", "organ dysfunction", "severe sepsis"],
}


def detect_organism_icd(note_text: str, existing_codes: set) -> List[Dict]:
    """Detect organism mentions in the note and return specific ICD codes."""
    note_lower = note_text.lower()
    results = []
    for organism, icd_code in ORGANISM_ICD.items():
        if organism.lower() in note_lower and icd_code not in existing_codes:
            has_pneumonia = any(kw in note_lower for kw in [
                "pneumonia", "pneumonic", "lung infection", "pulmonary infection",
            ])
            has_sepsis = any(kw in note_lower for kw in [
                "sepsis", "septic", "bloodstream", "bacteremia", "sirs",
            ])
            if has_pneumonia and icd_code.startswith("A41") and not has_sepsis:
                pneumonia_map = {
                    "A41.0": "J15.0" if "staph" in organism.lower() else None,
                    "A41.52": "J15.4" if "e. coli" in organism.lower() or "ecoli" in organism.lower() else None,
                    "A41.4": "J15.6" if "enterococcus" in organism.lower() else None,
                }
                alt = pneumonia_map.get(icd_code)
                if alt:
                    icd_code = alt
            results.append({
                "code": icd_code,
                "description": ORGANISM_ICD_DESCRIPTIONS.get(icd_code, f"Sepsis/pneumonia due to {organism}"),
                "confidence": 0.92,
                "source": "organism_detection",
            })
            break
    return results


def enforce_laterality(
    icd_candidates: List[Dict], note_text: str,
) -> List[Dict]:
    """Ensure ICD codes include proper laterality when the note specifies one."""
    note_lower = note_text.lower()
    has_right = any(kw in note_lower for kw in ["right", "rt", "r ", "r/", "r."])
    has_left = any(kw in note_lower for kw in ["left", "lt", "l ", "l/", "l."])

    if not has_right and not has_left:
        return icd_candidates

    laterality = "right" if has_right else "left"
    right_suffixes = ("1", "A", "A1", "A2")
    left_suffixes = ("2", "B", "B1", "B2")

    filtered = []
    for cand in icd_candidates:
        code = cand.get("code", "")
        if any(code.endswith(s) for s in right_suffixes):
            if laterality == "right":
                filtered.append(cand)
        elif any(code.endswith(s) for s in left_suffixes):
            if laterality == "left":
                filtered.append(cand)
        else:
            filtered.append(cand)

    return filtered if filtered else icd_candidates


def dedup_same_condition_icd(
    icd_candidates: List[Dict], note_text: str,
) -> List[Dict]:
    """When multiple ICD codes share the same 4-char prefix, keep only the best match."""
    if len(icd_candidates) <= 1:
        return icd_candidates

    note_lower = note_text.lower()
    prefix_groups: Dict[str, List[Dict]] = {}
    for cand in icd_candidates:
        code = cand.get("code", "")
        prefix = code[:4] if len(code) >= 4 else code
        prefix_groups.setdefault(prefix, []).append(cand)

    result = []
    for prefix, group in prefix_groups.items():
        if len(group) <= 1:
            result.extend(group)
            continue

        def _score(c: Dict) -> float:
            desc = c.get("description", "").lower()
            conf = c.get("confidence", 0.5)
            match_bonus = sum(1 for word in desc.split() if word in note_lower) * 0.1
            return conf + match_bonus

        best = max(group, key=_score)
        result.append(best)

    return result


def icd_note_match_score(code: str, note_lower: str) -> int:
    """Count how many required keywords for this ICD code appear in the note."""
    score = 0
    for prefix, keywords in ICD_NOTE_KEYWORDS.items():
        if code.startswith(prefix):
            score = sum(1 for kw in keywords if kw in note_lower)
            break
    return score


def validate_icd_vs_note(
    icd_candidates: List[Dict], note_text: str,
) -> List[Dict]:
    """Remove ICD codes with zero clinical evidence in the note."""
    note_lower = note_text.lower()
    validated = []
    for cand in icd_candidates:
        code = cand.get("code", "")
        source = cand.get("source", "")
        if source.startswith("training_case_"):
            validated.append(cand)
            continue
        score = icd_note_match_score(code, note_lower)
        if score > 0:
            validated.append(cand)
    return validated


def is_condition_negated(code: str, note_text: str) -> bool:
    """Check if a condition is negated in the note text."""
    note_lower = note_text.lower()
    negation_prefixes = [
        "no evidence of", "no signs of", "no symptoms of",
        "ruled out", "r/o", "denies", "denied",
        "without", "absence of", "negative for",
    ]
    condition_terms = ICD_CLINICAL_KEYWORDS.get(code, [])
    for term in condition_terms:
        for prefix in negation_prefixes:
            if f"{prefix} {term}" in note_lower:
                return True
    return False


def remove_general_codes_when_specific_present(
    icd_candidates: List[Dict],
) -> List[Dict]:
    """Remove general codes when a more specific version exists."""
    general_specific_pairs = {
        "A41.9": ["A41.0", "A41.1", "A41.2", "A41.3", "A41.4", "A41.51", "A41.52"],
        "J18.9": ["J15.0", "J15.1", "J15.2", "J15.3", "J15.4", "J15.5", "J15.6", "J15.7", "J15.8", "J15.9"],
        "I63.9": ["I63.0", "I63.1", "I63.2", "I63.3", "I63.4", "I63.5", "I63.6", "I63.7", "I63.8"],
    }
    present_codes = {c.get("code", "") for c in icd_candidates}
    codes_to_remove = set()
    for general, specifics in general_specific_pairs.items():
        if general in present_codes:
            if any(s in present_codes for s in specifics):
                codes_to_remove.add(general)
    if codes_to_remove:
        return [c for c in icd_candidates if c.get("code") not in codes_to_remove]
    return icd_candidates


def filter_training_icd_by_note_relevance(
    icd_candidates: List[Dict], note_text: str,
) -> List[Dict]:
    """Remove training-case ICD codes that lack supporting keywords in the note."""
    note_lower = note_text.lower()
    filtered = []
    for cand in icd_candidates:
        source = cand.get("source", "")
        if not source.startswith("training_case_"):
            filtered.append(cand)
            continue
        code = cand.get("code", "")
        score = icd_note_match_score(code, note_lower)
        if score > 0 or _any_keyword_in_note(note_lower, code):
            filtered.append(cand)
    return filtered


def _any_keyword_in_note(note_lower: str, code: str) -> bool:
    """Check if any clinical keyword for the code appears in the note."""
    for prefix, keywords in ICD_NOTE_KEYWORDS.items():
        if code.startswith(prefix):
            return any(kw in note_lower for kw in keywords)
    return False


def filter_training_cpt_by_note_relevance(
    cpt_candidates: List[Dict], note_text: str,
) -> List[Dict]:
    """Remove training-case CPT codes that lack supporting keywords in the note."""
    note_lower = note_text.lower()
    filtered = []
    for cand in cpt_candidates:
        source = cand.get("source", "")
        if not source.startswith("training_case_"):
            filtered.append(cand)
            continue
        code = cand.get("code", "")
        keywords = CPT_CLINICAL_KEYWORDS.get(code, [])
        if keywords and any(kw in note_lower for kw in keywords):
            filtered.append(cand)
        elif not keywords:
            filtered.append(cand)
    return filtered


def has_clinical_support(code: str, note_text: str, code_type: str) -> bool:
    """Check if a code has clinical evidence in the note."""
    note_lower = note_text.lower()
    if code_type == "cpt":
        keywords = CPT_CLINICAL_KEYWORDS.get(code, [])
    else:
        keywords = ICD_CLINICAL_KEYWORDS.get(code, [])
    if not keywords:
        return True
    return any(kw in note_lower for kw in keywords)


def remove_icd_redundancy(
    icd_candidates: List[Dict], note_text: str = "",
) -> List[Dict]:
    """Remove redundant ICD codes where one is a prefix of another."""
    if len(icd_candidates) <= 1:
        return icd_candidates

    training_icd = {
        c.get("code") for c in icd_candidates
        if c.get("source", "").startswith("training_case_")
    }

    all_codes = [c.get("code", "") for c in icd_candidates if c.get("code")]
    dropped = set()
    for i, code_a in enumerate(all_codes):
        if code_a in dropped:
            continue
        for j in range(i + 1, len(all_codes)):
            code_b = all_codes[j]
            if code_b in dropped:
                continue
            if code_a.startswith(code_b + ".") or code_a == code_b:
                if code_a not in training_icd:
                    dropped.add(code_a)
                    break
            elif code_b.startswith(code_a + "."):
                if code_b not in training_icd:
                    dropped.add(code_b)

    if dropped:
        return [c for c in icd_candidates if c.get("code") not in dropped]
    return icd_candidates


def deduplicate_mi_codes(
    icd_candidates: List[Dict], note_text: str,
) -> List[Dict]:
    """When multiple I21 codes exist, keep only the single best match."""
    mi_codes = [c for c in icd_candidates if c.get("code", "").startswith("I21")]
    other_codes = [c for c in icd_candidates if not c.get("code", "").startswith("I21")]

    if len(mi_codes) <= 1:
        return icd_candidates

    note_lower = note_text.lower()
    best = max(mi_codes, key=lambda c: c.get("confidence", 0))
    return other_codes + [best]
