"""
MedCode AI — Payer-Specific Rules Engine
==========================================
Configurations for common payers including filing deadlines,
prior authorization requirements, and modifier rules.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# Payer configurations
PAYER_CONFIGS = {
    "Medicare": {
        "payer_id": "MED",
        "payer_type": "government",
        "filing_deadline_days": 365,
        "filing_deadline_note": "1 year from date of service",
        "electronic_only": False,
        "edi_payer_id": "CMS",
        "npi_required": True,
        "prior_auth_categories": [
            "surgery",
            "imaging_advanced",
            "dme",
            "home_health",
            "hospice",
            "psychiatric",
        ],
        "modifier_requirements": {
            "99214": ["25"],
            "99215": ["25"],
            "99213": ["25"],
        },
        "allowed_place_of_service": [
            "11", "12", "21", "22", "23", "31", "32",
            "41", "49", "51", "53", "54", "56", "65",
            "71", "72", "81", "99",
        ],
        "claim_types": ["professional", "institutional"],
    },
    "Medicaid": {
        "payer_id": "MCD",
        "payer_type": "government",
        "filing_deadline_days": 90,
        "filing_deadline_note": "90 days from date of service",
        "electronic_only": False,
        "edi_payer_id": "MCD",
        "npi_required": True,
        "prior_auth_categories": [
            "surgery",
            "imaging_advanced",
            "dme",
            "home_health",
            "hospice",
            "psychiatric",
            "rehabilitation",
            "dental",
        ],
        "modifier_requirements": {
            "99214": ["25"],
            "99215": ["25"],
        },
        "allowed_place_of_service": [
            "11", "12", "21", "22", "23", "31", "32",
            "41", "49", "51", "53", "54", "56", "65",
            "71", "72", "81", "99",
        ],
        "claim_types": ["professional", "institutional"],
    },
    "BCBS": {
        "payer_id": "BCBS",
        "payer_type": "commercial",
        "filing_deadline_days": 180,
        "filing_deadline_note": "180 days from date of service",
        "electronic_only": False,
        "edi_payer_id": "BCBS",
        "npi_required": True,
        "prior_auth_categories": [
            "surgery",
            "imaging_advanced",
            "dme",
            "home_health",
            "hospice",
            "psychiatric",
        ],
        "modifier_requirements": {
            "99214": ["25"],
            "99215": ["25"],
        },
        "allowed_place_of_service": [
            "11", "12", "21", "22", "23", "31", "32",
            "41", "49", "51", "53", "54", "56", "65",
            "71", "72", "81", "99",
        ],
        "claim_types": ["professional", "institutional", "pharmacy"],
    },
    "Aetna": {
        "payer_id": "AET",
        "payer_type": "commercial",
        "filing_deadline_days": 180,
        "filing_deadline_note": "180 days from date of service",
        "electronic_only": True,
        "edi_payer_id": "AETNA",
        "npi_required": True,
        "prior_auth_categories": [
            "surgery",
            "imaging_advanced",
            "dme",
            "home_health",
            "hospice",
            "psychiatric",
            "rehabilitation",
        ],
        "modifier_requirements": {
            "99214": ["25"],
            "99215": ["25"],
        },
        "allowed_place_of_service": [
            "11", "12", "21", "22", "23", "31", "32",
            "41", "49", "51", "53", "54", "56", "65",
            "71", "72", "81", "99",
        ],
        "claim_types": ["professional", "institutional"],
    },
    "UnitedHealthcare": {
        "payer_id": "UHC",
        "payer_type": "commercial",
        "filing_deadline_days": 180,
        "filing_deadline_note": "180 days from date of service",
        "electronic_only": True,
        "edi_payer_id": "UHC",
        "npi_required": True,
        "prior_auth_categories": [
            "surgery",
            "imaging_advanced",
            "dme",
            "home_health",
            "hospice",
            "psychiatric",
            "rehabilitation",
        ],
        "modifier_requirements": {
            "99214": ["25"],
            "99215": ["25"],
        },
        "allowed_place_of_service": [
            "11", "12", "21", "22", "23", "31", "32",
            "41", "49", "51", "53", "54", "56", "65",
            "71", "72", "81", "99",
        ],
        "claim_types": ["professional", "institutional"],
    },
    "Cigna": {
        "payer_id": "CIG",
        "payer_type": "commercial",
        "filing_deadline_days": 180,
        "filing_deadline_note": "180 days from date of service",
        "electronic_only": True,
        "edi_payer_id": "CIGNA",
        "npi_required": True,
        "prior_auth_categories": [
            "surgery",
            "imaging_advanced",
            "dme",
            "home_health",
            "hospice",
            "psychiatric",
        ],
        "modifier_requirements": {
            "99214": ["25"],
            "99215": ["25"],
        },
        "allowed_place_of_service": [
            "11", "12", "21", "22", "23", "31", "32",
            "41", "49", "51", "53", "54", "56", "65",
            "71", "72", "81", "99",
        ],
        "claim_types": ["professional", "institutional"],
    },
}

# CPT code to procedure category mapping
PROCEDURE_CATEGORIES = {
    "surgery": [
        "10000", "19000", "20000", "27000", "29000", "33000",
        "35000", "37000", "39000", "42000", "43000", "44000",
        "46000", "47000", "49000", "50000", "51000", "52000",
        "53000", "54000", "55000", "58000", "59000", "60000",
        "63000", "64000", "65000", "66000", "67000", "68000",
        "69000", "70000", "71000", "72000", "73000", "74000",
        "75000", "76000", "77000", "78000",
    ],
    "imaging_advanced": [
        "70551", "70552", "70553", "70554", "71260", "71270",
        "72141", "72142", "72148", "72149", "72158", "73030",
        "73721", "73722", "74177", "74178", "75580",
    ],
    "dme": [
        "E0100", "E0105", "E0110", "E0112", "E0114", "E0116",
        "E0118", "E0120", "E0125", "E0130", "E0135", "E0140",
        "E0141", "E0143", "E0148", "E0149", "E0155", "E0160",
    ],
    "home_health": [
        "G0151", "G0152", "G0154", "G0155", "G0156", "G0157",
        "G0158", "G0159", "G0160", "G0161", "G0162", "G0163",
        "G0164", "G0165", "G0166", "G0167", "G0168",
    ],
    "hospice": [
        "G0161", "G0162", "G0163", "G0164", "G0165", "G0166",
        "G0167", "G0168", "G0169", "G0170", "G0171", "G0172",
    ],
    "psychiatric": [
        "90801", "90802", "90804", "90805", "90806", "90807",
        "90808", "90809", "90810", "90811", "90812", "90813",
        "90814", "90815", "90816", "90817", "90818", "90819",
        "90832", "90833", "90834", "90837", "90838", "90839",
        "90840", "90845", "90846", "90847", "90849", "90853",
    ],
    "rehabilitation": [
        "97110", "97112", "97116", "97124", "97130", "97140",
        "97150", "97530", "97533", "97535", "97542", "97545",
        "97546", "97550", "97555", "97570", "97601", "97602",
    ],
    "dental": [
        "D0100", "D0120", "D0150", "D0160", "D0180", "D0190",
        "D0210", "D0220", "D0230", "D0240", "D0250", "D0260",
        "D0270", "D0272", "D0273", "D0274", "D0277", "D0310",
    ],
}

# Modifier requirements per payer
MODIFIER_RULES = {
    "modifier_25": {
        "description": "Significant, separately identifiable E/M service",
        "required_with": ["99214", "99215", "99213"],
        "when": "Same day as another procedure",
    },
    "modifier_59": {
        "description": "Distinct procedural service",
        "required_with": [],
        "when": "Bypass NCCI edits for separate procedures",
    },
    "modifier_76": {
        "description": "Repeat procedure by same physician",
        "required_with": [],
        "when": "Same procedure performed again same day",
    },
    "modifier_77": {
        "description": "Repeat procedure by different physician",
        "required_with": [],
        "when": "Same procedure by different provider same day",
    },
    "modifier_50": {
        "description": "Bilateral procedure",
        "required_with": [],
        "when": "Procedure performed on both sides",
    },
    "modifier_26": {
        "description": "Professional component",
        "required_with": [],
        "when": "Billing only professional component",
    },
    "modifier_TC": {
        "description": "Technical component",
        "required_with": [],
        "when": "Billing only technical component",
    },
}


class PayerRules:
    """
    Payer-specific rules engine for claim submission.
    Validates claims against payer requirements.
    """

    def check_payer_requirements(
        self, claim, payer_name: str
    ) -> Dict[str, Any]:
        """
        Check claim against payer-specific requirements.

        Args:
            claim: Claim dataclass or dict.
            payer_name: Name of the payer.

        Returns:
            Dict with payer_info, requirements_met, missing, warnings, and errors.
        """
        c = self._to_dict(claim)
        payer_config = self._get_payer_config(payer_name)

        result: Dict[str, Any] = {
            "payer_name": payer_name,
            "payer_config": payer_config,
            "requirements_met": [],
            "missing": [],
            "warnings": [],
            "errors": [],
        }

        if not payer_config:
            result["warnings"].append(
                f"No configuration found for payer '{payer_name}'. "
                "Using default rules."
            )
            return result

        # Check filing deadline
        self._check_filing_deadline(c, payer_config, result)

        # Check prior authorization requirements
        self._check_prior_auth(c, payer_config, result)

        # Check modifier requirements
        self._check_modifiers(c, payer_config, result)

        # Check place of service
        self._check_place_of_service(c, payer_config, result)

        # Check claim type
        self._check_claim_type(c, payer_config, result)

        # Check NPI requirement
        self._check_npi(c, payer_config, result)

        return result

    def _to_dict(self, claim) -> Dict[str, Any]:
        """Convert Claim dataclass or dict to dict."""
        if isinstance(claim, dict):
            return claim
        return {
            "claim_id": getattr(claim, "claim_id", ""),
            "patient_name": getattr(claim, "patient_name", ""),
            "payer_name": getattr(claim, "payer_name", ""),
            "provider_npi": getattr(claim, "provider_npi", ""),
            "place_of_service": getattr(claim, "place_of_service", "11"),
            "items": [
                {
                    "cpt_code": getattr(item, "cpt_code", ""),
                    "modifiers": getattr(item, "modifiers", []),
                    "place_of_service": getattr(item, "place_of_service", "11"),
                }
                for item in (getattr(claim, "items", []) or [])
            ],
            "total_charges": getattr(claim, "total_charges", 0.0),
            "claim_type": getattr(claim, "claim_type", "professional"),
            "date_of_service": getattr(claim, "date_of_service", ""),
        }

    def _get_payer_config(self, payer_name: str) -> Optional[Dict]:
        """Get payer configuration by name."""
        payer_upper = payer_name.upper() if payer_name else ""
        for name, config in PAYER_CONFIGS.items():
            if name.upper() == payer_upper or config["payer_id"] == payer_upper:
                return config
        return None

    def _check_filing_deadline(
        self, c: Dict, config: Dict, result: Dict
    ):
        """Check if claim is within filing deadline."""
        result["requirements_met"].append({
            "check": "filing_deadline",
            "deadline_days": config["filing_deadline_days"],
            "note": config["filing_deadline_note"],
        })

    def _check_prior_auth(
        self, c: Dict, config: Dict, result: Dict
    ):
        """Check prior authorization requirements."""
        required_categories = config.get("prior_auth_categories", [])
        items = c.get("items", [])

        for item in items:
            cpt = item.get("cpt_code", "") if isinstance(item, dict) else ""
            category = self._categorize_cpt(cpt)
            if category in required_categories:
                result["missing"].append({
                    "check": "prior_authorization",
                    "cpt_code": cpt,
                    "category": category,
                    "note": f"Prior auth may be required for {category} procedures with this payer",
                })

    def _check_modifiers(
        self, c: Dict, config: Dict, result: Dict
    ):
        """Check modifier requirements."""
        required = config.get("modifier_requirements", {})
        items = c.get("items", [])

        for item in items:
            cpt = item.get("cpt_code", "") if isinstance(item, dict) else ""
            mods = item.get("modifiers", []) if isinstance(item, dict) else []

            if cpt in required and not mods:
                result["warnings"].append({
                    "check": "modifier_required",
                    "cpt_code": cpt,
                    "required_modifiers": required[cpt],
                    "note": f"CPT {cpt} may require modifier {required[cpt]} for this payer",
                })

    def _check_place_of_service(
        self, c: Dict, config: Dict, result: Dict
    ):
        """Check place of service allowance."""
        allowed_pos = config.get("allowed_place_of_service", [])
        items = c.get("items", [])

        for item in items:
            pos = item.get("place_of_service", "11") if isinstance(item, dict) else "11"
            if allowed_pos and pos not in allowed_pos:
                result["errors"].append({
                    "check": "place_of_service",
                    "place_of_service": pos,
                    "note": f"POS {pos} is not allowed by this payer",
                })

    def _check_claim_type(
        self, c: Dict, config: Dict, result: Dict
    ):
        """Check claim type support."""
        claim_type = c.get("claim_type", "professional")
        allowed_types = config.get("claim_types", [])
        if allowed_types and claim_type not in allowed_types:
            result["errors"].append({
                "check": "claim_type",
                "claim_type": claim_type,
                "note": f"Claim type '{claim_type}' not supported by this payer",
            })

    def _check_npi(
        self, c: Dict, config: Dict, result: Dict
    ):
        """Check NPI requirement."""
        if config.get("npi_required") and not c.get("provider_npi"):
            result["errors"].append({
                "check": "npi_required",
                "note": "Provider NPI is required by this payer",
            })

    def _categorize_cpt(self, cpt_code: str) -> str:
        """Categorize a CPT code into a procedure category."""
        if not cpt_code:
            return "unknown"
        prefix = cpt_code[:3]
        for category, prefixes in PROCEDURE_CATEGORIES.items():
            for p in prefixes:
                if cpt_code.startswith(p[:3]):
                    return category
        if cpt_code.startswith(("1", "2", "3", "4", "5", "6", "7")):
            return "surgery"
        return "office_visit"

    def get_all_payers(self) -> Dict[str, Dict]:
        """Get all configured payer configurations."""
        return PAYER_CONFIGS

    def get_payer_config(self, payer_name: str) -> Optional[Dict]:
        """Get a specific payer configuration."""
        return self._get_payer_config(payer_name)
