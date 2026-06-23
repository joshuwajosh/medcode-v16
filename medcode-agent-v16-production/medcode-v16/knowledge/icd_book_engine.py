"""
ICD-10-CM 2026 OCR Book Engine
===============================
Parses books/icd_ocr_full.txt and builds a structured knowledge engine.
Extracts ICD-10-CM codes with descriptions from index and tabular sections.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_BOOK_DIR = Path(__file__).resolve().parent.parent / "books"
_ICD_FILE = _BOOK_DIR / "icd_ocr_full.txt"
_CACHE_FILE = Path(__file__).resolve().parent / "icd_book_data.json"

_ICD_CODE_RE = re.compile(r"^[A-Z]\d{2}(?:\.\d{1,4})?")
_ICD_CHAPTERS = {
    "I": {"name": "Certain infectious and parasitic diseases", "range": ("A00", "B99")},
    "II": {"name": "Neoplasms", "range": ("C00", "D49")},
    "III": {"name": "Diseases of the blood and blood-forming organs", "range": ("D50", "D89")},
    "IV": {"name": "Endocrine, nutritional and metabolic diseases", "range": ("E00", "E89")},
    "V": {"name": "Mental, behavioral and neurodevelopmental disorders", "range": ("F01", "F99")},
    "VI": {"name": "Diseases of the nervous system", "range": ("G00", "G99")},
    "VII": {"name": "Diseases of the eye and adnexa", "range": ("H00", "H59")},
    "VIII": {"name": "Diseases of the ear and mastoid process", "range": ("H60", "H95")},
    "IX": {"name": "Diseases of the circulatory system", "range": ("I00", "I99")},
    "X": {"name": "Diseases of the respiratory system", "range": ("J00", "J99")},
    "XI": {"name": "Diseases of the digestive system", "range": ("K00", "K95")},
    "XII": {"name": "Diseases of the skin and subcutaneous tissue", "range": ("L00", "L99")},
    "XIII": {"name": "Diseases of the musculoskeletal system and connective tissue", "range": ("M00", "M99")},
    "XIV": {"name": "Diseases of the genitourinary system", "range": ("N00", "N99")},
    "XV": {"name": "Pregnancy, childbirth and the puerperium", "range": ("O00", "O9A")},
    "XVI": {"name": "Certain conditions originating in the perinatal period", "range": ("P00", "P96")},
    "XVII": {"name": "Congenital malformations, deformations, and chromosomal abnormalities", "range": ("Q00", "QA0")},
    "XVIII": {"name": "Symptoms, signs and abnormal clinical and laboratory findings", "range": ("R00", "R99")},
    "XIX": {"name": "Injury, poisoning and certain other consequences of external causes", "range": ("S00", "T88")},
    "XX": {"name": "External causes of morbidity", "range": ("V00", "Y99")},
    "XXI": {"name": "Factors influencing health status and contact with health services", "range": ("Z00", "Z99")},
    "XXII": {"name": "Codes for special purposes", "range": ("U00", "U85")},
}

_CHAPTER_RANGES: List[Tuple[str, str, str, str]] = [
    ("A00", "B99", "I", "Infectious and parasitic diseases"),
    ("C00", "D49", "II", "Neoplasms"),
    ("D50", "D89", "III", "Diseases of blood/blood-forming organs"),
    ("E00", "E89", "IV", "Endocrine, nutritional, metabolic"),
    ("F01", "F99", "V", "Mental, behavioral, neurodevelopmental"),
    ("G00", "G99", "VI", "Diseases of the nervous system"),
    ("H00", "H59", "VII", "Diseases of the eye and adnexa"),
    ("H60", "H95", "VIII", "Diseases of the ear and mastoid"),
    ("I00", "I99", "IX", "Diseases of the circulatory system"),
    ("J00", "J99", "X", "Diseases of the respiratory system"),
    ("K00", "K95", "XI", "Diseases of the digestive system"),
    ("L00", "L99", "XII", "Diseases of the skin and subcutaneous tissue"),
    ("M00", "M99", "XIII", "Diseases of the musculoskeletal system"),
    ("N00", "N99", "XIV", "Diseases of the genitourinary system"),
    ("O00", "O9A", "XV", "Pregnancy, childbirth and puerperium"),
    ("P00", "P96", "XVI", "Conditions originating in perinatal period"),
    ("Q00", "QA0", "XVII", "Congenital malformations"),
    ("R00", "R99", "XVIII", "Symptoms, signs, abnormal findings"),
    ("S00", "T88", "XIX", "Injury, poisoning, external causes"),
    ("V00", "Y99", "XX", "External causes of morbidity"),
    ("Z00", "Z99", "XXI", "Health status and contact with health services"),
    ("U00", "U85", "XXII", "Codes for special purposes"),
]

_SEVENTH_CHAR_CATEGORIES = {
    "S", "T", "M", "N", "O", "P", "Q", "R",
}


def _code_sort_key(code: str) -> Tuple[str, str]:
    letter = code[0] if code else "Z"
    rest = code[1:] if len(code) > 1 else "0"
    return (letter, rest)


def _code_to_tuple(code: str) -> Tuple[str, str]:
    m = re.match(r"([A-Z])(\d+\.?\d*)", code)
    if m:
        return (m.group(1), m.group(2))
    return (code[:1], code[1:])


def _code_in_range(code: str, start: str, end: str) -> bool:
    letter = code[0] if code else ""
    start_letter = start[0]
    end_letter = end[0]
    if letter < start_letter or letter > end_letter:
        return False
    if letter == start_letter:
        s1 = _code_to_tuple(code)[1]
        s2 = _code_to_tuple(start)[1]
        if s1 < s2:
            return False
    if letter == end_letter:
        e1 = _code_to_tuple(code)[1]
        e2 = _code_to_tuple(end)[1]
        if e1 > e2:
            return False
    return True


def _detect_chapter(code: str) -> str:
    for start, end, roman, _name in _CHAPTER_RANGES:
        if _code_in_range(code, start, end):
            return roman
    return ""


def _detect_category_from_code(code: str) -> str:
    for start, end, _, name in _CHAPTER_RANGES:
        if _code_in_range(code, start, end):
            return name
    return "Unknown"


def _needs_seventh_char(code: str) -> bool:
    if len(code) < 3:
        return False
    letter = code[0]
    if letter in _SEVENTH_CHAR_CATEGORIES:
        if letter in ("S", "T"):
            if len(code) >= 4:
                return True
        elif letter in ("M"):
            if len(code) >= 4:
                return True
    return False


def _clean_ocr_text(text: str) -> str:
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class ICDBookEngine:
    def __init__(self, force_rebuild: bool = False):
        self.codes: Dict[str, Dict[str, Any]] = {}
        self.index_terms: Dict[str, List[str]] = {}
        if force_rebuild or not _CACHE_FILE.exists():
            self._parse_book()
            self._save_cache()
        else:
            self._load_cache()

    def _load_cache(self):
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.codes = data.get("codes", {})
        self.index_terms = data.get("index_terms", {})

    def _save_cache(self):
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"codes": self.codes, "index_terms": self.index_terms}, f, indent=1)

    def _parse_book(self):
        if not _ICD_FILE.exists():
            return
        text = _ICD_FILE.read_text(encoding="utf-8", errors="replace")
        pages = text.split("--- PAGE ")

        in_index = False
        in_tabular = False
        current_chapter = ""
        current_chapter_name = ""

        for page in pages:
            if not page.strip():
                continue
            lines = page.split("\n")
            page_text = "\n".join(lines)

            if "Index to Diseases" in page_text or "Alphabetic Index" in page_text:
                in_index = True
                in_tabular = False
            elif "Tabular List" in page_text and "Chapter" in page_text:
                in_index = False
                in_tabular = True
                m = re.search(r"Chapter\s+(\d+)\s*[:\-]?\s*(.*?)\s*\(", page_text)
                if m:
                    current_chapter = m.group(1)
                    current_chapter_name = m.group(2).strip()

            if in_index:
                self._parse_index_page(page_text)
            elif in_tabular:
                self._parse_tabular_page(page_text, current_chapter, current_chapter_name)

    def _parse_index_page(self, page_text: str):
        lines = page_text.split("\n")
        for line in lines:
            line_s = line.strip()
            if not line_s or len(line_s) < 5:
                continue
            if re.match(r"---\s*PAGE", line_s):
                continue
            if re.match(r"\d+$", line_s):
                continue
            if re.match(r"ICD-10-CM", line_s, re.IGNORECASE):
                continue

            code_match = re.search(r"\b([A-Z]\d{2}(?:\.\d{1,4})?)\b", line_s)
            if not code_match:
                continue
            code = code_match.group(1)
            code_upper = code.upper()

            term_part = line_s[:code_match.start()].strip()
            term_part = re.sub(r"\s*[-—]\s*see\s+.*$", "", term_part, flags=re.IGNORECASE)
            term_part = re.sub(r"\s*[-—]\s*see also\s+.*$", "", term_part, flags=re.IGNORECASE)
            term_part = _clean_ocr_text(term_part)
            if not term_part or len(term_part) < 2:
                continue
            term_part = term_part[:200]

            chapter = _detect_chapter(code_upper)
            category = _detect_category_from_code(code_upper)

            if code_upper not in self.codes:
                self.codes[code_upper] = {
                    "desc": "",
                    "category": category,
                    "chapter": chapter,
                    "billable": True,
                }

            if term_part:
                key = term_part.lower()[:100]
                if key not in self.index_terms:
                    self.index_terms[key] = []
                if code_upper not in self.index_terms[key]:
                    self.index_terms[key].append(code_upper)

    def _parse_tabular_page(self, page_text: str, chapter_num: str, chapter_name: str):
        lines = page_text.split("\n")
        current_code = ""
        current_desc_lines: List[str] = []

        for line in lines:
            line_s = line.strip()
            if not line_s:
                if current_code and current_desc_lines:
                    desc = " ".join(current_desc_lines)
                    desc = _clean_ocr_text(desc)
                    if desc and current_code in self.codes:
                        if not self.codes[current_code]["desc"]:
                            self.codes[current_code]["desc"] = desc[:500]
                    elif desc and current_code:
                        chapter = _detect_chapter(current_code)
                        category = _detect_category_from_code(current_code)
                        self.codes[current_code] = {
                            "desc": desc[:500],
                            "category": category,
                            "chapter": chapter or chapter_num,
                            "billable": True,
                        }
                current_code = ""
                current_desc_lines = []
                continue

            code_match = re.match(r"^\s*([A-Z]\d{2}(?:\.\d{1,4})?)\s+(.*)", line_s)
            if code_match:
                if current_code and current_desc_lines:
                    desc = " ".join(current_desc_lines)
                    desc = _clean_ocr_text(desc)
                    if desc and current_code in self.codes:
                        if not self.codes[current_code]["desc"]:
                            self.codes[current_code]["desc"] = desc[:500]
                    elif desc and current_code:
                        chapter = _detect_chapter(current_code)
                        category = _detect_category_from_code(current_code)
                        self.codes[current_code] = {
                            "desc": desc[:500],
                            "category": category,
                            "chapter": chapter or chapter_num,
                            "billable": True,
                        }

                new_code = code_match.group(1).upper()
                rest = code_match.group(2).strip()
                if re.match(r"^[A-Z]\d{2}", new_code) and len(new_code) >= 3:
                    current_code = new_code
                    current_desc_lines = [rest] if rest else []
                    if current_code not in self.codes:
                        chapter = _detect_chapter(current_code)
                        category = _detect_category_from_code(current_code)
                        self.codes[current_code] = {
                            "desc": "",
                            "category": category,
                            "chapter": chapter or chapter_num,
                            "billable": True,
                        }
                else:
                    current_desc_lines.append(line_s)
            else:
                stripped_match = re.match(r"^\s*(\d{2,3}(?:\.\d{1,4})?)\s+([A-Z].{5,})", line_s)
                if stripped_match:
                    potential_code = stripped_match.group(1)
                    desc_part = stripped_match.group(2)
                    if current_code and current_desc_lines:
                        desc = " ".join(current_desc_lines)
                        desc = _clean_ocr_text(desc)
                        if desc and current_code in self.codes:
                            if not self.codes[current_code]["desc"]:
                                self.codes[current_code]["desc"] = desc[:500]

                    code_num = int(potential_code.split(".")[0]) if potential_code.split(".")[0].isdigit() else 0
                    if 10 <= code_num <= 999:
                        recovered_code = "I" + potential_code
                    elif code_num >= 1000:
                        recovered_code = "D" + potential_code
                    else:
                        recovered_code = potential_code

                    current_code = recovered_code
                    current_desc_lines = [desc_part]
                    if current_code not in self.codes:
                        chapter = _detect_chapter(current_code)
                        category = _detect_category_from_code(current_code)
                        self.codes[current_code] = {
                            "desc": "",
                            "category": category,
                            "chapter": chapter or chapter_num,
                            "billable": True,
                        }
                elif current_code:
                    current_desc_lines.append(line_s)

        if current_code and current_desc_lines:
            desc = " ".join(current_desc_lines)
            desc = _clean_ocr_text(desc)
            if desc and current_code in self.codes:
                if not self.codes[current_code]["desc"]:
                    self.codes[current_code]["desc"] = desc[:500]

    def lookup_icd(self, code: str) -> Optional[Dict[str, Any]]:
        code_upper = code.upper()
        result = self.codes.get(code_upper)
        if not result:
            for key in self.codes:
                if key.startswith(code_upper):
                    result = self.codes[key]
                    break
        return result

    def search_icd(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        keyword_lower = keyword.lower()
        results = []
        for term_key, code_list in self.index_terms.items():
            if keyword_lower in term_key:
                for code in code_list[:2]:
                    entry = self.codes.get(code, {})
                    results.append({
                        "code": code,
                        "term": term_key,
                        "desc": entry.get("desc", ""),
                        "category": entry.get("category", ""),
                        "chapter": entry.get("chapter", ""),
                    })
                    if len(results) >= limit:
                        return results
        for code, data in self.codes.items():
            desc = data.get("desc", "").lower()
            if keyword_lower in desc or keyword_lower in code.lower():
                results.append({
                    "code": code,
                    "desc": data.get("desc", ""),
                    "category": data.get("category", ""),
                    "chapter": data.get("chapter", ""),
                })
                if len(results) >= limit:
                    break
        return results

    def get_chapter_codes(self, chapter: str) -> List[Dict[str, Any]]:
        results = []
        for code, data in sorted(self.codes.items(), key=lambda x: _code_sort_key(x[0])):
            if data.get("chapter") == chapter:
                results.append({"code": code, **data})
        return results

    def get_codes_by_category(self, category: str) -> List[Dict[str, Any]]:
        results = []
        for code, data in sorted(self.codes.items(), key=lambda x: _code_sort_key(x[0])):
            if data.get("category") == category:
                results.append({"code": code, **data})
        return results

    def expand_seventh_char(self, code: str, description: str = "") -> List[Dict[str, Any]]:
        code_upper = code.upper()
        base_match = re.match(r"^([A-Z]\d{2}(?:\.\d{1,4})?)[A-D]$", code_upper)
        if not base_match:
            return [{"code": code_upper, "desc": description}]
        base = base_match.group(1)
        seventh_chars = {
            "A": "initial encounter",
            "B": "subsequent encounter",
            "C": "sequela",
            "D": "subsequent encounter (fracture healing)",
        }
        results = []
        for char, encounter_type in seventh_chars.items():
            full_code = base + char
            entry = self.codes.get(full_code, {})
            desc = entry.get("desc", description)
            if not desc:
                desc = f"{description} ({encounter_type})"
            results.append({
                "code": full_code,
                "desc": desc,
                "encounter_type": encounter_type,
                "chapter": entry.get("chapter", _detect_chapter(full_code)),
            })
        return results

    @property
    def total_codes(self) -> int:
        return len(self.codes)

    @property
    def total_index_terms(self) -> int:
        return len(self.index_terms)


_engine: Optional[ICDBookEngine] = None


def get_engine(force: bool = False) -> ICDBookEngine:
    global _engine
    if _engine is None or force:
        _engine = ICDBookEngine(force_rebuild=force)
    return _engine


def lookup_icd(code: str) -> Optional[Dict[str, Any]]:
    return get_engine().lookup_icd(code)


def search_icd(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    return get_engine().search_icd(keyword, limit)


def get_chapter_codes(chapter: str) -> List[Dict[str, Any]]:
    return get_engine().get_chapter_codes(chapter)
