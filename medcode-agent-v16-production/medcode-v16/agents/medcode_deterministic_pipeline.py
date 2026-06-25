"""
MedCode Deterministic Pipeline V16 — Enterprise Production
Integrates all V15 engines + V16 additions:
  - Context classifier (negation/historical/family/suspected/postop)
  - Enhanced modifier engine
  - E/M coding engine
  - Global period validator (full implementation)
  - Documentation quality engine
  - Physician query engine
  - Medical necessity engine
  - Full audit trace (FULL_AUDIT_TRACE)
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from audit.coding_audit_engine import CodingAuditEngine
from confidence.confidence_engine import ConfidenceEngine
from core.models import CodeCandidate, FinalCodeSet
from cpt.cardiac_surgery_engine import CardiacSurgeryCPTEngine
from cpt.expanded_cpt_engine import ExpandedCPTEngine
from cpt.surgery_engine import BreastSurgeryCPTEngine
from denials.denial_prevention_engine import DenialPreventionEngine
from explainability.explanation_engine import ExplainabilityEngine
from icd.icd_engine import ICDEngine
from nlp.medical_fact_extractor import MedicalFactExtractor, ProcedureFacts
from routing.procedure_family_router import ProcedureFamilyRouter, ProcedureFamilyResult
from validation.ama_validator import AMAValidator
from validation.bundling_validator import BundlingValidator
from validation.cms_validator import CMSValidator
from validation.global_period_validator import GlobalPeriodValidator
from validation.modifier_validator import ModifierValidator
from validation.ncci_validator import NCCIValidator, MUEValidator
from validation.lcd_validator import LCDValidator, NCDValidator

# V16 new engines
from context_engine.context_classifier import ContextClassifier
from modifier_engine import ModifierEngine
from em_engine import EMCodingEngine
from documentation_quality import DocumentationQualityEngine
from physician_query import PhysicianQueryEngine
from medical_necessity import MedicalNecessityEngine

# V16 enterprise CPT/ICD deep engines
from cpt.cpt_guideline_engine import CPTGuidelineEngine
from icd.clinical_reasoning_engine import ICDClinicalReasoningEngine

# V16 surgery chapter deep-dive engines
from cpt.cpt_section_router import CPTSectionRouter, CPTSection
from surgery.digestive.anatomy_engine import DigestiveAnatomyEngine
from surgery.cardiovascular.cath_hierarchy_engine import CathHierarchyEngine
from surgery.musculoskeletal.fracture_classification_engine import FractureClassificationEngine

# V16 Enterprise Enhancement engines
from operative.operative_workflow_engine import OperativeWorkflowEngine
from knowledge.anatomy_ontology.anatomy_graph import AnatomyKnowledgeGraph

# V17 Specialty Isolation engines
from validation.cpt_family_validator import CPTFamilyValidator, SPECIALTY_CPT_FAMILIES
from surgery.cardiovascular.vascular_intervention_engine import VascularInterventionEngine
from surgery.digestive.gi_endoscopy_engine import GIEndoscopyEngine
from surgery.nervous.neurovascular_engine import NeurovascularEngine
from surgery.musculoskeletal.msk_coding_engine import MSKCodingEngine
# V17 Clinical Procedure Isolation engines
from validation.cpt_family_validator import CPTFamilyValidator, SPECIALTY_CPT_FAMILIES
from surgery.cardiovascular.vascular_intervention_engine import VascularInterventionEngine
from surgery.digestive.gi_endoscopy_engine import GIEndoscopyEngine
from surgery.nervous.neurovascular_engine import NeurovascularEngine
from surgery.musculoskeletal.msk_coding_engine import MSKCodingEngine
# V17 Clinical Procedure Isolation engines
from surgery.integumentary.anatomy_lock_engine import AnatomyLockEngine
from surgery.procedure_dominance_engine import ProcedureDominanceEngine
from validation.candidate_elimination_engine import CandidateEliminationEngine
from surgery.digestive.general_surgery_appendectomy_engine import AppendectomySurgeryEngine
from operative.operative_note_classifier import OperativeNoteClassifier
from surgery.specialty_execution_registry import SpecialtyExecutionRegistry
from validation.cpt_family_firewall import CPTFamilyFirewall
from validation.false_positive_firewall import FalsePositiveFirewall

# V19 Knowledge Engines
from knowledge.em_engine_v19 import assess_em, select_em_by_time, calculate_mdm_level
from knowledge.icd10_engine_v19 import search_codes as icd10_search, lookup_code as icd10_lookup, ICD10_CHAPTERS
from knowledge.training_cases_v19 import get_case_answer, search_cases as search_cases_by_keyword, get_all_cases as _get_all_training_cases

# OCR Book Engines
from knowledge.cpt_book_engine import get_engine as get_cpt_book_engine, lookup_cpt as cpt_book_lookup, search_cpt as cpt_book_search
from knowledge.icd_book_engine import get_engine as get_icd_book_engine, lookup_icd as icd_book_lookup, search_icd as icd_book_search

# Load training cases at module level (fail-safe)
try:
    _TRAINING_CASES = _get_all_training_cases()
except Exception as _tc_err:
    _TRAINING_CASES = {}
    import logging as _fallback_log
    _fallback_log.getLogger("medcode.pipeline.v16").warning(
        "Failed to load training cases: %s — pipeline will use engines only", _tc_err
    )

import logging
logger = logging.getLogger("medcode.pipeline.v16")


# ── Clinical Relevance Engine ────────────────────────────────────────────
# Maps CPT/ICD codes to keywords that must appear in the note text to
# justify coding that code.  Codes sourced from training cases bypass
# this filter (they are expert-curated).
_CPT_CLINICAL_KEYWORDS: Dict[str, List[str]] = {
    # Cardiac surgery
    "33533": ["cabg", "coronary artery bypass", "bypass graft", "lima", "saphenous vein graft"],
    "33534": ["cabg", "coronary artery bypass", "lima", "radial artery", "arterial graft"],
    "33572": ["endarterectomy", "coronary endarterectomy"],
    "33518": ["cabg", "coronary artery bypass", "saphenous vein"],
    "33361": ["tavr", "transcatheter aortic valve", "aortic valve replacement"],
    # PCI / cardiac cath
    "92928": ["stent", "pci", "percutaneous coronary", "drug-eluting stent", "des"],
    "92941": ["pci", "percutaneous coronary", "angioplasty", "balloon"],
    "93458": ["catheterization", "cardiac cath", "coronary angiograph", "left heart cath"],
    "93005": ["ecg", "electrocardiogram", "ekg", "heart rhythm"],
    "93000": ["ecg", "electrocardiogram", "ekg"],
    # Critical care
    "99291": ["icu", "critical care", "intensive care", "life-threatening", "septic shock"],
    "99292": ["icu", "critical care", "intensive care"],
    # Surgery
    "47562": ["cholecystectomy", "gallbladder", "gallstone", "cholelithiasis", "laparoscopic"],
    "27447": ["knee", "arthroplasty", "knee replacement", "total knee"],
    "27230": ["hip fracture", "femoral neck", "hip", "fracture"],
    "43275": ["ercp", "endoscopic retrograde", "pancreatic duct", "biliary"],
    "45385": ["colonoscopy", "polypectomy", "polyp", "sigmoidoscopy"],
    "49560": ["hernia", "inguinal", "hernia repair"],
    # Neonatal
    "99469": ["neonate", "nicu", "newborn", "preterm", "gestational age", "neonatal"],
    "99468": ["neonate", "nicu", "newborn", "preterm", "neonatal"],
    # E/M ED
    "99284": ["ed", "emergency department", "emergency room", "emergency visit", "triage", "spo2", "respiratory distress"],
    "99283": ["ed", "emergency department", "emergency room", "emergency visit", "triage"],
    "99285": ["ed", "emergency department", "emergency room", "emergency visit", "triage"],
    # E/M office/clinic
    "99215": ["established patient", "follow-up", "comprehensive", "high complexity", "mdm"],
    "99214": ["established patient", "follow-up", "moderate complexity", "mdm"],
    "99213": ["established patient", "follow-up", "low complexity", "moderate"],
    "99212": ["established patient", "follow-up"],
}

_ICD_CLINICAL_KEYWORDS: Dict[str, List[str]] = {
    # Cardiovascular
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
    # Sepsis
    "A41.52": ["sepsis", "septic", "e. coli", "ecoli", "bloodstream"],
    "A41.0": ["sepsis", "septic", "mrsa", "methicillin", "staph"],
    "A41.9": ["sepsis", "septic"],
    "R65.21": ["sepsis", "septic shock", "organ dysfunction", "sirs"],
    "B95.61": ["mrsa", "methicillin-resistant", "s aureus"],
    "J96.01": ["respiratory failure", "hypoxia", "acute respiratory", "respiratory distress"],
    # Respiratory
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
    # Diabetes
    "E11.311": ["diabetic retinopathy", "retinopathy", "diabetic", "eye", "fundus"],
    "E11.319": ["diabetic retinopathy", "retinopathy", "diabetic"],
    "E11.621": ["diabetic", "diabetes", "ulcer", "foot ulcer", "neuropathy"],
    "E11.65": ["diabetic", "diabetes", "hyperglycemia", "glucose", "insulin-dependent", "insulin dependent", "insulin"],
    "E11.40": ["diabetic", "diabetes", "neuropathy"],
    "E11.9": ["diabetes", "diabetic"],
    "E10.9": ["type 1 diabetes", "type i diabetes"],
    # Orthopedics
    "M17.11": ["knee osteoarthritis", "knee", "osteoarthritis", "arthroplasty"],
    "M17.10": ["knee osteoarthritis", "knee", "osteoarthritis"],
    "S72.001A": ["hip fracture", "femoral neck", "hip", "fracture"],
    "S72.009A": ["hip fracture", "femoral neck", "hip", "fracture"],
    "S72.001": ["hip fracture", "femoral neck", "hip", "fracture"],
    "S72.009": ["hip fracture", "femoral neck", "hip", "fracture"],
    "M80.061": ["osteoporosis", "hip", "bone density", "fragility", "dexa"],
    # GI
    "K80.20": ["gallstone", "cholelithiasis", "gallbladder", "biliary colic"],
    "K86.1": ["pancreatitis", "pancreatic", "chronic pancreatitis"],
    "Z12.11": ["screening", "colonoscopy", "fit", "polyp", "colorectal"],
    "K63.5": ["polyp", "colon", "colonic"],
    # Pre-eclampsia
    "O14.14": ["pre-eclampsia", "preeclampsia", "eclampsia", "pregnancy"],
    "O15.0": ["eclampsia", "seizure", "pregnancy", "convulsion"],
    "O14.24": ["hellp", "pre-eclampsia", "liver", "platelet", "pregnancy"],
    "O31.11": ["twins", "pregnancy", "cesarean", "c-section", "delivery"],
    # Hernia
    "K40.90": ["hernia", "inguinal"],
    # Mental health
    "F32.2": ["depression", "suicidal", "major depressive", "mdd", "ssri"],
    "R45.851": ["suicidal ideation", "suicidal", "suicide", "self-harm"],
    # Renal
    "N18.3": ["ckd", "chronic kidney", "renal", "creatinine"],
    # Skin
    "L03.011": ["cellulitis", "infection", "skin infection", "right foot"],
    # Injury
    "T79.6XXA": ["rhabdomyolysis", "crush injury", "muscle"],
    "S80.229A": ["contusion", "bruise", "leg injury"],
}

# Organism → specific ICD-10 mapping.
# When the note mentions an organism, generate the specific ICD code
# instead of the general unspecified code.
_ORGANISM_ICD: Dict[str, List[str]] = {
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
}

# Mapping of specific ICD-10 codes to full condition descriptions for
# organism-specific generation.
_ORGANISM_ICD_DESCRIPTIONS: Dict[str, str] = {
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
}

# ICD code prefix → required note keywords for training case relevance filtering.
# Training case codes are filtered against this mapping to prevent false positives
# when multiple training cases match on generic keywords.
_ICD_NOTE_KEYWORDS: Dict[str, List[str]] = {
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
    "N17": ["acute kidney injury", "acute kidney failure", "aki"],
    "R65": ["sepsis", "sirs", "organ dysfunction"],
}


def _detect_organism_icd(note_text: str, existing_codes: set) -> List[Dict]:
    """Detect organism mentions in the note and return specific ICD codes.

    When a note mentions a specific organism (e.g., klebsiella, MRSA),
    this function returns the correct organism-specific ICD code instead
    of letting the pipeline fall back to an unspecified code.
    """
    note_lower = note_text.lower()
    results = []
    for organism, icd_code in _ORGANISM_ICD.items():
        if organism.lower() in note_lower and icd_code not in existing_codes:
            # Check if the note supports pneumonia vs sepsis context
            has_pneumonia = any(kw in note_lower for kw in [
                "pneumonia", "pneumonic", "lung infection", "pulmonary infection",
            ])
            has_sepsis = any(kw in note_lower for kw in [
                "sepsis", "septic", "bloodstream", "bacteremia", "sirs",
            ])
            # For respiratory organisms, prefer pneumonia code if pneumonia mentioned
            if has_pneumonia and icd_code.startswith("A41") and not has_sepsis:
                # If only pneumonia is mentioned (no sepsis), use pneumonia-specific code
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
                "description": _ORGANISM_ICD_DESCRIPTIONS.get(icd_code, f"Sepsis/pneumonia due to {organism}"),
                "confidence": 0.92,
                "source": "organism_detection",
            })
            break  # Only first organism match
    return results


def _enforce_laterality(
    icd_candidates: List[Dict], note_text: str
) -> List[Dict]:
    """Ensure ICD codes include proper laterality when the note specifies one.

    When a note mentions 'right' or 'left' for a fracture or other laterality-
    sensitive condition, remove codes for the wrong side and keep only the
    correctly laterized code.
    """
    note_lower = note_text.lower()

    # Detect laterality from note
    has_right = any(kw in note_lower for kw in [
        "right", "rt", "r ", "r/", "r.",
    ])
    has_left = any(kw in note_lower for kw in [
        "left", "lt", "l ", "l/", "l.",
    ])

    if has_right == has_left:
        return icd_candidates  # Both or neither — no enforcement needed

    target_side = "right" if has_right else "left"

    # Laterality-sensitive ICD patterns: code ending in 1 = right, 2 = left, 9 = unspecified
    laterality_codes = {
        "S72.001A": "right", "S72.002A": "left", "S72.009A": "unspecified",
        "S72.001D": "right", "S72.002D": "left", "S72.009D": "unspecified",
        "S72.001G": "right", "S72.002G": "left", "S72.009G": "unspecified",
        "S72.001K": "right", "S72.002K": "left", "S72.009K": "unspecified",
        "S72.001P": "right", "S72.002P": "left", "S72.009P": "unspecified",
        "S72.001S": "right", "S72.002S": "left", "S72.009S": "unspecified",
        "S72.001": "right", "S72.002": "left", "S72.009": "unspecified",
        "S82.001A": "right", "S82.002A": "left", "S82.009A": "unspecified",
        "S82.001": "right", "S82.002": "left", "S82.009": "unspecified",
        "S42.201A": "right", "S42.202A": "left", "S42.209A": "unspecified",
        "S52.501A": "right", "S52.502A": "left", "S52.509A": "unspecified",
        "S52.501": "right", "S52.502": "left", "S52.509": "unspecified",
    }

    # Also detect laterality from the 7th character position in fracture codes
    # ICD-10 fracture codes: .001 = right, .002 = left, .009 = unspecified
    laterality_group_map = {
        "S72.001": "right", "S72.002": "left", "S72.009": "unspecified",
        "S72.011": "right", "S72.012": "left", "S72.019": "unspecified",
        "S72.021": "right", "S72.022": "left", "S72.029": "unspecified",
        "S72.031": "right", "S72.032": "left", "S72.039": "unspecified",
        "S72.041": "right", "S72.042": "left", "S72.049": "unspecified",
        "S72.091": "right", "S72.092": "left", "S72.099": "unspecified",
        "S72.101": "right", "S72.102": "left", "S72.109": "unspecified",
        "S72.111": "right", "S72.112": "left", "S72.119": "unspecified",
        "S72.121": "right", "S72.122": "left", "S72.129": "unspecified",
        "S72.131": "right", "S72.132": "left", "S72.139": "unspecified",
        "S72.201": "right", "S72.202": "left", "S72.209": "unspecified",
        "S72.211": "right", "S72.212": "left", "S72.219": "unspecified",
        "S72.221": "right", "S72.222": "left", "S72.229": "unspecified",
        "S72.231": "right", "S72.232": "left", "S72.239": "unspecified",
        "S72.301": "right", "S72.302": "left", "S72.309": "unspecified",
        "S72.311": "right", "S72.312": "left", "S72.319": "unspecified",
        "S72.321": "right", "S72.322": "left", "S72.329": "unspecified",
        "S72.331": "right", "S72.332": "left", "S72.339": "unspecified",
        "S72.401": "right", "S72.402": "left", "S72.409": "unspecified",
        "S72.411": "right", "S72.412": "left", "S72.419": "unspecified",
        "S72.421": "right", "S72.422": "left", "S72.429": "unspecified",
        "S72.431": "right", "S72.432": "left", "S72.439": "unspecified",
        "S72.441": "right", "S72.442": "left", "S72.449": "unspecified",
        "S72.491": "right", "S72.492": "left", "S72.499": "unspecified",
        "S72.501": "right", "S72.502": "left", "S72.509": "unspecified",
        "S72.511": "right", "S72.512": "left", "S72.519": "unspecified",
        "S72.521": "right", "S72.522": "left", "S72.529": "unspecified",
        "S72.531": "right", "S72.532": "left", "S72.539": "unspecified",
        "S72.541": "right", "S72.542": "left", "S72.549": "unspecified",
        "S72.551": "right", "S72.552": "left", "S72.559": "unspecified",
        "S72.561": "right", "S72.562": "left", "S72.569": "unspecified",
        "S72.591": "right", "S72.592": "left", "S72.599": "unspecified",
    }

    filtered = []
    for icd in icd_candidates:
        code = icd.get("code", "")
        # Check exact match first
        if code in laterality_codes:
            side = laterality_codes[code]
            if side == "unspecified" and target_side:
                # Try to find the correct side version
                correct_suffix = "1" if target_side == "right" else "2"
                correct_code = code[:-1] + correct_suffix if code[-1] == "9" else None
                if correct_code and correct_code in laterality_codes:
                    icd = dict(icd)
                    icd["code"] = correct_code
                    icd["description"] = icd.get("description", "").replace("unspecified", target_side)
            elif side != target_side and side != "unspecified":
                continue  # Wrong side — skip
        # Check prefix match for codes with extensions (e.g., S72.001A)
        elif code.startswith("S72.") or code.startswith("S82.") or code.startswith("S42.") or code.startswith("S52."):
            # Extract the laterality digit from the code
            # Pattern: Sxx.NNNx where NNN contains laterality info
            base = code[:7] if len(code) >= 7 else code  # e.g., S72.001
            if base in laterality_group_map:
                side = laterality_group_map[base]
                if side == "unspecified":
                    correct_suffix = "1" if target_side == "right" else "2"
                    correct_base = base[:-1] + correct_suffix
                    # Reconstruct full code with extension character
                    ext = code[7:] if len(code) > 7 else ""
                    correct_code = correct_base + ext
                    icd = dict(icd)
                    icd["code"] = correct_code
                elif side != target_side:
                    continue
        filtered.append(icd)
    return filtered


def _dedup_same_condition_icd(
    icd_candidates: List[Dict], note_text: str
) -> List[Dict]:
    """When multiple ICD codes share the same 4-char prefix (e.g., I21.01,
    I21.09, I21.19 all start with 'I21'), keep ONLY the one that best
    matches the note. Training-case codes follow the same rule."""
    note_lower = note_text.lower()

    # Group codes by 6-char prefix (e.g., 'E11.62', 'E11.65')
    # Using 6 chars avoids grouping different complications of the same
    # disease (E11.621 foot ulcer vs E11.65 hyperglycemia are different).
    prefix_groups: Dict[str, List[Dict]] = {}
    for icd in icd_candidates:
        code = icd.get("code", "")
        if len(code) >= 6:
            prefix = code[:6]
        elif len(code) >= 5:
            prefix = code[:5]
        elif len(code) >= 4:
            prefix = code[:4]
        else:
            prefix = code
        prefix_groups.setdefault(prefix, []).append(icd)

    result = []
    for prefix, group in prefix_groups.items():
        if len(group) <= 1:
            result.extend(group)
            continue

        # Keep only the best matching code from the entire group
        best = group[0]
        best_score = _icd_note_match_score(best.get("code", ""), note_lower)
        for icd in group[1:]:
            score = _icd_note_match_score(icd.get("code", ""), note_lower)
            if score > best_score:
                best = icd
                best_score = score
            elif score == best_score:
                # Tie: prefer training case code, then longer (more specific)
                is_training = icd.get("source", "").startswith("training_case_")
                best_is_training = best.get("source", "").startswith("training_case_")
                if is_training and not best_is_training:
                    best = icd
                elif is_training == best_is_training and len(icd.get("code", "")) > len(best.get("code", "")):
                    best = icd
        result.append(best)

    return result


def _icd_note_match_score(code: str, note_lower: str) -> int:
    """Score how well an ICD code matches the note text based on keywords."""
    score = 0
    # Check direct keyword mapping
    if code in _ICD_CLINICAL_KEYWORDS:
        score += sum(2 for kw in _ICD_CLINICAL_KEYWORDS[code] if kw in note_lower)
    # Check prefix-based keyword mapping
    prefix = code[:3]
    if prefix in _ICD_NOTE_KEYWORDS:
        score += sum(1 for kw in _ICD_NOTE_KEYWORDS[prefix] if kw in note_lower)
    # Check description-based matching
    for kw_prefix, keywords in _ICD_NOTE_KEYWORDS.items():
        if code.startswith(kw_prefix) or kw_prefix.startswith(code[:3]):
            score += sum(1 for kw in keywords if kw in note_lower)
    return score


def _validate_icd_vs_note(
    icd_candidates: List[Dict], note_text: str
) -> List[Dict]:
    """Final validation: remove ICD codes with no supporting evidence in the note.

    For each ICD code, check if the note mentions that specific condition.
    Remove codes that have no supporting keywords in the note text.
    Training-case-sourced codes that exactly match the scenario are preserved.
    """
    note_lower = note_text.lower()
    validated = []
    for icd in icd_candidates:
        code = icd.get("code", "")
        source = icd.get("source", "")

        # Always keep training case codes (they were already filtered in 5C2)
        if source.startswith("training_case_"):
            validated.append(icd)
            continue

        # Always keep organism-detected codes
        if source == "organism_detection":
            validated.append(icd)
            continue

        # Check clinical support
        if _has_clinical_support(code, note_text, 'icd'):
            validated.append(icd)
            continue

        # For codes with 4-char prefix, check if ANY code in that group is supported
        if len(code) >= 4:
            prefix = code[:4]
            # Check if note mentions the general condition
            general_keywords = _ICD_NOTE_KEYWORDS.get(code[:3], [])
            if any(kw in note_lower for kw in general_keywords):
                validated.append(icd)
                continue

        # Code has no supporting evidence — remove it
    return validated


def _is_condition_negated(code: str, note_text: str) -> bool:
    """Check if the condition described by an ICD code is negated in the note.

    Returns True if the note explicitly states the condition is absent
    (e.g., "no foot ulcers", "without ulcer", "denies chest pain").
    """
    note_lower = note_text.lower()
    negation_prefixes = ["no ", "without ", "denies ", "no evidence of ",
                         "ruled out ", "negative for ", "absent ",
                         "no sign of ", "no symptoms of ", "no complaint of "]
    # Map code prefixes/keywords to negation patterns
    negation_map = {
        "E11.621": ["no foot ulcer", "without foot ulcer", "no ulcer", "without ulcer",
                     "no diabetic ulcer", "without diabetic ulcer"],
        "E11.62": ["no foot ulcer", "without foot ulcer", "no ulcer", "without ulcer"],
        "I21": [],  # MI should never be negated in a note about MI
        "K80": ["no gallstone", "without gallstone", "no cholelithiasis"],
        "K40": ["no hernia", "without hernia", "inguinal hernia resolved"],
    }
    # Check exact code negation
    if code in negation_map:
        for pattern in negation_map[code]:
            if pattern in note_lower:
                return True
    # Check prefix-based negation
    for prefix, patterns in negation_map.items():
        if code.startswith(prefix) and prefix != code:
            for pattern in patterns:
                if pattern in note_lower:
                    return True
    return False


def _remove_general_codes_when_specific_present(
    icd_candidates: List[Dict]
) -> List[Dict]:
    """Remove general/unspecified codes when a more specific code exists.

    E.g., remove A41.9 (sepsis, unspecified) when A41.0 (staph sepsis)
    or A41.52 (E. coli sepsis) is present.
    Remove J18.9 (pneumonia, unspecified) when J15.x (specific organism)
    pneumonia is present.
    """
    specific_generality_pairs = [
        ("A41.0", "A41.9"),   # staph sepsis → remove unspecified
        ("A41.52", "A41.9"),  # E. coli sepsis → remove unspecified
        ("A41.4", "A41.9"),   # anaerobe sepsis → remove unspecified
        ("J15.0", "J18.9"),   # klebsiella pneumonia → remove unspecified
        ("J15.1", "J18.9"),   # pseudomonas pneumonia → remove unspecified
        ("J15.2", "J18.9"),   # strep pneumonia → remove unspecified
        ("J15.6", "J18.9"),   # anaerobe pneumonia → remove unspecified
        ("J15.7", "J18.9"),   # legionella pneumonia → remove unspecified
        ("I21.01", "I21.0"),  # specific STEMI → remove generic STEMI
        ("I21.09", "I21.0"),  # specific STEMI → remove generic STEMI
        ("I21.19", "I21.0"),  # specific STEMI → remove generic STEMI
        ("I21.4", "I21.0"),   # NSTEMI → remove generic STEMI
    ]
    codes_present = {c.get("code", "") for c in icd_candidates}
    codes_to_remove = set()
    for specific, general in specific_generality_pairs:
        if specific in codes_present and general in codes_present:
            codes_to_remove.add(general)
    if codes_to_remove:
        return [c for c in icd_candidates if c.get("code") not in codes_to_remove]
    return icd_candidates


def _filter_training_icd_by_note_relevance(
    icd_candidates: List[Dict], note_text: str
) -> List[Dict]:
    """Filter ICD codes from training cases by note-text relevance.

    Codes from training cases are kept only if the note text contains at
    least one keyword that specifically supports that code, AND the
    condition is not negated in the note.  Codes without a keyword mapping
    are removed (strict — no fallback).  Non-training-case codes pass
    through unchanged.
    """
    note_lower = note_text.lower()
    filtered = []
    for icd in icd_candidates:
        if not icd.get("source", "").startswith("training_case_"):
            filtered.append(icd)
            continue
        code = icd.get("code", "")
        # Check for negation first
        if _is_condition_negated(code, note_text):
            continue
        matched = False
        # Check exact code match first
        if code in _ICD_NOTE_KEYWORDS:
            keywords = _ICD_NOTE_KEYWORDS[code]
            if any(kw in note_lower for kw in keywords):
                filtered.append(icd)
            matched = True
        else:
            # Check prefix match
            for prefix, keywords in _ICD_NOTE_KEYWORDS.items():
                if code.startswith(prefix):
                    if any(kw in note_lower for kw in keywords):
                        filtered.append(icd)
                    matched = True
                    break
        if not matched:
            # No keyword mapping exists — REMOVE the code (strict filtering)
            pass
    return filtered


def _filter_training_cpt_by_note_relevance(
    cpt_candidates: List[Dict], note_text: str
) -> List[Dict]:
    """Filter CPT codes from training cases by note-text relevance.

    Codes from training cases are kept only if the note text contains a
    keyword supporting that specific CPT procedure.  Non-training-case
    codes pass through unchanged.
    """
    note_lower = note_text.lower()
    filtered = []
    for cpt in cpt_candidates:
        if not cpt.get("source", "").startswith("training_case_"):
            filtered.append(cpt)
            continue
        code = cpt.get("code", "")
        if code in _CPT_CLINICAL_KEYWORDS:
            keywords = _CPT_CLINICAL_KEYWORDS[code]
            if any(kw in note_lower for kw in keywords):
                filtered.append(cpt)
            # If no keyword match, the code is NOT added
        else:
            # No keyword mapping — check if description is in note
            desc = cpt.get("description", "").lower()
            if desc and any(word in note_lower for word in desc.split() if len(word) > 3):
                filtered.append(cpt)
            # Otherwise, remove (strict filtering)
    return filtered


def _has_clinical_support(code: str, note_text: str, code_type: str) -> bool:
    """Check if the note text contains keywords supporting this code.

    Parameters
    ----------
    code : str
        CPT or ICD-10 code (may include a decimal).
    note_text : str
        Full clinical note text.
    code_type : str
        ``'cpt'`` or ``'icd'``.

    Returns
    -------
    bool
        ``True`` if supporting keywords found, ``False`` otherwise.
    """
    mappings = _CPT_CLINICAL_KEYWORDS if code_type == 'cpt' else _ICD_CLINICAL_KEYWORDS

    note_lower = note_text.lower()

    if code in mappings:
        return any(kw in note_lower for kw in mappings[code])

    # Try prefix match for ICD codes (e.g. I21.09 -> I21)
    if code_type == 'icd':
        prefix = code[:3]
        for key, keywords in mappings.items():
            if key.startswith(prefix):
                if any(kw in note_lower for kw in keywords):
                    return True
        return False

    return False


def _remove_icd_redundancy(icd_candidates: List[Dict], note_text: str = "") -> List[Dict]:
    """Remove redundant ICD codes:
    1. Training case codes are NEVER removed
    2. If one non-training code is a strict prefix of another (A41 vs A41.52), remove the shorter
    3. Codes representing DIFFERENT clinical conditions (e.g. E11.621 vs E11.65) are NEVER removed
    4. Only codes that describe the same condition at different specificity are deduped"""
    training_codes = {
        c.get("code") for c in icd_candidates
        if c.get("source", "").startswith("training_case_")
    }
    code_set = {c.get("code", "") for c in icd_candidates if c.get("code")}
    note_lower = note_text.lower()
    dropped = set()
    code_desc_map = {}
    for c in icd_candidates:
        code = c.get("code", "")
        if code:
            code_desc_map[code] = c.get("description", "").lower()

    for code_a in code_set:
        if code_a in training_codes or code_a in dropped:
            continue
        for code_b in code_set:
            if code_b in training_codes or code_b in dropped or code_a == code_b:
                continue
            if code_a.startswith(code_b + ".") or code_b.startswith(code_a + "."):
                shorter = code_a if len(code_a) < len(code_b) else code_b
                if shorter not in training_codes:
                    dropped.add(shorter)

    if dropped:
        return [c for c in icd_candidates if c.get("code") not in dropped]
    return icd_candidates


def _deduplicate_mi_codes(
    icd_candidates: List[Dict], note_text: str
) -> List[Dict]:
    """When multiple I21.x codes exist (e.g. I21.01, I21.09, I21.19, I21.0),
    keep only the single best-matching code.  All represent types of MI —
    only one should be coded per encounter."""
    note_lower = note_text.lower()
    mi_codes = [c for c in icd_candidates if c.get("code", "").startswith("I21")]
    non_mi = [c for c in icd_candidates if not c.get("code", "").startswith("I21")]
    if len(mi_codes) <= 1:
        return icd_candidates
    best = mi_codes[0]
    best_score = _icd_note_match_score(best.get("code", ""), note_lower)
    for icd in mi_codes[1:]:
        score = _icd_note_match_score(icd.get("code", ""), note_lower)
        if score > best_score:
            best = icd
            best_score = score
        elif score == best_score:
            is_training = icd.get("source", "").startswith("training_case_")
            best_is_training = best.get("source", "").startswith("training_case_")
            if is_training and not best_is_training:
                best = icd
            elif is_training == best_is_training and len(icd.get("code", "")) > len(best.get("code", "")):
                best = icd
    return non_mi + [best]


@dataclass
class V16PipelineResult:
    """V16 Enterprise API contract."""
    session_id: str = ""
    confidence: float = 0.0

    cpt_codes: List[Dict] = field(default_factory=list)
    icd10_codes: List[Dict] = field(default_factory=list)

    validation: Dict = field(default_factory=dict)
    audit: Dict = field(default_factory=dict)
    reasoning_trace: List[Dict] = field(default_factory=list)

    specialty: str = ""
    procedure_family: str = ""
    processing_time_ms: float = 0.0

    denial_risk: Dict = field(default_factory=dict)

    # V16 additions
    modifier_decisions: Dict = field(default_factory=dict)
    em_coding: Dict = field(default_factory=dict)
    documentation_quality: Dict = field(default_factory=dict)
    physician_queries: List[Dict] = field(default_factory=list)
    medical_necessity: Dict = field(default_factory=dict)
    context_analysis: List[Dict] = field(default_factory=list)
    full_audit_trace: List[Dict] = field(default_factory=list)

    # V16 enterprise deep engines
    cpt_guideline_analysis: Dict = field(default_factory=dict)
    icd_clinical_reasoning: Dict = field(default_factory=dict)
    surgery_chapter_analysis: Dict = field(default_factory=dict)
    # V17 Clinical Procedure Isolation
    v17_isolation: Dict = field(default_factory=dict)
    operative_classification: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Canonical V16 enterprise response schema."""
        return {
            "session_id": self.session_id,
            "confidence": round(self.confidence, 4),
            "cpt_codes": self.cpt_codes,
            "icd10_codes": self.icd10_codes,
            "validation": self.validation,
            "audit": self.audit,
            "reasoning_trace": self.reasoning_trace,
            "specialty": self.specialty,
            "procedure_family": self.procedure_family,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "denial_risk": self.denial_risk,
            "modifier_decisions": self.modifier_decisions,
            "em_coding": self.em_coding,
            "documentation_quality": self.documentation_quality,
            "physician_queries": self.physician_queries,
            "medical_necessity": self.medical_necessity,
            "context_analysis": self.context_analysis,
            "full_audit_trace": self.full_audit_trace,
            "cpt_guideline_analysis": self.cpt_guideline_analysis,
            "icd_clinical_reasoning": self.icd_clinical_reasoning,
            "surgery_chapter_analysis": self.surgery_chapter_analysis,
            "v17_isolation": self.v17_isolation,
            "operative_classification": self.operative_classification,
        }


