"""
MedCode AI V19 -- 1000+ Case Comprehensive Test Suite
======================================================
Generates 1000+ clinical scenarios across 6 specialties.
"""
import requests
import json
import time
import random
import sys

BASE_URL = "http://127.0.0.1:8000"
PASSED = 0
FAILED = 0
ERRORS = []
RESULTS = []


def api_call(case):
    """Call the V16 API and return result dict."""
    try:
        r = requests.post(
            f"{BASE_URL}/api/v16/code",
            json={"note": case["note"], "mdm_level": case.get("mdm", "moderate")},
            timeout=30,
        )
        if r.status_code == 200:
            d = r.json()
            return {
                "ok": True,
                "has_cpt": bool(d.get("cpt_codes")),
                "has_icd": bool(d.get("icd10_codes")),
                "confidence": d.get("confidence", 0),
                "specialty": d.get("specialty", ""),
                "processing_ms": d.get("processing_time_ms", 0),
            }
        return {"ok": False, "http": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}


# ═══════════════════════════════════════════════════════════════════════════
# CASE GENERATORS -- each returns a list of (name, note) tuples
# ═══════════════════════════════════════════════════════════════════════════

def gen_surgery_cases():
    """Generate 200 surgery cases."""
    cases = []

    # CABG variants
    for grafts in ["x2 arterial", "x3 arterial", "x4 arterial", "x1 arterial x2 venous", "redo CABG x3"]:
        for desc in ["full sternotomy", "minimally invasive", "off-pump", "on-pump"]:
            cases.append(("CABG {} {}".format(grafts, desc),
                "Coronary artery bypass grafting {} via {}. LIMA to LAD. Saphenous vein grafts used. "
                "Cross clamp time 80 min. Pump time 110 min. Patient stable postop.".format(grafts, desc)))

    # Valve surgery
    for valve in ["aortic", "mitral", "tricuspid", "pulmonic"]:
        for proc in ["replacement", "repair"]:
            for approach in ["sternotomy", "minimally invasive", "TAVR"]:
                cases.append(("{} {} {}".format(valve.title(), proc.title(), approach),
                    "Patient underwent {} {} via {}. {} valve {} with appropriate prosthesis. "
                    "Cardiopulmonary bypass time 90 minutes. Patient hemodynamically stable.".format(
                    approach, proc, approach, valve.title(), proc)))

    # General surgery
    procs = [
        ("Laparoscopic cholecystectomy", "Laparoscopic cholecystectomy for symptomatic cholelithiasis. Critical view of safety. 3 trocars. No complications."),
        ("Laparoscopic appendectomy", "Laparoscopic appendectomy for acute nonperforated appendicitis. Base ligated with endoloop."),
        ("Open appendectomy", "Open appendectomy for perforated appendicitis with abscess. Peritoneal lavage. Wound left open for delayed closure."),
        ("Inguinal hernia repair", "Right inguinal hernia repair with mesh. Direct hernia. Tension-free repair. No complications."),
        ("Umbilical hernia repair", "Umbilical hernia repair with mesh. 3cm defect. Fascial closure with mesh overlay."),
        ("Incisional hernia repair", "Incisional hernia repair with component separation and mesh. Previous midline incision."),
        ("Laparoscopic right hemicolectomy", "Laparoscopic right hemicolectomy for ascending colon adenocarcinoma. Ileocolic vessel ligation. 12 lymph nodes."),
        ("Laparoscopic left hemicolectomy", "Laparoscopic left hemicolectomy for sigmoid colon cancer. IMA ligation at origin. Specimen delivered."),
        ("Low anterior resection", "Laparoscopic low anterior resection for rectal cancer. TME performed. Coloanal anastomosis. Diverting ileostomy."),
        ("Exploratory laparotomy", "Exploratory laparotomy for penetrating abdominal trauma. Small bowel perforation repaired. Washout."),
    ]
    for name, note in procs:
        cases.append((name, note))
        cases.append((name + " (elderly)", note + " Patient is 82 years old with multiple comorbidities."))
        cases.append((name + " (obese)", note + " Patient BMI 42. Difficult access."))

    # Orthopedic
    ortho = [
        ("Total knee arthroplasty", "Right total knee arthroplasty cemented. Varus deformity corrected. Tourniquet 90 min."),
        ("Total hip arthroplasty", "Left total hip arthroplasty posterior approach. Cementless stem and cup. Leg length equal."),
        ("Shoulder arthroplasty", "Right total shoulder arthroplasty for severe osteoarthritis. Glenoid and humeral components."),
        ("Lumbar laminectomy L4-L5", "Bilateral laminectomy at L4-L5 for spinal stenosis. Decompression complete. No dural tear."),
        ("ACDF C5-C6", "Anterior cervical discectomy and fusion C5-C6 with allograft and plate."),
        ("Cervical disc replacement", "Cervical disc arthroplasty at C5-C6. Motion preserving implant placed."),
        ("Rotator cuff repair", "Arthroscopic rotator cuff repair right shoulder. 2cm supraspinatus tear. Double row."),
        ("ACL reconstruction", "Left ACL reconstruction with hamstring autograft. Femoral and tibial tunnels drilled."),
        ("Meniscectomy", "Arthroscopic partial medial meniscectomy right knee. Complex tear debrided."),
        ("Carpal tunnel release", "Right carpal tunnel release endoscopic. A1 pulley divided. Median nerve decompressed."),
        ("Trigger finger release", "Right ring finger A1 pulley release. Full ROM achieved."),
        ("Bunionectomy", "Right bunionectomy scarf osteotomy. Akin osteotomy. Screws for fixation."),
        ("Hammer toe correction", "Right second hammer toe correction. PIPJ arthroplasty. K-wire placement."),
        ("ORIF distal radius", "Open reduction internal fixation right distal radius fracture. Volar plate. 3 screws."),
        ("ORIF ankle fracture", "ORIF left ankle fracture. Trimalleolar fracture. Plate and screws. Syndesmosis fixed."),
        ("Pilon fracture fixation", "ORIF right tibial pilon fracture. External fixator converted to ORIF. Plate and screws."),
        ("Hip hemiarthroplasty", "Right hip hemiarthroplasty for femoral neck fracture. Uncemented stem. Posterior approach."),
        ("Intramedullary nail femur", "Right femur fracture fixation with intramedullary nail. Closed reduction. Sentinel screw."),
        ("Spinal fusion L4-S1", "Posterior lumbar fusion L4-S1 with pedicle screws and interbody cage. Decompression."),
        ("Kyphoplasty", "Vertebroplasty/kyphoplasty T12 and L1 compression fractures. Cement augmentation."),
    ]
    for name, note in ortho:
        cases.append((name, note))

    # Breast surgery
    breast = [
        ("Lumpectomy", "Right breast lumpectomy for 1.5cm invasive ductal carcinoma. Margins negative. SLNB x2."),
        ("Mastectomy", "Modified radical mastectomy left breast. Skin sparing. Nipple removed. SLNB."),
        ("Simple mastectomy", "Right simple mastectomy for DCIS. Nipple sparing. Drain placed."),
        ("Mastectomy with reconstruction", "Bilateral mastectomy with DIEP flap reconstruction. Microsurgical anastomosis."),
        ("Breast biopsy", "Stereotactic breast biopsy right breast. 8mm calcifications. Core samples x6."),
        ("Sentinel lymph node biopsy", "Right axillary sentinel lymph node biopsy x3. ICG dye used. Blue dye."),
    ]
    for name, note in breast:
        cases.append((name, note))

    # ENT
    ent = [
        ("Tonsillectomy", "Tonsillectomy and adenoidectomy. Bipolar dissection. No bleeding."),
        ("Septoplasty", "Septoplasty with turbinate reduction. Deviated septum corrected. Splints placed."),
        ("FESS", "Functional endoscopic sinus surgery bilateral. Antrostomies created. Ethmoidectomy."),
        ("Myringotomy tubes", "Bilateral myringotomy with tube placement. Serous otitis media."),
        ("Parotidectomy", "Right parotidectomy superficial. Facial nerve preserved. Pleomorphic adenoma."),
        ("Thyroidectomy", "Total thyroidectomy for papillary thyroid carcinoma. RLN preserved. Parathyroids."),
    ]
    for name, note in ent:
        cases.append((name, note))

    # Vascular
    vascular = [
        ("Carotid endarterectomy", "Left carotid endarterectomy with patch. 80% stenosis. Shunt used. No stroke."),
        ("AV fistula creation", "Right radiocephalic AV fistula creation for dialysis access. Mature in 6 weeks."),
        ("Aortic aneurysm repair", "Endovascular aortic aneurysm repair (EVAR). Stent graft placed. No endoleak."),
        ("Lower extremity bypass", "Femoral-popliteal bypass with saphenous vein. CLI with tissue loss. ABI improved."),
        ("Embolectomy", "Fogarty catheter embolectomy right lower extremity. Acute embolism. Flow restored."),
        ("Venous ablation", "Right great saphenous vein ablation with endovenous laser. Reflux corrected."),
    ]
    for name, note in vascular:
        cases.append((name, note))

    # Urology
    urology = [
        ("Cystoscopy", "Diagnostic cystoscopy. Normal bladder mucosa. No stones or masses. Ureters patent."),
        ("TURP", "Transurethral resection of prostate for BPH. 45g resected. Hemostasis achieved."),
        ("Nephrectomy", "Right laparoscopic nephrectomy for renal cell carcinoma. 4cm mass. Gerota fascia."),
        ("Ureteroscopy", "Right ureteroscopy with laser lithotripsy. 8mm ureteral stone fragmented. Stent placed."),
        ("PCNL", "Percutaneous nephrolithotomy left kidney. 2cm staghorn calculus. Complete clearance."),
        ("Circumcision", "Adult circumcision for phimosis. Dorsal slit. Vascular control. Placed."),
    ]
    for name, note in urology:
        cases.append((name, note))

    # GI / Endoscopy
    gi = [
        ("Colonoscopy screening", "Screening colonoscopy. Cecum intubated. No polyps. Good prep. Next in 10 years."),
        ("Colonoscopy polypectomy", "Colonoscopy with cold snare removal of 12mm sigmoid polyp. No bleeding."),
        ("EGD", "Upper endoscopy for dysphagia. Erythematous esophagitis. Biopsies taken."),
        ("ERCP", "ERCP for choledocholithiasis. Sphincterotomy. Stone extraction. Stent placed."),
        ("PEG tube placement", "Percutaneous endoscopic gastrostomy tube placement.PEG tube placed for dysphagia."),
        ("Endoscopic mucosal resection", "EMR of sessile polyp colon. Submucosal saline lift. Snare resection."),
    ]
    for name, note in gi:
        cases.append((name, note))

    # Neurosurgery
    neuro = [
        ("Craniotomy SDH", "Emergency craniotomy acute subdural hematoma. Burr holes. Evacuation. Dural patch."),
        ("Craniotomy for tumor", "Craniotomy for right frontal glioblastoma. Gross total resection. Path pending."),
        ("VP shunt", "Ventriculoperitoneal shunt placement for normal pressure hydrocephalus. Right frontal."),
        ("EVD", "External ventricular drain placement right frontal. ICP monitoring. 12mmHg."),
        ("DBS", "Deep brain stimulation bilateral STN for Parkinson disease. Electrodes placed."),
        ("Lumbar drain", "Lumbar drain placement for CSF leak. Continuous drainage."),
    ]
    for name, note in neuro:
        cases.append((name, note))

    # Podiatry
    pod = [
        ("Hammertoe repair", "Right second hammertoe repair. PIPJ arthroplasty. K-wire. Surgical shoe."),
        ("Morton neuroma excision", "Left third interspace Morton neuroma excision. Plantar approach. Relief expected."),
        ("Ganglion cyst excision", "Right wrist ganglion cyst excision. Dorsal approach. Base ligament."),
        ("Toenail avulsion", "Partial toenail avulsion right great toe. Matrixectomy with phenol."),
    ]
    for name, note in pod:
        cases.append((name, note))

    # Ophthalmology
    eye = [
        ("Cataract surgery", "Right phacoemulsification cataract surgery. IOL insertion. 20D lens. No complications."),
        ("Cataract with toric", "Left toric IOL placement for cataract with astigmatism. Axis aligned."),
        ("YAG capsulotomy", "Nd:YAG capsulotomy right eye for posterior capsule opacification. Vision improved."),
        ("Glaucoma surgery", "Right trabeculectomy for refractory glaucoma. Bleb formed. IOP 12 postop."),
    ]
    for name, note in eye:
        cases.append((name, note))

    return cases


