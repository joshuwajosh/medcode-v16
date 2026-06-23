"""
MedCode AI V19 — Clinical Note Parser
=====================================
Automatically extracts CPT and ICD-10 codes from free-text clinical notes.
Uses multi-layer approach: direct code detection, keyword matching, book engines, E/M engine.
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# LAYER 2: PROCEDURE KEYWORD → CPT CODE MAP (200+ entries)
# ═══════════════════════════════════════════════════════════════════
PROCEDURE_MAP = {
    # E/M
    "office visit": "99213", "established patient": "99213",
    "new patient visit": "99203", "follow-up visit": "99213",
    "annual physical": "99395", "annual wellness": "99397",
    "telehealth visit": "99441", "telephone e/m": "99441",
    "critical care": "99291", "critical care initial": "99291",
    "critical care subsequent": "99292",
    "emergency department": "99283", "ed visit": "99283",
    "hospital admission": "99223", "inpatient admission": "99223",
    "hospital observation": "99218", "observation care": "99218",
    "discharge management": "99238", "hospital discharge": "99238",
    "nursing facility": "99310", "snf visit": "99310",
    "home visit": "99350", "house call": "99350",
    "care coordination": "99490", "chronic care management": "99490",
    "advance care planning": "99497",
    # Cardiovascular
    "cabg": "33533", "coronary artery bypass": "33533",
    "cabg x3": "33533", "cabg x4": "33534",
    "off-pump cabg": "33530", "minimally invasive cabg": "33530",
    "valve replacement": "33430", "aortic valve replacement": "33430",
    "mitral valve replacement": "33430",
    "tavr": "33361", "transcatheter aortic valve": "33361",
    "mitraclip": "33418",
    "pacemaker implant": "33230", "pacemaker insertion": "33230",
    "icd implant": "33240", "defibrillator implant": "33240",
    "cardiac catheterization": "93458", "heart catheterization": "93458",
    "right heart cath": "93503", "pulmonary artery catheter": "93503",
    "coronary angiogram": "93458", "angiography coronary": "93458",
    "pci": "92928", "percutaneous coronary intervention": "92928",
    "stent placement": "92928", "coronary stent": "92928",
    "angioplasty": "92928", "balloon angioplasty": "92928",
    "echocardiogram": "93306", "transthoracic echo": "93306",
    "tte": "93306", "transesophageal echo": "93312",
    "tee": "93312", "stress echo": "93350",
    "ecg": "93000", "ekg": "93000", "electrocardiogram": "93000",
    "12-lead ecg": "93000", "holter monitor": "93224",
    "event monitor": "93224", "cardiac monitoring": "93224",
    "pericardiocentesis": "33016", "pericardial window": "33016",
    "cardioversion": "92960", "electrical cardioversion": "92960",
    "ablation": "93656", "cardiac ablation": "93656",
    "rf ablation": "93656", "radiofrequency ablation": "93656",
    "evar": "34900", "endovascular repair aorta": "34900",
    "tevar": "33910", "thoracic endovascular": "33910",
    "carotid endarterectomy": "35301", "cea": "35301",
    "carotid stent": "37215",
    "av fistula": "36825", "arteriovenous fistula": "36825",
    "dialysis catheter": "36556",
    # General Surgery
    "cholecystectomy": "47562", "laparoscopic cholecystectomy": "47562",
    "lap chole": "47562", "open cholecystectomy": "47600",
    "appendectomy": "44970", "laparoscopic appendectomy": "44970",
    "open appendectomy": "44960",
    "hernia repair": "49560", "inguinal hernia repair": "44950",
    "inguinal hernia": "44950", "umbilical hernia": "49585",
    "incisional hernia": "49560", "ventral hernia": "49560",
    "laparoscopic hernia": "44970",
    "colonoscopy": "45378", "diagnostic colonoscopy": "45378",
    "colonoscopy with biopsy": "45380",
    "colonoscopy with polypectomy": "45385", "polypectomy": "45385",
    "upper endoscopy": "43239", "egd": "43239",
    "esophagogastroduodenoscopy": "43239",
    "endoscopy with biopsy": "43239", "endoscopy diagnostic": "43235",
    "ercp": "43279", "endoscopic retrograde cholangiopancreatography": "43279",
    "ercp with stent": "43279", "ercp with sphincterotomy": "43260",
    "bowel resection": "44160", "small bowel resection": "44160",
    "colectomy": "44160", "right hemicolectomy": "44160",
    "left hemicolectomy": "44160", "sigmoid colectomy": "44160",
    "low anterior resection": "44145", "rectal resection": "44145",
    "whipple procedure": "48150", "pancreaticoduodenectomy": "48150",
    "splenectomy": "38120", "laparoscopic splenectomy": "38120",
    "herniotomy": "49505", "herniorrhaphy": "49505",
    "proctectomy": "45110", "hemorrhoidectomy": "46922",
    "fistulotomy": "46250", "anal fistula repair": "46250",
    "pilonidal cyst excision": "11770",
    "gastrostomy": "43760", "peg tube": "43760",
    "jejunostomy": "43760", "feeding tube": "43760",
    # Orthopedics
    "total knee replacement": "27447", "tkr": "27447",
    "total knee arthroplasty": "27447",
    "total hip replacement": "27130", "tha": "27130",
    "total hip arthroplasty": "27130",
    "partial knee replacement": "27446",
    "reverse shoulder": "23473",
    "shoulder replacement": "23472",
    "rotator cuff repair": "29827", "rotator cuff": "29827",
    "arthroscopy knee": "29881", "knee arthroscopy": "29881",
    "meniscectomy": "29881",
    "arthroscopy shoulder": "29826",
    "acl reconstruction": "29888", "acl repair": "29888",
    "carpal tunnel release": "64721",
    "trigger finger release": "26055",
    "spinal fusion": "22612", "lumbar fusion": "22612",
    "cervical fusion": "22551", "acdf": "22551",
    "laminectomy": "63047", "lumbar laminectomy": "63047",
    "discectomy": "63030", "microdiscectomy": "63030",
    "disc replacement": "22558",
    "fracture repair": "27752", "orif": "27752",
    "open reduction internal fixation radius": "25607",
    "open reduction internal fixation tibia": "27756",
    "open reduction and internal fixation radius": "25607",
    "open reduction and internal fixation tibia": "27756",
    "hip fracture repair": "27230", "femoral neck fracture repair": "27230",
    "femoral neck fracture orif": "27230",
    "internal fixation right hip fracture": "27230",
    "internal fixation hip fracture": "27230",
    "distal radius fracture": "25607",
    "tibial fracture": "27756",
    "clavicle fracture": "23500",
    "achilles repair": "27652",
    "achilles tendon repair": "27652",
    "biceps tendon repair": "23412",
    "hardware removal": "20670",
    # Cardiovascular Procedures
    "coronary angioplasty stent": "92928",
    "percutaneous coronary stent": "92928",
    # Neurosurgery
    "craniotomy": "61304", "craniectomy": "61304",
    "brain tumor resection": "61304",
    "aneurysm clipping": "61700",
    "vp shunt": "37800", "ventriculoperitoneal shunt": "37800",
    "dbs": "61850", "deep brain stimulation": "61850",
    "pituitary resection": "61546",
    "chiari decompression": "63001",
    "spine fusion": "22612", "spinal cord stimulator": "63650",
    # Urology
    "turbt": "51100", "bladder tumor resection": "51100",
    "nephrectomy": "50220", "radical nephrectomy": "50220",
    "partial nephrectomy": "50240",
    "prostatectomy": "55840", "radical prostatectomy": "55840",
    "robotic prostatectomy": "55842",
    "cystoscopy": "52000",
    "ureteral stent": "52332", "stent placement ureteral": "52332",
    "pcnl": "50080", "percutaneous nephrolithotomy": "50080",
    "eswl": "50590", "lithotripsy": "50590",
    "vasectomy": "55250",
    # ENT
    "tonsillectomy": "42820", "adenoidectomy": "42830",
    "myringotomy": "69424", "ear tubes": "69424",
    "tympanoplasty": "69610", "tympanostomy": "69424",
    "mastoidectomy": "69502",
    "parotidectomy": "42420",
    "thyroidectomy": "60240", "total thyroidectomy": "60240",
    "partial thyroidectomy": "60220",
    "septoplasty": "30520", "septorhinoplasty": "30520",
    "rhinoplasty": "30520", "sinus surgery": "31256",
    "fess": "31256", "functional endoscopic sinus surgery": "31256",
    "cochlear implant": "69930",
    "neck dissection": "38542",
    "laryngoscopy": "31575", "direct laryngoscopy": "31575",
    "upp": "21270", "uvulopalatopharyngoplasty": "21270",
    # OB/GYN
    "cesarean section": "59510", "c-section": "59510",
    "cesarean delivery": "59510", "c section": "59510",
    "vaginal delivery": "59400",
    "hysterectomy": "58150", "total hysterectomy": "58150",
    "vaginal hysterectomy": "58290",
    "laparoscopic hysterectomy": "58570",
    "tubal ligation": "58670", "bilateral tubal ligation": "58670",
    "ectopic pregnancy": "59120",
    "ovarian cystectomy": "58660",
    "colposcopy": "57452", "leep": "57452",
    "d&c": "58120", "dilation curettage": "58120",
    "hysteroscopy": "58555",
    "mid-urethral sling": "57287",
    # Pulmonology
    "bronchoscopy": "31622", "bronchoscopy with biopsy": "31625",
    "thoracentesis": "32405", "chest tube": "32480",
    "chest tube insertion": "32480",
    "lobectomy lung": "32480", "lung lobectomy": "32480",
    "wedge resection lung": "32480",
    "vats": "32480", "video assisted thoracoscopic": "32480",
    "tracheostomy": "31500",
    "sleep study": "95810", "polysomnography": "95810",
    "pulmonary function test": "94010", "pft": "94010",
    "ebus": "31629", "endobronchial ultrasound": "31629",
    "methacholine challenge": "95070",
    # Radiology
    "mri brain": "70553", "mri head": "70553",
    "mri lumbar spine": "72148", "mri cervical spine": "72141",
    "mri knee": "73721", "mri right knee": "73721", "mri left knee": "73721",
    "mri shoulder": "73020", "mri right shoulder": "73020",
    "ct head": "70450", "ct brain": "70450",
    "ct chest": "71260", "ct abdomen": "74177",
    "ct pelvis": "72198",
    "ct chest abdomen pelvis": "74177",
    "ct angiography": "71277",
    "pet ct": "78814", "pet scan": "78814",
    "mammography": "77067", "screening mammogram": "77067",
    "diagnostic mammogram": "77065",
    "ultrasound abdomen": "76700",
    "ultrasound pelvic": "76856",
    "cardiac ultrasound": "93306",
    "doppler ultrasound": "93880",
    "bone scan": "78300", "nuclear medicine bone": "78300",
    "dexa scan": "77080", "bone density": "77080",
    # Pathology/Lab
    "biopsy": "11102", "skin biopsy": "11102",
    "punch biopsy": "11102", "shave biopsy": "11102",
    "excision biopsy": "11602",
    "fine needle aspiration": "10021", "fna": "10021",
    "bone marrow biopsy": "38220", "bone marrow aspirate": "38220",
    "pap smear": "88141",
    # Pain Management
    "epidural injection": "62322", "epidural steroid injection": "62322",
    "lumbar epidural": "62322", "cervical epidural": "62322",
    "facet joint injection": "64490", "facet injection": "64490",
    "medial branch block": "64490",
    "trigger point injection": "20552",
    "joint injection": "20610", "intra-articular injection": "20610",
    "shoulder injection": "20610", "knee injection": "20610",
    "hip injection": "20610",
    "nerve block": "64450", "stellate ganglion block": "64450",
    "radiofrequency ablation spine": "64635",
    "spinal cord stimulator": "63650",
    "botox injection": "64612", "botulinum toxin": "64612",
    "botox migraine": "64612",
    # Anesthesia
    "general anesthesia": "00100",
    "regional anesthesia": "01960",
    "spinal anesthesia": "01967", "epidural anesthesia": "01967",
    "mac": "01960", "monitored anesthesia care": "01960",
    # Oncology
    "chemotherapy": "96401", "chemo infusion": "96401",
    "immunotherapy": "96401", "immunotherapy infusion": "96401",
    "radiation therapy": "77427", "radiation treatment": "77427",
    "imrt": "77301", "intensity modulated radiation": "77301",
    "sbrt": "77373", "stereotactic body radiation": "77373",
    "sentinel lymph node biopsy": "38900",
    "tumor debulking": "58200",
    # Dermatology
    "mohs surgery": "17315", "mohs micrographic surgery": "17315",
    "skin excision": "11602", "lesion excision": "11602",
    "cryotherapy": "17000", "cryosurgery": "17000",
    "edc": "17000", "electrodessication curettage": "17000",
    "laser treatment": "17000",
    "skin graft": "15100", "split thickness skin graft": "15100",
    "chemical peel": "17000",
    "dermal filler": "11900", "filler injection": "11900",
    # Ophthalmology
    "cataract surgery": "66984", "cataract extraction": "66984",
    "phacoemulsification": "66984", "lens implant": "66984",
    "glaucoma surgery": "66170", "trabeculectomy": "66170",
    "retinal laser": "67228",
    "avitreo retinal surgery": "67108",
    "intravitreal injection": "67028",
    # Nephrology
    "hemodialysis": "90935", "dialysis": "90935",
    "peritoneal dialysis": "90945",
    "kidney transplant": "50323",
    "renal biopsy": "50200",
    # Transplant
    "liver transplant": "47135",
    "heart transplant": "33910",
    "lung transplant": "32480",
    "bone marrow transplant": "38230",
    "stem cell transplant": "38230",
}

# ═══════════════════════════════════════════════════════════════════
# LAYER 3: DIAGNOSIS KEYWORD → ICD-10 CODE MAP (200+ entries)
# ═══════════════════════════════════════════════════════════════════
DIAGNOSIS_MAP = {
    # Cardiovascular
    "atrial fibrillation": "I48.91", "afib": "I48.91", "a-fib": "I48.91",
    "paroxysmal atrial fibrillation": "I48.0", "paroxysmal afib": "I48.0",
    "persistent atrial fibrillation": "I48.1", "chronic atrial fibrillation": "I48.91",
    "atrial flutter": "I48.3",
    "hypertension": "I10", "high blood pressure": "I10",
    "heart failure": "I50.9", "chf": "I50.9", "congestive heart failure": "I50.9",
    "systolic heart failure": "I50.20", "diastolic heart failure": "I50.30",
    "coronary artery disease": "I25.10", "cad": "I25.10",
    "atherosclerotic heart disease": "I25.10",
    "myocardial infarction": "I21.9", "heart attack": "I21.9",
    "acute mi": "I21.9", "st elevation mi": "I21.3",
    "st elevation myocardial infarction": "I21.3", "stemi": "I21.3",
    "nstemi": "I21.4", "non-st elevation mi": "I21.4",
    "nstemi": "I21.4",
    "angina": "I20.9", "chest pain": "R07.9",
    "dvt": "I82.402", "deep vein thrombosis": "I82.402",
    "pulmonary embolism": "I26.99",
    "pericarditis": "I30.9",
    "endocarditis": "I33.0",
    "cardiomyopathy": "I42.9",
    "aortic stenosis": "I35.0",
    "mitral regurgitation": "I34.0",
    "aortic aneurysm": "I71.4",
    "peripheral vascular disease": "I73.9",
    "claudication": "I73.9",
    "carotid stenosis": "I65.22",
    "stroke": "I63.9", "cerebrovascular accident": "I63.9",
    "cva": "I63.9", "brain attack": "I63.9",
    "ischemic stroke": "I63.9", "acute ischemic stroke": "I63.9",
    "hemorrhagic stroke": "I62.9",
    "transient ischemic attack": "G45.9", "tia": "G45.9",
    # Respiratory
    "copd": "J44.1", "chronic obstructive pulmonary disease": "J44.1",
    "emphysema": "J43.9",
    "asthma": "J45.901", "bronchial asthma": "J45.901",
    "mild asthma": "J45.20", "moderate asthma": "J45.40",
    "severe asthma": "J45.50", "asthma exacerbation": "J45.901",
    "moderate asthma exacerbation": "J45.41",
    "severe asthma exacerbation": "J45.51",
    "pneumonia": "J18.9", "bacterial pneumonia": "J15.9",
    "aspiration pneumonia": "J69.0",
    "bronchitis": "J20.9", "acute bronchitis": "J20.9",
    "pneumothorax": "J93.9",
    "pleural effusion": "J91.8",
    "respiratory failure": "J96.9",
    "acute respiratory failure": "J96.00",
    "interstitial lung disease": "J84.10",
    "pulmonary fibrosis": "J84.10",
    "sleep apnea": "G47.33", "osa": "G47.33",
    "croup": "J04.2",
    "bronchiolitis": "J21.9",
    # Endocrine
    "diabetes mellitus": "E11.9", "diabetes": "E11.9",
    "type 2 diabetes": "E11.9", "type 2 dm": "E11.9",
    "type 1 diabetes": "E10.9", "type 1 dm": "E10.9",
    "diabetic neuropathy": "E11.40",
    "diabetic retinopathy": "E11.319",
    "hypothyroidism": "E03.9", "hypothyroid": "E03.9",
    "hashimoto": "E06.3",
    "hyperthyroidism": "E05.90", "hyperthyroid": "E05.90",
    "graves disease": "E05.00",
    "cushing syndrome": "E24.9",
    "adrenal insufficiency": "E27.40",
    "hyperaldosteronism": "E26.9",
    "hypoglycemia": "E16.2",
    "hyperglycemia": "R73.9",
    # GI
    "gerd": "K21.0", "reflux": "K21.0", "acid reflux": "K21.0",
    "gastritis": "K29.70", "duodenitis": "K29.8",
    "peptic ulcer": "K27.9", "gastric ulcer": "K25.9",
    "duodenal ulcer": "K26.9",
    "cholecystitis": "K81.0", "cholelithiasis": "K80.20",
    "gallstones": "K80.20", "biliary colic": "K80.60",
    "pancreatitis": "K85.9", "acute pancreatitis": "K85.9",
    "chronic pancreatitis": "K86.1",
    "diverticulitis": "K57.32", "diverticulosis": "K57.31",
    "ulcerative colitis": "K51.0", "crohn disease": "K50.90",
    "inflammatory bowel disease": "K59.9",
    "cirrhosis": "K74.60", "liver cirrhosis": "K74.60",
    "hepatitis": "K75.9", "hepatitis b": "B18.1",
    "hepatitis c": "B18.2",
    "hepatocellular carcinoma": "C22.0",
    "esophageal varices": "I85.0",
    "appendicitis": "K35.80",
    "right inguinal hernia": "K40.91", "left inguinal hernia": "K40.90",
    "indirect inguinal hernia": "K40.91", "direct inguinal hernia": "K40.90",
    "femoral hernia": "K41.9",
    "constipation": "K59.00", "obstipation": "K56.009",
    "diarrhea": "K59.1",
    "dysphagia": "R13.10",
    "gi bleeding": "K92.2", "gastrointestinal bleeding": "K92.2",
    "lower gi bleed": "K92.2", "upper gi bleed": "K92.1",
    "intestinal obstruction": "K56.609", "bowel obstruction": "K56.609",
    "ileus": "K56.009",
    # Renal
    "ckd": "N18.9", "chronic kidney disease": "N18.9",
    "acute kidney injury": "N17.9", "aki": "N17.9",
    "renal failure": "N19", "kidney failure": "N19",
    "nephrotic syndrome": "N04.9",
    "nephritis": "N10", "pyelonephritis": "N10",
    "kidney stones": "N20.0", "renal calculi": "N20.0",
    "nephrolithiasis": "N20.0",
    "urinary tract infection": "N39.0", "uti": "N39.0",
    "pyelonephritis": "N10",
    "glomerulonephritis": "N05.9",
    # Neurological
    "alzheimer": "G30.9", "alzheimer disease": "G30.9",
    "dementia": "F03.90", "vascular dementia": "F01.50",
    "parkinson": "G20", "parkinson disease": "G20",
    "epilepsy": "G40.909", "seizure": "G40.909",
    "migraine": "R51.9", "tension headache": "R51.0",
    "multiple sclerosis": "G35",
    "peripheral neuropathy": "G62.9",
    "carpal tunnel syndrome": "G56.0",
    "radiculopathy": "M54.10", "sciatica": "M54.40",
    "back pain": "M54.5", "low back pain": "M54.5",
    "cervicalgia": "M54.2",
    "spinal stenosis": "M48.00",
    "herniated disc": "M51.10", "disc herniation": "M51.10",
    "degenerative disc disease": "M51.30", "ddd": "M51.30",
    "spondylosis": "M47.816",
    "paresthesia": "R20.9", "numbness": "R20.9",
    "weakness": "R53.1",
    # Musculoskeletal
    "osteoarthritis": "M19.90",
    "osteoarthritis right knee": "M17.11", "oa right knee": "M17.11",
    "osteoarthritis left knee": "M17.12", "oa left knee": "M17.12",
    "osteoarthritis right hip": "M16.11",
    "osteoarthritis left hip": "M16.12",
    "rheumatoid arthritis": "M06.9",
    "gout": "M10.9", "gouty arthritis": "M10.9",
    "fibromyalgia": "M79.0",
    "tendinitis": "M77.90", "tendonitis": "M77.90",
    "bursitis": "M70.90",
    "rotator cuff syndrome": "M75.10",
    "plantar fasciitis": "M72.10",
    "osteoporosis": "M81.0", "osteopenia": "M85.80",
    "osteomyelitis": "M86.9",
    "fracture": "T14.90", "broken bone": "T14.90",
    "hip fracture": "S72.009A", "femoral neck fracture": "S72.001A",
    "colles fracture": "S52.571A",
    "ankle fracture": "S82.891A",
    "clavicle fracture": "S42.009A",
    "tibia fracture": "S82.201A",
    # Psychiatric
    "depression": "F32.9", "major depressive disorder": "F32.9",
    "bipolar": "F31.9", "bipolar disorder": "F31.9",
    "anxiety": "F41.9", "anxiety disorder": "F41.9",
    "generalized anxiety": "F41.1",
    "panic disorder": "F41.0",
    "ptsd": "F43.10", "post-traumatic stress": "F43.10",
    "ocd": "F42.9", "obsessive compulsive": "F42.9",
    "schizophrenia": "F20.9",
    "adhd": "F90.0", "attention deficit hyperactivity": "F90.0",
    "insomnia": "F51.01",
    "substance abuse": "F19.90",
    "alcohol abuse": "F10.90", "alcohol dependence": "F10.20",
    # Infectious
    "sepsis": "A41.9", "septic shock": "A41.9",
    "urinary tract infection": "N39.0",
    "cellulitis": "L03.90",
    "abscess": "L02.91",
    "pneumonia": "J18.9",
    "tuberculosis": "A15.9",
    "hiv": "B20", "hiv infection": "B20",
    "covid": "U07.1", "covid-19": "U07.1", "coronavirus": "U07.1",
    "influenza": "J09.X2",
    "c diff": "A04.72", "clostridium difficile": "A04.72",
    # Hematology
    "anemia": "D64.9", "iron deficiency anemia": "D50.9",
    "thrombocytopenia": "D69.6",
    "leukocytosis": "D72.829",
    "leukopenia": "D72.810",
    "neutropenia": "D70.0",
    "lymphoma": "C85.9", "hodgkin lymphoma": "C81.9",
    "non-hodgkin lymphoma": "C85.9",
    "leukemia": "C95.9", "aml": "C92.00",
    " CLL": "C91.10",
    "myeloma": "C90.00", "multiple myeloma": "C90.00",
    # Oncology
    "cancer": "C80.1", "malignancy": "C80.1",
    "breast cancer": "C50.919", "lung cancer": "C34.90",
    "colon cancer": "C18.9", "prostate cancer": "C61",
    "pancreatic cancer": "C25.9",
    "melanoma": "C43.9", "skin cancer": "C44.90",
    # Rheumatology
    "lupus": "M32.9", "sle": "M32.9",
    "scleroderma": "M34.9",
    "sjogren": "M35.00",
    "vasculitis": "M31.9",
    "polymyalgia rheumatica": "M35.3",
    # Obstetric
    "pregnancy": "Z33.1", "pregnant": "Z33.1",
    "pre-eclampsia": "O14.90", "preeclampsia": "O14.90",
    "gestational diabetes": "O24.4",
    "placenta previa": "O44.00",
    "abruption placenta": "O45.00",
    "ectopic pregnancy": "O00.9",
    # Pediatrics
    "failure to thrive": "R62.51", "ftt": "R62.51",
    "jaundice": "R17.9", "neonatal jaundice": "P59.9",
    "apnea": "R06.82", "apnea of prematurity": "P28.4",
    # General/Round-up
    "obesity": "E66.01", "morbid obesity": "E66.01",
    "malnutrition": "E44.0", "severe malnutrition": "E43",
    "dehydration": "E86.0",
    "fever": "R50.9", "febrile": "R50.9",
    "syncope": "R55", "fainting": "R55",
    "dyspnea": "R06.02", "shortness of breath": "R06.02",
    "wheezing": "R06.2",
    "nausea": "R11.0", "vomiting": "R11.10",
    "abdominal pain": "R10.9",
    "dizziness": "R42",
    "fatigue": "R53.83",
    "cough": "R05.9",
    "edema": "R60.9", "swelling": "R60.9",
    "skin lesion": "L98.9", "rash": "R21",
    "weight loss": "R63.4", "weight gain": "R63.4",
    "insomnia": "F51.01", "sleep disturbance": "G47.00",
    "smoking": "F17.210", "tobacco use": "F17.210",
    "family history": "Z80.9",
    "family history of colon cancer": "Z80.0",
    "family history of breast cancer": "Z80.3",
    "family history of heart disease": "Z82.49",
    "family history of diabetes": "Z83.3",
    "personal history": "Z87.891",
    "status post": "Z90.89",
    "well child": "Z00.121", "well-child visit": "Z00.121",
    "well child examination": "Z00.121",
    "screening colonoscopy": "Z12.11", "colon cancer screening": "Z12.11",
}


# ═══════════════════════════════════════════════════════════════════
# ENCOUNTER TYPE DETECTION
# ═══════════════════════════════════════════════════════════════════
ENCOUNTER_KEYWORDS = {
    "emergency": ["emergency", "ed visit", "ed note", "emergency department", "trauma activation"],
    "inpatient": ["admission", "admitted", "hospital", "inpatient", "floor", "ward", "icu", "nicu", "picu"],
    "subsequent": ["progress note", "day 2", "day 3", "hospital day", "subsequent", "continued care"],
    "office": ["office visit", "clinic", "outpatient", "office", "ambulatory"],
    "surgery": ["operative report", "surgery", "surgical", "procedure", "anesthesia", "pre-op", "post-op"],
    "observation": ["observation", "obs unit", "telemetry"],
    "discharge": ["discharge summary", "discharge", "discharged"],
    "home": ["home visit", "home health", "house call", "domiciliary"],
    "telehealth": ["telehealth", "telemedicine", "phone", "virtual"],
    "nursing": ["nursing facility", "snf", "long-term care"],
}


class ClinicalNoteParser:
    """Multi-layer clinical note parser for CPT/ICD extraction."""

    def parse(self, note_text: str) -> Dict:
        """Parse a clinical note and return structured coding suggestions."""
        if not note_text or not note_text.strip():
            return {"error": "Empty note text", "cpt_codes": [], "icd_codes": []}

        encounter_type = self._detect_encounter_type(note_text)
        direct_cpt, direct_icd = self._detect_direct_codes(note_text)
        proc_codes = self._match_procedures(note_text)
        diag_codes = self._match_diagnoses(note_text)

        all_cpt = {}
        for code, info in direct_cpt.items():
            all_cpt[code] = {**info, "source": "direct_detection"}
        for code, info in proc_codes.items():
            if code not in all_cpt:
                all_cpt[code] = {**info, "source": "keyword_match"}

        all_icd = {}
        for code, info in direct_icd.items():
            all_icd[code] = {**info, "source": "direct_detection"}
        for code, info in diag_codes.items():
            if code not in all_icd:
                all_icd[code] = {**info, "source": "keyword_match"}

        if not any(c.startswith("99") for c in all_cpt):
            em_suggestion = self._suggest_em_level(note_text, encounter_type)
            if em_suggestion:
                all_cpt[em_suggestion["code"]] = {
                    "desc": em_suggestion["desc"],
                    "confidence": em_suggestion["confidence"],
                    "reasoning": em_suggestion["reasoning"],
                    "source": "em_engine",
                }

        pos = self._suggest_pos(encounter_type, note_text)
        avg_conf = 0.0
        all_codes = list(all_cpt.values()) + list(all_icd.values())
        if all_codes:
            avg_conf = sum(c.get("confidence", 0) for c in all_codes) / len(all_codes)

        return {
            "encounter_type": encounter_type,
            "cpt_codes": [
                {"code": k, **v} for k, v in sorted(all_cpt.items())
            ],
            "icd_codes": [
                {"code": k, **v} for k, v in sorted(all_icd.items())
            ],
            "place_of_service": pos,
            "total_confidence": round(avg_conf, 3),
            "notes": f"Auto-generated from clinical note ({len(note_text)} chars)",
        }

    def _detect_encounter_type(self, text: str) -> str:
        text_lower = text.lower()
        scores = {}
        for etype, keywords in ENCOUNTER_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[etype] = score
        if scores:
            return max(scores, key=scores.get)
        return "office"

    def _detect_direct_codes(self, text: str) -> Tuple[Dict, Dict]:
        cpt_pattern = r'\b(\d{5})\b'
        cpt_matches = re.findall(cpt_pattern, text)
        cpt_codes = {}
        for code in cpt_matches:
            if 10000 <= int(code) <= 99999:
                try:
                    from knowledge.cpt_book_engine import lookup_cpt
                    info = lookup_cpt(code)
                    if info:
                        cpt_codes[code] = {
                            "desc": info.get("desc", f"CPT {code}"),
                            "confidence": 0.90,
                            "reasoning": f"Directly mentioned in note text",
                        }
                except Exception:
                    cpt_codes[code] = {
                        "desc": f"CPT {code}",
                        "confidence": 0.85,
                        "reasoning": "Directly mentioned in note text",
                    }

        icd_pattern = r'\b([A-TV-Z]\d{2}(?:\.\d{1,4})?)\b'
        icd_matches = re.findall(icd_pattern, text, re.IGNORECASE)
        icd_codes = {}
        for code in icd_matches:
            code_upper = code.upper()
            try:
                from knowledge.icd_book_engine import lookup_icd
                info = lookup_icd(code_upper)
                if info:
                    icd_codes[code_upper] = {
                        "desc": info.get("desc", f"ICD {code_upper}"),
                        "confidence": 0.90,
                        "reasoning": "Directly mentioned in note text",
                    }
            except Exception:
                icd_codes[code_upper] = {
                    "desc": f"ICD {code_upper}",
                    "confidence": 0.85,
                    "reasoning": "Directly mentioned in note text",
                }

        return cpt_codes, icd_codes

    def _kw_match(self, keyword: str, text_lower: str) -> bool:
        if len(keyword) < 4:
            return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text_lower))
        return keyword in text_lower

    def _match_procedures(self, text: str) -> Dict:
        text_lower = text.lower()
        matched = {}
        sorted_procs = sorted(PROCEDURE_MAP.items(), key=lambda x: -len(x[0]))

        used_codes = set()
        for keyword, cpt_code in sorted_procs:
            if self._kw_match(keyword, text_lower) and cpt_code not in used_codes:
                try:
                    from knowledge.cpt_book_engine import lookup_cpt
                    info = lookup_cpt(cpt_code)
                    desc = info.get("desc", f"CPT {cpt_code}") if info else f"CPT {cpt_code}"
                except Exception:
                    desc = f"CPT {cpt_code}"

                matched[cpt_code] = {
                    "desc": desc,
                    "confidence": 0.85,
                    "reasoning": f"Matched keyword: \"{keyword}\"",
                }
                used_codes.add(cpt_code)

        return matched

    def _match_diagnoses(self, text: str) -> Dict:
        text_lower = text.lower()
        matched = {}
        sorted_diags = sorted(DIAGNOSIS_MAP.items(), key=lambda x: -len(x[0]))

        used_codes = set()
        for keyword, icd_code in sorted_diags:
            kw_lower = keyword.lower()
            if self._kw_match(kw_lower, text_lower) and icd_code not in used_codes:
                try:
                    from knowledge.icd_book_engine import lookup_icd
                    info = lookup_icd(icd_code)
                    desc = info.get("desc", f"ICD {icd_code}") if info else f"ICD {icd_code}"
                except Exception:
                    desc = f"ICD {icd_code}"

                matched[icd_code] = {
                    "desc": desc,
                    "confidence": 0.85,
                    "reasoning": f"Matched keyword: \"{keyword}\"",
                }
                used_codes.add(icd_code)

        return matched

    def _suggest_em_level(self, text: str, encounter_type: str = "office") -> Optional[Dict]:
        text_lower = text.lower()
        moderate_indicators = [
            "moderate mdm", "chronic illness", "multiple medications",
            "new data", "diagnostic test", "specialist referral",
            "suboptimally", "uncontrolled", "complicated",
            "multiple chronic", "comorbidities",
        ]
        high_indicators = [
            "high mdm", "life-threatening", "emergency",
            "urgent", "severe", "acute decompensation",
            "multiple problems", "complex decision",
        ]
        low_indicators = [
            "low mdm", "straightforward",
            "single chronic", "stable", "routine",
        ]

        mod_score = sum(1 for ind in moderate_indicators if ind in text_lower)
        high_score = sum(1 for ind in high_indicators if ind in text_lower)
        low_score = sum(1 for ind in low_indicators if ind in text_lower)

        if encounter_type == "emergency":
            if high_score > 0:
                return {"code": "99285", "desc": "ED visit high complexity", "confidence": 0.75, "reasoning": "ED high complexity"}
            elif mod_score > 0:
                return {"code": "99284", "desc": "ED visit moderate-high complexity", "confidence": 0.70, "reasoning": "ED moderate complexity"}
            else:
                return {"code": "99283", "desc": "ED visit moderate complexity", "confidence": 0.65, "reasoning": "ED moderate complexity"}

        if encounter_type == "inpatient":
            if high_score > 0:
                return {"code": "99223", "desc": "Hospital admission high complexity", "confidence": 0.75, "reasoning": "Inpatient high complexity"}
            elif mod_score > 0:
                return {"code": "99222", "desc": "Hospital admission moderate complexity", "confidence": 0.70, "reasoning": "Inpatient moderate complexity"}
            else:
                return {"code": "99221", "desc": "Hospital admission straightforward", "confidence": 0.65, "reasoning": "Inpatient straightforward"}

        if encounter_type == "subsequent":
            if high_score > 0:
                return {"code": "99233", "desc": "Subsequent hospital care high complexity", "confidence": 0.75, "reasoning": "Subsequent care high complexity"}
            elif mod_score > 0:
                return {"code": "99232", "desc": "Subsequent hospital care moderate complexity", "confidence": 0.70, "reasoning": "Subsequent care moderate complexity"}
            else:
                return {"code": "99231", "desc": "Subsequent hospital care straightforward", "confidence": 0.65, "reasoning": "Subsequent care straightforward"}

        if encounter_type in ("surgery", "observation"):
            if high_score > 0:
                return {"code": "99223", "desc": "Hospital admission high complexity", "confidence": 0.70, "reasoning": "Surgical/observation high complexity"}
            elif mod_score > 0:
                return {"code": "99222", "desc": "Hospital admission moderate complexity", "confidence": 0.65, "reasoning": "Surgical/observation moderate complexity"}
            else:
                return {"code": "99221", "desc": "Hospital admission straightforward", "confidence": 0.60, "reasoning": "Surgical/observation straightforward"}

        if encounter_type == "office":
            if high_score > 0:
                return {"code": "99215", "desc": "Office visit established high MDM", "confidence": 0.75, "reasoning": "High complexity indicators detected"}
            elif mod_score > 0:
                return {"code": "99214", "desc": "Office visit established moderate MDM", "confidence": 0.70, "reasoning": "Moderate complexity indicators detected"}
            else:
                return {"code": "99213", "desc": "Office visit established low MDM", "confidence": 0.65, "reasoning": "Low complexity indicators detected"}

        return {"code": "99213", "desc": "Office visit established low MDM", "confidence": 0.55, "reasoning": "Default low complexity"}

    def _suggest_pos(self, encounter_type: str, text: str) -> str:
        pos_map = {
            "office": "11", "inpatient": "21", "emergency": "23",
            "surgery": "22", "observation": "22", "home": "12",
            "nursing": "31", "telehealth": "02",
        }
        return pos_map.get(encounter_type, "11")


_parser_instance = None

def get_clinical_note_parser() -> ClinicalNoteParser:
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ClinicalNoteParser()
    return _parser_instance
