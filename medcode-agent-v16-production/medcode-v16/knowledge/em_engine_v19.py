"""
CPT 2026 Evaluation & Management Knowledge Engine
===================================================
Complete E/M coding engine based on AMA CPT 2026 guidelines.
Covers: Office, Hospital, Emergency, Critical Care, Consultations, Nursing.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EMEncounter:
    encounter_type: str = "office"
    is_new_patient: bool = False
    mdm_problems: int = 0
    mdm_data: int = 0
    mdm_risk: int = 0
    total_time_minutes: int = 0
    procedure_performed: bool = False


EM_OFFICE_CODES = {
    "new": {
        (1, 1, 1): {"code": "99202", "desc": "Office visit, new, straightforward MDM", "time": 15},
        (2, 2, 1): {"code": "99203", "desc": "Office visit, new, low MDM", "time": 30},
        (3, 3, 2): {"code": "99204", "desc": "Office visit, new, moderate MDM", "time": 45},
        (4, 4, 3): {"code": "99205", "desc": "Office visit, new, high MDM", "time": 60},
    },
    "established": {
        (1, 1, 1): {"code": "99212", "desc": "Office visit, established, straightforward MDM", "time": 10},
        (2, 2, 1): {"code": "99213", "desc": "Office visit, established, low MDM", "time": 20},
        (3, 3, 2): {"code": "99214", "desc": "Office visit, established, moderate MDM", "time": 30},
        (4, 4, 3): {"code": "99215", "desc": "Office visit, established, high MDM", "time": 40},
    },
}

MDM_PROBLEMS = {
    1: "Minimal (1 self-limited or minor problem)",
    2: "Low (2 or more self-limited/minor problems; 1 stable chronic illness; 1 acute uncomplicated illness)",
    3: "Moderate (1 or more chronic illnesses with mild exacerbation, progression, or side effects; 2 or more stable chronic illnesses; 1 undiagnosed new problem with uncertain prognosis; 1 acute illness with systemic symptoms)",
    4: "High (1 or more chronic illnesses with severe exacerbation; 1 acute or chronic illness posing threat to life or bodily function)",
}

MDM_DATA = {
    1: "Minimal (none or self-limited/limited external sources)",
    2: "Limited (minimal clinical data from tests, documents, or old records; independent interpretation of test; discussion of management with external physician)",
    3: "Moderate (order of tests in category II/III; independent interpretation of test; assessment requiring independent historian; independent interpretation of external source data)",
    4: "Extensive (independent interpretation of advanced diagnostic test; independent interpretation of external source data; discussion of management with external physician)",
}

MDM_RISK = {
    1: "Low risk (minimal risk of morbidity from additional diagnostic testing or treatment; simple dressing, splinting; prescription of non-controlled drugs)",
    2: "Moderate risk (risk of morbidity from additional diagnostic testing or treatment; prescription of controlled drug; decision regarding minor surgery; decision regarding hospitalization)",
    3: "High risk (risk of morbidity or mortality from additional diagnostic testing or treatment; decision to hospitalize or escalate care; decision regarding DNR; diagnosis or treatment significantly limited by social determinants)",
}

EM_TIME_BASED = {
    "office_new": [
        (99202, 15, 29), (99203, 30, 44), (99204, 45, 59), (99205, 60, 74),
    ],
    "office_established": [
        (99212, 10, 19), (99213, 20, 29), (99214, 30, 39), (99215, 40, 54),
    ],
    "hospital_initial": [
        (99221, 40, 54), (99222, 55, 74), (99223, 75, None),
    ],
    "hospital_subsequent": [
        (99231, 25, 34), (99232, 35, 49), (99233, 50, None),
    ],
    "observation": [
        (99218, 0, 89), (99219, 90, 119), (99220, 120, None),
    ],
    "emergency": [
        (99281, 0, 14), (99282, 15, 29), (99283, 30, 44),
        (99284, 45, 59), (99285, 60, None),
    ],
    "critical_care": [
        (99291, 0, 73), (99292, 74, None),
    ],
}

CRITICAL_CARE_CPT = {
    "99291": "Critical care, evaluation and management of the critically ill or injured patient; first 30-74 minutes",
    "99292": "Each additional 30 minutes (list separately)",
}

CONSULTATION_CODES = {
    "outpatient": {(1, 1, 1): "99241", (2, 2, 1): "99242", (3, 3, 2): "99243", (4, 4, 2): "99244", (5, 5, 3): "99245"},
    "inpatient": {(1, 1, 1): "99251", (2, 2, 1): "99252", (3, 3, 2): "99253", (4, 4, 2): "99254", (5, 5, 3): "99255"},
}

HOSPITAL_CODES = {
    "initial": {1: "99221", 2: "99222", 3: "99223"},
    "subsequent": {1: "99231", 2: "99232", 3: "99233"},
    "discharge": {1: "99238", 2: "99239"},
}

EMERGENCY_CODES = {1: "99281", 2: "99282", 3: "99283", 4: "99284", 5: "99285"}

NURSING_CODES = {
    "initial": {1: "99304", 2: "99305", 3: "99306"},
    "subsequent": {1: "99307", 2: "99308", 3: "99309", 4: "99310"},
}

NEONATAL_CRITICAL_CARE_CODES = {
    "99468": "Initial hospital care of the newborn, per day",
    "99469": "Subsequent daily hospital care of the newborn, per day",
}

PROLONGED_CODES = {
    "99354": "Prolonged E/M, first hour (outpatient, not on same day)",
    "99355": "Each additional 30 minutes",
    "99356": "Prolonged E/M, first hour (inpatient)",
    "99357": "Each additional 30 minutes",
    "99417": "Prolonged E/M, each additional 15 minutes beyond primary time",
}

EM_MODIFIERS = {
    "25": "Significant, separately identifiable E/M service by same physician on same day as procedure",
    "57": "Decision for surgery (E/M on same day as major surgery)",
    "95": "Synchronous telemedicine service",
}


def calculate_mdm_level(problems: int, data: int, risk: int) -> str:
    mdm = max(problems, data, risk)
    if mdm <= 1:
        return "straightforward"
    elif mdm == 2:
        return "low"
    elif mdm == 3:
        return "moderate"
    else:
        return "high"


def select_office_em(problems: int, data: int, risk: int, is_new: bool = False) -> Dict:
    level = calculate_mdm_level(problems, data, risk)
    key = (problems, data, risk)
    patient_type = "new" if is_new else "established"

    mdm_to_key = {
        "straightforward": (1, 1, 1),
        "low": (2, 2, 1),
        "moderate": (3, 3, 2),
        "high": (4, 4, 3),
    }
    lookup = mdm_to_key.get(level, (1, 1, 1))
    code_info = EM_OFFICE_CODES[patient_type].get(lookup, EM_OFFICE_CODES[patient_type][(1, 1, 1)])
    return {
        "code": code_info["code"],
        "description": code_info["desc"],
        "mdm_level": level,
        "mdm_problems": MDM_PROBLEMS.get(problems, ""),
        "mdm_data": MDM_DATA.get(data, ""),
        "mdm_risk": MDM_RISK.get(risk, ""),
    }


def select_em_by_time(encounter_type: str, total_time: int) -> Dict:
    type_key = encounter_type
    if type_key not in EM_TIME_BASED:
        return {"code": "", "error": f"Unknown encounter type: {encounter_type}"}

    for code, min_time, max_time in EM_TIME_BASED[type_key]:
        if max_time is None and total_time >= min_time:
            return {"code": str(code), "time": total_time}
        elif max_time and min_time <= total_time <= max_time:
            return {"code": str(code), "time": total_time}

    return {"code": "", "error": f"No code for {total_time} minutes in {encounter_type}"}


def get_modifier_25_eligibility(procedure_cpt: str, em_code: str) -> bool:
    minor_procedures = {"11102", "11104", "17000", "17003", "17004", "20610", "21501",
                        "36415", "43239", "45378", "45380", "45385", "51701", "51702",
                        "71046", "71047", "73030", "76856", "90471", "90472", "93000"}
    em_level = int(em_code[-1]) if em_code.isdigit() else 0
    return procedure_cpt in minor_procedures and em_level >= 3


def get_prolonged_service(total_minutes: int, base_em_code: str, is_inpatient: bool = False) -> List[Dict]:
    result = []
    base_times = {
        "99202": 15, "99203": 30, "99204": 45, "99205": 60,
        "99212": 10, "99213": 20, "99214": 30, "99215": 40,
        "99221": 40, "99222": 55, "99223": 75,
    }
    base_time = base_times.get(base_em_code, 30)
    extra = total_minutes - base_time
    if extra >= 15:
        result.append({"code": "99417", "description": "Prolonged service, each 15 min beyond primary"})
        additional_blocks = (extra - 15) // 15
        if additional_blocks > 0:
            result[-1]["additional_units"] = additional_blocks
    return result


def classify_encounter_type(note_text: str) -> str:
    text_lower = note_text.lower()
    # CRITICAL: Check for neonatal BEFORE other checks
    if any(kw in text_lower for kw in ["neonat", "nicu", "newborn", "preterm", "gestational age",
                                         "apnea of prematurity", "surfactant", "isolette"]):
        return "neonatal_critical"
    if any(kw in text_lower for kw in ["emergency", "ed visit", "emergency department", "trauma bay"]):
        return "emergency"
    if any(kw in text_lower for kw in ["critical care", "icu", "intensive care", "unstable"]):
        return "critical_care"
    if any(kw in text_lower for kw in ["observation", "obs unit", "clinical decision unit"]):
        return "observation"
    if any(kw in text_lower for kw in ["inpatient", "hospital day", "admitted", "floor"]):
        return "hospital_initial"
    if any(kw in text_lower for kw in ["consult", "consultation", "requested opinion"]):
        return "consultation"
    if any(kw in text_lower for kw in ["nursing facility", "snf", "nursing home"]):
        return "nursing"
    if any(kw in text_lower for kw in ["telehealth", "telemedicine", "virtual visit"]):
        return "telehealth"
    return "office"


def assess_mdm_problems(note_text: str) -> int:
    text_lower = note_text.lower()
    high_keywords = ["critical", "life-threatening", "deteriorating", "acute organ failure",
                     "severe exacerbation", "unstable", "code blue", "arrest"]
    mod_keywords = ["chronic", "exacerbation", "new diagnosis", "uncertain prognosis",
                    "multiple chronic", "systemic symptoms", "moderate", "worsening"]
    low_keywords = ["stable chronic", "well-controlled", "follow-up", "routine",
                    "mild", "uncomplicated", "simple"]
    minimal_keywords = ["self-limited", "minor", "routine check", "simple dressing"]

    if any(kw in text_lower for kw in high_keywords):
        return 4
    if any(kw in text_lower for kw in mod_keywords):
        return 3
    if any(kw in text_lower for kw in low_keywords):
        return 2
    if any(kw in text_lower for kw in minimal_keywords):
        return 1
    return 2


def assess_mdm_data(note_text: str) -> int:
    text_lower = note_text.lower()
    ext_interpret = ["independently interpreted", "ci read", "ekg interpreted", "imaging reviewed"]
    ext_discuss = ["discussed with", "called physician", "conference with"]
    tests_ordered = ["ordered", "sent", "scheduled", "obtained"]

    score = 1
    if any(kw in text_lower for kw in ext_interpret):
        score = max(score, 3)
    if any(kw in text_lower for kw in ext_discuss):
        score = max(score, 2)
    if any(kw in text_lower for kw in tests_ordered):
        test_count = sum(1 for kw in tests_ordered if kw in text_lower)
        if test_count >= 3:
            score = max(score, 3)
        else:
            score = max(score, 2)
    return score


def assess_mdm_risk(note_text: str) -> int:
    text_lower = note_text.lower()
    high_risk = ["hospitalize", "dnr", "life-threatening", "cardiac arrest",
                 "intubation", "pressors", "dialysis", "social determinants",
                 "significant limitation"]
    moderate_risk = ["controlled substance", "prescription", "minor surgery",
                     "decision to hospitalize", "decision for surgery",
                     "chronic illness", "drug management"]
    low_risk = ["otc medication", "simple dressing", "bandage",
                "superficial wound care", "non-controlled prescription"]

    if any(kw in text_lower for kw in high_risk):
        return 3
    if any(kw in text_lower for kw in moderate_risk):
        return 2
    if any(kw in text_lower for kw in low_risk):
        return 1
    return 2


def assess_em(note_text: str) -> Dict:
    encounter_type = classify_encounter_type(note_text)
    problems = assess_mdm_problems(note_text)
    data = assess_mdm_data(note_text)
    risk = assess_mdm_risk(note_text)
    mdm_level = calculate_mdm_level(problems, data, risk)

    mdm_to_num = {"straightforward": 1, "low": 2, "moderate": 3, "high": 4}
    mdm_num = mdm_to_num[mdm_level]

    # NEONATAL CRITICAL CARE — special handling (per-day, not time-based)
    if encounter_type == "neonatal_critical":
        # Determine if initial or subsequent day
        text_lower = note_text.lower()
        is_initial = any(kw in text_lower for kw in [
            "day 1", "nicu day 1", "day of life 1", "initial day",
            "admission day", "birth day",
        ])
        # Check for day number
        import re
        day_match = re.search(r'(?:day|nicu day|dol)\s*(\d+)', text_lower)
        day_num = int(day_match.group(1)) if day_match else 1

        if day_num <= 1 or is_initial:
            code = "99468"
            desc = "Initial hospital care of the newborn, per day"
        else:
            code = "99469"
            desc = "Subsequent daily hospital care of the newborn, per day"

        return {
            "code": code,
            "description": desc,
            "encounter_type": "neonatal_critical",
            "mdm_level": mdm_level,
            "mdm_components": {
                "problems": {"score": problems, "description": MDM_PROBLEMS.get(problems, "")},
                "data": {"score": data, "description": MDM_DATA.get(data, "")},
                "risk": {"score": risk, "description": MDM_RISK.get(risk, "")},
            },
        }

    if encounter_type == "office":
        result = select_office_em(problems, data, risk, is_new=False)
    elif encounter_type == "emergency":
        result = {"code": EMERGENCY_CODES.get(mdm_num, "99283"),
                  "description": f"Emergency department visit, level {mdm_num}"}
    elif encounter_type == "hospital_initial":
        result = {"code": HOSPITAL_CODES["initial"].get(mdm_num, "99222"),
                  "description": f"Initial hospital care, level {mdm_num}"}
    elif encounter_type == "hospital_subsequent":
        result = {"code": HOSPITAL_CODES["subsequent"].get(mdm_num, "99232"),
                  "description": f"Subsequent hospital care, level {mdm_num}"}
    elif encounter_type == "critical_care":
        result = {"code": "99291", "description": CRITICAL_CARE_CPT["99291"]}
    elif encounter_type == "consultation":
        result = {"code": "99253", "description": "Inpatient consultation, moderate"}
    else:
        result = select_office_em(problems, data, risk, is_new=False)

    result["encounter_type"] = encounter_type
    result["mdm_level"] = mdm_level
    result["mdm_components"] = {
        "problems": {"score": problems, "description": MDM_PROBLEMS.get(problems, "")},
        "data": {"score": data, "description": MDM_DATA.get(data, "")},
        "risk": {"score": risk, "description": MDM_RISK.get(risk, "")},
    }
    return result
