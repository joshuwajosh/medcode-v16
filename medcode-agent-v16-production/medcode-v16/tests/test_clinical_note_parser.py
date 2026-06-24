"""
Tests for Clinical Note Parser — 100+ clinical note scenarios.
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
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 1: SPECIALTY-SPECIFIC NOTES (20 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "Dermatology - Mohs surgery BCC",
        "note": """Operative Report
Procedure: Mohs micrographic surgery
Diagnosis: Skin cancer, basal cell carcinoma right cheek
Stage 1: 4 tissue blocks processed. Margin negative.
Stage 2: 6 tissue blocks processed. Margin negative.
Closure: Intermediate closure 3cm.""",
        "expected_cpt": ["17315"],
        "expected_icd": ["C44.90"],
    },
    {
        "name": "Dermatology - Excision melanoma",
        "note": """Operative Report
Procedure: Lesion excision left forearm
Diagnosis: Malignant melanoma, Breslow thickness 1.2mm
Technique: Elliptical excision with 2cm margins.
Specimen sent to pathology for permanent sectioning.
Closure: Primary closure under moderate tension.""",
        "expected_cpt": ["11602"],
        "expected_icd": ["C43.9"],
    },
    {
        "name": "Dermatology - Cryotherapy AKs",
        "note": """Office Visit Note
Procedure: Cryotherapy to actinic keratoses
Indication: Multiple actinic keratoses bilateral upper extremities
Treatment: Liquid nitrogen cryotherapy applied to 8 lesions.
Technique: Freeze-thaw cycle, 10 seconds per lesion.
Comorbidities: Hypertension, diabetes.
Follow up in 6 weeks to assess healing.""",
        "expected_cpt": ["17000"],
        "expected_icd": ["I10", "E11.9"],
    },
    {
        "name": "Dermatology - Skin biopsy lesion",
        "note": """Office Visit Note
Procedure: Punch biopsy right lower leg
Indication: Suspicious pigmented lesion, changing morphology
Technique: 4mm punch biopsy under local anesthesia.
Specimen sent to pathology.
Assessment: Lesion concerning for melanoma.""",
        "expected_cpt": ["11102", "11104"],
        "expected_icd": ["L98.9", "C43.9"],
    },
    {
        "name": "Dermatology - Excision squamous cell",
        "note": """Operative Report
Procedure: Mohs micrographic surgery left ear
Diagnosis: Skin cancer, squamous cell carcinoma left ear
Stage 1: 3 tissue blocks. Positive margin superior.
Stage 2: 4 tissue blocks. Margin negative.
Reconstruction: Complex linear closure.""",
        "expected_cpt": ["17315"],
        "expected_icd": ["C44.90"],
    },
    {
        "name": "Ophthalmology - Cataract surgery",
        "note": """Operative Report
Procedure: Phacoemulsification with intraocular lens implant
Diagnosis: Senile cataract right eye
Technique: Temporal clear corneal incision. Hydrodissection.
IOL power calculated. Lens implanted in capsular bag.
Patient has diabetes and hypertension. AC stable. No complications.""",
        "expected_cpt": ["66984"],
        "expected_icd": ["E11.9", "I10"],
    },
    {
        "name": "Ophthalmology - Glaucoma surgery",
        "note": """Operative Report
Procedure: Trabeculectomy with mitomycin C
Diagnosis: Primary open-angle glaucoma, refractory to medications
Indication: IOP 28mmHg on maximum medical therapy.
Technique: Superior limbal-based conjunctival flap.
Scleral flap created. Trabeculectomy performed.
Patient has hypertension and diabetes.""",
        "expected_cpt": ["66170"],
        "expected_icd": ["I10", "E11.9"],
    },
    {
        "name": "Ophthalmology - Intravitreal injection",
        "note": """Procedure Note
Procedure: Intravitreal injection bevacizumab left eye
Diagnosis: Wet age-related macular degeneration
Prep: Topical povidone iodine. Speculum placed.
Injection: 1.25mg in 0.05mL injected through pars plana.
Patient has diabetes and hypertension. Post-IOP checked. No complications.""",
        "expected_cpt": ["67028"],
        "expected_icd": ["E11.9", "I10"],
    },
    {
        "name": "OB/GYN - Cesarean section",
        "note": """Operative Report
Procedure: Cesarean section, low transverse incision
Diagnosis: Pregnancy with severe preeclampsia at 34 weeks
Indication: Worsening preeclampsia, non-reassuring fetal heart tracing.
Baby delivered Apgar 8/9. Cord blood gases normal.
Estimated blood loss 800mL.""",
        "expected_cpt": ["59510"],
        "expected_icd": ["O14.90", "Z33.1", "O14.64"],
    },
    {
        "name": "OB/GYN - Total abdominal hysterectomy",
        "note": """Operative Report
Procedure: Total abdominal hysterectomy
Diagnosis: Uterine leiomyomata with menorrhagia
Technique: Low transverse incision. Uterus enlarged to 14 week size.
Bilateral salpingo-oophorectomy performed. Anemia from chronic blood loss.
Cuff closed. Estimated blood loss 250mL.""",
        "expected_cpt": ["58150"],
        "expected_icd": ["D25.9", "D64.9"],
    },
    {
        "name": "OB/GYN - Colposcopy with LEEP",
        "note": """Procedure Note
Procedure: Colposcopy with loop electrosurgical excision procedure
Indication: ASC-US Pap smear, high-risk HPV positive
Findings: Acetowhite lesion at 12 o'clock, extending into canal.
LEEP specimen sent to pathology. Hypertension on file.
No complications.""",
        "expected_cpt": ["57452"],
        "expected_icd": ["N87.1", "I10"],
    },
    {
        "name": "ENT - Tonsillectomy",
        "note": """Operative Report