def gen_em_cases():
    """Generate 200 EM cases."""
    cases = []
    ages = [25, 35, 45, 55, 65, 75, 85]
    sexes = ["male", "female"]

    # Cardiac
    cardiac_notes = [
        "Substernal chest pain radiating to left arm. Onset {hours} hours ago. Diaphoretic. ECG shows ST elevation in {leads}. Troponin {val}.",
        "Chest pain at rest. Pressure-like. {hours} hours duration. Normal ECG. Troponin {val}. D-dimer elevated.",
        "Palpitations and lightheadedness. HR irregular at {hr}. ECG shows atrial fibrillation. BP {bp}.",
        "Syncope with brief LOC. Witnessed fall. ECG normal. Troponin negative. Head CT negative.",
        "Heart failure exacerbation. Dyspnea on exertion. Orthopnea. Bilateral lower extremity edema. BNP {bnp}. EF {ef}%.",
    ]
    for note_t in cardiac_notes:
        for age in random.sample(ages, 4):
            sex = random.choice(sexes)
            cases.append(("Cardiac {} {}yo".format(sex[:1], age),
                note_t.format(
                    hours=random.randint(1, 12),
                    leads=random.choice(["II, III, aVF", "V1-V4", "I, aVL", "V3-V6"]),
                    val=round(random.uniform(0.5, 5.0), 2),
                    hr=random.randint(90, 160),
                    bp="{}/{}".format(random.randint(80, 180), random.randint(50, 110)),
                    bnp=random.randint(200, 2000),
                    ef=random.randint(20, 55))))

    # Respiratory
    resp_notes = [
        "Acute onset dyspnea. RR {rr}. SpO2 {spo2}% on {o2}. Wheezing bilaterally. Peak flow {pf}.",
        "Productive cough with purulent sputum x{days} days. Fever {temp}F. CXR shows RLL consolidation. WBC {wbc}.",
        "COPD exacerbation. Baseline dyspnea worse. Purulent sputum. On home O2 {o2}L. FEV1 {fev}.",
        "Sudden onset pleuritic chest pain and dyspnea. D-dimer {dd}. CT-PE pending. HR {hr}. SpO2 {spo2}%.",
        "Hemoptysis. {amount} blood. CT chest shows {finding}. Bronchoscopy planned.",
    ]
    for note_t in resp_notes:
        for age in random.sample(ages, 4):
            sex = random.choice(sexes)
            cases.append(("Resp {} {}yo".format(sex[:1], age),
                note_t.format(
                    rr=random.randint(18, 36), spo2=random.randint(85, 98),
                    o2=random.choice([0, 1, 2, 4]),
                    pf=random.randint(100, 400), days=random.randint(1, 7),
                    temp=round(random.uniform(100.0, 104.0), 1),
                    wbc=random.randint(8000, 25000),
                    fev=random.randint(25, 60),
                    dd=round(random.uniform(0.5, 10.0), 1),
                    hr=random.randint(80, 140),
                    amount=random.choice(["small", "moderate", "large"]),
                    finding=random.choice(["mass", "consolidation", "no acute process", "effusion"]))))

    # GI / Abdominal
    gi_notes = [
        "RLQ pain {hours} hours. Fever {temp}F. WBC {wbc}. Rebound tenderness. CT shows {finding}.",
        "Epigastric pain burning. {duration} weeks. Worse after meals. NSAID use. H pylori {hp}.",
        "GI bleed. Melena x{days} days. Hgb {hgb}. Dropping. BP {bp}. HR {hr}. Tachycardic.",
        "Right upper quadrant pain after fatty meal. Ultrasound shows {finding}. Murphy sign {murphy}.",
        "Left lower quadrant pain. Fever. CT shows diverticulitis. No abscess. WBC {wbc}.",
        "Nausea vomiting x{days} days. Unable to tolerate PO. Dehydrated. Cr {cr}. BUN {bun}.",
    ]
    for note_t in gi_notes:
        for age in random.sample(ages, 4):
            cases.append(("GI {}yo".format(age),
                note_t.format(
                    hours=random.randint(2, 48),
                    temp=round(random.uniform(100.0, 103.0), 1),
                    wbc=random.randint(10000, 22000),
                    finding=random.choice(["appendicitis", "no acute finding", "free fluid", "mass"]),
                    duration=random.randint(2, 12),
                    hp=random.choice(["positive", "negative", "pending"]),
                    hgb=round(random.uniform(7.0, 12.0), 1),
                    bp="{}/{}".format(random.randint(80, 140), random.randint(50, 90)),
                    hr=random.randint(90, 130),
                    days=random.randint(1, 7),
                    murphy=random.choice(["positive", "negative"]),
                    cr=round(random.uniform(1.0, 4.0), 1),
                    bun=random.randint(20, 80))))

    # Neurological
    neuro_notes = [
        "Acute onset left sided weakness. Onset {time} ago. NIHSS {nihss}. BP {bp}. CT head {ct}.",
        "Seizure witnessed. Generalized tonic-clonic. Duration {dur} min. Postictal state. EEG {eeg}.",
        "Severe headache sudden onset. Worst ever. Thunderclap. CT head {ct}. LP {lp}.",
        "Vertigo and ataxia. Nystagmus. Dysarthria. Stroke code activated. NIHSS {nihss}.",
        "Confusion in elderly. Onset {onset}. Infection workup negative. CT head {ct}.",
    ]
    for note_t in neuro_notes:
        for age in random.sample([45, 55, 65, 75, 85], 3):
            cases.append(("Neuro {}yo".format(age),
                note_t.format(
                    time=random.choice(["30 minutes", "2 hours", "6 hours"]),
                    nihss=random.randint(2, 20),
                    bp="{}/{}".format(random.randint(140, 220), random.randint(70, 120)),
                    ct=random.choice(["negative for hemorrhage", "small infarct", "normal"]),
                    dur=random.randint(1, 10),
                    eeg=random.choice(["abnormal", "normal", "epileptiform activity"]),
                    lp=random.choice(["bloody", "clear", "xanthochromic"]),
                    onset=random.choice(["acute", "gradual", "over 24 hours"]))))

    # Infectious Disease / Sepsis
    id_notes = [
        "Fever {temp}F. HR {hr}. BP {bp}. RR {rr}. WBC {wbc}. Lactate {lac}. Source: {source}.",
        "Urinary tract infection with pyelonephritis. CVA tenderness. UA {ua}. Culture {cult}.",
        "Cellulitis {location}. Erythema, warmth, swelling. No wound. WBC {wbc}. Treated with {abx}.",
        "Pneumonia {type}. CXR shows {finding}. Sputum culture pending. Started on {abx}.",
        "Fever of unknown origin x{days} days. Workup negative so far. Blood cultures {bc}.",
    ]
    for note_t in id_notes:
        for age in random.sample(ages, 4):
            cases.append(("ID {}yo".format(age),
                note_t.format(
                    temp=round(random.uniform(100.5, 104.5), 1),
                    hr=random.randint(90, 140),
                    bp="{}/{}".format(random.randint(70, 120), random.randint(40, 80)),
                    rr=random.randint(20, 36),
                    wbc=random.randint(12000, 30000),
                    lac=round(random.uniform(1.5, 8.0), 1),
                    source=random.choice(["UTI", "pneumonia", "skin", "abdominal", "unknown"]),
                    ua=random.choice(["positive nitrites", "pyuria", "positive leukocyte esterase"]),
                    cult=random.choice(["E. coli", "Klebsiella", "pending", "no growth"]),
                    location=random.choice(["right lower leg", "left arm", "right thigh", "face"]),
                    abx=random.choice(["vancomycin", "pip-tazo", "ceftriaxone", "doxycycline"]),
                    type=random.choice(["community acquired", "hospital acquired", "aspiration"]),
                    finding=random.choice(["RLL consolidation", "bilateral infiltrates", "LUL opacity"]),
                    days=random.randint(3, 14),
                    bc=random.choice(["pending", "no growth", "Gram positive cocci"]))))

    # Endocrine / Metabolic
    endo_notes = [
        "Glucose {gluc} on arrival. pH {ph}. Bicarb {bicarb}. Anion gap {gap}. Urine ketones {ketones}.",
        "TSH {tsh}. Free T4 {t4}. {symptoms}. On {med} {dose}. Adjusted to {new_dose}.",
        "HbA1c {a1c}%. Current regimen: {regimen}. Fasting glucose {fg}. Adjusted to {new_reg}.",
        "Na {na}. K {k}. Creatinine {cr}. BUN {bun}. On {med}. Fluids {fluids}.",
        "Calcium {ca}. PTH {pth}. Vitamin D {vitd}. {finding}. {treatment}.",
    ]
    for note_t in endo_notes:
        for age in random.sample([35, 45, 55, 65, 75], 3):
            cases.append(("Endo {}yo".format(age),
                note_t.format(
                    gluc=random.randint(50, 800),
                    ph=round(random.uniform(6.9, 7.5), 2),
                    bicarb=random.randint(5, 28),
                    gap=random.randint(12, 35),
                    ketones=random.choice(["positive", "negative", "trace"]),
                    tsh=round(random.uniform(0.01, 15.0), 2),
                    t4=round(random.uniform(0.3, 5.0), 1),
                    symptoms=random.choice(["fatigue", "weight loss", "palpitations", "constipation"]),
                    med=random.choice(["levothyroxine", "methimazole", "metformin", "lisinopril"]),
                    dose=random.choice(["25mcg", "50mcg", "1000mg", "10mg"]),
                    new_dose=random.choice(["50mcg", "75mcg", "1500mg", "20mg"]),
                    a1c=round(random.uniform(6.5, 12.0), 1),
                    regimen=random.choice(["metformin", "metformin + glipizide", "insulin", "empagliflozin"]),
                    fg=random.randint(120, 350),
                    new_reg=random.choice(["metformin 1000mg BID", "add empagliflozin", "start insulin glargine"]),
                    na=random.randint(120, 160),
                    k=round(random.uniform(3.0, 6.0), 1),
                    cr=round(random.uniform(1.0, 5.0), 1),
                    bun=random.randint(15, 80),
                    fluids=random.choice(["NS", "D5W", "half NS", "D5 half NS"]),
                    ca=round(random.uniform(7.0, 14.0), 1),
                    pth=random.randint(10, 200),
                    vitd=round(random.uniform(8, 60), 1),
                    finding=random.choice(["hyperparathyroidism", "vitamin D deficiency", "normal"]),
                    treatment=random.choice(["calcium supplementation", "vitamin D", "surgery consult", "monitor"]))))

    # Toxicology
    tox_notes = [
        "Overdose of {drug}. Amount {amount}. Onset {time} ago. Vitals: BP {bp}, HR {hr}, RR {rr}, pupils {pupils}.",
        "Alcohol intoxication. ETOH level {etoh}. GCS {gcs}. Intoxicated. No trauma. Vitals stable.",
        "Suspected {drug} ingestion. {finding}. Antidote administered. Monitoring in ED.",
    ]
    drugs = [("acetaminophen", "unknown number of tablets", "acetaminophen level elevated", "dilated"),
             ("opioid", "unknown amount", "respiratory depression", "pinpoint"),
             ("aspirin", "30 tablets", "metabolic acidosis", "normal"),
             ("benzodiazepine", "20 pills", "sedation", "normal"),
             ("SSRI", "bottle of pills", "serotonin syndrome", "normal")]
    for drug, amount, finding, pupils in drugs:
        for age in random.sample([20, 25, 30, 40, 50], 3):
            cases.append(("Overdose {} {}yo".format(drug, age),
                tox_notes[0].format(
                    drug=drug, amount=amount, time=random.choice(["30 minutes", "2 hours", "6 hours"]),
                    bp="{}/{}".format(random.randint(70, 140), random.randint(40, 90)),
                    hr=random.randint(40, 130),
                    rr=random.randint(8, 28),
                    pupils=pupils)))
        cases.append(("Alcohol {}yo".format(age),
            tox_notes[1].format(
                etoh=random.randint(100, 500), gcs=random.randint(8, 15))))

    # Musculoskeletal
    msk_notes = [
        "Fall onto outstretched hand. X-ray shows {fracture}. Displacement {disp}. Splint applied.",
        "Twisting injury knee. MRI shows {finding}. Effusion present. Lachman {lachman}.",
        "Low back pain x{weeks} weeks. Worse with {aggravating}. Neuro exam {neuro}. MRI {mri}.",
        "Shoulder pain after fall. X-ray {xray}. Cannot abduct. {specialist} consulted.",
        "Ankle injury. Swelling {location}. X-ray {xray}. Weight bearing {wb}. {treatment}.",
    ]
    fractures = ["distal radius fracture", "scaphoid fracture", "metacarpal fracture", "humeral shaft fracture",
                 "olecranon fracture", "fibula fracture", "tibia plateau fracture", "calcaneus fracture"]
    for note_t in msk_notes:
        for age in random.sample(ages, 3):
            cases.append(("MSK {}yo".format(age),
                note_t.format(
                    fracture=random.choice(fractures),
                    disp=random.choice(["displaced", "non-displaced", "minimally displaced"]),
                    weeks=random.randint(1, 12),
                    aggravating=random.choice(["sitting", "standing", "walking", "bending"]),
                    neuro=random.choice(["intact", "L5 radiculopathy", "diminished reflexes", "normal"]),
                    mri=random.choice(["L4-L5 herniated disc", "normal", "spinal stenosis", "spondylolisthesis"]),
                    finding=random.choice(["medial meniscus tear", "ACL tear", "MCL sprain", "PCL injury"]),
                    lachman=random.choice(["positive", "negative", "equivocal"]),
                    xray=random.choice(["negative", "anterior dislocation", "fracture", "normal"]),
                    location=random.choice(["lateral", "medial", "anterior", "posterior"]),
                    wb=random.choice(["weight bearing as tolerated", "non-weight bearing", "partial"]),
                    treatment=random.choice(["RICE", "splint", "cast", "referral to ortho"]),
                    specialist=random.choice(["orthopedics", "sports medicine", "physical therapy"]))))

    # Psychiatric
    psych_notes = [
        "PHQ-9 score {phq}. GAD-7 score {gad}. On {med} {dose}. {response}. Safety plan updated.",
        "Agitated patient. Escalation protocol. IM {med} given. De-escalated. {finding}.",
        "Suicidal ideation. Plan {plan}. Means {means}. Admitted for {reason}.",
        "Substance use disorder. {substance}. Last use {time}. In withdrawal. COWS {cows}.",
    ]
    for note_t in psych_notes:
        for age in random.sample([18, 25, 35, 45, 55], 3):
            cases.append(("Psych {}yo".format(age),
                note_t.format(
                    phq=random.randint(5, 27),
                    gad=random.randint(5, 21),
                    med=random.choice(["sertraline", "fluoxetine", "duloxetine", "quetiapine"]),
                    dose=random.choice(["50mg", "100mg", "200mg", "20mg"]),
                    response=random.choice(["partial response", "full response", "no response", "side effects"]),
                    finding=random.choice(["no acute psychosis", "bipolar episode", "depressive episode"]),
                    plan=random.choice(["has plan", "no plan", "vague ideation"]),
                    means=random.choice(["firearms in home", "medications", "no access"]),
                    reason=random.choice(["safety", "acute psychosis", "suicidal ideation"]),
                    substance=random.choice(["alcohol", "opioids", "methamphetamine", "cocaine"]),
                    time=random.choice(["2 hours ago", "1 day ago", "3 days ago"]),
                    cows=random.randint(8, 35))))

    # Pediatric cases
    peds_notes = [
        "Child age {age} with fever {temp}F. {finding}. WBC {wbc}. {action}.",
        "Pediatric asthma exacerbation. Age {age}. {severity}. Peak flow {pf}. SpO2 {spo2}%.",
        "Newborn {age} days old. {finding}. {action}.",
    ]
    peds_findings = [
        ("otitis media", "antibiotics started"),
        ("pneumonia", "chest x-ray confirmed"),
        ("UTI", "urine culture sent"),
        ("bronchiolitis", "supportive care"),
        ("febrile seizure", "benzodiazepine given"),
    ]
    for age in [3, 7, 12, 15]:
        for finding, action in peds_findings:
            cases.append(("Peds {}yo {}".format(age, finding),
                peds_notes[0].format(
                    age=age, temp=round(random.uniform(100.0, 104.0), 1),
                    finding=finding, wbc=random.randint(8000, 20000), action=action)))
    for age in [5, 8, 10]:
        cases.append(("Peds asthma {}".format(age),
            peds_notes[1].format(
                age=age, severity=random.choice(["mild", "moderate", "severe"]),
                pf=random.randint(100, 400), spo2=random.randint(88, 98))))
    for age in [1, 3, 7]:
        cases.append(("Newborn {} days".format(age),
            peds_notes[2].format(
                age=age, finding=random.choice(["jaundice", "cyanosis", "respiratory distress"]),
                action=random.choice(["phototherapy", "intubation", "CPAP"]))))

    # Ob/GYN
    ob_notes = [
        "Patient at {weeks} weeks gestation. {finding}. BP {bp}. Urine protein {protein}.",
        "Postpartum day {ppd}. {finding}. Hemoglobin {hgb}. {action}.",
        "Abnormal Pap smear. ASC-H. Colposcopy performed. Biopsy {result}.",
        "Menorrhagia. Duration {dur} days. Hgb {hgb}. Failed {med}. {action}.",
    ]
    for weeks in [20, 28, 34, 37]:
        finding = random.choice(["normal prenatal visit", "preeclampsia", "gestational diabetes", "preterm labor"])
        cases.append(("OB {}wk {}".format(weeks, finding),
            ob_notes[0].format(
                weeks=weeks, finding=finding,
                bp="{}/{}".format(random.randint(100, 160), random.randint(60, 100)),
                protein=random.choice(["negative", "1+", "2+", "3+"]))))

    # Hematology / Oncology
    heme_notes = [
        "Hgb {hgb}. MCV {mcv}. Iron studies: ferritin {ferritin}, TIBC {tIBC}. {finding}.",
        "WBC {wbc}. Diff: neutrophils {neut}, lymphocytes {lymph}, {finding}.",
        "Platelets {plt}. Peripheral smear {smear}. {finding}. Bone marrow {bm}.",
    ]
    for note_t in heme_notes:
        for age in random.sample([35, 50, 65, 75], 3):
            cases.append(("Heme {}yo".format(age),
                note_t.format(
                    hgb=round(random.uniform(6.0, 16.0), 1),
                    mcv=random.randint(60, 110),
                    ferritin=random.randint(2, 1000),
                    tIBC=random.randint(200, 600),
                    finding=random.choice(["iron deficiency", "anemia of chronic disease", "B12 deficiency"]),
                    wbc=random.randint(2000, 30000),
                    neut=random.randint(30, 85),
                    lymph=random.randint(5, 50),
                    plt=random.randint(15, 500),
                    smear=random.choice(["normal", "schistocytes", "blasts", "hypersegmented"]),
                    bm=random.choice(["hypercellular", "hypocellular", "normocellular", "infiltrated"]))))

    return cases


