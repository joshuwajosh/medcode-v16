"""
MedCode AI V19 — Comprehensive 100+ Case Test Suite
=====================================================
Tests the agent across: Surgery, EM, Pathology, Radiology, Medicine, ICD-10
"""
import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"
PASSED = 0
FAILED = 0
ERRORS = []

# ═══════════════════════════════════════════════════════════════════════════
# TEST CASES — 100+ clinical scenarios across all specialties
# ═══════════════════════════════════════════════════════════════════════════

TEST_CASES = [
    # ═══ SURGERY (20 cases) ═══════════════════════════════════════════════
    {"name": "CABG x3", "note": "Patient underwent CABG x3 using LIMA to LAD, SVG to RCA, SVG to OM1. Cross clamp time 85 min. Pump time 120 min. Patient hemodynamically stable postop.", "category": "surgery"},
    {"name": "CABG x4 arterial", "note": "Coronary artery bypass grafting x4 arterial grafts: LIMA to LAD, RIMA to OM1, radial artery to OM2, radial artery to diagonal. Full sternotomy.", "category": "surgery"},
    {"name": "Mitral valve replacement", "note": "Patient underwent mitral valve replacement with 29mm mechanical prosthesis. Cardiopulmonary bypass time 95 minutes. Cross clamp 65 minutes.", "category": "surgery"},
    {"name": "Aortic valve replacement", "note": "AVR with 23mm bioprosthetic valve. Standard sternotomy. Cross clamp 55 minutes. Patient in AF postop.", "category": "surgery"},
    {"name": "Laparoscopic cholecystectomy", "note": "Laparoscopic cholecystectomy for symptomatic cholelithiasis. Three 5mm trocars used. Critical view of safety achieved. Gallbladder removed in endocatch bag. No complications.", "category": "surgery"},
    {"name": "Laparoscopic appendectomy", "note": "Laparoscopic appendectomy for acute appendicitis. Appendage was inflamed but not perforated. Base ligated with endoloop. Specimen sent to pathology.", "category": "surgery"},
    {"name": "Inguinal hernia repair", "note": "Right inguinal hernia repair with mesh. Direct hernia identified. Mesh secured with sutures. No complications.", "category": "surgery"},
    {"name": "Total knee replacement", "note": "Right total knee arthroplasty using cemented components. Varus deformity corrected. Tourniquet time 90 minutes. Patient ambulating POD1.", "category": "surgery"},
    {"name": "Total hip replacement", "note": "Left total hip arthroplasty. Posterior approach. Cementless femoral stem, press-fit acetabular cup. Leg length equal. No dislocation.", "category": "surgery"},
    {"name": "Lumbar laminectomy", "note": "L4-L5 laminectomy for lumbar spinal stenosis. Bilateral decompression. Ligamentum flavum hypertrophied. Neural elements decompressed. No dural tear.", "category": "surgery"},
    {"name": "Anterior cervical discectomy fusion", "note": "ACDF at C5-C6 with allograft and anterior plate. Disc herniation with radiculopathy. Decompression complete. No recurrence of symptoms.", "category": "surgery"},
    {"name": "Craniotomy for SDH", "note": "Emergency craniotomy for acute subdural hematoma. Burr holes placed, hematoma evacuated. Dural patch applied. Bone flap replaced.", "category": "surgery"},
    {"name": "Thyroidectomy", "note": "Total thyroidectomy for papillary thyroid carcinoma. Recurrent laryngeal nerve identified and preserved. Parathyroid glands preserved. Specimen sent to pathology.", "category": "surgery"},
    {"name": "Colectomy for colon cancer", "note": "Laparoscopic right hemicolectomy for ascending colon adenocarcinoma. Ileocolic and right colic vessels ligated. Specimen with 12cm margin. Lymph nodes harvested.", "category": "surgery"},
    {"name": "Mastectomy", "note": "Modified radical mastectomy for invasive ductal carcinoma left breast. Skin sparing. Sentinel lymph node biopsy x2. Nipple removed.", "category": "surgery"},
    {"name": "Carotid endarterectomy", "note": "Left carotid endarterectomy with patch angioplasty. Shunt used. 80% stenosis preop. Neuro monitoring stable throughout. No postop stroke.", "category": "surgery"},
    {"name": "Tonsillectomy", "note": "Tonsillectomy and adenoidectomy for recurrent tonsillitis and obstructive sleep apnea. Bipolar dissection. Bleeding controlled. Specimen sent to pathology.", "category": "surgery"},
    {"name": "Colonoscopy with polypectomy", "note": "Diagnostic colonoscopy with removal of 12mm sessile polyp in sigmoid colon using cold snare polypectomy. No bleeding. Pathology sent.", "category": "surgery"},
    {"name": "EGD with biopsy", "note": "Upper endoscopy for GERD symptoms. Erythematous esophagitis LA grade B. Biopsies taken from distal esophagus. No Barrett esophagus.", "category": "surgery"},
    {"name": "Rotator cuff repair", "note": "Arthroscopic rotator cuff repair right shoulder. Supraspinatus tear 2cm. Double row technique. 4 anchors used. Deltoid and rotator interval closed.", "category": "surgery"},

    # ═══ EMERGENCY MEDICINE (20 cases) ═════════════════════════════════════
    {"name": "Chest pain evaluation", "note": "45 year old male presenting with substernal chest pain radiating to left arm. Onset 2 hours ago. Diaphoretic. ECG shows ST elevation in leads II, III, aVF. Troponin pending.", "category": "em"},
    {"name": "Acute MI", "note": "68 year old male with acute ST elevation myocardial infarction. Cath lab activated. LAD 99% occlusion. Drug eluting stent placed. Echo shows EF 40%. Heart failure management initiated.", "category": "em"},
    {"name": "Stroke code", "note": "72 year old female with acute onset left sided weakness and aphasia. Onset 45 minutes ago. NIHSS 14. CT head negative for hemorrhage. TPA administered.", "category": "em"},
    {"name": "Sepsis", "note": "55 year old male with fever 102.5F, HR 120, BP 85/50, RR 28. WBC 22000. Lactate 4.2. Urine culture pending. Started on broad spectrum antibiotics and fluids.", "category": "em"},
    {"name": "Diabetic ketoacidosis", "note": "28 year old female with DKA. Glucose 650, pH 7.1, bicarb 8. Positive ketones. Anion gap 28. Insulin drip and IV fluids initiated. Potassium replaced.", "category": "em"},
    {"name": "Asthma exacerbation", "note": "35 year old female with acute severe asthma exacerbation. SpO2 91% on room air. Using accessory muscles. Nebulized albuterol and ipratropium x3. IV magnesium given.", "category": "em"},
    {"name": "COPD exacerbation", "note": "67 year old male with COPD exacerbation. Increased dyspnea and purulent sputum. On home O2 2L. BiPAP initiated. Steroids and antibiotics started.", "category": "em"},
    {"name": "Pneumonia", "note": "45 year old female with community acquired pneumonia. Fever 101.5F, productive cough. CXR shows RLL consolidation. Started on azithromycin and ceftriaxone.", "category": "em"},
    {"name": "Pulmonary embolism", "note": "50 year old female with sudden onset dyspnea and pleuritic chest pain. D-dimer elevated. CT pulmonary angiography shows bilateral PE. Anticoagulation started.", "category": "em"},
    {"name": "Abdominal pain - appendicitis", "note": "22 year old male with RLQ pain, fever, and elevated WBC. CT abdomen shows acute appendicitis with appendicolith. Surgical consultation obtained.", "category": "em"},
    {"name": "Kidney stones", "note": "40 year old male with severe flank pain and hematuria. CT abdomen shows 6mm ureteral stone at UVJ. Tamsulosin prescribed. Pain managed with ketorolac.", "category": "em"},
    {"name": "Anaphylaxis", "note": "30 year old female with peanut allergy. Developed urticaria, angioedema, wheezing after eating peanuts. Epinephrine IM given. Responded well. Diphenhydramine and steroids given.", "category": "em"},
    {"name": "Head trauma", "note": "25 year old male after MVA. GCS 14. CT head shows small right frontal contusion without hemorrhage. No midline shift. Neurosurgery consulted.", "category": "em"},
    {"name": "Laceration repair", "note": "8 year old male with 3cm laceration to forehead after fall. Wound irrigated and closed with 5-0 nylon. Tetanus updated. Wound care instructions given.", "category": "em"},
    {"name": "Fracture - distal radius", "note": "65 year old female with distal radius fracture after fall on outstretched hand. X-ray shows displaced fracture. Closed reduction performed. Sugar tong splint applied.", "category": "em"},
    {"name": "Hypertensive urgency", "note": "58 year old male with BP 210/120. Asymptomatic. No end organ damage. Oral labetalol started. Blood pressure monitored. Discharged with followup.", "category": "em"},
    {"name": "Hypoglycemia", "note": "70 year old female on insulin found confused by family. Fingerstick glucose 42. IV dextrose given. Glucose normalized. Insulin regimen adjusted.", "category": "em"},
    {"name": "UTI with pyelonephritis", "note": "32 year old female with fever 101.8F, dysuria, and CVA tenderness. UA shows pyuria and bacteriuria. WBC 15000. Started on IV antibiotics.", "category": "em"},
    {"name": "Cellulitis", "note": "55 year old male with erythematous, warm, swollen right lower leg. No wound. WBC elevated. Started on IV vancomycin and pip-tazo.外科会诊 obtained.", "category": "em"},
    {"name": "Syncope evaluation", "note": "42 year old female with witnessed syncope at work. No prodrome. Brief LOC. ECG normal. Troponin negative. CBC and BMP normal. Discharged with cardiology followup.", "category": "em"},

    # ═══ PATHOLOGY (15 cases) ═════════════════════════════════════════════
    {"name": "Breast biopsy - DCIS", "note": "Core needle biopsy of right breast mass 2cm. Pathology shows ductal carcinoma in situ, intermediate grade. ER positive, PR positive, HER2 negative. Excision recommended.", "category": "pathology"},
    {"name": "Lung biopsy - adenocarcinoma", "note": "CT guided biopsy of right lower lobe mass. Pathology shows moderately differentiated adenocarcinoma. TTF-1 positive. Staging PET CT ordered.", "category": "pathology"},
    {"name": "Colon polyp - tubular adenoma", "note": "Sigmoid colon polyp removed during colonoscopy. Pathology: tubular adenoma with low grade dysplasia. Margin negative. Surveillance colonoscopy in 3 years.", "category": "pathology"},
    {"name": "Skin biopsy - melanoma", "note": "Shave biopsy of suspicious lesion on left arm. Pathology shows melanoma, Breslow thickness 0.8mm, Clark level III. No ulceration. Wide local excision recommended.", "category": "pathology"},
    {"name": "Thyroid FNA - papillary carcinoma", "note": "Fine needle aspiration of thyroid nodule. Cytology shows papillary thyroid carcinoma. Total thyroidectomy recommended.", "category": "pathology"},
    {"name": "Liver biopsy - cirrhosis", "note": "Percutaneous liver biopsy. Pathology shows micronodular cirrhosis with active steatohepatitis. Bridging fibrosis. Consistent with alcoholic liver disease.", "category": "pathology"},
    {"name": "Bone marrow biopsy", "note": "Bone marrow biopsy and aspiration. Hypercellular marrow 80%. Myeloid to erythroid ratio 10:1. No blasts. Iron stores decreased. Consistent with myeloproliferative disorder.", "category": "pathology"},
    {"name": "Prostate biopsy - Gleason 7", "note": "Transrectal prostate biopsy x12 cores. Right apex shows adenocarcinoma Gleason 3+4=7. 3 of 12 cores positive. PSA 8.5.", "category": "pathology"},
    {"name": "Lymph node biopsy - lymphoma", "note": "Excisional biopsy of left axillary lymph node. Pathology shows diffuse large B-cell lymphoma. CD20 positive. Staging workup initiated.", "category": "pathology"},
    {"name": "Kidney biopsy - glomerulonephritis", "note": "Percutaneous renal biopsy. Pathology shows membranous glomerulonephritis. Electron dense deposits along capillary loops. PLA2R antibody positive.", "category": "pathology"},
    {"name": "Endometrial biopsy - hyperplasia", "note": "Endometrial biopsy. Pathology shows complex endometrial hyperplasia without atypia. Progesterone therapy recommended. Followup biopsy in 6 months.", "category": "pathology"},
    {"name": "Gastric biopsy - H pylori", "note": "Upper endoscopy with gastric biopsies. Pathology shows chronic active gastritis with H pylori organisms. Triple therapy initiated.", "category": "pathology"},
    {"name": "Skin biopsy - basal cell carcinoma", "note": "Punch biopsy of lesion on nose. Pathology shows nodular basal cell carcinoma. Mohs surgery recommended.", "category": "pathology"},
    {"name": "Cervical biopsy - CIN III", "note": "Colposcopy with cervical biopsy. Pathology shows CIN III (carcinoma in situ). Cold knife cone biopsy recommended.", "category": "pathology"},
    {"name": "Testicular biopsy", "note": "Testicular biopsy for infertility workup. Pathology shows Sertoli cell only syndrome. No germ cells present. Azoospermia confirmed.", "category": "pathology"},

    # ═══ RADIOLOGY (15 cases) ═════════════════════════════════════════════
    {"name": "CXR - pneumonia", "note": "Chest X-ray shows right lower lobe consolidation with air bronchograms. Consistent with pneumonia. No pleural effusion.", "category": "radiology"},
    {"name": "CT head - hemorrhage", "note": "CT head without contrast shows 15mm left temporal epidural hematoma with 5mm midline shift. Fracture of left temporal bone. Neurosurgery stat consultation.", "category": "radiology"},
    {"name": "CT abdomen - appendicitis", "note": "CT abdomen with contrast shows dilated appendix 14mm with periappendiceal fat stranding and appendicolith. Acute appendicitis confirmed.", "category": "radiology"},
    {"name": "CT chest - PE", "note": "CT pulmonary angiography shows filling defects in right and left main pulmonary arteries extending to segmental branches. Bilateral pulmonary emboli.", "category": "radiology"},
    {"name": "MRI brain - stroke", "note": "MRI brain with diffusion weighted imaging shows acute infarction in right MCA territory. Restricted diffusion in right parietal and temporal lobes.", "category": "radiology"},
    {"name": "X-ray - fracture", "note": "X-ray of right wrist shows displaced distal radius fracture with dorsal angulation. No carpal bone abnormality.", "category": "radiology"},
    {"name": "CT spine - herniated disc", "note": "CT lumbar spine shows large posterolateral disc herniation at L4-L5 left side with impingement on traversing L5 nerve root.", "category": "radiology"},
    {"name": "Mammogram - suspicious mass", "note": "Bilateral diagnostic mammogram shows 1.5cm spiculated mass in left upper outer quadrant. BI-RADS 4B. Ultrasound guided biopsy recommended.", "category": "radiology"},
    {"name": "Echo - heart failure", "note": "Echocardiogram shows dilated left ventricle with EF 25%. Global hypokinesis. Moderate MR. Diastolic dysfunction grade II.", "category": "radiology"},
    {"name": "CT abdomen - liver mass", "note": "CT abdomen with contrast shows 4cm hypervascular mass in right hepatic lobe. Classic appearance of hepatocellular carcinoma. AFP elevated at 450.", "category": "radiology"},
    {"name": "Bone scan - metastasis", "note": "Whole body bone scan shows multiple focal areas of increased uptake in ribs, spine, and pelvis consistent with osseous metastatic disease.", "category": "radiology"},
    {"name": "CT chest - lung nodule", "note": "Low dose CT chest shows 8mm solid nodule in right upper lobe. No other nodules. Previous CT 12 months ago showed 4mm nodule. Growth noted.", "category": "radiology"},
    {"name": "MRI knee - meniscus tear", "note": "MRI right knee shows complex tear of medial meniscus with horizontal cleavage component. Intact ACL. Mild MCL sprain.", "category": "radiology"},
    {"name": "CT sinus - sinusitis", "note": "CT sinuses shows complete opacification of right maxillary sinus and ethmoid air cells with mucosal thickening. Left sphenoid sinus partially opacified.", "category": "radiology"},
    {"name": "Ultrasound - gallstones", "note": "Right upper quadrant ultrasound shows multiple gallstones with posterior shadowing. Gallbladder wall normal thickness. No pericholecystic fluid.", "category": "radiology"},

    # ═══ INTERNAL MEDICINE (20 cases) ══════════════════════════════════════
    {"name": "Diabetes management", "note": "55 year old male with type 2 diabetes. HbA1c 8.2%. Currently on metformin 1000mg BID. Fasting glucose 180. Adding empagliflozin 10mg daily. Diet counseling provided.", "category": "medicine"},
    {"name": "Hypertension management", "note": "62 year old female with hypertension. BP today 152/94. On lisinopril 20mg. Increasing to 40mg. Continue low sodium diet. Recheck BP in 4 weeks.", "category": "medicine"},
    {"name": "Heart failure management", "note": "68 year old male with HFrEF, EF 30%. On carvedilol 25mg BID, lisinopril 40mg, furosemide 40mg. Weight stable. BNP 850. No edema. Continue current regimen.", "category": "medicine"},
    {"name": "Atrial fibrillation", "note": "72 year old female with new onset AF. HR 110. CHA2DS2-VASc score 4. Started on apixaban 5mg BID and metoprolol for rate control.", "category": "medicine"},
    {"name": "COPD management", "note": "65 year old male with COPD GOLD stage III. On tiotropium and fluticasone/salmeterol. FEV1 42%. No exacerbations this year. Continue current regimen. Smoking cessation counseling.", "category": "medicine"},
    {"name": "Asthma management", "note": "28 year old female with moderate persistent asthma. On fluticasone/salmeterol. Spirometry shows FEV1 72%. Well controlled. Continue current therapy.", "category": "medicine"},
    {"name": "Hypothyroidism", "note": "45 year old female with hypothyroidism. TSH 4.8 on levothyroxine 50mcg. Increase to 75mcg. Recheck TSH in 6 weeks.", "category": "medicine"},
    {"name": "Hyperthyroidism", "note": "32 year old female with Graves disease. TSH undetectable, T4 elevated. Started on methimazole 10mg daily. Beta blocker for symptoms. Endocrine followup.", "category": "medicine"},
    {"name": "Chronic kidney disease", "note": "70 year old male with CKD stage 3b. GFR 38. Creatinine 1.8. On lisinopril 20mg. Continue ACE inhibitor. Avoid nephrotoxins. Recheck labs in 3 months.", "category": "medicine"},
    {"name": "Anemia workup", "note": "45 year old female with fatigue. Hgb 9.2, MCV 72. Ferritin low. Iron studies consistent with iron deficiency anemia. Start ferrous sulfate 325mg TID.", "category": "medicine"},
    {"name": "Pneumonia treatment", "note": "67 year old male with community acquired pneumonia. On azithromycin and ceftriaxone. Afebrile 24 hours. WBC trending down. Continue antibiotics.", "category": "medicine"},
    {"name": "UTI treatment", "note": "35 year old female with uncomplicated UTI. E. coli on culture sensitive to nitrofurantoin. Complete 5 day course. Followup if symptoms persist.", "category": "medicine"},
    {"name": "GERD management", "note": "50 year old male with GERD. On omeprazole 20mg daily. Symptoms controlled. Continue PPI. Avoid trigger foods. Sleep with head elevated.", "category": "medicine"},
    {"name": "Iron deficiency", "note": "28 year old female with iron deficiency anemia. Hgb 10. Ferritin 8. Start IV iron infusion due to oral intolerance. Recheck in 4 weeks.", "category": "medicine"},
    {"name": "Hyperlipidemia", "note": "55 year old male with LDL 180. On atorvastatin 20mg. Increase to 40mg. Lifestyle modifications. Recheck lipid panel in 3 months.", "category": "medicine"},
    {"name": "Gout management", "note": "60 year old male with acute gout flare. Right great toe swollen and erythematous. UA shows monosodium urate crystals. Started on colchicine and indomethacin.", "category": "medicine"},
    {"name": "Osteoporosis", "note": "68 year old female with osteoporosis. T-score -2.8 spine. On alendronate 70mg weekly. Vitamin D and calcium supplementation. DEXA in 2 years.", "category": "medicine"},
    {"name": "Depression management", "note": "35 year old female with major depressive disorder. PHQ-9 score 16. On sertraline 50mg. Increase to 100mg. Therapy referrals provided. Safety plan discussed.", "category": "medicine"},
    {"name": "DVT treatment", "note": "45 year old male with left lower extremity DVT. On apixaban 10mg BID x7 days then 5mg BID. Compression stocking. Elevate leg. Followup in 1 week.", "category": "medicine"},
    {"name": "PE treatment", "note": "55 year old female with bilateral PE. On rivaroxaban. Hemodynamically stable. Oxygen supplementation. Repeat CT in 3 months. Anticoagulation x 6 months minimum.", "category": "medicine"},

    # ═══ ICD-10 CODING SPECIFIC (10 cases) ═════════════════════════════════
    {"name": "Diabetes with complications", "note": "55 year old female with type 2 diabetes mellitus with diabetic retinopathy, proliferative. Also has diabetic neuropathy and diabetic nephropathy stage 3.", "category": "icd10"},
    {"name": "COPD with acute exacerbation", "note": "72 year old male with COPD gold stage 3 presenting with acute exacerbation. Increased dyspnea, purulent sputum. Pneumonia ruled out.", "category": "icd10"},
    {"name": "Heart failure with preserved EF", "note": "68 year old female with heart failure with preserved ejection fraction. EF 55%. Chronic hypertension. Atrial fibrillation.", "category": "icd10"},
    {"name": "Acute kidney injury", "note": "65 year old male with acute kidney injury on chronic kidney disease. Creatinine rose from 1.5 to 3.2. Likely nephrotoxic from NSAIDs.", "category": "icd10"},
    {"name": "Sepsis with organ dysfunction", "note": "58 year old female with sepsis secondary to UTI. Sepsis-induced acute kidney injury. Lactate 4.5. On norepinephrine.", "category": "icd10"},
    {"name": "Multiple trauma", "note": "30 year old male after MVA. Ribs fractures 4-7, splenic laceration grade 2, left pneumothorax. GCS 14. Chest tube placed.", "category": "icd10"},
    {"name": "Neoplasm staging", "note": "60 year old male with newly diagnosed non-small cell lung cancer. PET CT shows right upper lobe mass with mediastinal lymph node involvement. Stage IIIB.", "category": "icd10"},
    {"name": "Maternal conditions", "note": "28 year old female at 34 weeks gestation with preeclampsia. BP 160/100, proteinuria. MgSO4 started. Antenatal corticosteroids given.", "category": "icd10"},
    {"name": "Mental health", "note": "40 year old male with bipolar disorder type 1, current episode manic. On lithium and quetiapine. Sleep deprived. Hospitalization considered.", "category": "icd10"},
    {"name": "External causes", "note": "45 year old male injured at work. Falling from ladder. Closed fracture of left radius and ulna. Worker compensation case. External cause coding required.", "category": "icd10"},

    # ═══ ADDITIONAL SURGERY/PROCEDURE (10 cases) ═══════════════════════════
    {"name": "Pacemaker implant", "note": "Dual chamber pacemaker implanted for sick sinus syndrome. Venous access via left cephalic vein. Atrial and ventricular leads placed. Thresholds satisfactory.", "category": "surgery"},
    {"name": "Cardiac catheterization", "note": "Diagnostic cardiac catheterization for chest pain evaluation. LAD 40% stenosis, RCA 30%, LCx 25%. LVEF 55%. No intervention needed.", "category": "surgery"},
    {"name": "Colonoscopy screening", "note": "Screening colonoscopy. Cecum intubated. No polyps found. Good bowel prep. Next colonoscopy in 10 years.", "category": "surgery"},
    {"name": "Arthroscopy shoulder", "note": "Diagnostic shoulder arthroscopy. Mild supraspinatus tendinopathy. No tears. Labrum intact. Subacromial impingement. Debridement performed.", "category": "surgery"},
    {"name": "Bunionectomy", "note": "Right bunionectomy with osteotomy. Akin and scarf osteotomies. Screws for fixation. Weight bearing as tolerated in surgical shoe.", "category": "surgery"},
    {"name": "Carpal tunnel release", "note": "Right carpal tunnel release, endoscopic. Transverse carpal ligament divided. Median nerve decompressed. No complications.", "category": "surgery"},
    {"name": "Trigger finger release", "note": "Right middle finger trigger finger release. A1 pulley divided. Full passive range of motion achieved. No complications.", "category": "surgery"},
    {"name": "Cystoscopy", "note": "Diagnostic cystoscopy for hematuria. Bladder mucosa normal. No stones or masses. Ureters visualized. No abnormalities.", "category": "surgery"},
    {"name": "Knee arthroscopy", "note": "Left knee arthroscopy. Medial meniscus tear confirmed. Partial meniscectomy performed. Chondromalacia grade 2 medial compartment. No ACL tear.", "category": "surgery"},
    {"name": "Hemorrhoidectomy", "note": "Excisional hemorrhoidectomy for grade III internal hemorrhoids. Three hemorrhoids excised. Wound left open. Sitz baths initiated.", "category": "surgery"},
]