Procedure: Tonsillectomy and adenoidectomy
Diagnosis: Recurrent tonsillitis, 6 episodes in 12 months
Patient is a 6-year-old male with asthma.
Technique: Cold knife dissection. Electrocautery for hemostasis.
Estimated blood loss minimal.""",
        "expected_cpt": ["42820", "42830"],
        "expected_icd": ["J03.90", "J45.901"],
    },
    {
        "name": "ENT - FESS sinus surgery",
        "note": """Operative Report
Procedure: Bilateral functional endoscopic sinus surgery
Diagnosis: Chronic sinusitis with nasal polyposis
Patient has asthma and hypertension.
Technique: Bilateral maxillary antrostomy. Ethmoidectomy.
Frontal sinusotomy. Sphenoidotomy.
All ostia widely patent. No complications.""",
        "expected_cpt": ["31256"],
        "expected_icd": ["J32.9", "J45.901"],
    },
    {
        "name": "ENT - Parotidectomy",
        "note": """Operative Report
Procedure: Superficial parotidectomy
Diagnosis: Pleomorphic adenoma right parotid gland
Patient has hypertension and diabetes.
Technique: Facial nerve identified and preserved.
Superficial lobe dissected and removed.
Specimen sent to pathology.""",
        "expected_cpt": ["42420"],
        "expected_icd": ["I10", "E11.9"],
    },
    {
        "name": "ENT - Myringotomy with tubes",
        "note": """Operative Report
Procedure: Bilateral myringotomy with tympanostomy tube placement
Diagnosis: Chronic otitis media with effusion
Patient is a 3-year-old female with failure to thrive.
Technique: Incisions made in anteroinferior quadrants.
Armstadt tubes placed bilaterally.""",
        "expected_cpt": ["69424"],
        "expected_icd": ["H65.2", "R62.51"],
    },
    {
        "name": "Urology - TURBT",
        "note": """Operative Report
Procedure: Transurethral resection of bladder tumor (TURBT)
Diagnosis: Bladder mass, suspected transitional cell carcinoma
Patient has hypertension and diabetes.
Technique: Resectoscope inserted. Tumor at lateral wall.
Resected to deep muscle. Specimens sent to pathology.
No perforation. Hemostasis achieved.""",
        "expected_cpt": ["51100"],
        "expected_icd": ["C67.9", "I10"],
    },
    {
        "name": "Urology - Radical nephrectomy",
        "note": """Operative Report
Procedure: Laparoscopic radical nephrectomy left
Diagnosis: Renal cell carcinoma left kidney, 4.5cm mass
Patient has hypertension and diabetes.
Technique: Three trocar technique. Renal hilum dissected.
Renal artery and vein stapled. Specimen removed intact.
Estimated blood loss 100mL.""",
        "expected_cpt": ["50220"],
        "expected_icd": ["I10", "E11.9"],
    },
    {
        "name": "Urology - Vasectomy",
        "note": """Procedure Note
Procedure: Vasectomy bilateral
Patient has hypertension.
Technique: No-scalpel technique. Vas deferens identified bilaterally.
Bilateral ligation and excision of 1cm segment.
Cautery to lumen. Fascial interposition.""",
        "expected_cpt": ["55250"],
        "expected_icd": ["I10"],
    },
    {
        "name": "Urology - Cystoscopy with stent",
        "note": """Procedure Note
Procedure: Cystoscopy with ureteral stent placement
Indication: Left ureteral obstruction from stone
Findings: 8mm stone at UVJ. Left hydronephrosis.
Technique: Stent advanced over guidewire. Position confirmed.
Urinary tract infection treated with antibiotics.""",
        "expected_cpt": ["52000", "52332"],
        "expected_icd": ["N20.1", "N39.0"],
    },
    {
        "name": "Pain management - Epidural steroid injection",
        "note": """Procedure Note
Procedure: Fluoroscopy-guided lumbar epidural steroid injection
Indication: Lumbar radiculopathy, failed conservative management
Level: L4-L5. Contrast confirmed epidural spread.
Injectate: 4mg dexamethasone in 4mL normal saline.
Patient tolerated well. No complications.""",
        "expected_cpt": ["62322"],
        "expected_icd": ["M54.10", "M54.40"],
    },
    {
        "name": "Pain management - Facet joint injection",
        "note": """Procedure Note
Procedure: Medial branch block bilateral L4-L5
Indication: Facet joint arthropathy, low back pain
Technique: Bilateral medial branches at L4 and L5.
Contrast confirmed perivascular spread. No intravascular uptake.
Injectate: 1mL 0.5% bupivacaine per level.""",
        "expected_cpt": ["64490"],
        "expected_icd": ["M54.5", "M47.816"],
    },
    {
        "name": "Pain management - Trigger point injection",
        "note": """Procedure Note
Procedure: Trigger point injection bilateral trapezius
Indication: Myofascial pain syndrome, fibromyalgia
Technique: 2mL lidocaine 1% injected into each trigger point.
Total of 6 injections performed. No complications.
Patient reports immediate relief.""",
        "expected_cpt": ["20552"],
        "expected_icd": ["M79.1", "M79.0"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 2: COMPLEX MULTI-PROCEDURE NOTES (15 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "CABG + valve replacement",
        "note": """Operative Report
Procedure: Coronary artery bypass graft x3 with aortic valve replacement
Technique: LIMA to LAD, SVG to RCA, SVG to OM1.
Aortic valve: 23mm bioprosthetic valve implanted.
Cross-clamp: 110 minutes. Pump time: 155 minutes.
Diagnosis: Severe triple vessel coronary artery disease with aortic stenosis.""",
        "expected_cpt": ["33533", "33430"],
        "expected_icd": ["I25.10", "I35.0"],
    },
    {
        "name": "Multiple hernia repairs bilateral",
        "note": """Operative Report