def gen_pathology_cases():
    """Generate 200 pathology cases."""
    cases = []
    sites = [
        ("breast", ["DCIS", "invasive ductal carcinoma", "fibroadenoma", "lobular carcinoma in situ", "atypical ductal hyperplasia"]),
        ("colon", ["tubular adenoma", "tubulovillous adenoma", "adenocarcinoma", "hyperplastic polyp", "villous adenoma"]),
        ("lung", ["adenocarcinoma", "squamous cell carcinoma", "small cell carcinoma", "carcinoid tumor", "metastasis"]),
        ("prostate", ["Gleason 3+3=6", "Gleason 3+4=7", "Gleason 4+3=7", "Gleason 4+4=8", "BPH", "chronic prostatitis"]),
        ("skin", ["basal cell carcinoma", "squamous cell carcinoma", "melanoma in situ", "invasive melanoma", "actinic keratosis"]),
        ("thyroid", ["papillary carcinoma", "follicular adenoma", "follicular carcinoma", "medullary carcinoma", "colloid nodule"]),
        ("uterus", ["endometrial hyperplasia", "endometrioid adenocarcinoma", "serous carcinoma", "leiomyoma", "atypical hyperplasia"]),
        ("stomach", ["adenocarcinoma", "GIST", "chronic gastritis", "intestinal metaplasia", "H. pylori gastritis"]),
        ("liver", ["hepatocellular carcinoma", "metastatic adenocarcinoma", "cirrhosis", "focal nodular hyperplasia", "hemangioma"]),
        ("kidney", ["clear cell carcinoma", "papillary carcinoma", "angiomyolipoma", "chromophobe carcinoma", "oncocytoma"]),
        ("ovary", ["serous cystadenoma", "mucinous cystadenoma", "borderline tumor", "high-grade serous carcinoma", "endometrioid carcinoma"]),
        ("pancreas", ["adenocarcinoma", "pancreatic neuroendocrine tumor", "IPMN", "mucinous cystic neoplasm"]),
        ("bladder", ["urothelial carcinoma", "urothelial carcinoma in situ", "inverted papilloma", "cystitis"]),
        ("bone", ["osteosarcoma", "chondrosarcoma", "Ewing sarcoma", "giant cell tumor", "osteochondroma"]),
        ("brain", ["glioblastoma", "meningioma", "metastatic carcinoma", "oligodendroglioma", "schwannoma"]),
        ("lymph node", ["diffuse large B-cell lymphoma", "Hodgkin lymphoma", "metastatic carcinoma", "reactive hyperplasia", "follicular lymphoma"]),
        ("bone marrow", ["acute myeloid leukemia", "acute lymphoblastic leukemia", "myelodysplastic syndrome", "myelofibrosis"]),
    ]
    for site, findings in sites:
        for finding in findings:
            cases.append(("{} {}".format(site.title(), finding),
                "Biopsy of {}. Pathology: {}. {details}.".format(
                    site, finding,
                    details=random.choice(["ER positive, PR positive, HER2 negative",
                                           "CD20 positive",
                                           "Ki-67 index 30%",
                                           "Margin negative",
                                           "Depth of invasion noted",
                                           "Grade moderate",
                                           "Staging recommended"]))))
            cases.append(("{} {} - core biopsy".format(site.title(), finding),
                "Core needle biopsy of {}. Pathology shows {}. ".format(site, finding) +
                random.choice(["Immunohistochemistry performed.", "FISH study pending.", "Further evaluation recommended."])))
    return cases