def run_case(case, index):
    """Run a single test case against the API."""
    global PASSED, FAILED, ERRORS

    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v16/code",
            json={"note": case["note"], "mdm_level": "moderate"},
            timeout=30,
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            has_cpt = bool(data.get("cpt_codes"))
            has_icd = bool(data.get("icd10_codes"))
            confidence = data.get("confidence", 0)
            specialty = data.get("specialty", "")
            processing_ms = data.get("processing_time_ms", 0)

            result = {
                "index": index + 1,
                "name": case["name"],
                "category": case["category"],
                "status": "PASS",
                "http_status": response.status_code,
                "has_cpt": has_cpt,
                "has_icd": has_icd,
                "confidence": round(confidence, 2),
                "specialty": specialty,
                "processing_ms": round(processing_ms, 1),
                "elapsed_s": round(elapsed, 2),
            }

            if has_cpt or has_icd:
                PASSED += 1
                result["verdict"] = "PASS"
            else:
                FAILED += 1
                result["verdict"] = "FAIL_NO_CODES"
                ERRORS.append(f"#{index+1} {case['name']}: No codes generated")
        else:
            FAILED += 1
            result = {
                "index": index + 1,
                "name": case["name"],
                "category": case["category"],
                "status": "FAIL",
                "verdict": f"HTTP_{response.status_code}",
                "http_status": response.status_code,
            }
            ERRORS.append(f"#{index+1} {case['name']}: HTTP {response.status_code}")

        return result

    except Exception as e:
        FAILED += 1
        result = {
            "index": index + 1,
            "name": case["name"],
            "category": case["category"],
            "status": "ERROR",
            "verdict": f"EXCEPTION: {str(e)[:80]}",
        }
        ERRORS.append(f"#{index+1} {case['name']}: {str(e)[:80]}")
        return result


