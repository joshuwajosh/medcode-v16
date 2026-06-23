"""
CPT 2026 OCR Book Engine
========================
Parses books/cpt_ocr_full.txt and builds a structured knowledge engine.
Extracts CPT codes with descriptions, guidelines, RVU values, and categories.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_BOOK_DIR = Path(__file__).resolve().parent.parent / "books"
_CPT_FILE = _BOOK_DIR / "cpt_ocr_full.txt"
_CACHE_FILE = Path(__file__).resolve().parent / "cpt_book_data.json"

_CPT_CODE_RE = re.compile(r"^(\d{5})\s*$")
_CPT_CODE_INLINE_RE = re.compile(r"(\d{5})\s")
_CATEGORY_MAP = {
    "E/M": (99202, 99499),
    "Anesthesia": (100, 1999),
    "Surgery": (10000, 69999),
    "Radiology": (70000, 79999),
    "Pathology/Laboratory": (80000, 89999),
    "Medicine": (90281, 99607),
}


def _detect_category(code: int) -> str:
    if 99202 <= code <= 99499:
        return "E/M"
    if 100 <= code <= 1999:
        return "Anesthesia"
    if 10000 <= code <= 69999:
        return "Surgery"
    if 70000 <= code <= 79999:
        return "Radiology"
    if 80000 <= code <= 89999:
        return "Pathology/Laboratory"
    if 90281 <= code <= 99607:
        return "Medicine"
    return "Unknown"


def _detect_surgery_section(text: str) -> str:
    sections = {
        "Integumentary System": "Integumentary",
        "Musculoskeletal System": "Musculoskeletal",
        "Respiratory System": "Respiratory",
        "Cardiovascular System": "Cardiovascular",
        "Digestive System": "Digestive",
        "Urinary System": "Urinary",
        "Male Reproductive System": "Male Reproductive",
        "Female Reproductive System": "Female Reproductive",
        "Nervous System": "Nervous",
        "Eye and Ocular Adnexa": "Eye",
        "Auditory System": "Auditory",
        "Hemic and Lymphatic Systems": "Hemic/Lymphatic",
        "Mediastinum": "Mediastinum",
        "Diaphragm": "Diaphragm",
    }
    for header, short in sections.items():
        if header.lower() in text.lower():
            return short
    return "Surgery"


def _is_rvu_line(line: str) -> bool:
    parts = line.strip().split()
    if len(parts) >= 2:
        try:
            float(parts[-1])
            return True
        except ValueError:
            pass
    return False


def _extract_em_time_minutes(desc_text: str) -> Optional[int]:
    m = re.search(r"(\d+)\s*minutes?\s*must\s*be\s*met\s*or\s*exceeded", desc_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _clean_ocr_text(text: str) -> str:
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class CPTBookEngine:
    def __init__(self, force_rebuild: bool = False):
        self.codes: Dict[str, Dict[str, Any]] = {}
        self._guidelines: Dict[str, str] = {}
        self._em_mdm_tables: List[Dict] = []
        if force_rebuild or not _CACHE_FILE.exists():
            self._parse_book()
            self._save_cache()
        else:
            self._load_cache()

    def _load_cache(self):
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.codes = data.get("codes", {})
        self._guidelines = data.get("guidelines", {})

    def _save_cache(self):
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"codes": self.codes, "guidelines": self._guidelines}, f, indent=1)

    def _parse_book(self):
        if not _CPT_FILE.exists():
            return
        text = _CPT_FILE.read_text(encoding="utf-8", errors="replace")
        pages = text.split("--- PAGE ")
        current_section = ""
        current_category = "Unknown"
        in_em_section = False

        for page in pages:
            if not page.strip():
                continue
            lines = page.split("\n")
            page_header = ""
            if lines:
                first_line = lines[0].strip()
                m = re.match(r"(\d+)\s*---", first_line)
                if m:
                    page_header = " ".join(lines[1:4]) if len(lines) > 1 else ""

            if "Evaluation and Management" in page_header or "evaluation and management" in page_header.lower():
                in_em_section = True
                current_category = "E/M"
            elif re.search(r"Surgery\s*/\s*", page_header):
                in_em_section = False
                current_category = "Surgery"
                current_section = _detect_surgery_section(page_header)
            elif "Radiology" in page_header:
                in_em_section = False
                current_category = "Radiology"
            elif "Pathology" in page_header or "Laboratory" in page_header:
                in_em_section = False
                current_category = "Pathology/Laboratory"
            elif "Medicine" in page_header:
                in_em_section = False
                current_category = "Medicine"
            elif "Anesthesia" in page_header:
                in_em_section = False
                current_category = "Anesthesia"

            if "Medical Decision Making" in page:
                self._parse_em_mdm_table(page)

            self._parse_page_codes(page, current_category, current_section)

            if in_em_section and len(page) > 200:
                guideline_text = _clean_ocr_text(page)
                if len(guideline_text) > 100:
                    self._guidelines.setdefault("E/M", "")
                    if len(self._guidelines["E/M"]) < 50000:
                        self._guidelines["E/M"] += "\n" + guideline_text[:2000]

    def _parse_em_mdm_table(self, page_text: str):
        lines = page_text.split("\n")
        mdm = {}
        for line in lines:
            line_s = line.strip()
            if "Straightforward" in line_s:
                mdm["straightforward"] = True
            elif "Low" in line_s and "level" not in line_s.lower():
                mdm["low"] = True
            elif "Moderate" in line_s:
                mdm["moderate"] = True
            elif "High" in line_s:
                mdm["high"] = True
        if mdm and mdm not in self._em_mdm_tables:
            self._em_mdm_tables.append(mdm)

    def _parse_page_codes(self, page_text: str, category: str, section: str):
        lines = page_text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            m = _CPT_CODE_RE.match(line)
            if m:
                code_str = m.group(1)
                code_int = int(code_str)
                if code_int < 100 or code_int > 99999:
                    i += 1
                    continue
                detected_cat = _detect_category(code_int)
                if detected_cat != "Unknown":
                    category = detected_cat
                desc_lines = []
                j = i + 1
                while j < len(lines) and j < i + 8:
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if _CPT_CODE_RE.match(next_line):
                        break
                    if re.match(r"CPT\s+\d{4}", next_line):
                        break
                    if re.match(r"---\s*PAGE", next_line):
                        break
                    if re.match(r"^\+\s*\d{5}", next_line):
                        break
                    if re.match(r"^\d{5}\s", next_line):
                        break
                    desc_lines.append(next_line)
                    j += 1

                description = " ".join(desc_lines).strip()
                description = _clean_ocr_text(description)
                if len(description) > 500:
                    description = description[:500]

                time_min = _extract_em_time_minutes(description)

                entry: Dict[str, Any] = {
                    "desc": description if description else f"CPT {code_str}",
                    "category": category,
                }
                if section and category == "Surgery":
                    entry["section"] = section
                if time_min:
                    entry["time_minutes"] = time_min

                if code_int >= 10000:
                    subcat = ""
                    if 10000 <= code_int <= 19999:
                        subcat = "Integumentary System"
                    elif 20000 <= code_int <= 29999:
                        subcat = "Musculoskeletal System"
                    elif 30000 <= code_int <= 32999:
                        subcat = "Respiratory System"
                    elif 33000 <= code_int <= 37799:
                        subcat = "Cardiovascular System"
                    elif 38000 <= code_int <= 49499:
                        subcat = "Digestive System"
                    elif 50010 <= code_int <= 53899:
                        subcat = "Urinary System"
                    elif 54000 <= code_int <= 56799:
                        subcat = "Male Reproductive System"
                    elif 57000 <= code_int <= 58999:
                        subcat = "Female Reproductive System"
                    elif 61000 <= code_int <= 64999:
                        subcat = "Nervous System"
                    elif 65090 <= code_int <= 68899:
                        subcat = "Eye and Ocular Adnexa"
                    elif 69000 <= code_int <= 69979:
                        subcat = "Auditory System"
                    if subcat:
                        entry["section"] = subcat

                existing = self.codes.get(code_str)
                if existing:
                    if len(description) > len(existing.get("desc", "")):
                        existing["desc"] = description
                else:
                    self.codes[code_str] = entry
                i = j
            else:
                i += 1

    def lookup_cpt(self, code: str) -> Optional[Dict[str, Any]]:
        return self.codes.get(code)

    def search_cpt(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        keyword_lower = keyword.lower()
        results = []
        for code, data in self.codes.items():
            desc = data.get("desc", "").lower()
            if keyword_lower in desc or keyword_lower in code:
                results.append({"code": code, **data})
                if len(results) >= limit:
                    break
        return results

    def get_em_codes(self) -> List[Dict[str, Any]]:
        return [
            {"code": code, **data}
            for code, data in sorted(self.codes.items())
            if data.get("category") == "E/M"
        ]

    def get_surgery_codes(self) -> List[Dict[str, Any]]:
        results = []
        for code, data in sorted(self.codes.items()):
            if data.get("category") == "Surgery":
                results.append({"code": code, **data})
        return results

    def get_guidelines(self, category: Optional[str] = None) -> Dict[str, str]:
        if category:
            return {category: self._guidelines.get(category, "")}
        return dict(self._guidelines)

    def get_em_mdm_tables(self) -> List[Dict]:
        return list(self._em_mdm_tables)

    @property
    def total_codes(self) -> int:
        return len(self.codes)


def _build_engine(force: bool = False) -> CPTBookEngine:
    return CPTBookEngine(force_rebuild=force)


_engine: Optional[CPTBookEngine] = None


def get_engine(force: bool = False) -> CPTBookEngine:
    global _engine
    if _engine is None or force:
        _engine = _build_engine(force)
    return _engine


def lookup_cpt(code: str) -> Optional[Dict[str, Any]]:
    return get_engine().lookup_cpt(code)


def search_cpt(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    return get_engine().search_cpt(keyword, limit)


def get_em_codes() -> List[Dict[str, Any]]:
    return get_engine().get_em_codes()


def get_surgery_codes() -> List[Dict[str, Any]]:
    return get_engine().get_surgery_codes()