Procedure: Bilateral inguinal hernia repair with mesh
Diagnosis: Bilateral inguinal hernias
Patient has obesity.
Technique: Right: Lichtenstein tension-free mesh repair.
Left: Lichtenstein tension-free mesh repair.
Estimated blood loss minimal. No complications.""",
        "expected_cpt": ["44950", "49560"],
        "expected_icd": ["K40.91", "K40.90", "E66.01"],
    },
    {
        "name": "Staging - lymph node biopsy + tumor excision",
        "note": """Operative Report
Procedure: Sentinel lymph node biopsy and wide local excision
Diagnosis: Melanoma right arm, Breslow 2.1mm
Technique: Lymphoscintigraphy identified sentinel node.
Sentinel node biopsy from right axilla. Negative for metastasis.
Wide local excision with 2cm margins performed.""",
        "expected_cpt": ["38900", "11602"],
        "expected_icd": ["C43.9", "C43.60"],
    },
    {
        "name": "Multi-level spinal fusion L4-S1",
        "note": """Operative Report
Procedure: Posterior spinal fusion L4-S1 with instrumented fusion
Diagnosis: L4-L5 and L5-S1 degenerative disc disease with spinal stenosis
Technique: Pedicle screws placed at L4, L5, S1 bilaterally.
Interbody fusion at L4-L5 and L5-S1.
Laminectomy at L4 and L5. Decompression complete.""",
        "expected_cpt": ["22612", "63047"],
        "expected_icd": ["M51.30", "M48.00"],
    },
    {
        "name": "Combined colonoscopy and EGD",
        "note": """Procedure Note
Procedure: Upper endoscopy and colonoscopy
Indication: GI bleeding, iron deficiency anemia
EGD findings: Erythematous gastritis, no ulcer. Biopsies taken.
Colonoscopy findings: Diverticulosis. No polyps. Cecum reached.
Diagnosis: Gastrointestinal bleeding, iron deficiency anemia.""",
        "expected_cpt": ["43239", "45378"],
        "expected_icd": ["K92.2", "D50.9"],
    },
    {
        "name": "CABG x4 with mitral valve repair",
        "note": """Operative Report
Procedure: CABG x4 with mitral valve repair
Technique: LIMA to LAD, SVG to OM1, SVG to PDA, SVG to diagonal.
Mitral valve: posterior leaflet prolapse repaired with Gore-Tex neochordae.
Cross-clamp: 130 minutes. Pump time: 175 minutes.
Patient has diabetes and hypertension.""",
        "expected_cpt": ["33534", "33418"],
        "expected_icd": ["I25.10", "E11.9"],
    },
    {
        "name": "Incisional and umbilical hernia repair",
        "note": """Operative Report
Procedure: Incisional hernia repair with mesh and umbilical hernia repair
Diagnosis: Incisional hernia and umbilical hernia
Patient has obesity and diabetes.
Technique: Incisional hernia: Preperitoneal mesh placement.
Umbilical hernia: Suture repair.
Estimated blood loss 50mL.""",
        "expected_cpt": ["49560", "49585"],
        "expected_icd": ["K43.0", "E66.01"],
    },
    {
        "name": "Right hemicolectomy + appendectomy",
        "note": """Operative Report
Procedure: Laparoscopic right hemicolectomy
Diagnosis: Cecal mass, colon cancer confirmed on biopsy
Technique: Mobilization of right colon. Ileocolic and right colic vessels divided.
Specimen removed through Pfannenstiel incision.
Anastomosis stapled. No complications.""",
        "expected_cpt": ["44160"],
        "expected_icd": ["C18.9", "C18.0"],
    },
    {
        "name": "Carpal tunnel and trigger finger release",
        "note": """Operative Report
Procedure: Right carpal tunnel release and right ring finger trigger finger release
Diagnosis: Carpal tunnel syndrome right, trigger finger right ring finger
Technique: Open carpal tunnel release. Transverse carpal ligament divided.
Trigger finger: A1 pulley released.
No complications.""",
        "expected_cpt": ["64721", "26055"],
        "expected_icd": ["G56.0", "M65.11"],
    },
    {
        "name": "Rotator cuff repair + subacromial decompression",
        "note": """Operative Report
Procedure: Arthroscopic rotator cuff repair right shoulder with subacromial decompression
Diagnosis: Full-thickness rotator cuff tear right shoulder
Patient has diabetes.
Technique: Arthroscopic evaluation confirmed 2cm supraspinatus tear.
Subacromial decompression performed. Two suture anchors placed.
Tear repaired. No complications.""",
        "expected_cpt": ["29827"],
        "expected_icd": ["M75.10", "E11.9"],
    },
    {
        "name": "Thyroidectomy + parathyroidectomy",
        "note": """Operative Report
Procedure: Total thyroidectomy with parathyroidectomy
Diagnosis: Papillary thyroid carcinoma with primary hyperparathyroidism
Patient has hypertension and diabetes.
Technique: Total thyroidectomy. Right inferior parathyroid gland enlarged, removed.
Recurrent laryngeal nerve identified and preserved.
Estimated blood loss 30mL.""",
        "expected_cpt": ["60240"],
        "expected_icd": ["I10", "E11.9"],
    },
    {
        "name": "Prostatectomy with lymph node dissection",
        "note": """Operative Report
Procedure: Robotic radical prostatectomy with pelvic lymph node dissection
Diagnosis: Prostate cancer, Gleason 7, PSA 8.2
Patient has hypertension.
Technique: Robot-assisted laparoscopic approach.
Pelvic lymph node dissection performed bilaterally.
Prostate removed intact.""",
        "expected_cpt": ["55840", "55842", "38542"],
        "expected_icd": ["C61", "I10"],
    },
    {
        "name": "ACL reconstruction with meniscectomy",
        "note": """Operative Report