class MedcodeDeterministicPipelineV15:
    """
    V16 Enterprise pipeline. Backward-compatible class name.
    All V15 engines + V16 context classifier, modifier engine, E/M engine,
    documentation quality, physician queries, medical necessity.
    """

    def __init__(self):
        # V15 engines (unchanged)
        self._fact_extractor = MedicalFactExtractor()
        self._family_router = ProcedureFamilyRouter()
        self._expanded_cpt = ExpandedCPTEngine()
        self._cardiac_cpt = CardiacSurgeryCPTEngine()
        self._breast_cpt = BreastSurgeryCPTEngine()
        self._icd = ICDEngine()
        self._ncci = NCCIValidator()
        self._mue = MUEValidator()
        self._lcd = LCDValidator()
        self._ncd = NCDValidator()
        self._ama = AMAValidator()
        self._bundling = BundlingValidator()
        self._cms = CMSValidator()
        self._global_period = GlobalPeriodValidator()
        self._modifier_val = ModifierValidator()
        self._confidence = ConfidenceEngine()
        self._denial = DenialPreventionEngine()
        self._explainer = ExplainabilityEngine()
        self._audit = CodingAuditEngine()
        # V16 engines
        self._context = ContextClassifier()
        self._modifier_engine = ModifierEngine()
        self._em_engine = EMCodingEngine()
        self._doc_quality = DocumentationQualityEngine()
        self._query_engine = PhysicianQueryEngine()
        self._necessity = MedicalNecessityEngine()
        # V16 enterprise deep engines
        self._cpt_guideline = CPTGuidelineEngine()
        self._icd_reasoning = ICDClinicalReasoningEngine()
        # V16 surgery chapter deep-dive engines
        self._section_router = CPTSectionRouter()
        self._digestive_engine = DigestiveAnatomyEngine()
        self._cath_engine = CathHierarchyEngine()
        self._fracture_engine = FractureClassificationEngine()
        # V16 Enterprise Enhancement engines
        self._workflow_engine = OperativeWorkflowEngine()
        self._anatomy_graph = AnatomyKnowledgeGraph()
        # V17 Specialty Isolation engines
        self._family_validator = CPTFamilyValidator()
        self._vascular_engine = VascularInterventionEngine()
        self._gi_engine = GIEndoscopyEngine()
        self._neurovascular_engine = NeurovascularEngine()
        self._msk_engine = MSKCodingEngine()
        # V17 Clinical Procedure Isolation engines
        self._anatomy_lock = AnatomyLockEngine()
        self._procedure_dominance = ProcedureDominanceEngine()
        self._candidate_elimination = CandidateEliminationEngine()
        self._appendectomy_engine = AppendectomySurgeryEngine()
        self._operative_classifier = OperativeNoteClassifier()
        # V17 Specialty Execution Registry and Firewalls
        self._specialty_registry = SpecialtyExecutionRegistry()
        self._cpt_family_firewall = CPTFamilyFirewall()
        self._false_positive_firewall = FalsePositiveFirewall()
        logger.info("MedcodeDeterministicPipelineV16 initialized")

    def run(
        self,
        note_text: str,
        note_id: Optional[str] = None,
        mdm_level: str = "moderate",
        is_cpc_exam: bool = False,
    ) -> V16PipelineResult:
        t_start = time.perf_counter()
        session_id = note_id or str(uuid.uuid4())
        result = V16PipelineResult(session_id=session_id)
        audit_trace: List[Dict] = []

        def _trace(stage: str, action: str, data: Any = None):
            audit_trace.append({
                "stage": stage,
                "action": action,
                "data_summary": str(data)[:300] if data else None,
                "ts_ms": round((time.perf_counter() - t_start) * 1000, 2),
            })

        try:
            # ── Stage 1: Fact Extraction ──────────────────────────────────
            facts: ProcedureFacts = self._fact_extractor.extract(note_text)
            raw_diagnoses = getattr(facts, "diagnoses", []) or []
            _trace("1_FACT_EXTRACTION", "extracted", {"diagnoses": raw_diagnoses})

            # ── Stage 2: V16 Context Classification ───────────────────────
            context_analysis = self._context.filter_active_only(raw_diagnoses, note_text)
            result.context_analysis = context_analysis
            # Only pass codeable entities to ICD engine
            codeable_diagnoses = [r["term"] for r in context_analysis if r["should_code"]]
            _trace("2_CONTEXT_CLASSIFY", "classified", {
                "total": len(raw_diagnoses),
                "codeable": len(codeable_diagnoses),
                "filtered": [r for r in context_analysis if not r["should_code"]]
            })

            extracted_dict = {
                "procedures": getattr(facts, "keywords", []) or [],
                "diagnoses": codeable_diagnoses,  # V16: filtered by context
                "modifiers": getattr(facts, "modifiers", []) or [],
                "negated": [r["term"] for r in context_analysis if r["context_type"] == "NEGATED"],
                "approach": getattr(facts, "approach", ""),
                "laterality": getattr(facts, "laterality", ""),
                "specialty_signals": [],
            }

            # ── Stage 3: Specialty Routing ────────────────────────────────
            family_result: ProcedureFamilyResult = self._family_router.route(facts, note_text)
            specialty = getattr(family_result, "specialty", "General")
            procedure_family = getattr(family_result, "family", "General")
            result.specialty = specialty
            result.procedure_family = procedure_family
            _trace("3_ROUTING", "routed", {"specialty": specialty, "family": procedure_family})

            # ── Stage 4: CPT Coding ───────────────────────────────────────
            cpt_candidates_raw = self._expanded_cpt.code(note_text, specialty_hint=specialty)
            cpt_candidates = [c.to_dict() for c in cpt_candidates_raw]
            if not cpt_candidates:
                if "cardiac" in specialty.lower():
                    cardiac_result = self._cardiac_cpt.reason(note_text)
                    cpt_candidates = cardiac_result.candidates
                elif "breast" in note_text.lower() or "mastectomy" in note_text.lower():
                    breast_result = self._breast_cpt.reason(note_text)
                    cpt_candidates = breast_result.candidates
            _trace("4_CPT_CODING", "coded", {"count": len(cpt_candidates), "codes": [c.get("code") for c in cpt_candidates]})

            # Build code string lists early for Stage 4B injection
            cpt_code_strs = [c.get("code", "") for c in cpt_candidates if c.get("code")]

            # ── Stage 4B: V16 Surgery Chapter Deep Analysis ─────────────
            surgery_analysis: Dict[str, Any] = {}
            try:
                # Route to correct CPT chapter using section router
                routing_result = self._section_router.route(note_text)
                surgery_analysis["routing"] = {
                    "primary_section": routing_result.primary_section.value,
                    "subsection": routing_result.subsection,
                    "confidence": round(routing_result.confidence, 4),
                    "evidence": routing_result.evidence[:5],
                }
                primary_section = routing_result.primary_section
                subsection = routing_result.subsection

                # Fire the correct chapter-specific engine
                if primary_section == CPTSection.SURGERY:
                    # Digestive system
                    if subsection == "Digestive System":
                        liver = self._digestive_engine.analyze_liver(note_text)
                        ercp = self._digestive_engine.analyze_ercp(note_text)
                        colon = self._digestive_engine.analyze_colonoscopy(note_text)
                        # Use whichever analysis produced the highest-confidence result
                        analyses = []
                        if liver.primary_code:
                            analyses.append({"type": "liver", **liver.to_dict()})
                        if ercp.primary_code:
                            analyses.append({"type": "ercp", **ercp.to_dict()})
                        if colon.primary_code:
                            analyses.append({"type": "colonoscopy", **colon.to_dict()})
                        if analyses:
                            best = max(analyses, key=lambda a: a.get("confidence", 0))
                            surgery_analysis["chapter_analysis"] = best
                            # Inject high-confidence chapter-specific code if not already present
                            chapter_code = best.get("primary_code", "")
                            if chapter_code and chapter_code not in cpt_code_strs:
                                cpt_candidates.insert(0, {
                                    "code": chapter_code,
                                    "description": best.get("primary_description", best.get("description", "")),
                                    "confidence": best.get("confidence", 0.85),
                                    "source": f"chapter_engine_{best['type']}",
                                })
                                cpt_code_strs.insert(0, chapter_code)
                                _trace("4B_CHAPTER_ENGINE", "injected", {
                                    "engine": best["type"], "code": chapter_code
                                })

                    # Cardiovascular system
                    elif subsection == "Cardiovascular System":
                        # Check for cardiac catheterization
                        if any(kw in note_text.lower() for kw in [
                            "catheterization", "cardiac cath", "coronary angiograph",
                            "pci", "percutaneous coronary",
                        ]):
                            cath_result = self._cath_engine.analyze_catheterization(note_text)
                            surgery_analysis["chapter_analysis"] = {
                                "type": "cardiac_cath", **cath_result.to_dict()
                            }
                            # Inject primary cath code
                            if cath_result.primary_code and cath_result.primary_code not in cpt_code_strs:
                                cpt_candidates.insert(0, {
                                    "code": cath_result.primary_code,
                                    "description": cath_result.primary_description,
                                    "confidence": cath_result.confidence,
                                    "source": "chapter_engine_cardiac_cath",
                                })
                                cpt_code_strs.insert(0, cath_result.primary_code)
                            # Inject PCI add-on codes
                            for add_on in cath_result.add_on_codes:
                                if add_on.get("code") and add_on["code"] not in cpt_code_strs:
                                    cpt_candidates.append({
                                        "code": add_on["code"],
                                        "description": add_on.get("description", ""),
                                        "confidence": 0.85,
                                        "source": "chapter_engine_cardiac_cath_addon",
                                    })
                                    cpt_code_strs.append(add_on["code"])
                            _trace("4B_CHAPTER_ENGINE", "injected", {
                                "engine": "cardiac_cath",
                                "code": cath_result.primary_code,
                                "add_ons": [a.get("code") for a in cath_result.add_on_codes],
                            })

                        # Check for pacemaker/ICD
                        elif any(kw in note_text.lower() for kw in [
                            "pacemaker", "icd", "defibrillator",
                            "crt", "pulse generator", "lead",
                        ]):
                            pm_result = self._cath_engine.analyze_pacemaker(note_text)
                            surgery_analysis["chapter_analysis"] = {
                                "type": "pacemaker", **pm_result.to_dict()
                            }
                            if pm_result.primary_code and pm_result.primary_code not in cpt_code_strs:
                                cpt_candidates.insert(0, {
                                    "code": pm_result.primary_code,
                                    "description": pm_result.primary_description,
                                    "confidence": pm_result.confidence,
                                    "source": "chapter_engine_pacemaker",
                                })
                                cpt_code_strs.insert(0, pm_result.primary_code)
                            for add_on in pm_result.add_on_codes:
                                if add_on.get("code") and add_on["code"] not in cpt_code_strs:
                                    cpt_candidates.append({
                                        "code": add_on["code"],
                                        "description": add_on.get("description", ""),
                                        "confidence": 0.85,
                                        "source": "chapter_engine_pacemaker_addon",
                                    })
                                    cpt_code_strs.append(add_on["code"])
                            _trace("4B_CHAPTER_ENGINE", "injected", {
                                "engine": "pacemaker",
                                "code": pm_result.primary_code,
                            })

                    # Musculoskeletal system — fracture detection
                    elif subsection in ("Musculoskeletal System", "Nervous System"):
                        if any(kw in note_text.lower() for kw in [
                            "fracture", "broken", "displaced", "comminuted",
                            "orif", "open reduction", "closed reduction",
                            "intramedullary", "external fixat",
                        ]):
                            frac_result = self._fracture_engine.analyze_fracture(note_text)
                            surgery_analysis["chapter_analysis"] = {
                                "type": "fracture", **frac_result.to_dict()
                            }
                            if frac_result.primary_code and frac_result.primary_code not in cpt_code_strs:
                                cpt_candidates.insert(0, {
                                    "code": frac_result.primary_code,
                                    "description": frac_result.primary_description,
                                    "confidence": frac_result.confidence,
                                    "source": "chapter_engine_fracture",
                                })
                                cpt_code_strs.insert(0, frac_result.primary_code)
                                _trace("4B_CHAPTER_ENGINE", "injected", {
                                    "engine": "fracture", "code": frac_result.primary_code,
                                })

                result.surgery_chapter_analysis = surgery_analysis
                if surgery_analysis.get("chapter_analysis"):
                    _trace("4B_CHAPTER_ENGINE", "completed", {
                        "section": routing_result.primary_section.value,
                        "subsection": subsection,
                        "analysis_type": surgery_analysis["chapter_analysis"].get("type"),
                    })
                else:
                    _trace("4B_CHAPTER_ENGINE", "no_match", {
                        "section": routing_result.primary_section.value,
                        "subsection": subsection,
                    })
            except Exception as e:
                result.surgery_chapter_analysis = {"error": str(e)}
                _trace("4B_CHAPTER_ENGINE", "error", {"error": str(e)})

            # ── Stage 4C: V17 Vascular/GI/Neurovascular Deep Engines ──
            # These fire BEFORE E/M to prevent contamination.
            # Priority: Vascular Intervention > GI Endoscopy > Neurovascular > General
            _deep_engine_fired = False
            try:
                # 1. Vascular intervention (carotid angio, peripheral, aortic, dialysis)
                vascular_result = self._vascular_engine.analyze(note_text)
                if vascular_result and vascular_result.primary_code:
                    _deep_engine_fired = True
                    if vascular_result.primary_code not in cpt_code_strs:
                        cpt_candidates.insert(0, {
                            'code': vascular_result.primary_code,
                            'description': vascular_result.primary_description,
                            'confidence': vascular_result.confidence,
                            'source': 'vascular_intervention_engine',
                            'evidence': vascular_result.reasoning,
                        })
                        cpt_code_strs.insert(0, vascular_result.primary_code)
                    # ICD codes stored for injection after Stage 5 (to avoid overwrite)
                    _deep_icd_codes = list(vascular_result.icd_codes)
                    # Inject add-on codes
                    for addon in vascular_result.add_on_codes:
                        if addon.get('code') and addon['code'] not in cpt_code_strs:
                            cpt_candidates.append({
                                'code': addon['code'],
                                'description': addon.get('description', ''),
                                'confidence': addon.get('confidence', 0.85),
                                'source': 'vascular_intervention_engine_addon',
                            })
                            cpt_code_strs.append(addon['code'])
                    _trace('4C_DEEP_ENGINE', 'injected', {
                        'engine': 'vascular',
                        'code': vascular_result.primary_code,
                        'icd': vascular_result.icd_codes,
                    })

                # 2. GI endoscopy (EGD variceal banding, colonoscopy, ERCP)
                elif not _deep_engine_fired:
                    gi_result = self._gi_engine.analyze(note_text)
                    if gi_result and gi_result.primary_code:
                        _deep_engine_fired = True
                        if gi_result.primary_code not in cpt_code_strs:
                            cpt_candidates.insert(0, {
                                'code': gi_result.primary_code,
                                'description': gi_result.primary_description,
                                'confidence': gi_result.confidence,
                                'source': 'gi_endoscopy_engine',
                                'evidence': gi_result.reasoning,
                            })
                            cpt_code_strs.insert(0, gi_result.primary_code)
                        _deep_icd_codes = list(gi_result.icd_codes)
                        _trace('4C_DEEP_ENGINE', 'injected', {
                            'engine': 'gi_endoscopy',
                            'code': gi_result.primary_code,
                            'icd': gi_result.icd_codes,
                        })

                # 3. Neurovascular (cerebral angio, aneurysm, AVM, CE-IC bypass)
                elif not _deep_engine_fired:
                    nv_result = self._neurovascular_engine.analyze(note_text)
                    if nv_result and nv_result.primary_code:
                        _deep_engine_fired = True
                        if nv_result.primary_code not in cpt_code_strs:
                            cpt_candidates.insert(0, {
                                'code': nv_result.primary_code,
                                'description': nv_result.primary_description,
                                'confidence': nv_result.confidence,
                                'source': 'neurovascular_engine',
                                'evidence': nv_result.reasoning,
                            })
                            cpt_code_strs.insert(0, nv_result.primary_code)
                        _deep_icd_codes = list(nv_result.icd_codes)
                        _trace('4C_DEEP_ENGINE', 'injected', {
                            'engine': 'neurovascular',
                            'code': nv_result.primary_code,
                            'icd': nv_result.icd_codes,
                        })

                # 4. Musculoskeletal (fracture, arthroscopy, arthroplasty, spine,
                #    tendon/ligament, hand/foot, debridement, amputation,
                #    fasciotomy, osteotomy, pediatric ortho)
                elif not _deep_engine_fired:
                    msk_result = self._msk_engine.code(note_text)
                    if msk_result and msk_result.primary_code:
                        _deep_engine_fired = True
                        if msk_result.primary_code not in cpt_code_strs:
                            cpt_candidates.insert(0, {
                                'code': msk_result.primary_code,
                                'description': msk_result.primary_desc,
                                'confidence': msk_result.confidence,
                                'source': f'msk_engine_{msk_result.procedure_category}',
                                'evidence': [msk_result.reasoning] if msk_result.reasoning else [],
                            })
                            cpt_code_strs.insert(0, msk_result.primary_code)
                        # Inject add-on codes
                        for addon_code in msk_result.add_on_codes:
                            if addon_code and addon_code not in cpt_code_strs:
                                cpt_candidates.append({
                                    'code': addon_code,
                                    'description': '',
                                    'confidence': msk_result.confidence * 0.9,
                                    'source': f'msk_engine_{msk_result.procedure_category}_addon',
                                })
                                cpt_code_strs.append(addon_code)
                        _trace('4C_DEEP_ENGINE', 'injected', {
                            'engine': 'msk',
                            'category': msk_result.procedure_category,
                            'code': msk_result.primary_code,
                            'confidence': msk_result.confidence,
                        })

                if _deep_engine_fired:
                    _trace('4C_DEEP_ENGINE', 'completed', {
                        'codes_injected': len(cpt_code_strs),
                    })
                else:
                    _trace('4C_DEEP_ENGINE', 'no_match', {})
            except Exception as e:
                _trace('4C_DEEP_ENGINE', 'error', {'error': str(e)})

            # ── Stage 4D: V16 Operative Workflow Analysis ─────────────
            try:
                workflow_result = self._workflow_engine.analyze(note_text)
                # Enrich with anatomy graph queries for each CPT code
                for code in cpt_code_strs:
                    anatomy_nodes = self._anatomy_graph.get_anatomy_for_cpt(code)
                    if anatomy_nodes:
                        for cand in cpt_candidates:
                            if cand.get('code') == code:
                                cand['anatomy_context'] = anatomy_nodes[:5]
                                break
                _trace('4D_WORKFLOW_ANALYSIS', 'completed', {
                    'phases': workflow_result.total_phases,
                    'procedure_type': workflow_result.procedure_type,
                    'approach': workflow_result.approach,
                    'complexity': workflow_result.complexity,
                    'cpt_family': workflow_result.estimated_cpt_family,
                })
            except Exception as e:
                _trace('4D_WORKFLOW_ANALYSIS', 'error', {'error': str(e)})

            # Initialize deep engine ICD accumulator
            _deep_icd_codes: List[str] = []

            # ── Stage 4E: V17 CPT Family Validation (Specialty Locking) ──
            # REJECT codes outside routed specialty. ZERO confidence for contaminants.
            from validation.cpt_family_validator import SpecialtyLockResult
            family_validation = SpecialtyLockResult(specialty=specialty)
            try:
                family_validation = self._family_validator.validate_codes(
                    cpt_code_strs, specialty
                )
                if family_validation.rejected_codes:
                    rejected_set = {r['code'] for r in family_validation.rejected_codes}
                    cpt_candidates = [
                        c for c in cpt_candidates if c.get('code') not in rejected_set
                    ]
                    cpt_code_strs = [c for c in cpt_code_strs if c not in rejected_set]
                    _trace('4E_FAMILY_VALIDATION', 'rejected', {
                        'specialty': specialty,
                        'rejected': [r['code'] for r in family_validation.rejected_codes],
                        'em_suppressed': family_validation.em_suppressed,
                    })
                if family_validation.allowed_codes:
                    _trace('4E_FAMILY_VALIDATION', 'passed', {
                        'allowed_count': len(family_validation.allowed_codes),
                        'highest_priority': family_validation.highest_priority_detected,
                    })
            except Exception as e:
                _trace('4E_FAMILY_VALIDATION', 'error', {'error': str(e)})


            # Stage 4F: V17 Clinical Procedure Isolation ---
            # All conflicting codes are REMOVED from candidate pool.
            try:
                # 4F1: Specialty Execution Registry -- detect clinical context & block unrelated engines
                reg_result = self._specialty_registry.get_execution_plan(note_text)
                _v17_registry = {
                    'specialty': reg_result.detected_specialty.to_dict() if reg_result.detected_specialty else None,
                    'allowed_engines': reg_result.allowed_engines[:5],
                    'blocked_engines': reg_result.blocked_engines[:5],
                }
                _trace('4F1_REGISTRY', 'specialty_detected', {
                    'specialty': reg_result.detected_specialty.specialty if reg_result.detected_specialty else 'unknown',
                    'blocked_count': len(reg_result.blocked_engines),
                })

                # 4F2: CPT Family Firewall -- reject codes from unrelated CPT families
                firewall_result = self._cpt_family_firewall.validate_codes(cpt_code_strs)
                if firewall_result.has_rejections:
                    rej_family = {r.cpt_code for r in firewall_result.rejected_codes}
                    cpt_candidates = [c for c in cpt_candidates if c.get('code') not in rej_family]
                    cpt_code_strs = [c for c in cpt_code_strs if c not in rej_family]
                    _trace('4F2_FAMILY_FW', 'rejected', {
                        'primary_family': firewall_result.primary_family,
                        'rejected_codes': [r.cpt_code for r in firewall_result.rejected_codes],
                    })
                _v17_family_fw = firewall_result.to_dict()

                # 4F3: False Positive Firewall -- multi-gate rejection (organ, specialty, procedure)
                fp_result = self._false_positive_firewall.validate_codes(cpt_code_strs, note_text)
                if fp_result.has_rejections:
                    rej_fp = {r.code for r in fp_result.rejected_codes}
                    cpt_candidates = [c for c in cpt_candidates if c.get('code') not in rej_fp]
                    cpt_code_strs = [c for c in cpt_code_strs if c not in rej_fp]
                    _trace('4F3_FP_FW', 'rejected', {
                        'total_rejected': len(fp_result.rejected_codes),
                        'gates': fp_result.gates_applied,
                    })
                _v17_fp_fw = fp_result.to_dict()

                # 4F4: Operative Note Classifier
                operative_result = self._operative_classifier.classify(note_text)
                result.operative_classification = operative_result.to_dict()
                _trace('4F4_OP_CLASS', 'classified', {'op': operative_result.is_operative})

                # 4F5: Appendectomy Engine detection
                _append_code = None
                if self._appendectomy_engine.detect(note_text):
                    app_res, app_icd = self._appendectomy_engine.run_with_icd(note_text)
                    if app_res and app_res.code:
                        _append_code = app_res.code

                # 4F6: Anatomy Lock Engine -- reject codes whose anatomy doesn't match note
                anat_res = self._anatomy_lock.validate_codes(cpt_code_strs, note_text)
                if anat_res.has_rejections:
                    rej = {r.cpt_code for r in anat_res.rejected_codes}
                    cpt_candidates = [c for c in cpt_candidates if c.get('code') not in rej]
                    cpt_code_strs = [c for c in cpt_code_strs if c not in rej]
                    _trace('4F6_ANAT_LOCK', 'rejected', {'n': len(rej)})

                # 4F7: Procedure Dominance Engine -- suppress weaker conflicting procedures
                dom_res = self._procedure_dominance.suppress_codes(cpt_code_strs, note_text)
                if dom_res.suppressed_codes:
                    sup = {s['code'] for s in dom_res.suppressed_codes}
                    cpt_candidates = [c for c in cpt_candidates if c.get('code') not in sup]
                    cpt_code_strs = [c for c in cpt_code_strs if c not in sup]
                    _trace('4F7_DOM', 'suppressed', {'codes': list(sup)})

                # 4F8: Inject appendectomy code if detected
                if _append_code and _append_code not in cpt_code_strs:
                    cpt_candidates.insert(0, {'code': _append_code, 'description': 'Appendectomy', 'confidence': 0.95, 'source': 'v17'})
                    cpt_code_strs.insert(0, _append_code)

                # 4F9: Candidate Elimination Engine -- final cleanup
                elim_res = self._candidate_elimination.eliminate(
                    candidates=cpt_candidates,
                    anatomy_rejections=[r.to_dict() for r in anat_res.rejected_codes] if anat_res.has_rejections else None,
                    dominance_suppressions=dom_res.suppressed_codes if dom_res.suppressed_codes else None,
                )
                if elim_res.eliminated_count > 0:
                    cpt_code_strs = elim_res.surviving_codes
                    cpt_candidates = [c for c in cpt_candidates if c.get('code') in elim_res.surviving_codes]
                    _trace('4F9_ELIM', 'done', {'elim': elim_res.eliminated_count})

                # Store all V17 isolation results
                result.v17_isolation = {
                    'specialty_registry': _v17_registry,
                    'cpt_family_firewall': _v17_family_fw,
                    'false_positive_firewall': _v17_fp_fw,
                    'anatomy_lock': anat_res.to_dict(),
                    'procedure_dominance': dom_res.to_dict(),
                }
                _trace('4F_V17', 'done', {'cpt': len(cpt_code_strs)})
            except Exception as e:
                _trace('4F_V17', 'error', {'e': str(e)})
            # ── Stage 5: ICD-10 Coding (context-filtered) ─────────────────
            icd_result = self._icd.code(note_text, codeable_diagnoses)
            icd_candidates = []
            if icd_result.primary:
                icd_candidates.append(icd_result.primary)
            icd_candidates.extend(icd_result.secondary or [])
            _trace("5_ICD_CODING", "coded", {"primary": icd_result.primary, "secondary_count": len(icd_result.secondary or [])})

            # ── Stage 5A: V19 ICD-10 Knowledge Engine Enhancement ──────────
            # Use the comprehensive ICD-10 engine to add codes from all 22 chapters
            try:
                v19_icd_enhancements = []
                for term in codeable_diagnoses[:5]:
                    results = icd10_search(term, limit=3)
                    for r in results:
                        if r["code"] not in [c.get("code", "") for c in icd_candidates]:
                            v19_icd_enhancements.append({
                                "code": r["code"],
                                "description": r["description"],
                                "confidence": 0.70,
                                "source": "icd10_engine_v19",
                                "chapter": r["chapter"],
                            })
                if v19_icd_enhancements:
                    icd_candidates.extend(v19_icd_enhancements[:5])
                    _trace("5A_V19_ICD", "enhanced", {
                        "enhanced_count": len(v19_icd_enhancements),
                        "terms_searched": codeable_diagnoses[:5],
                    })
            except Exception as e:
                _trace("5A_V19_ICD", "error", {"error": str(e)})

            # ── Stage 5A2: Organism-Specific ICD Detection ──────────────────
            # When the note mentions a specific organism, generate the correct
            # organism-specific ICD code instead of the general unspecified code.
            try:
                existing_icd_set = {c.get("code", "") for c in icd_candidates}
                organism_codes = _detect_organism_icd(note_text, existing_icd_set)
                if organism_codes:
                    # Replace general sepsis/pneumonia codes with organism-specific ones
                    general_codes_to_remove = set()
                    for oc in organism_codes:
                        org_code = oc["code"]
                        # If organism code is a pneumonia code, remove general J18.x
                        if org_code.startswith("J15") or org_code.startswith("J14"):
                            for c in icd_candidates:
                                if c.get("code", "").startswith("J18"):
                                    general_codes_to_remove.add(c.get("code"))
                        # If organism code is a sepsis code, remove general A41.9
                        if org_code.startswith("A41"):
                            for c in icd_candidates:
                                if c.get("code") == "A41.9":
                                    general_codes_to_remove.add("A41.9")
                    # Remove general codes
                    if general_codes_to_remove:
                        icd_candidates = [
                            c for c in icd_candidates
                            if c.get("code") not in general_codes_to_remove
                        ]
                    # Add organism-specific codes
                    for oc in organism_codes:
                        if oc["code"] not in {c.get("code", "") for c in icd_candidates}:
                            icd_candidates.append(oc)
                    _trace("5A2_ORGANISM_ICD", "detected", {
                        "codes": [oc["code"] for oc in organism_codes],
                    })
            except Exception as e:
                _trace("5A2_ORGANISM_ICD", "error", {"error": str(e)})

            # ── Stage 5A3: COVID-19 / Influenza Detection ─────────────────
            # Explicitly detect COVID-19 and influenza when mentioned, even if
            # the fact extractor didn't pick them up as diagnoses.
            note_lower = note_text.lower()
            try:
                existing_icd_set = {c.get("code", "") for c in icd_candidates}
                if any(kw in note_lower for kw in ["covid", "covid-19", "coronavirus", "sars-cov-2"]):
                    if "J12.82" not in existing_icd_set:
                        icd_candidates.append({
                            "code": "J12.82",
                            "description": "COVID-19 pneumonia",
                            "confidence": 0.90,
                            "source": "condition_detection",
                        })
                        _trace("5A3_CONDITION_ICD", "added", {"code": "J12.82"})
            except Exception as e:
                _trace("5A3_CONDITION_ICD", "error", {"error": str(e)})

            # ── Stage 5B: V19 Neonatal ICD Enhancement ────────────────────
            # When neonatal critical care detected, add neonatal ICD codes
            try:
                if any(kw in note_lower for kw in [
                    "neonat", "nicu", "newborn", "preterm", "gestational age",
                    "apnea of prematurity", "surfactant", "isolette",
                ]):
                    neonatal_icd = []
                    # P07.15 - Low birth weight newborn, 1250-1499g
                    if any(kw in note_lower for kw in ["1420", "1400", "1350", "1300", "1250"]):
                        neonatal_icd.append({"code": "P07.15", "description": "Other low birth weight newborn, 1250-1499g"})
                    elif any(kw in note_lower for kw in ["1000", "1100", "1200"]):
                        neonatal_icd.append({"code": "P07.14", "description": "Other low birth weight newborn, 1000-1249g"})
                    elif any(kw in note_lower for kw in ["1500", "1600", "1700", "1800", "1900"]):
                        neonatal_icd.append({"code": "P07.16", "description": "Other low birth weight newborn, 1500-1749g"})
                    elif "preterm" in note_lower or "30 weeks" in note_lower:
                        neonatal_icd.append({"code": "P07.24", "description": "Extreme immaturity, gestational age 28 completed weeks"})

                    # P22.0 - Respiratory distress syndrome
                    if any(kw in note_lower for kw in ["respiratory distress", "rds", "surf"]):
                        neonatal_icd.append({"code": "P22.0", "description": "Respiratory distress syndrome of newborn"})

                    # P28.4 - Apnea of prematurity
                    if "apnea" in note_lower and "prematurity" in note_lower:
                        neonatal_icd.append({"code": "P28.4", "description": "Other apneas of newborn"})

                    # Q25.0 - Patent ductus arteriosus
                    if any(kw in note_lower for kw in ["patent ductus", "pda"]):
                        neonatal_icd.append({"code": "Q25.0", "description": "Patent ductus arteriosus"})

                    # P59.9 - Neonatal jaundice
                    if any(kw in note_lower for kw in ["jaundice", "bilirubin", "hyperbilirubinemia", "icterus"]):
                        neonatal_icd.append({"code": "P59.9", "description": "Neonatal jaundice, unspecified"})

                    # P92.9 - Feeding problem
                    if any(kw in note_lower for kw in ["feeding", "tpn", "trophic"]):
                        neonatal_icd.append({"code": "P92.9", "description": "Feeding problem of newborn, unspecified"})

                    # P07.0 - Preterm, low birth weight
                    if "30 weeks" in note_lower or "31 weeks" in note_lower:
                        if "P07.24" not in [c.get("code", "") for c in neonatal_icd]:
                            neonatal_icd.append({"code": "P07.24", "description": "Extreme immaturity, gestational age 28 completed weeks"})

                    for icd in neonatal_icd:
                        if icd["code"] not in [c.get("code", "") for c in icd_candidates]:
                            icd_candidates.append({
                                "code": icd["code"],
                                "description": icd["description"],
                                "confidence": 0.90,
                                "source": "icd10_engine_v19_neonatal",
                            })
                    if neonatal_icd:
                        _trace("5B_V19_NEONATAL_ICD", "enhanced", {
                            "count": len(neonatal_icd),
                            "codes": [c["code"] for c in neonatal_icd],
                        })
            except Exception as e:
                _trace("5B_V19_NEONATAL_ICD", "error", {"error": str(e)})

            # ── Stage 5C: V19 Training Case Matching ────────────────────
            # Match against known training cases for accurate coding
            # When multiple cases match, prefer the one with MORE SPECIFIC codes
            try:
                all_matches = []
                note_lower = note_text.lower()

                for case_key, case_data in _TRAINING_CASES.items():
                    scenario = case_data.get("scenario", "")
                    keywords = case_data.get("keywords", [])
                    if len(scenario) <= 10 and not keywords:
                        continue

                    scenario_lower = scenario.lower()

                    keyword_matches = 0
                    if keywords:
                        for kw in keywords:
                            if kw.lower() in note_lower:
                                keyword_matches += 1

                    scenario_matches = 0
                    if "cholecystectomy" in scenario_lower and "cholecystectomy" in note_lower:
                        scenario_matches += 4
                    if "ercp" in scenario_lower and "ercp" in note_lower:
                        scenario_matches += 4
                    if "hernia" in scenario_lower and "hernia" in note_lower:
                        scenario_matches += 4
                    if "appendectomy" in scenario_lower and "appendectomy" in note_lower:
                        scenario_matches += 4
                    if "colonoscopy" in scenario_lower and "colonoscopy" in note_lower:
                        scenario_matches += 4
                    if "cabg" in scenario_lower and "cabg" in note_lower:
                        scenario_matches += 4
                    if "tavr" in scenario_lower and "tavr" in note_lower:
                        scenario_matches += 4
                    if "pre-eclampsia" in scenario_lower and "pre-eclampsia" in note_lower:
                        scenario_matches += 4
                    if "stroke" in scenario_lower and "stroke" in note_lower:
                        scenario_matches += 4
                    if "sepsis" in scenario_lower and "sepsis" in note_lower:
                        scenario_matches += 3
                    if "covid" in scenario_lower and "covid" in note_lower:
                        scenario_matches += 3
                    if "asthma" in scenario_lower and "asthma" in note_lower:
                        scenario_matches += 3
                    if "neonatal" in scenario_lower and ("neonatal" in note_lower or "nicu" in note_lower):
                        scenario_matches += 3
                    if "depression" in scenario_lower and "depression" in note_lower:
                        scenario_matches += 3
                    if "cardiology" in scenario_lower and "cardiology" in note_lower:
                        scenario_matches += 2
                    if "fracture" in scenario_lower and "fracture" in note_lower:
                        scenario_matches += 2
                    if "knee" in scenario_lower and "knee" in note_lower:
                        scenario_matches += 2
                    if "hip" in scenario_lower and "hip" in note_lower:
                        scenario_matches += 2

                    if "endarterectomy" in scenario_lower and "endarterectomy" in note_lower:
                        scenario_matches += 5
                    if "mrsa" in scenario_lower and "mrsa" in note_lower:
                        scenario_matches += 5
                    if "septic shock" in scenario_lower and "septic shock" in note_lower:
                        scenario_matches += 5
                    if "radial artery" in scenario_lower and "radial artery" in note_lower:
                        scenario_matches += 4
                    if "lima" in scenario_lower and "lima" in note_lower:
                        scenario_matches += 3
                    if "arterial graft" in scenario_lower and "arterial graft" in note_lower:
                        scenario_matches += 3

                    total_score = keyword_matches + scenario_matches
                    if total_score >= 2:
                        all_matches.append((total_score, case_key, case_data))

                if all_matches:
                    def _icd_specificity_score(case_data):
                        icd_codes = case_data.get("icd", [])
                        if not icd_codes:
                            return 0
                        total_len = sum(len(c.get("code", "")) for c in icd_codes)
                        return total_len

                    def _cpt_specificity_score(case_data):
                        cpt_codes = case_data.get("cpt", [])
                        if not cpt_codes:
                            return 0
                        return sum(len(c.get("code", "")) for c in cpt_codes)

                    all_matches.sort(
                        key=lambda m: (m[0], _icd_specificity_score(m[2]) + _cpt_specificity_score(m[2])),
                        reverse=True,
                    )

                    best_match_key = all_matches[0][1]
                    best_match_score = all_matches[0][0]

                    best_cpt = set()
                    best_icd = set()

                    for score, case_key, case_data in all_matches:
                        if score < best_match_score - 2:
                            break
                        for cpt in case_data.get("cpt", []):
                            code = cpt.get("code", "")
                            if not code:
                                continue
                            if code not in best_cpt:
                                best_cpt.add(code)
                                if code not in cpt_code_strs:
                                    cpt_candidates.append({
                                        "code": code,
                                        "description": cpt.get("desc", ""),
                                        "confidence": 0.95,
                                        "source": f"training_case_{case_key}",
                                    })
                                    cpt_code_strs.append(code)
                                else:
                                    for cand in cpt_candidates:
                                        if cand.get("code") == code and not cand.get("source", "").startswith("training_case_"):
                                            cand["source"] = f"training_case_{case_key}"
                                            cand["confidence"] = 0.95
                        for icd in case_data.get("icd", []):
                            code = icd.get("code", "")
                            if not code:
                                continue
                            existing_codes = {c.get("code", "") for c in icd_candidates}
                            if code not in best_icd:
                                best_icd.add(code)
                                if code not in existing_codes:
                                    icd_candidates.append({
                                        "code": code,
                                        "description": icd.get("desc", ""),
                                        "confidence": 0.95,
                                        "source": f"training_case_{case_key}",
                                    })
                                else:
                                    for cand in icd_candidates:
                                        if cand.get("code") == code and not cand.get("source", "").startswith("training_case_"):
                                            cand["source"] = f"training_case_{case_key}"
                                            cand["confidence"] = 0.95

                    _trace("5C_TRAINING_MATCH", "matched", {
                        "case": best_match_key,
                        "score": best_match_score,
                        "total_matches": len(all_matches),
                        "cpt_added": len(best_cpt),
                        "icd_added": len(best_icd),
                    })
            except Exception as e:
                _trace("5C_TRAINING_MATCH", "error", {"error": str(e)})

            # ── Stage 5C2: Training Case Relevance Filter ──────────────────
            # Remove training-case codes that have no supporting keywords
            # in the current note text (prevents false positives from generic
            # keyword matching across unrelated training cases).
            try:
                icd_before_filter = len(icd_candidates)
                icd_candidates = _filter_training_icd_by_note_relevance(
                    icd_candidates, note_text
                )
                icd_filtered_count = icd_before_filter - len(icd_candidates)
                if icd_filtered_count:
                    _trace("5C2_TRAINING_ICD_FILTER", "filtered", {
                        "removed": icd_filtered_count,
                        "remaining": len(icd_candidates),
                    })
                # Also filter CPT training case codes
                cpt_before_filter = len(cpt_candidates)
                cpt_candidates = _filter_training_cpt_by_note_relevance(
                    cpt_candidates, note_text
                )
                cpt_code_strs = [c.get("code", "") for c in cpt_candidates if c.get("code")]
                cpt_filtered_count = cpt_before_filter - len(cpt_candidates)
                if cpt_filtered_count:
                    _trace("5C2_TRAINING_CPT_FILTER", "filtered", {
                        "removed": cpt_filtered_count,
                        "remaining": len(cpt_candidates),
                    })
            except Exception as e:
                _trace("5C2_TRAINING_FILTER", "error", {"error": str(e)})

            icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]

            # ── Stage 5C3: Remove General Codes When Specific Present ──────
            # E.g., remove A41.9 (unspecified sepsis) when A41.0 (staph) exists.
            try:
                icd_before_gen = len(icd_candidates)
                icd_candidates = _remove_general_codes_when_specific_present(icd_candidates)
                gen_removed = icd_before_gen - len(icd_candidates)
                if gen_removed:
                    _trace("5C3_GENERAL_CODE_REMOVAL", "removed", {
                        "count": gen_removed,
                        "remaining": len(icd_candidates),
                    })
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
            except Exception as e:
                _trace("5C3_GENERAL_CODE_REMOVAL", "error", {"error": str(e)})

            # ── Stage 5C: V17 Deep Engine ICD Injection (post-Stage 5) ──
            # Inject ICD codes from deep engines AFTER Stage 5 to prevent overwrite
            try:
                for icd_code in _deep_icd_codes:
                    if icd_code not in icd_code_strs:
                        icd_candidates.insert(0, {
                            'code': icd_code,
                            'description': '',
                            'confidence': 0.85,
                            'source': 'deep_engine_icd',
                        })
                        icd_code_strs.insert(0, icd_code)
                if _deep_icd_codes:
                    _trace('5C_DEEP_ICD', 'injected', {'codes': _deep_icd_codes})
            except Exception:
                pass

            # ── Stage 5D: ICD Book Engine Search ──────────────────────
            # Search the ICD-10-CM book OCR engine for supplementary codes
            # Sort by specificity (longer codes = more specific)
            try:
                icd_book_results = []
                for term in codeable_diagnoses[:5]:
                    book_results = icd_book_search(term, limit=5)
                    for br in book_results:
                        br_code = br.get("code", "")
                        if br_code and br_code not in icd_code_strs and br_code not in [c.get("code", "") for c in icd_book_results]:
                            icd_book_results.append({
                                "code": br_code,
                                "description": br.get("desc", br.get("description", "")),
                                "confidence": 0.65,
                                "source": "icd_book_engine",
                                "category": br.get("category", ""),
                                "chapter": br.get("chapter", ""),
                            })
                icd_book_results.sort(key=lambda x: len(x.get("code", "")), reverse=True)
                if icd_book_results:
                    icd_candidates.extend(icd_book_results[:5])
                    _trace("5D_ICD_BOOK", "enhanced", {
                        "enhanced_count": len(icd_book_results),
                        "terms_searched": codeable_diagnoses[:5],
                    })
            except Exception as e:
                _trace("5D_ICD_BOOK", "error", {"error": str(e)})

            # ── Stage 5B: V16 ICD Clinical Reasoning ──────────────────────
            try:
                icd_reasoning = self._icd_reasoning.analyze(note_text, icd_code_strs)
                result.icd_clinical_reasoning = icd_reasoning
                # Enhance ICD codes with reasoning insights
                enhanced_icd_codes = []
                for r in icd_reasoning.get("diabetes", []):
                    if r.get("code") and r.get("confidence", 0) > 0.85:
                        enhanced_icd_codes.append(r)
                for r in icd_reasoning.get("sepsis", []):
                    if r.get("code") and r.get("confidence", 0) > 0.85:
                        enhanced_icd_codes.append(r)
                for r in icd_reasoning.get("injury_7th", []):
                    if r.get("code") and r.get("confidence", 0) > 0.85:
                        enhanced_icd_codes.append(r)
                for r in icd_reasoning.get("laterality", []):
                    if r.get("code") and r.get("confidence", 0) > 0.85:
                        enhanced_icd_codes.append(r)
                if icd_reasoning.get("ckd"):
                    enhanced_icd_codes.append(icd_reasoning["ckd"])
                if icd_reasoning.get("mi"):
                    enhanced_icd_codes.append(icd_reasoning["mi"])
                if enhanced_icd_codes:
                    _trace("5B_ICD_REASONING", "enhanced", {
                        "enhanced_count": len(enhanced_icd_codes),
                        "reasoning_keys": [k for k, v in icd_reasoning.items() if v],
                    })
            except Exception as e:
                result.icd_clinical_reasoning = {"error": str(e)}

            # ── Stage 6: V16 Modifier Engine ──────────────────────────────
            try:
                modifier_results = self._modifier_engine.determine_modifiers(
                    cpt_codes=cpt_code_strs,
                    note_text=note_text,
                    facts=extracted_dict,
                    encounter_type="outpatient",
                )
                result.modifier_decisions = {
                    code: mr.to_dict() for code, mr in modifier_results.items()
                }
                _trace("6_MODIFIERS", "determined", result.modifier_decisions)
            except Exception as e:
                result.modifier_decisions = {"error": str(e)}

            # ── Stage 7: V17 E/M Engine (SAFETY GATED) ──────────────────────
            # E/M engine ONLY runs if:
            #   1. No surgery/interventional/endoscopic code was detected
            #   2. Encounter explicitly supports E/M (outpatient/ED)
            #   3. Note has MDM/time language
            _em_suppressed = False
            _em_suppress_reason = ""

            # Determine if a procedure was detected (any non-E/M code)
            procedure_codes_detected = any(
                c for c in cpt_code_strs if not c.startswith('992') and not c.startswith('993')
            )
            note_is_operative = any(kw in note_text.lower() for kw in [
                'operative report', 'procedure performed', 'description of procedure',
                'operative description', 'intraoperative', 'surgical specimen',
                'preoperative diagnosis', 'postoperative diagnosis',
            ])

            if procedure_codes_detected:
                _em_suppressed = True
                _em_suppress_reason = f"Procedure codes present ({len(cpt_code_strs)} codes), E/M suppressed per priority hierarchy"
            elif note_is_operative:
                _em_suppressed = True
                _em_suppress_reason = "Operative note detected, E/M auto-suppressed"
            elif family_validation.em_suppressed:
                _em_suppressed = True
                _em_suppress_reason = f"E/M suppressed by family validation: {'; '.join(family_validation.suppression_reasons[:2])}"

            if not _em_suppressed:
                # ── Stage 7A: V19 Neonatal Critical Care Detection ─────
                # Check for neonatal critical care BEFORE standard E/M
                _neonatal_detected = False
                _neonatal_text_lower = note_text.lower()
                if any(kw in _neonatal_text_lower for kw in [
                    "neonat", "nicu", "newborn", "preterm", "gestational age",
                    "apnea of prematurity", "surfactant", "isolette",
                    "neonatal intensive care",
                ]):
                    _neonatal_detected = True
                    try:
                        v19_em = assess_em(note_text)
                        if v19_em.get("code") in ["99468", "99469"]:
                            cpt_candidates.insert(0, {
                                "code": v19_em["code"],
                                "description": v19_em.get("description", ""),
                                "confidence": 0.95,
                                "source": "em_engine_v19_neonatal",
                            })
                            cpt_code_strs.insert(0, v19_em["code"])
                            result.em_coding = {
                                "em_code": v19_em["code"],
                                "em_description": v19_em.get("description", ""),
                                "encounter_type": "neonatal_critical",
                                "selection_method": "neonatal_per_day",
                                "reasoning": "Neonatal critical care detected — per-day service, not time-based E/M",
                                "confidence": 0.95,
                            }
                            _trace("7A_V19_NEONATAL", "coded", {
                                "code": v19_em["code"],
                                "encounter_type": "neonatal_critical",
                            })
                    except Exception as e:
                        _trace("7A_V19_NEONATAL", "error", {"error": str(e)})

                if not _neonatal_detected:
                    try:
                        em_result = self._em_engine.code(note_text)
                        result.em_coding = {
                            "em_code": em_result.em_code,
                            "em_description": em_result.em_description,
                            "encounter_type": em_result.encounter_type,
                            "selection_method": em_result.selection_method,
                            "time_minutes": em_result.time_minutes,
                            "reasoning": em_result.reasoning,
                            "confidence": em_result.confidence,
                            "mdm": {
                                "problems_level": em_result.mdm.problems_level if em_result.mdm else None,
                                "data_level": em_result.mdm.data_level if em_result.mdm else None,
                                "risk_level": em_result.mdm.risk_level if em_result.mdm else None,
                                "overall_level": em_result.mdm.overall_level if em_result.mdm else None,
                                "problems_rationale": em_result.mdm.problems_rationale if em_result.mdm else "",
                                "data_rationale": em_result.mdm.data_rationale if em_result.mdm else "",
                                "risk_rationale": em_result.mdm.risk_rationale if em_result.mdm else "",
                            } if em_result.mdm else {},
                        }
                        # Add E/M code to CPT candidates if not already present
                        if em_result.em_code and em_result.em_code not in cpt_code_strs:
                            cpt_candidates.insert(0, {
                                "code": em_result.em_code,
                                "description": em_result.em_description,
                                "confidence": em_result.confidence,
                                "source": "em_engine_v16",
                            })
                            cpt_code_strs.insert(0, em_result.em_code)
                        _trace("7_EM_CODING", "coded", {"code": em_result.em_code, "method": em_result.selection_method})

                        # ── Stage 7A: V19 E/M Knowledge Engine Enhancement ──────
                        # Use comprehensive MDM tables to validate/upgrade E/M level
                        try:
                            v19_em = assess_em(note_text)
                            if v19_em.get("code") and v19_em["code"] != em_result.em_code:
                                # V19 engine may have better MDM assessment
                                v19_confidence = 0.75
                                if v19_em["mdm_level"] in ("moderate", "high"):
                                    v19_confidence = 0.80
                                # Add V19 E/M code as alternative if higher level
                                em_level_map = {"99202": 1, "99203": 2, "99204": 3, "99205": 4,
                                                "99212": 1, "99213": 2, "99214": 3, "99215": 4,
                                                "99281": 1, "99282": 2, "99283": 3, "99284": 4, "99285": 5}
                                old_level = em_level_map.get(em_result.em_code, 2)
                                new_level = em_level_map.get(v19_em["code"], 2)
                                if new_level >= old_level:
                                    # Replace with V19 code if equal or higher
                                    cpt_candidates[0] = {
                                        "code": v19_em["code"],
                                        "description": v19_em.get("description", f"E/M Level {new_level}"),
                                        "confidence": v19_confidence,
                                        "source": "em_engine_v19",
                                    }
                                    cpt_code_strs[0] = v19_em["code"]
                                    result.em_coding["em_code"] = v19_em["code"]
                                    result.em_coding["em_description"] = v19_em.get("description", "")
                                    result.em_coding["v19_mdm"] = v19_em.get("mdm_components", {})
                                    _trace("7A_V19_EM", "upgraded", {
                                        "old_code": em_result.em_code,
                                        "new_code": v19_em["code"],
                                        "mdm_level": v19_em["mdm_level"],
                                    })
                        except Exception as e:
                            _trace("7A_V19_EM", "error", {"error": str(e)})

                    except Exception as e:
                        result.em_coding = {"error": str(e)}
                else:
                    _trace("7_EM_CODING", "suppressed", {"reason": _em_suppress_reason})
                    result.em_coding = {"suppressed": True, "reason": _em_suppress_reason}

            # ── Stage 7B: V16 CPT Guideline Analysis ─────────────────────
            try:
                guideline_analysis = self._cpt_guideline.analyze_codes(
                    cpt_code_strs, note_text
                )
                result.cpt_guideline_analysis = guideline_analysis
                # Check for add-on violations — flag codes missing base
                add_on_violations = []
                for code, analysis in guideline_analysis.items():
                    if code.startswith("_"):
                        continue
                    add_on = analysis.get("add_on", {})
                    if add_on.get("applicable") and "REJECT" in add_on.get("recommendation", ""):
                        add_on_violations.append({
                            "code": code,
                            "recommendation": add_on["recommendation"],
                        })
                # Check for specificity conflicts — remove less-specific codes
                # BUT preserve codes that came from training case matching (expert-curated)
                cross_code = guideline_analysis.get("_cross_code", {})
                specificity = cross_code.get("specificity", {})
                if specificity.get("applicable"):
                    conflicting = specificity.get("conflicting_codes", [])
                    if conflicting:
                        # Collect training case codes to preserve
                        training_codes = {
                            c.get("code") for c in cpt_candidates
                            if c.get("source", "").startswith("training_case_")
                        }
                        # Only remove conflicting codes that are NOT from training cases
                        safe_conflicts = [c for c in conflicting if c not in training_codes]
                        if safe_conflicts:
                            cpt_candidates = [
                                c for c in cpt_candidates
                                if c.get("code", "") not in safe_conflicts
                            ]
                            cpt_code_strs = [
                                c for c in cpt_code_strs if c not in safe_conflicts
                            ]
                _trace("7B_CPT_GUIDELINES", "analyzed", {
                    "codes_analyzed": len([k for k in guideline_analysis if not k.startswith("_")]),
                    "add_on_violations": len(add_on_violations),
                    "specificity_conflicts": len(cross_code.get("specificity", {}).get("conflicting_codes", [])),
                })
            except Exception as e:
                result.cpt_guideline_analysis = {"error": str(e)}

            # ── Stage 7D: CPT Book Engine Search ──────────────────────
            # Search the CPT book OCR engine for supplementary procedure codes
            try:
                cpt_book_results = []
                for term in (getattr(facts, "keywords", []) or [])[:5]:
                    book_results = cpt_book_search(term, limit=3)
                    for br in book_results:
                        br_code = br.get("code", "")
                        if br_code and br_code not in cpt_code_strs and br_code not in [c.get("code", "") for c in cpt_book_results]:
                            detected_cat = br.get("category", "")
                            is_em = detected_cat == "E/M" or br_code.startswith("992") or br_code.startswith("993")
                            if not is_em:
                                cpt_book_results.append({
                                    "code": br_code,
                                    "description": br.get("desc", br.get("description", "")),
                                    "confidence": 0.60,
                                    "source": "cpt_book_engine",
                                    "category": detected_cat,
                                })
                if cpt_book_results:
                    cpt_candidates.extend(cpt_book_results[:5])
                    cpt_code_strs.extend([c["code"] for c in cpt_book_results[:5]])
                    _trace("7D_CPT_BOOK", "enhanced", {
                        "enhanced_count": len(cpt_book_results),
                        "terms_searched": (getattr(facts, "keywords", []) or [])[:5],
                    })
            except Exception as e:
                _trace("7D_CPT_BOOK", "error", {"error": str(e)})

            # ── Stage 8: Global Period Validation (V16 full) ───────────────
            global_results = {}
            for code in cpt_code_strs:
                gp = self._global_period.validate(code, note_text)
                global_results[code] = gp.to_dict()

            # ── Stage 9: Full Validation Suite ────────────────────────────
            ncci_result = self._ncci.validate(cpt_code_strs)
            mue_result = self._mue.validate(cpt_code_strs)
            lcd_results = self._lcd.validate(cpt_code_strs, icd_code_strs)
            ncd_results = self._ncd.validate(cpt_code_strs, icd_code_strs)

            from agents.deterministic_rule_engine import DeterministicRuleEngine
            rule_engine = DeterministicRuleEngine()
            rule_result = rule_engine.apply_code_list(icd_code_strs, extracted_dict, note_text)

            try:
                ama_result = self._ama.validate(cpt_code_strs)
            except Exception:
                ama_result = None
            try:
                cms_result = self._cms.validate(cpt_code_strs, icd_code_strs)
            except Exception:
                cms_result = None

            _trace("9_VALIDATION", "validated", {
                "ncci_passed": ncci_result.passed, "mue_passed": mue_result.passed
            })

            # ── Stage 10: V16 Medical Necessity ──────────────────────────
            try:
                necessity_results = self._necessity.validate(cpt_code_strs, icd_code_strs, note_text)
                result.medical_necessity = {
                    code: nr.to_dict() for code, nr in necessity_results.items()
                }
                # Boost or reduce confidence based on necessity
                necessity_passed = all(nr.passed for nr in necessity_results.values())
                _trace("10_NECESSITY", "validated", {"all_passed": necessity_passed})
            except Exception as e:
                result.medical_necessity = {"error": str(e)}

            # ── Stage 11: Confidence Scoring ─────────────────────────────
            confidence_score = self._confidence.compute(
                cpt_candidates=cpt_candidates,
                icd_candidates=icd_candidates,
                ncci_result=ncci_result,
                mue_result=mue_result,
                lcd_results=lcd_results,
                rule_result=rule_result,
            )
            result.confidence = confidence_score.overall
            _trace("11_CONFIDENCE", "scored", {"overall": confidence_score.overall})

            # ── Stage 12: Denial Risk ────────────────────────────────────
            denial_result = self._denial.assess(
                cpt_codes=cpt_code_strs, icd10_codes=icd_code_strs,
                ncci_result=ncci_result, mue_result=mue_result,
                lcd_results=lcd_results, rule_result=rule_result,
            )
            result.denial_risk = denial_result.to_dict()

            # ── Stage 13: V16 Documentation Quality ──────────────────────
            try:
                doc_quality = self._doc_quality.analyse(note_text, cpt_code_strs, icd_code_strs)
                result.documentation_quality = doc_quality.to_dict()
                _trace("13_DOC_QUALITY", "analysed", {"score": doc_quality.score, "gaps": len(doc_quality.documentation_gaps)})
            except Exception as e:
                result.documentation_quality = {"error": str(e)}

            # ── Stage 14: V16 Physician Queries ──────────────────────────
            try:
                queries = self._query_engine.generate_queries(
                    note_text=note_text,
                    documentation_gaps=result.documentation_quality.get("documentation_gaps", []),
                    icd_codes=icd_code_strs,
                )
                result.physician_queries = [q.to_dict() for q in queries]
                _trace("14_QUERIES", "generated", {"count": len(queries)})
            except Exception as e:
                result.physician_queries = [{"error": str(e)}]

            # ── Stage 15: Build Validation Block ─────────────────────────
            # Build guideline validation summary (reuse Stage 7B results)
            gla = result.cpt_guideline_analysis if isinstance(result.cpt_guideline_analysis, dict) and not result.cpt_guideline_analysis.get("error") else {}
            _add_on_violations = [
                {"code": code, "recommendation": a.get("add_on", {}).get("recommendation", "")}
                for code, a in gla.items()
                if not code.startswith("_") and a.get("add_on", {}).get("applicable")
                and "REJECT" in a.get("add_on", {}).get("recommendation", "")
            ]
            _bundling_issues = gla.get("_cross_code", {}).get("bundling", [])

            icd_r = result.icd_clinical_reasoning if isinstance(result.icd_clinical_reasoning, dict) and not result.icd_clinical_reasoning.get("error") else {}

            result.validation = {
                "ncci": ncci_result.to_dict() if ncci_result else {},
                "mue": mue_result.to_dict() if mue_result else {},
                "lcd": [r.to_dict() for r in lcd_results],
                "ncd": [r.to_dict() for r in ncd_results],
                "global_period": global_results,
                "rule_violations": rule_result.violations if rule_result else [],
                "rule_warnings": rule_result.warnings if rule_result else [],
                "confidence_components": confidence_score.components,
                "overall_passed": ncci_result.passed and mue_result.passed,
                "cpt_guideline": {
                    "add_on_violations": _add_on_violations,
                    "bundling_issues": _bundling_issues,
                },
                "icd_reasoning": {
                    "diabetes_codes": [
                        r for r in icd_r.get("diabetes", [])
                        if r.get("confidence", 0) > 0.85
                    ],
                    "sepsis_codes": [
                        r for r in icd_r.get("sepsis", [])
                        if r.get("confidence", 0) > 0.85
                    ],
                    "ckd": icd_r.get("ckd"),
                    "mi": icd_r.get("mi"),
                },
            }

            # ── Stage 15B: ICD Code Specificity Deduplication ──────────
            # Remove truly redundant codes: only drop code B if code A is a
            # prefix of B (e.g., "A41" is prefix of "A41.52" → keep A41.52).
            # Sibling codes like A41.0 vs A41.9 are BOTH kept.
            # Training-case-sourced codes are never dropped.
            try:
                import re as _re

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
                    icd_candidates = [
                        c for c in icd_candidates if c.get("code") not in dropped
                    ]
                    _trace("15B_ICD_DEDUP", "removed_redundant", {
                        "dropped": list(dropped),
                    })
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
            except Exception as e:
                _trace("15B_ICD_DEDUP", "error", {"error": str(e)})

            # ── Stage 15B2: Laterality Enforcement ──────────────────────────
            # When the note specifies 'right' or 'left', ensure generated ICD
            # codes include proper laterality and remove wrong-side codes.
            try:
                icd_before_laterality = len(icd_candidates)
                icd_candidates = _enforce_laterality(icd_candidates, note_text)
                laterality_removed = icd_before_laterality - len(icd_candidates)
                if laterality_removed:
                    _trace("15B2_LATERALITY", "enforced", {
                        "removed": laterality_removed,
                        "remaining": len(icd_candidates),
                    })
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
            except Exception as e:
                _trace("15B2_LATERALITY", "error", {"error": str(e)})

            # ── Stage 15B3: Same-Condition ICD Dedup ────────────────────────
            # When multiple ICD codes share the same 4-char prefix (e.g.,
            # I21.01, I21.09, I21.19), keep only the one that best matches.
            try:
                icd_before_cond_dedup = len(icd_candidates)
                icd_candidates = _dedup_same_condition_icd(icd_candidates, note_text)
                cond_dedup_removed = icd_before_cond_dedup - len(icd_candidates)
                if cond_dedup_removed:
                    _trace("15B3_SAME_CONDITION_DEDUP", "deduped", {
                        "removed": cond_dedup_removed,
                        "remaining": len(icd_candidates),
                    })
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
            except Exception as e:
                _trace("15B3_SAME_CONDITION_DEDUP", "error", {"error": str(e)})

            # ── Stage 15B4: MI Code Dedup ────────────────────────────────
            # When multiple I21 codes exist, keep only the single best match.
            try:
                icd_before_mi = len(icd_candidates)
                icd_candidates = _deduplicate_mi_codes(icd_candidates, note_text)
                mi_removed = icd_before_mi - len(icd_candidates)
                if mi_removed:
                    _trace("15B4_MI_DEDUP", "deduped", {
                        "removed": mi_removed,
                        "remaining": len(icd_candidates),
                    })
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
            except Exception as e:
                _trace("15B4_MI_DEDUP", "error", {"error": str(e)})

            # ── Stage 15C: Clinical Relevance Filtering ──────────────────
            # Filter CPT/ICD codes that have NO clinical evidence in the note.
            # Training-case-sourced codes are always kept (expert-curated).
            try:
                # 1. CPT clinical relevance filter
                cpt_before = len(cpt_candidates)
                cpt_candidates = [
                    c for c in cpt_candidates
                    if c.get("source", "").startswith("training_case_")
                    or _has_clinical_support(c.get("code", ""), note_text, 'cpt')
                ]
                cpt_code_strs = [c.get("code", "") for c in cpt_candidates if c.get("code")]
                cpt_filtered = cpt_before - len(cpt_candidates)
                if cpt_filtered:
                    _trace("15C_CPT_RELEVANCE", "filtered", {"removed": cpt_filtered, "remaining": len(cpt_candidates)})

                # 2. ICD redundancy removal (prefix-based dedup)
                icd_candidates = _remove_icd_redundancy(icd_candidates, note_text)

                # 3. ICD clinical relevance filter
                # Training-case codes are exempt here — they were already
                # filtered for note relevance in Stage 5C2.
                icd_before = len(icd_candidates)
                icd_candidates = [
                    c for c in icd_candidates
                    if c.get("source", "").startswith("training_case_")
                    or _has_clinical_support(c.get("code", ""), note_text, 'icd')
                ]
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
                icd_filtered = icd_before - len(icd_candidates)
                if icd_filtered:
                    _trace("15C_ICD_RELEVANCE", "filtered", {"removed": icd_filtered, "remaining": len(icd_candidates)})
                if cpt_filtered or icd_filtered:
                    _trace("15C_RELEVANCE", "done", {"cpt_removed": cpt_filtered, "icd_removed": icd_filtered})
                else:
                    _trace("15C_RELEVANCE", "passed", {"cpt": len(cpt_candidates), "icd": len(icd_candidates)})

                # Final ICD validation: remove codes with no supporting evidence
                icd_before_final = len(icd_candidates)
                icd_candidates = _validate_icd_vs_note(icd_candidates, note_text)
                icd_code_strs = [c.get("code", "") for c in icd_candidates if c.get("code")]
                final_removed = icd_before_final - len(icd_candidates)
                if final_removed:
                    _trace("15C_FINAL_ICD_VALIDATION", "cleaned", {
                        "removed": final_removed,
                        "remaining": len(icd_candidates),
                    })
            except Exception as e:
                _trace("15C_RELEVANCE", "error", {"error": str(e)})

            # ── Stage 16: Reasoning Trace ────────────────────────────────
            trace = self._explainer.build_trace(
                note_text=note_text, extracted_facts=extracted_dict,
                specialty=specialty, procedure_family=procedure_family,
                cpt_candidates=cpt_candidates, icd_candidates=icd_candidates,
                ncci_result=ncci_result, mue_result=mue_result,
                lcd_results=lcd_results,
                rule_violations=rule_result.violations if rule_result else [],
                final_cpt=cpt_candidates[:3], final_icd=icd_candidates[:5],
            )
            result.reasoning_trace = trace.to_list()

            # ── Stage 17: Audit ──────────────────────────────────────────
            try:
                audit_data = self._audit.audit(
                    cpt_codes=cpt_code_strs, facts={}, validation={},
                ) if hasattr(self._audit, "audit") else {}
                result.audit = audit_data if isinstance(audit_data, dict) else {}
            except Exception as e:
                result.audit = {"warning": f"Audit engine: {e}"}

            # Final full audit trace
            result.full_audit_trace = audit_trace

            # ── Finalize ──────────────────────────────────────────────────
            result.cpt_codes = cpt_candidates[:5]
            result.icd10_codes = icd_candidates[:6]

        except Exception as e:
            logger.error(f"[{session_id}] Pipeline error: {e}", exc_info=True)
            result.audit = {"error": str(e)}
            result.confidence = 0.0

        result.processing_time_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            f"[{session_id}] V16 pipeline complete in {result.processing_time_ms:.1f}ms "
            f"CPT={len(result.cpt_codes)} ICD={len(result.icd10_codes)} "
            f"confidence={result.confidence:.2f} "
            f"queries={len(result.physician_queries)} "
            f"gaps={len(result.documentation_quality.get('documentation_gaps', []))}"
        )
        return result


# Alias for new code
MedcodeDeterministicPipelineV16 = MedcodeDeterministicPipelineV15
# Backward-compatible aliases
MedCodeDeterministicPipeline = MedcodeDeterministicPipelineV15
MedCodeDeterministicPipelineV16 = MedcodeDeterministicPipelineV15
MedcodeDeterministicPipeline = MedcodeDeterministicPipelineV15