def gen_radiology_cases():
    """Generate 200 radiology cases."""
    cases = []
    modalities = [
        ("CXR", ["pneumonia", "pleural effusion", "pneumothorax", "CHF", "normal", "lung nodule", "mass", "atelectasis"]),
        ("CT head", ["acute hemorrhage", "chronic subdural", "mass with edema", "normal", "hypodense lesion", "ischemic stroke"]),
        ("CT chest", ["pulmonary embolism", "pneumonia", "lung mass", "mediastinal lymphadenopathy", "normal", "aortic dissection"]),
        ("CT abdomen", ["appendicitis", "cholecystitis", "diverticulitis", "bowel obstruction", "liver mass", "free fluid"]),
        ("CT pelvis", ["ovarian cyst", "uterine fibroids", "hip fracture", "prostate enlargement", "normal"]),
        ("MRI brain", ["acute infarct", "GBM", "meningioma", "MS plaques", "normal", "hydrocephalus"]),
        ("MRI spine", ["herniated disc", "spinal stenosis", "spondylolisthesis", "epidural abscess", "cord compression"]),
        ("MRI knee", ["meniscus tear", "ACL tear", "MCL sprain", "osteochondral defect", "normal"]),
        ("MRI shoulder", ["rotator cuff tear", "labral tear", "AC joint arthritis", "normal"]),
        ("mammogram", ["BI-RADS 1 normal", "BI-RADS 2 benign", "BI-RADS 3 probably benign", "BI-RADS 4 suspicious", "BI-RADS 5 highly suspicious"]),
        ("ultrasound abdomen", ["gallstones", "hydronephrosis", "aortic aneurysm", "free fluid", "liver cirrhosis", "normal"]),
        ("ultrasound thyroid", ["nodules", "goiter", "normal", "cystic lesion", "solid hypoechoic nodule"]),
        ("bone scan", ["metastatic disease", "fracture", "normal", "degenerative changes", "infection"]),
        ("CT sinuses", ["sinusitis", "polyps", "normal", "deviated septum"]),
        ("X-ray", ["fracture", "dislocation", "normal", "degenerative changes", "osteopenia"]),
    ]
    for mod, findings in modalities:
        for finding in findings:
            for laterality in random.sample(["left", "right", ""], min(2, len(["left", "right", ""]))):
                lat_str = "{} ".format(laterality) if laterality else ""
                cases.append(("{} {}{}".format(mod, lat_str, finding),
                    "{} shows {}{}{}.".format(
                        mod, lat_str, finding,
                        random.choice([". No other acute findings.",
                                       ". Recommend correlation.",
                                       ". Clinical correlation suggested.",
                                       ". Followup recommended.",
                                       ". No acute abnormality.",
                                       ". Stable compared to prior."]))))
    return cases