def main():
    global PASSED, FAILED, ERRORS

    print("=" * 70)
    print("  MedCode AI V19 — Comprehensive 100+ Case Test Suite")
    print("=" * 70)
    print(f"  Running {len(TEST_CASES)} test cases across 6 specialties...")
    print("=" * 70)

    all_results = []
    category_stats = {}

    for i, case in enumerate(TEST_CASES):
        result = run_case(case, i)
        all_results.append(result)

        cat = case["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "failed": 0}
        category_stats[cat]["total"] += 1
        if result.get("verdict") == "PASS":
            category_stats[cat]["passed"] += 1
        else:
            category_stats[cat]["failed"] += 1

        status_icon = "PASS" if result.get("verdict") == "PASS" else "FAIL"
        codes = "CPT:{} ICD:{}".format(result.get("has_cpt", "?"), result.get("has_icd", "?")) if "has_cpt" in result else result.get("verdict", "???")
        conf = "conf={}".format(result.get("confidence", "?")) if "confidence" in result else ""
        spec = "spec={}".format(result.get("specialty", "?")) if "specialty" in result else ""
        ms = "{}ms".format(result.get("processing_ms", "?")) if "processing_ms" in result else ""

        print("  {} [{:3d}/{}] {:35s} | {:20s} | {:12s} | {:20s} | {}".format(
            status_icon, i+1, len(TEST_CASES), case["name"][:35], codes, conf, spec, ms))

        time.sleep(0.5)

    # Summary
    total = PASSED + FAILED
    print()
    print("=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print("  Total Cases:     {}".format(total))
    print("  Passed:          {} ({:.1f}%)".format(PASSED, PASSED/total*100))
    print("  Failed:          {} ({:.1f}%)".format(FAILED, FAILED/total*100))
    print()

    print("  BY SPECIALTY:")
    print("  " + "-" * 66)
    for cat, stats in sorted(category_stats.items()):
        rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        filled = int(rate / 5)
        bar = "#" * filled + "." * (20 - filled)
        print("  {:15s} | {:3d}/{:3d} | {} | {:5.1f}%".format(cat, stats["passed"], stats["total"], bar, rate))

    if ERRORS:
        print()
        print("  ERRORS:")
        for err in ERRORS[:20]:
            print(f"    - {err}")

    print()
    print("=" * 70)

    # Save results to JSON
    with open("test_results_100_cases.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": PASSED,
                "failed": FAILED,
                "pass_rate": round(PASSED / total * 100, 1) if total > 0 else 0,
                "category_stats": category_stats,
            },
            "results": all_results,
        }, f, indent=2)
    print("  Results saved to test_results_100_cases.json")
    print("=" * 70)

    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