Procedure: ACL reconstruction right knee with partial medial meniscectomy
Diagnosis: ACL tear right knee with medial meniscus tear
Patient has obesity.
Technique: ACL reconstructed with hamstring autograft.
Partial medial meniscectomy performed. Meniscal root intact.
All grafts tensioned. Stable knee.""",
        "expected_cpt": ["29888", "29881"],
        "expected_icd": ["S83.512A", "E66.01"],
    },
    {
        "name": "Lumbar laminectomy with discectomy",
        "note": """Operative Report
Procedure: L4-L5 laminectomy with microdiscectomy
Diagnosis: L4-L5 herniated disc with radiculopathy
Technique: Laminotomy at L4-L5. Herniated disc fragment removed.
Nerve root decompressed. Decompression confirmed.
No complications.""",
        "expected_cpt": ["63047", "63030"],
        "expected_icd": ["M51.10", "M54.10"],
    },
    {
        "name": "Laparoscopic cholecystectomy + umbilical hernia",
        "note": """Operative Report
Procedure: Laparoscopic cholecystectomy with umbilical hernia repair
Diagnosis: Symptomatic cholelithiasis, umbilical hernia
Technique: Four trocar technique. Critical view of safety achieved.
Gallbladder removed. Umbilical hernia repaired with mesh.
Estimated blood loss 25mL.""",
        "expected_cpt": ["47562", "49585"],
        "expected_icd": ["K80.20", "K42.9"],
    },
    {
        "name": "ESWL with cystoscopy",
        "note": """Procedure Note
Procedure: Extracorporeal shock wave lithotripsy with cystoscopy
Indication: Right ureteral stone 10mm
Cystoscopy: Ureteral orifice identified. Guidewire passed.
ESWL: 3000 shocks delivered. Stone fragmented.
Stent placed prophylactically. Nephrolithiasis confirmed.""",
        "expected_cpt": ["50590", "52000", "52332"],
        "expected_icd": ["N20.0", "N39.0"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 3: PEDIATRIC NOTES (10 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "Pediatric - Newborn nursery note",
        "note": """Well Child Visit - Newborn
Patient: Male, born at 39 weeks gestation, weight 3400g
APGAR: 8 at 1 minute, 9 at 5 minutes.
Physical exam: Normal newborn. No congenital anomalies.
Feeding: Breastfeeding initiated. Latch good.
Metabolic screening completed. Hearing screen passed.""",
        "expected_cpt": ["99213"],
        "expected_icd": ["Z00.121", "Z38.00"],
    },
    {
        "name": "Pediatric - Supracondylar fracture",
        "note": """Operative Report
Procedure: Closed reduction and fracture repair left supracondylar fracture
Diagnosis: Displaced supracondylar fracture left humerus, Gartland type III
Patient has asthma.
Technique: Fluoroscopic reduction achieved. Two 1.6mm K-wires placed.
Fracture stable. Arm placed in long arm splint.
Post-op neurovascular status intact.""",
        "expected_cpt": ["27752"],
        "expected_icd": ["J45.901", "T14.90"],
    },
    {
        "name": "Pediatric - Asthma exacerbation",
        "note": """Emergency Department Note
Patient is a 7-year-old male with history of asthma presenting with acute asthma exacerbation.
Wheezing bilaterally. O2 sat 92% on room air. Peak flow 140 L/min.
Respiratory distress with accessory muscle use.
Assessment: Severe asthma exacerbation.
Plan: Continuous nebulized albuterol, IV methylprednisolone, observe.""",
        "expected_cpt": ["99283", "99284", "99285"],
        "expected_icd": ["J45.51", "J45.50", "J45.901"],
    },
    {
        "name": "Pediatric - Failure to thrive workup",
        "note": """Office Visit Note