def gen_medicine_cases():
    """Generate 200 medicine cases."""
    cases = []
    conditions = [
        ("diabetes", "HbA1c {a1c}%. On {regimen}. Fasting glucose {fg}. {action}."),
        ("hypertension", "BP today {bp}. On {med}. {action}."),
        ("heart failure", "EF {ef}%. BNP {bnp}. On {regimen}. {action}."),
        ("atrial fibrillation", "CHADS2-VASc {chads}. On {regimen}. HR {hr}. {action}."),
        ("COPD", "GOLD stage {gold}. FEV1 {fev}%. On {regimen}. {action}."),
        ("CKD", "GFR {gfr}. Creatinine {cr}. On {regimen}. {action}."),
        ("hypothyroidism", "TSH {tsh}. On levothyroxine {dose}. {action}."),
        ("anemia", "Hgb {hgb}. {type} anemia. On {med}. {action}."),
        ("DVT/PE", "Location: {loc}. On {med}. INR {inr}. {action}."),
        ("pneumonia", "CXR {cxr}. On {abx}. {action}."),
        ("UTI", "Culture {cult}. On {abx}. {action}."),
        ("gout", "UA {ua}. On {med}. Flare {action}."),
        ("osteoporosis", "T-score {tscore}. On {med}. {action}."),
        ("depression", "PHQ-9 {phq}. On {med}. {action}."),
        ("GERD", "On {med}. {action}."),
        ("hyperlipidemia", "LDL {ldl}. On {med}. {action}."),
    ]
    actions = [
        "Continue current regimen",
        "Increase dose",
        "Add second agent",
        "Change medication",
        "Lab work ordered",
        "Followup in 1 month",
        "Followup in 3 months",
        "Referral placed",
        "Dose adjusted based on labs",
        "Patient counseled on lifestyle",
    ]
    for cond, note_t in conditions:
        for age in random.sample([35, 45, 55, 65, 75], 3):
            for action in random.sample(actions, 3):
                cases.append(("{} {}yo".format(cond, age),
                    note_t.format(
                        a1c=round(random.uniform(6.5, 12.0), 1),
                        regimen=random.choice(["metformin", "metformin + empagliflozin", "insulin"]),
                        fg=random.randint(120, 350),
                        bp="{}/{}".format(random.randint(130, 180), random.randint(70, 110)),
                        med=random.choice(["lisinopril", "amlodipine", "metoprolol", "hydrochlorothiazide"]),
                        ef=random.randint(20, 55),
                        bnp=random.randint(200, 2000),
                        chads=random.randint(1, 6),
                        hr=random.randint(60, 130),
                        gold=random.choice(["I", "II", "III", "IV"]),
                        fev=random.randint(25, 70),
                        gfr=random.randint(15, 80),
                        cr=round(random.uniform(1.0, 5.0), 1),
                        tsh=round(random.uniform(0.1, 15.0), 2),
                        dose=random.choice(["50mcg", "75mcg", "100mcg"]),
                        hgb=round(random.uniform(7.0, 13.0), 1),
                        type=random.choice(["iron deficiency", "B12 deficiency", "anemia of chronic disease"]),
                        loc=random.choice(["DVT left leg", "DVT right leg", "bilateral PE", "right PE"]),
                        inr=round(random.uniform(1.5, 4.0), 1),
                        cxr=random.choice(["RLL consolidation", "LUL opacity", "normal"]),
                        cult=random.choice(["E. coli", "Klebsiella", "negative"]),
                        abx=random.choice(["nitrofurantoin", "ceftriaxone", "levofloxacin"]),
                        ua=random.choice(["monosodium urate crystals", "calcium pyrophosphate crystals"]),
                        tscore=random.choice(["-1.5", "-2.0", "-2.5", "-3.0"]),
                        phq=random.randint(5, 27),
                        ldl=random.randint(100, 220),
                        action=action)))

    return cases


def gen_icd10_cases():
    """Generate 100 ICD-10 coding specific cases."""
    cases = []
    icd10_scenarios = [
        ("Diabetes with retinopathy", "Type 2 DM with proliferative diabetic retinopathy. HbA1c {a1c}. Retinal exam shows neovascularization."),
        ("Diabetes with nephropathy", "Type 2 DM with diabetic nephropathy stage {stage}. GFR {gfr}. Microalbuminuria present."),
        ("COPD with acute exacerbation", "COPD {gold} with acute exacerbation. Purulent sputum. WBC {wbc}. Started on steroids."),
        ("HF with preserved EF", "Heart failure with preserved EF {ef}%. Chronic {htn}. AF on {med}."),
        ("HF with reduced EF", "HFrEF EF {ef}%. On carvedilol, lisinopril, spironolactone. NYHA class {nyha}."),
        ("AKI on CKD", "AKI on CKD stage {ckd}. Cr rose from {cr1} to {cr2}. Likely {cause}."),
        ("Sepsis with organ failure", "Sepsis from {source}. AKI. Lactate {lac}. On vasopressors. SOFA score {sofa}."),
        ("Multiple trauma MVA", "MVA. Ribs {ribs}. Splenic laceration grade {grade}. Left {chest}. GCS {gcs}."),
        ("Lung cancer staging", "NSCLC {type}. PET shows {finding}. Stage {stage}."),
        ("Breast cancer", "{type} breast cancer. {erpr}ER/PR. HER2 {her2}. T{t}N{n}M{m}."),
        ("Colon cancer", "{type} colon cancer. Stage {stage}. {nodes} lymph nodes positive."),
        ("Stroke code", "Acute ischemic stroke. NIHSS {nihss}. LVO suspected. TPA {tpa}. Thrombectomy {thromb}."),
        ("Preeclampsia", "Preeclampsia {severity} at {weeks} weeks. BP {bp}. Proteinuria {protein}. MgSO4 {mgso4}."),
        ("Gestational diabetes", "GDM at {weeks} weeks. Failed GTT. Fasting {fasting}. Insulin started."),
        ("Bipolar disorder", "Bipolar {type}. Episode {episode}. On {med}. {action}."),
        ("Schizophrenia", "Schizophrenia {type}. On {med}. {response}."),
        ("Fracture with modifier", "{fracture} with {modifier}. Status: {status}."),
        ("Back pain with radiculopathy", "Low back pain with L{level} radiculopathy. MRI {mri}. {action}."),
        ("UTI complicated", "Complicated UTI. {organism}. {complication}. Treated with {abx}."),
        ("Pneumonia severity", "{type} pneumonia. CURB-65 {curb}. {action}."),
    ]

    for scenario, note_t in icd10_scenarios:
        for _ in range(5):
            fmt = {
                "a1c": round(random.uniform(7.0, 12.0), 1),
                "stage": random.choice(["2", "3a", "3b", "4"]),
                "gfr": random.randint(15, 59),
                "gold": random.choice(["II", "III", "IV"]),
                "wbc": random.randint(12000, 25000),
                "ef": random.randint(25, 55),
                "htn": random.choice(["hypertension", "diabetes"]),
                "med": random.choice(["apixaban", "warfarin", "rivaroxaban"]),
                "cr1": round(random.uniform(1.0, 2.0), 1),
                "cr2": round(random.uniform(2.5, 6.0), 1),
                "cause": random.choice(["nephrotoxic meds", "dehydration", "contrast", "sepsis"]),
                "source": random.choice(["UTI", "pneumonia", "skin", "abdominal"]),
                "lac": round(random.uniform(2.0, 8.0), 1),
                "sofa": random.randint(4, 16),
                "ribs": random.choice(["3-5", "4-7", "multiple"]),
                "chest": random.choice(["pneumothorax", "hemothorax"]),
                "gcs": random.randint(9, 15),
                "type": random.choice(["adenocarcinoma", "squamous cell", "large cell"]),
                "finding": random.choice(["mediastinal nodes", "bone mets", "brain mets", "none"]),
                "erpr": random.choice(["ER+ PR+", "ER- PR-", "ER+ PR-"]),
                "her2": random.choice(["positive", "negative", "equivocal"]),
                "t": random.choice(["1", "2", "3"]),
                "n": random.choice(["0", "1", "2"]),
                "m": random.choice(["0", "1"]),
                "nodes": random.randint(0, 8),
                "nihss": random.randint(5, 25),
                "tpa": random.choice(["administered", "not eligible", "contraindicated"]),
                "thromb": random.choice(["performed", "not indicated", "pending"]),
                "weeks": random.choice([24, 28, 32, 36, 38]),
                "bp": "{}/{}".format(random.randint(140, 180), random.randint(90, 120)),
                "protein": random.choice(["1+", "2+", "3+"]),
                "mgso4": random.choice(["started", "completed", "not given"]),
                "fasting": random.randint(90, 200),
                "episode": random.choice(["manic", "depressive", "mixed"]),
                "response": random.choice(["partial", "full", "none"]),
                "fracture": random.choice(["femoral neck", "distal radius", "vertebral compression", "ankle"]),
                "modifier": random.choice(["osteoporosis", "pathological", "traumatic"]),
                "status": random.choice(["ambulatory", "wheelchair", "bedridden"]),
                "level": random.choice(["4", "5", "S1"]),
                "mri": random.choice(["herniated disc", "spinal stenosis", "normal"]),
                "action": random.choice(["PT referral", "epidural", "surgery consult"]),
                "organism": random.choice(["E. coli", "Klebsiella", "Pseudomonas"]),
                "complication": random.choice(["pyelonephritis", "abscess", "sepsis"]),
                "abx": random.choice(["ceftriaxone", "levofloxacin", "pip-tazo"]),
                "curb": random.choice(["0", "1", "2", "3"]),
                "nyha": random.choice(["I", "II", "III", "IV"]),
                "ckd": random.choice(["2", "3", "4"]),
                "severity": random.choice(["mild", "moderate", "severe"]),
                "grade": random.randint(1, 5),
            }
            # Only fill keys used in this template
            import re as _re
            used_keys = set(_re.findall(r'\{(\w+)\}', note_t))
            safe_fmt = {k: v for k, v in fmt.items() if k in used_keys}
            cases.append(("ICD10: {}".format(scenario[:30]),
                note_t.format(**safe_fmt)))
    return cases