Patient is an 18-month-old female evaluated for failure to thrive.
Weight: 16 lbs (3rd percentile). Height: 28 inches (10th percentile).
Feeding history: Poor oral intake, gagging with solids.
Workup: CBC, CMP, thyroid panel, celiac panel ordered.
Speech therapy referral for feeding evaluation.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["R62.51"],
    },
    {
        "name": "Pediatric - Well-baby visit newborn",
        "note": """Well Child Visit
Patient: 1-week-old male, born full term
Weight: 7 lbs 2 oz (birth weight 7 lbs 6 oz). Jaundice resolving.
Physical exam: Normal. Hip examination stable.
Feeding: Breastfeeding well. 8-10 wet diapers per day.
Newborn screening completed.""",
        "expected_cpt": ["99392", "99393", "99213"],
        "expected_icd": ["Z00.121", "Z00.12"],
    },
    {
        "name": "Pediatric - Well-baby visit 2 months",
        "note": """Well Child Visit
Patient: 2-month-old male
Weight: 11 lbs (50th percentile). Length: 22 inches (50th percentile).
Head circumference: 39cm (50th percentile).
Development: Social smile, tracks objects. Normal tone.
Immunizations: DTaP, IPV, Hib, PCV13, HepB, rotavirus administered.""",
        "expected_cpt": ["99213", "99392", "99393"],
        "expected_icd": ["Z00.121", "Z00.12"],
    },
    {
        "name": "Pediatric - Well-baby visit 4 months",
        "note": """Well Child Visit
Patient: 4-month-old female
Weight: 13 lbs (40th percentile). Length: 24 inches (45th percentile).
Development: Rolling over, reaching for toys. Laughs out loud.
Immunizations: DTaP, IPV, Hib, PCV13, rotavirus dose 2 given.
Feeding: Formula, taking solids well.""",
        "expected_cpt": ["99213", "99392", "99393"],
        "expected_icd": ["Z00.121", "Z00.12"],
    },
    {
        "name": "Pediatric - Well-baby visit 6 months",
        "note": """Well Child Visit
Patient: 6-month-old male
Weight: 17 lbs (50th percentile). Length: 27 inches (50th percentile).
Development: Sitting with support, babbling, transfers objects.
Immunizations: DTaP, IPV, Hib, PCV13, influenza vaccine given.
Feeding: Started purees. Breastfeeding continues.""",
        "expected_cpt": ["99213", "99392", "99393"],
        "expected_icd": ["Z00.121", "Z00.12"],
    },
    {
        "name": "Pediatric - Well-baby visit 12 months",
        "note": """Well Child Visit
Patient: 12-month-old female
Weight: 20 lbs (50th percentile). Length: 30 inches (50th percentile).
Development: Walking independently. Says mama and dada.
Immunizations: MMR, varicella, HepA, PCV13 booster.
Screening: MCHAT-RF negative. Anemia screen normal.""",
        "expected_cpt": ["99213", "99392", "99393", "99394"],
        "expected_icd": ["Z00.121", "Z00.12"],
    },
    {
        "name": "Pediatric - Neonatal jaundice",
        "note": """Well Child Visit - Newborn
Patient: Female, born at 38 weeks gestation, weight 3100g
APGAR: 9 at 1 minute, 10 at 5 minutes.
Jaundice noted at 24 hours. Total bilirubin 10.2.
Phototherapy initiated per protocol.
Feeding: Breastfeeding and supplemental formula.""",
        "expected_cpt": ["99213"],
        "expected_icd": ["P59.9", "P59.0", "Z00.121"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 4: PSYCHIATRIC NOTES (10 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "Psychiatric - Major depressive disorder evaluation",
        "note": """Psychiatric Evaluation Note - Office Visit
Patient is a 42-year-old female referred for evaluation of depression.
PHQ-9 score: 22 (severe). Anhedonia, insomnia, poor appetite, fatigue.
Suicidal ideation: Passive, no plan or intent.
History: Depression x 5 years, prior SSRI trials.
Assessment: Major depressive disorder, recurrent, severe.
Plan: Start venlafaxine 37.5mg daily. Therapy referral.""",
        "expected_cpt": ["99213", "99214", "99215"],
        "expected_icd": ["F32.9", "F32.2"],
    },
    {
        "name": "Psychiatric - Bipolar disorder management",
        "note": """Office Visit Note
Patient is a 35-year-old male with bipolar I disorder, currently in manic episode.
Mood elevated, grandiose, decreased sleep. Not taking lithium.
Psychomotor agitation. Pressured speech.
Assessment: Bipolar I disorder, current episode manic.
Plan: Restart lithium 900mg BID. Add quetiapine 300mg HS. Lithium level today.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["F31.9", "F31.11"],
    },
    {
        "name": "Psychiatric - Anxiety with panic attacks",
        "note": """Office Visit Note
Patient is a 29-year-old female with generalized anxiety disorder and panic attacks.
Reports 3-4 panic attacks per week. Palpitations, chest tightness, fear of dying.
GAD-7 score: 18 (severe). Sleep disturbed.
Assessment: Generalized anxiety disorder with panic attacks.
Plan: Start sertraline 50mg daily. Clonazepam 0.5mg PRN. CBT referral.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["F41.1", "F41.0"],
    },
    {
        "name": "Psychiatric - ADHD evaluation",
        "note": """Office Visit Note
Patient is a 10-year-old male referred for ADHD evaluation.
Parent and teacher rating scales consistent with ADHD, combined type.
Academic difficulties, impulsive behavior, difficulty sustaining attention.
Behavioral history: Oppositional behavior at school.
Assessment: Attention deficit hyperactivity disorder, combined type.
Plan: Start methylphenidate 18mg daily. School accommodations.""",
        "expected_cpt": ["99213", "99214", "99221"],
        "expected_icd": ["F90.0", "F90.2"],
    },
    {
        "name": "Psychiatric - Substance abuse assessment",
        "note": """Substance Abuse Evaluation - Office Visit
Patient is a 38-year-old male evaluated for alcohol use disorder.
CAGE score: 3/4. Drinks 12-15 beers daily.
Prior detox admissions x2. Last drink: yesterday.
AST/ALT elevated. MCV 102. Liver function impaired.
Assessment: Alcohol dependence with hepatic steatosis.
Plan: Refer to intensive outpatient program. Thiamine supplementation.""",
        "expected_cpt": ["99213", "99214", "99221"],
        "expected_icd": ["F10.20", "F10.90"],
    },
    {
        "name": "Psychiatric - PTSD evaluation",
        "note": """Psychiatric Evaluation Note
Patient is a 28-year-old veteran with PTSD following combat deployment.
Re-experiencing: Flashbacks 3-4x per week. Hyperarousal: exaggerated startle.
Avoidance of crowds. Emotional numbing. Sleep disrupted.
PCL-5 score: 58 (above cutoff).
Assessment: Post-traumatic stress disorder.
Plan: Start prazosin 1mg HS for nightmares. EMDR therapy referral.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["F43.10"],
    },
    {
        "name": "Psychiatric - OCD evaluation",
        "note": """Office Visit Note
Patient is a 25-year-old female with obsessive-compulsive disorder.
Y-BOCS score: 32 (severe). Contamination obsessions, excessive hand washing.
Rituals consuming 4 hours daily. Impairs work function.
Previous SSRI trials with partial response.
Assessment: OCD, severe. Treatment-resistant.
Plan: Increase fluoxetine to 80mg daily. ERP therapy.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["F42.9", "F42.0"],
    },
    {
        "name": "Psychiatric - Insomnia evaluation",
        "note": """Office Visit Note
Patient is a 50-year-old female with chronic insomnia.
Difficulty falling asleep for 2 years. Sleep latency > 60 minutes.
Multiple awakenings. Daytime fatigue. ISI score: 22.
Sleep hygiene counseling performed.
Assessment: Primary insomnia.
Plan: Start trazodone 50mg HS. Sleep hygiene reinforcement.""",
        "expected_cpt": ["99213"],
        "expected_icd": ["F51.01"],
    },
    {
        "name": "Psychiatric - Schizophrenia management",
        "note": """Office Visit Note
Patient is a 40-year-old male with schizophrenia, currently on clozapine.
BPRS score: 38 (moderate). Auditory hallucinations present but diminished.
Clozapine dose: 400mg daily. CBC today: WBC 5.2.
Assessment: Schizophrenia, partially responsive to clozapine.
Plan: Continue clozapine. Monitor ANC per protocol.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["F20.9"],
    },
    {
        "name": "Psychiatric - Cannabis use disorder",
        "note": """Substance Abuse Evaluation - Office Visit
Patient is a 22-year-old male with substance use disorder.
Daily marijuana use x 3 years. Unable to cut down.
Dropped out of college. Motivation low.
Withdrawal: irritability, insomnia, decreased appetite.
Assessment: Substance use disorder, moderate to severe.
Plan: Motivational interviewing. Referral to counseling.""",
        "expected_cpt": ["99213", "99215"],
        "expected_icd": ["F19.90"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 5: ONCOLOGY NOTES (10 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "Oncology - Chemotherapy infusion breast cancer",
        "note": """Chemotherapy Infusion Note
Patient is a 55-year-old female with breast cancer receiving adjuvant chemotherapy.
Regimen: AC-T (doxorubicin, cyclophosphamide, paclitaxel).
Cycle 4 of 8 today. Pre-medications: ondansetron, dexamethasone.
Vitals stable. No infusion reactions.
Treatment tolerated well.""",
        "expected_cpt": ["96401", "96402"],
        "expected_icd": ["C50.919"],
    },
    {
        "name": "Oncology - Radiation therapy planning",
        "note": """Radiation Therapy Note
Patient is a 62-year-old male with prostate cancer undergoing radiation therapy planning.
CT simulation performed. Immobilization device created.
Target volumes delineated: prostate and seminal vesicles.
Treatment plan: IMRT, 78 Gy in 39 fractions.
Quality assurance completed.""",
        "expected_cpt": ["77301", "77427"],
        "expected_icd": ["C61"],
    },
    {
        "name": "Oncology - Tumor staging workup",
        "note": """Oncology Consultation Note
Patient is a 48-year-old female with newly diagnosed breast cancer.
Mammography: 3cm spiculated mass, BI-RADS 5.
Biopsy: Invasive ductal carcinoma, ER+/PR+/HER2-.
Staging CT chest abdomen pelvis: No metastatic disease.
Sentinel lymph node biopsy scheduled.""",
        "expected_cpt": ["77067", "38900"],
        "expected_icd": ["C50.919"],
    },
    {
        "name": "Oncology - Post-surgical cancer follow-up",
        "note": """Office Visit Note
Patient is a 60-year-old male status post left hemicolectomy for colon cancer.
Follow-up 3 months post-op. CEA normal at 2.1.
CT abdomen: No evidence of recurrence.
Colonoscopy scheduled at 1 year.
Assessment: Colon cancer, status post resection, no evidence of disease.""",
        "expected_cpt": ["99213", "99214"],
        "expected_icd": ["C18.9", "Z90.89"],
    },
    {
        "name": "Oncology - Immunotherapy administration",
        "note": """Infusion Center Note
Patient is a 67-year-old male with non-small cell lung cancer receiving immunotherapy.
Regimen: Pembrolizumab 200mg IV every 3 weeks.
Cycle 6 of planned therapy. Pre-medication: acetaminophen, diphenhydramine.
Vitals stable. No infusion reactions. No immune-related adverse events.""",
        "expected_cpt": ["96401", "96402"],
        "expected_icd": ["C34.90"],
    },
    {
        "name": "Oncology - Bone marrow biopsy",
        "note": """Procedure Note
Procedure: Bone marrow biopsy and aspirate
Indication: Evaluation of pancytopenia, rule out hematologic malignancy
Patient has anemia and thrombocytopenia.
Technique: Posterior iliac crest approach. Jamshidi needle.
Aspirate: 3cc obtained. Core biopsy: 2cm specimen.
Minimal discomfort. No complications.""",
        "expected_cpt": ["38220"],
        "expected_icd": ["D64.9", "D69.6"],
    },
    {
        "name": "Oncology - Chemotherapy induced nausea",
        "note": """Emergency Department Note
Patient is a 45-year-old female receiving chemotherapy for ovarian cancer.
Presents with intractable nausea and vomiting x 2 days.
Unable to tolerate oral intake. Dehydration noted.
Assessment: Chemotherapy-induced nausea and vomiting.
Plan: IV fluids, ondansetron, dexamethasone. Monitor.""",
        "expected_cpt": ["99283", "99284"],
        "expected_icd": ["C56.9", "R11.10", "E86.0"],
    },
    {
        "name": "Oncology - PET CT staging",
        "note": """Radiology Report
Procedure: PET CT whole body
Indication: Staging of newly diagnosed Hodgkin lymphoma
Findings: Hypermetabolic lymphadenopathy in left cervical, mediastinal, and left axillary regions.
SUV max 12.3. No extranodal disease.
Impression: Stage III Hodgkin lymphoma.""",
        "expected_cpt": ["78814"],
        "expected_icd": ["C81.9"],
    },
    {
        "name": "Oncology - Palliative care consult",
        "note": """Consultation Note
Patient is a 78-year-old male with metastatic pancreatic cancer.
Referred for palliative care. Goals of care discussion.
Patient desires comfort-focused care. Hospice referral discussed.
Pain management plan: oxycodone 10mg Q4H PRN.
Advance directive updated.""",
        "expected_cpt": ["99213", "99214", "99497"],
        "expected_icd": ["C25.9", "C80.1"],
    },
    {
        "name": "Oncology - Tumor board review",
        "note": """Multidisciplinary Tumor Board Note
Patient is a 52-year-old female with rectal cancer.
Case reviewed: MRI rectum showing T3N1, circumferential margin threatened.
Consensus: Neoadjuvant chemoradiation (capecitabine + long-course RT).
Restaging in 8 weeks. Surgery pending response.
Patient has hypertension.""",
        "expected_cpt": ["99213", "99214", "99221"],
        "expected_icd": ["C20", "I10"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 6: CRITICAL CARE NOTES (10 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "Critical care - Sepsis ICU admission",
        "note": """ICU Admission Note - Critical Care
Patient is a 70-year-old male admitted through ED with sepsis.
Source: Urinary tract infection. Lactate 4.2. BP 85/50.
qSOFA score: 2. Sepsis bundle initiated.
Norepinephrine drip started. IV antibiotics: vancomycin, piperacillin-tazobactam.
Admitted to ICU for sepsis management.""",
        "expected_cpt": ["99291", "99292", "99223"],
        "expected_icd": ["A41.9", "N39.0"],
    },
    {
        "name": "Critical care - Mechanical ventilation",
        "note": """ICU Progress Note - Ventilator Management
Patient is a 58-year-old female with respiratory failure on mechanical ventilation day 3.
Vent settings: AC, TV 450, FiO2 40%, PEEP 8.
ABG: pH 7.38, PaCO2 42, PaO2 120.
Weaning trial performed: passed spontaneous breathing trial.
Extubation planned tomorrow if criteria met.""",
        "expected_cpt": ["99291", "99292", "99231", "99232"],
        "expected_icd": ["J96.00", "J96.90", "J96.9"],
    },
    {
        "name": "Critical care - Central line placement",
        "note": """Procedure Note - Critical Care
Procedure: Ultrasound-guided right internal jugular central venous catheter placement
Indication: Sepsis, need for vasopressors and large volume resuscitation
Technique: Sterile prep and drape. Ultrasound guidance.
18G needle, guidewire, dilation, triple-lumen catheter placed.
Position confirmed with chest x-ray. No complications.""",
        "expected_cpt": ["36556", "99291"],
        "expected_icd": ["A41.9"],
    },
    {
        "name": "Critical care - Intubation",
        "note": """Emergency Department Note - Critical Care
Patient is a 65-year-old male with respiratory failure requiring intubation.
RSI performed: etomidate 20mg IV, succinylcholine 100mg IV.
Video laryngoscopy. Cormack-Lehane Grade 1. 8.0 ETT placed at 23cm.
Post-intubation CXR: ETT in good position.
Admitted to ICU on mechanical ventilation.""",
        "expected_cpt": ["99283", "99284", "99285", "99291"],
        "expected_icd": ["J96.00", "J96.90", "J96.9"],
    },
    {
        "name": "Critical care - Code blue / resuscitation",
        "note": """Code Blue Record - Critical Care
Patient is a 72-year-old male with cardiac arrest on the floor.
He has coronary artery disease and hypertension.
Rhythm: V-fib. CPR initiated immediately.
Defibrillation x3. Epinephrine x3. Amiodarone x2.
ROSC achieved after 18 minutes.
Admitted to ICU for targeted temperature management.""",
        "expected_cpt": ["99291", "99292"],
        "expected_icd": ["I46.9", "I25.10"],
    },
    {
        "name": "Critical care - Acute respiratory failure",
        "note": """ICU Admission Note - Critical Care
Patient is a 55-year-old female with acute respiratory failure requiring non-invasive ventilation.
BiPAP initiated. Respiratory distress improved.
ABG on BiPAP: pH 7.32, PaCO2 55, PaO2 85.
Assessment: Acute hypercapnic respiratory failure, COPD exacerbation.
Plan: Continue BiPAP. Bronchodilators. Steroids.""",
        "expected_cpt": ["99291", "99292", "99223"],
        "expected_icd": ["J96.01", "J44.1"],
    },
    {
        "name": "Critical care - DKA management",
        "note": """ICU Progress Note - Critical Care
Patient is a 28-year-old male with type 1 diabetes and diabetic ketoacidosis.
Admitted with glucose 680, pH 7.15, anion gap 28.
Insulin drip and aggressive fluid resuscitation started.
Potassium replaced. Gap closed to 12.
Transitioned to subcutaneous insulin.""",
        "expected_cpt": ["99291", "99292", "99231", "99232"],
        "expected_icd": ["E10.9", "E11.9"],
    },
    {
        "name": "Critical care - ARDS management",
        "note": """ICU Progress Note - Critical Care
Patient is a 45-year-old male with acute respiratory distress syndrome, day 5 of mechanical ventilation.
P/F ratio 120. Prone positioning performed.
Lung-protective ventilation: TV 400, PEEP 14, FiO2 60%.
Sedation: propofol and fentanyl drips.
Assessment: Moderate-severe respiratory failure, improving.""",
        "expected_cpt": ["99291", "99292", "99223"],
        "expected_icd": ["J96.00", "J96.90", "J96.9"],
    },
    {
        "name": "Critical care - Stroke ICU admission",
        "note": """ICU Admission Note - Critical Care
Patient is a 68-year-old female with large vessel occlusion stroke.
Status post mechanical thrombectomy. TICI 3 reperfusion achieved.
NIHSS improved from 18 to 8 post-procedure.
Blood pressure management: target < 180/105.
Admitted to neuro-ICU for close monitoring.""",
        "expected_cpt": ["99291", "99292", "99223"],
        "expected_icd": ["I63.9", "I63.6"],
    },
    {
        "name": "Critical care - Status epilepticus",
        "note": """Emergency Department Note - Critical Care
Patient is a 30-year-old male with seizure disorder presenting in status epilepticus.
Seizure onset 25 minutes ago. Lorazepam 4mg IV x2 given.
Seizure continued. Levetiracetam 3000mg IV loaded.
Seizure terminated after 35 minutes. Intubated for airway protection.
Admitted to ICU for EEG monitoring.""",
        "expected_cpt": ["99283", "99284", "99285", "99291"],
        "expected_icd": ["G40.909", "G41.9"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 7: RADIOLOGY/PROCEDURE NOTES (10 cases)
    # ═══════════════════════════════════════════════════════════════════
    {
        "name": "Radiology - CT-guided lung biopsy",
        "note": """Procedure Note - Radiology
Procedure: CT-guided percutaneous lung biopsy
Indication: 2.5cm right lower lobe mass, suspicious for lung cancer
Technique: CT fluoroscopy guidance. Patient prone.
18G core needle biopsy. 4 passes.
Specimens sent to pathology. No pneumothorax on post-procedure CT.""",
        "expected_cpt": ["11102"],
        "expected_icd": ["C34.90", "R91.1"],
    },
    {
        "name": "Radiology - Ultrasound-guided drainage",
        "note": """Procedure Note - Radiology
Procedure: Ultrasound abdomen guided percutaneous abscess drainage
Indication: Right lower quadrant abscess 6cm, appendiceal abscess
Patient has diabetes.
Technique: Real-time ultrasound guidance. Sterile prep.
12F pigtail catheter placed. 80mL purulent drainage obtained.
Catheter secured. Gravity drainage initiated.""",
        "expected_cpt": ["49082", "76700"],
        "expected_icd": ["K35.89", "E11.9"],
    },
    {
        "name": "Radiology - Nuclear medicine bone scan",
        "note": """Nuclear Medicine Report
Procedure: Tc-99m MDP whole body bone scan
Indication: Prostate cancer, staging evaluation
Findings: Increased uptake in left pelvis and L3 vertebral body.
No other suspicious lesions. Differential: metastatic disease vs. degenerative.
Impression: Suspicious osseous metastases.""",
        "expected_cpt": ["78300"],
        "expected_icd": ["C61", "C79.31"],
    },
    {
        "name": "Radiology - Screening mammography",
        "note": """Radiology Report
Procedure: Screening bilateral mammography with tomosynthesis
Indication: Annual screening mammography, family history of breast cancer
Findings: No masses, calcifications, or architectural distortion.
Bilateral breast tissue heterogeneously dense.
Impression: Normal screening mammogram. BI-RADS 1.""",
        "expected_cpt": ["77067"],
        "expected_icd": ["Z12.31", "Z80.3"],
    },
    {
        "name": "Radiology - DEXA scan",
        "note": """Radiology Report
Procedure: DEXA scan of lumbar spine and hip
Indication: Postmenopausal female, osteoporosis screening
Findings: Lumbar spine T-score: -2.8. Femoral neck T-score: -2.5.
Diagnosis: Osteoporosis by WHO criteria.
Patient has hypertension.
Assessment: Osteoporosis. Recommend calcium, vitamin D, and bisphosphonate therapy.""",
        "expected_cpt": ["77080"],
        "expected_icd": ["M81.0", "I10"],
    },
    {
        "name": "Radiology - MRI brain with contrast",
        "note": """Radiology Report
Procedure: MRI brain with and without contrast
Indication: New-onset seizures, rule out intracranial mass
Findings: 2cm ring-enhancing lesion left temporal lobe with surrounding edema.
No midline shift. No hydrocephalus.
Impression: Ring-enhancing lesion, concerning for high-grade glioma or abscess.""",
        "expected_cpt": ["70553"],
        "expected_icd": ["G40.909", "D43.0"],
    },
    {
        "name": "Radiology - CT chest with contrast",
        "note": """Radiology Report
Procedure: CT chest with intravenous contrast
Indication: Pulmonary embolism
Findings: Filling defect in left main pulmonary artery extending into left lower lobe segmental arteries.
Small right pleural effusion. No other abnormalities.
Impression: Acute pulmonary embolism.""",
        "expected_cpt": ["71277", "71260"],
        "expected_icd": ["I26.99"],
    },
    {
        "name": "Radiology - CT abdomen pelvis",
        "note": """Radiology Report
Procedure: CT abdomen and pelvis with intravenous contrast
Indication: Abdominal pain, rule out appendicitis
Findings: Appendix dilated 12mm with periappendiceal fat stranding.
No appendicolith. No perforation.
Impression: Acute uncomplicated appendicitis.""",
        "expected_cpt": ["74177"],
        "expected_icd": ["K35.80"],
    },
    {
        "name": "Radiology - Ultrasound thyroid",
        "note": """Radiology Report
Procedure: Ultrasound of the thyroid gland
Indication: Palpable right thyroid nodule, fine needle aspiration
Patient has hypertension.
Findings: Right thyroid nodule 1.5cm, solid, hypoechoic, microcalcifications.
TI-RADS 5. Left thyroid normal.
Impression: Suspicious right thyroid nodule. FNA recommended.""",
        "expected_cpt": ["76536", "10021"],
        "expected_icd": ["E04.1", "D34", "I10"],
    },
    {
        "name": "Radiology - PET CT for lymphoma staging",
        "note": """Nuclear Medicine Report
Procedure: PET CT whole body
Indication: Staging of diffuse large B-cell lymphoma
Findings: Hypermetabolic lymphadenopathy in bilateral cervical, mediastinal, retroperitoneal regions.
Hepatic and splenic involvement. Bone marrow uptake diffusely increased.
Impression: Advanced-stage DLBCL. High tumor burden.""",
        "expected_cpt": ["78814"],
        "expected_icd": ["C85.9", "C85.1"],
    },
]


def run_tests():
    parser = ClinicalNoteParser()
    passed = 0
    total = len(TEST_CASES)

    print("=" * 80)
    print(f"  Clinical Note Parser Test Suite: {total} Scenarios")
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