def main():
    global PASSED, FAILED, ERRORS, RESULTS

    print("=" * 70)
    print("  MedCode AI V19 -- 1000+ Case Comprehensive Test Suite")
    print("=" * 70)
    print("  Generating cases...")
    sys.stdout.flush()

    all_cases = []
    all_cases.extend(gen_surgery_cases())
    all_cases.extend(gen_em_cases())
    all_cases.extend(gen_pathology_cases())
    all_cases.extend(gen_radiology_cases())
    all_cases.extend(gen_medicine_cases())
    all_cases.extend(gen_icd10_cases())

    # Pad to 1000+ with variations
    extra = []
    variations = [
        "Patient is postoperative day {pod}. {finding}. Vitals stable.",
        "Followup visit. {cond}. On {med}. Labs {labs}.",
        "Preoperative evaluation for {proc}. Hgb {hgb}. ECG {ecg}.",
        "Discharge summary. {dx}. Discharged to {dest}. Followup {fu}.",
    ]
    for _ in range(120):
        v = random.choice(variations)
        extra.append(("Extra: followup",
            v.format(
                pod=random.randint(1, 14),
                finding=random.choice(["afebrile", "mild pain", "drain output minimal", "ambulating"]),
                cond=random.choice(["diabetes", "hypertension", "COPD", "CHF"]),
                med=random.choice(["metformin", "lisinopril", "albuterol", "furosemide"]),
                labs=random.choice(["stable", "improved", "mildly abnormal"]),
                proc=random.choice(["cholecystectomy", "hernia repair", "knee replacement"]),
                hgb=round(random.uniform(10, 15), 1),
                ecg=random.choice(["normal sinus", "AF", "sinus tachycardia"]),
                dx=random.choice(["appendicitis", "cholelithiasis", "inguinal hernia"]),
                dest=random.choice(["home", "SNF", "rehab", "home with services"]),
                fu=random.choice(["PCP 1 week", "surgery 2 weeks", "cardiology 1 month"]),
            )))
    all_cases.extend(extra)

    print("  Total cases generated: {}".format(len(all_cases)))
    print("  Running against API at {}...".format(BASE_URL))
    print("=" * 70)
    sys.stdout.flush()

    start_time = time.time()
    category_stats = {}
    last_print = 0

    for i, (name, note) in enumerate(all_cases):
        case = {"name": name, "note": note, "category": name.split(":")[0].split(" ")[0].lower() if ":" in name else name.split(" ")[0].lower()}

        # Determine category
        cat = "other"
        name_lower = name.lower()
        if any(x in name_lower for x in ["cabg", "valve", "chol", "app", "hernia", "knee", "hip", "laminectomy", "acdf", "craniotomy", "thyroid", "colectomy", "mastectomy", "carotid", "tonsil", "colonoscop", "egd", "rotator", "pacer", "cath", "bunion", "carpal", "trigger", "cystoscop", "arthroscop", "hemorrhoid", "parotid", "septoplast", "fess", "myringotomy", "av fist", "aortic an", "embolect", "venous", "nephrect", "ureterosc", "pcnl", "circumcis", "peg", "emr", "vp shunt", "evd", "dbs", "lumbar drain", "hammertoe", "morton", "ganglion", "toenail", "phaco", "yag", "glaucoma", "emr breast", "lumpectomy", "simple mast", "mastectomy with", "breast biopsy", "sentinel", "shoulder arth", "spinal fusion", "kyphoplasty", "radial", "pilon", "hip hemi", "intramedullary", "meniscectomy", "acl recon"]):
            cat = "surgery"
        elif any(x in name_lower for x in ["cardiac", "resp", "gi ", "neuro ", "id ", "endo", "tox", "msk", "psych", "peds", "ob ", "heme", "em ", "chest pain", "acute mi", "stroke", "sepsis", "dka", "asthma", "copd ex", "pneumonia", "pe ", "appendicitis", "kidney stone", "anaphylaxis", "head trauma", "laceration", "fracture", "hypertensive", "hypoglycemia", "uti", "cellulitis", "syncope", "overdose", "alcohol"]):
            cat = "em"
        elif any(x in name_lower for x in ["patholog", "biopsy", "dcis", "adenocarcinoma", "carcinoma", "adenoma", "melanoma", "leukemia", "lymphoma", "glioblast", "meningioma", "sarcoma", "leiomyoma"]):
            cat = "pathology"
        elif any(x in name_lower for x in ["cxr", "ct ", "mri", "mammogram", "ultrasound", "bone scan", "x-ray", "xray"]):
            cat = "radiology"
        elif any(x in name_lower for x in ["diabetes", "hypertension", "heart failure", "atrial", "copd gold", "ckd", "hypothyroid", "anemia", "dvt", "pneumonia treat", "uti treat", "gout", "osteoporosis", "depression", "gerd", "hyperlipidemia"]):
            cat = "medicine"
        elif "icd10" in name_lower:
            cat = "icd10"
        case["category"] = cat

        result = api_call(case)
        RESULTS.append({**case, "result": result})

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "failed": 0, "no_codes": 0, "http_err": 0}
        category_stats[cat]["total"] += 1

        if result.get("ok") and (result.get("has_cpt") or result.get("has_icd")):
            PASSED += 1
            category_stats[cat]["passed"] += 1
            verdict = "PASS"
        elif result.get("ok") and not result.get("has_cpt") and not result.get("has_icd"):
            FAILED += 1
            category_stats[cat]["no_codes"] += 1
            verdict = "NO_CODES"
        else:
            FAILED += 1
            category_stats[cat]["http_err"] += 1
            verdict = result.get("http", result.get("error", "?"))
            ERRORS.append("#{} {} - {}".format(i+1, name[:30], str(verdict)[:40]))

        # Print progress every 50 cases
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print("  [{:4d}/{}] {} | {} | {:.0f} cases/sec | {:.0f}s elapsed".format(
                i + 1, len(all_cases), verdict.ljust(8), name[:40], rate, elapsed))
            sys.stdout.flush()

    elapsed = time.time() - start_time

    # Summary
    total = PASSED + FAILED
    print()
    print("=" * 70)
    print("  FINAL RESULTS -- {} cases in {:.1f} seconds".format(total, elapsed))
    print("=" * 70)
    print("  Passed:         {} ({:.1f}%)".format(PASSED, PASSED/total*100))
    print("  Failed:         {} ({:.1f}%)".format(FAILED, FAILED/total*100))
    print()
    print("  BY SPECIALTY:")
    print("  " + "-" * 68)
    for cat in ["surgery", "em", "pathology", "radiology", "medicine", "icd10", "other"]:
        stats = category_stats.get(cat, {"total": 0, "passed": 0})
        if stats["total"] == 0:
            continue
        rate = stats["passed"] / stats["total"] * 100
        filled = int(rate / 5)
        bar = "#" * filled + "." * (20 - filled)
        print("  {:12s} | {:4d}/{:4d} | {} | {:5.1f}% | no_codes:{:3d} | err:{:3d}".format(
            cat, stats["passed"], stats["total"], bar, rate,
            stats.get("no_codes", 0), stats.get("http_err", 0)))

    if ERRORS:
        print()
        print("  SAMPLE ERRORS (first 30):")
        for err in ERRORS[:30]:
            print("    - {}".format(err))

    print()
    print("=" * 70)

    # Save
    with open("test_results_1000_cases.json", "w") as f:
        json.dump({
            "summary": {
                "total": total, "passed": PASSED, "failed": FAILED,
                "pass_rate": round(PASSED / total * 100, 1),
                "elapsed_seconds": round(elapsed, 1),
                "cases_per_second": round(total / elapsed, 1),
                "category_stats": category_stats,
            },
            "results": [{"name": r["name"], "category": r["category"],
                         "ok": r["result"].get("ok", False),
                         "has_cpt": r["result"].get("has_cpt", False),
                         "has_icd": r["result"].get("has_icd", False),
                         "confidence": r["result"].get("confidence", 0)} for r in RESULTS],
        }, f, indent=2)
    print("  Results saved to test_results_1000_cases.json")
    print("=" * 70)

    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
