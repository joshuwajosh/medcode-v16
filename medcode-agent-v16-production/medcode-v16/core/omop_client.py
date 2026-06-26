"""
MedCode AI Agent -- OMOPHub Client
====================================
Wrapper around the OMOPHub SDK for:
  - Semantic search over 10M+ medical concepts
  - Hierarchy navigation (parents, children)
  - Cross-vocabulary mapping
  - Code validation
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from core.config import OMOPHUB_API_KEY, OMOPHUB_TIMEOUT

logger = logging.getLogger('medcode.omop')
from core.models import CodeCandidate


@dataclass
class ConceptResult:
    """A single concept returned from OMOPHub semantic search."""
    concept_id: int = 0
    concept_name: str = ""
    domain_id: str = ""
    vocabulary_id: str = ""
    concept_code: str = ""
    similarity_score: float = 0.0
    confidence: str = "LOW"

    @classmethod
    def from_dict(cls, d: dict) -> "ConceptResult":
        score = float(d.get("similarity_score", d.get("score", 0)) or 0)
        if score >= 0.8:
            conf = "HIGH"
        elif score >= 0.6:
            conf = "MED"
        else:
            conf = "LOW"
        return cls(
            concept_id=int(d.get("concept_id", 0) or 0),
            concept_name=str(d.get("concept_name", "") or ""),
            domain_id=str(d.get("domain_id", "") or ""),
            vocabulary_id=str(d.get("vocabulary_id", "") or ""),
            concept_code=str(d.get("concept_code", "") or ""),
            similarity_score=score,
            confidence=conf,
        )

    @classmethod
    def from_concept(cls, obj) -> "ConceptResult":
        """Create from an OMOPHub concept object (dict or object)."""
        if obj is None:
            return cls()
        if isinstance(obj, dict):
            return cls.from_dict(obj)
        return cls(
            concept_id=int(getattr(obj, "concept_id", 0) or 0),
            concept_name=str(getattr(obj, "concept_name", "") or ""),
            domain_id=str(getattr(obj, "domain_id", "") or ""),
            vocabulary_id=str(getattr(obj, "vocabulary_id", "") or ""),
            concept_code=str(getattr(obj, "concept_code", "") or ""),
            similarity_score=1.0,
            confidence="HIGH",
        )

    def to_code_candidate(self) -> CodeCandidate:
        return CodeCandidate(
            code=self.concept_code,
            name=self.concept_name,
            vocabulary=self.vocabulary_id,
            similarity_score=self.similarity_score,
        )


@dataclass
class SearchResult:
    """Collection of concept search results."""
    query: str = ""
    results: list = field(default_factory=list)
    total: int = 0

    @property
    def top_result(self) -> Optional[ConceptResult]:
        return self.results[0] if self.results else None


class OMOPClient:
    """
    Wrapper around OMOPHub SDK for semantic medical concept search.
    Falls back to a REST API approach if the SDK is not installed.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OMOPHUB_API_KEY
        self._sdk = None
        self._init_sdk()

    def _init_sdk(self):
        """Try to initialize OMOPHub SDK."""
        try:
            from omophub import OMOPHubClient
            self._sdk = OMOPHubClient(api_key=self.api_key)
            logger.info("SDK initialized")
        except ImportError:
            logger.warning("omophub SDK not installed. Using REST fallback.")
            self._sdk = None
        except Exception as e:
            logger.warning("SDK init failed: %s", e)
            self._sdk = None

    def semantic_search(
        self,
        query: str,
        vocabulary_ids: list[str] = None,
        limit: int = 15,
    ) -> SearchResult:
        """
        Semantic search over medical concepts.
        Falls back to local ICD-10 database when OMOPHub API is unavailable.
        
        Args:
            query: Natural language query (e.g., "type 2 diabetes with neuropathy")
            vocabulary_ids: Filter to specific vocabularies (default: ICD10CM)
            limit: Max results to return
            
        Returns:
            SearchResult with ConceptResult items
        """
        if vocabulary_ids is None:
            vocabulary_ids = ["ICD10CM", "CPT"]

        # Try SDK first
        if self._sdk:
            try:
                resp = self._sdk.search(
                    query=query,
                    vocabulary_ids=vocabulary_ids,
                    limit=limit,
                )
                sr = self._parse_search_response(resp, query)
                if sr.results:
                    return sr
            except Exception as e:
                logger.error("SDK search error: %s", e)

        # Try local SQLite OMOP vocabulary search (Tier 2)
        local_result = self._local_search(query, vocabulary_ids, limit)
        if local_result.results:
            return local_result

        # Final fallback: REST API (unreliable, returns wrong codes often)
        return self._rest_search(query, vocabulary_ids, limit)

    def get_parents(self, vocabulary_id: str, code: str) -> list[ConceptResult]:
        """Get parent concepts (broader categories) for a code."""
        if self._sdk:
            try:
                resp = self._sdk.get_parents(vocabulary_id, code)
                results = self._parse_hierarchy_response(resp)
                if results:
                    return results
            except Exception as e:
                logger.error("get_parents error: %s", e)
        rest_result = self._rest_hierarchy(vocabulary_id, code, "parents")
        if rest_result:
            return rest_result
        from search.icd10_database import get_parents_local
        try:
            clean = code.replace(".", "").upper().strip()
            return [ConceptResult(concept_code=p, concept_name=n, vocabulary_id=vocabulary_id,
                                   similarity_score=1.0, confidence="HIGH")
                    for p, n in get_parents_local(clean)]
        except Exception:
            return []

    def get_children(self, vocabulary_id: str, code: str) -> list[ConceptResult]:
        """Get child concepts (more specific codes) for a code."""
        if self._sdk:
            try:
                resp = self._sdk.get_children(vocabulary_id, code)
                results = self._parse_hierarchy_response(resp)
                if results:
                    return results
            except Exception as e:
                logger.error("get_children error: %s", e)
        rest_result = self._rest_hierarchy(vocabulary_id, code, "children")
        if rest_result:
            return rest_result
        from search.icd10_database import get_children_local
        try:
            clean = code.replace(".", "").upper().strip()
            return [ConceptResult(concept_code=c, concept_name=n, vocabulary_id=vocabulary_id,
                                   similarity_score=1.0, confidence="HIGH")
                    for c, n in get_children_local(clean)]
        except Exception:
            return []

    def validate_code(self, vocabulary_id: str, code: str) -> Optional[ConceptResult]:
        """Validate a code exists in the vocabulary."""
        if self._sdk:
            try:
                resp = self._sdk.get_concept(vocabulary_id, code)
                if resp:
                    return ConceptResult.from_concept(resp)
                return None
            except Exception:
                pass
        from search.icd10_database import validate_code_exists, get_name
        normalized = code.upper().replace(".", "").strip()
        if validate_code_exists(normalized):
            name = get_name(normalized) or code
            return ConceptResult(
                concept_code=code,
                concept_name=name,
                vocabulary_id=vocabulary_id,
                similarity_score=1.0,
                confidence="HIGH",
            )
        return None

    def map_code(
        self,
        concept_code: str,
        source_vocabulary: str = "ICD10CM",
        target_vocabulary: str = "SNOMED",
    ) -> list[ConceptResult]:
        """Map a code from one vocabulary to another (ICD-10 ↔ SNOMED)."""
        if self._sdk:
            try:
                concept = self._sdk.get_concept(source_vocabulary, concept_code,
                                                 include_relationships=True)
                if concept:
                    rels = getattr(concept, "relationships", concept.get("relationships") if isinstance(concept, dict) else None)
                    if not rels:
                        return []
                    if isinstance(rels, dict):
                        rel_list = []
                        for v in rels.values():
                            if isinstance(v, list):
                                rel_list.extend(v)
                            elif isinstance(v, dict):
                                rel_list.append(v)
                        rels = rel_list
                    mapped = []
                    for rel in rels:
                        target = rel.get("related_concept", rel) if isinstance(rel, dict) else getattr(rel, "related_concept", rel)
                        tvocab = target.get("vocabulary_id", "") if isinstance(target, dict) else getattr(target, "vocabulary_id", "")
                        if tvocab == target_vocabulary:
                            tcode = target.get("concept_code", "") if isinstance(target, dict) else getattr(target, "concept_code", "")
                            tname = target.get("concept_name", "") if isinstance(target, dict) else getattr(target, "concept_name", "")
                            mapped.append(ConceptResult(concept_code=tcode, concept_name=tname,
                                                        vocabulary_id=tvocab, similarity_score=1.0, confidence="HIGH"))
                    return mapped
            except Exception as e:
                logger.error("map_code error: %s", e)
        return []

    def resolve_fhir_coding(self, system: str, code: str) -> Optional[ConceptResult]:
        """Resolve a FHIR Coding (system + code) to an OMOP concept."""
        if self._sdk:
            try:
                resp = self._sdk.resolve_fhir(system=system, code=code)
                if resp:
                    if isinstance(resp, dict):
                        return ConceptResult(
                            concept_code=resp.get("concept_code", code),
                            concept_name=resp.get("concept_name", resp.get("display", "")),
                            vocabulary_id=resp.get("vocabulary_id", ""),
                            domain_id=resp.get("domain_id", ""),
                            similarity_score=1.0,
                            confidence="HIGH",
                        )
                    return ConceptResult(
                        concept_code=getattr(resp, "concept_code", code),
                        concept_name=getattr(resp, "concept_name", getattr(resp, "display", "")),
                        vocabulary_id=getattr(resp, "vocabulary_id", ""),
                        domain_id=getattr(resp, "domain_id", ""),
                        similarity_score=1.0,
                        confidence="HIGH",
                    )
            except Exception as e:
                logger.error("resolve_fhir error: %s", e)
        return None

    def suggest(self, prefix: str, limit: int = 8) -> list[dict]:
        """Autocomplete suggestions as user types."""
        if self._sdk:
            try:
                suggestions = self._sdk.autocomplete(query=prefix, page_size=limit)
                result = []
                for s in (suggestions or []):
                    if isinstance(s, dict):
                        result.append(s)
                    else:
                        result.append({
                            "concept_id": getattr(s, "concept_id", 0),
                            "concept_name": getattr(s, "concept_name", ""),
                            "concept_code": getattr(s, "concept_code", ""),
                            "vocabulary_id": getattr(s, "vocabulary_id", ""),
                        })
                return result
            except Exception as e:
                logger.error("suggest error: %s", e)
        from search.icd10_database import search
        raw = search(prefix, limit=limit)
        return [{
            "concept_code": c,
            "concept_name": n,
            "vocabulary_id": "ICD10CM",
            "similarity_score": s,
        } for c, n, s in raw]

    def _parse_search_response(self, resp, query: str) -> SearchResult:
        """Parse OMOPHub search response into SearchResult."""
        result = SearchResult(query=query)

        if not resp:
            return result

        items = []
        total = 0

        if isinstance(resp, list):
            items = resp
            total = len(resp)
        elif isinstance(resp, dict):
            items = resp.get("results", resp.get("items", resp.get("data", [])))
            total = resp.get("total", len(items))

        for item in items:
            if isinstance(item, dict):
                result.results.append(ConceptResult.from_dict(item))
            else:
                result.results.append(ConceptResult.from_concept(item))

        result.total = total or len(result.results)
        return result

    def _parse_hierarchy_response(self, resp) -> list[ConceptResult]:
        """Parse hierarchy response into list of ConceptResult."""
        results = []
        if not resp:
            return results

        items = []
        if isinstance(resp, list):
            items = resp
        elif isinstance(resp, dict):
            for key in ("parents", "children", "results", "items", "data"):
                if key in resp:
                    items = resp[key]
                    break

        for item in items:
            if isinstance(item, dict):
                results.append(ConceptResult.from_dict(item))
            else:
                results.append(ConceptResult.from_concept(item))

        return results

    def _rest_search(self, query: str, vocabulary_ids: list[str], limit: int) -> SearchResult:
        """REST API fallback for semantic search."""
        import requests

        result = SearchResult(query=query)
        try:
            url = f"https://api.omophub.com/v1/search"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "query": query,
                "vocabulary_ids": vocabulary_ids,
                "limit": limit,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=OMOPHUB_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_search_response(data, query)
        except Exception as e:
            logger.error("REST search error: %s", e)

        return result

    def _rest_hierarchy(self, vocabulary_id: str, code: str, direction: str) -> list[ConceptResult]:
        """REST API fallback for hierarchy."""
        import requests

        try:
            url = f"https://api.omophub.com/v1/concepts/{vocabulary_id}/{code}/{direction}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(url, headers=headers, timeout=OMOPHUB_TIMEOUT)
            if resp.status_code == 200:
                return self._parse_hierarchy_response(resp.json())
        except Exception as e:
            logger.error("REST %s error: %s", direction, e)
        return []

    def _local_search(self, query: str, vocabulary_ids: list[str], limit: int) -> SearchResult:
        """
        Local search using OMOP vocabulary tables in SQLite.
        Queries CONCEPT + CONCEPT_SYNONYM tables, falls back to
        the static Python dictionary (icd10_database.py).
        """
        import sqlite3
        from pathlib import Path

        result = SearchResult(query=query)

        # Step 1: Try SQLite OMOP vocabulary tables
        db_path = Path(__file__).parent.parent / "medcode.db"
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            q = query.lower().strip()
            import re  # needed for fts_word splitting

            # Build vocabulary filter
            if vocabulary_ids and "ALL" not in vocabulary_ids:
                placeholders = ",".join(f"'{v}'" for v in vocabulary_ids)
                vocab_filter = f"AND c.vocabulary_id IN ({placeholders})"
            else:
                vocab_filter = ""

            # Try FTS5 full-text search first
            fts_words = [w for w in re.split(r'[\s,;:-]+', q) if len(w) > 1]
            if fts_words:
                fts_query = " AND ".join(f'"{w}"' for w in fts_words[:6])
                sql = "SELECT c.concept_id, c.concept_name, c.vocabulary_id, "
                sql += "c.concept_code, c.domain_id "
                sql += "FROM concept_fts fts JOIN concept c ON c.rowid = fts.rowid "
                sql += "WHERE concept_fts MATCH ? " + vocab_filter + " LIMIT ?"
                try:
                    cur.execute(sql, (fts_query, limit))
                    for row in cur.fetchall():
                        result.results.append(ConceptResult(
                            concept_id=int(row["concept_id"]),
                            concept_name=str(row["concept_name"]),
                            vocabulary_id=str(row["vocabulary_id"]),
                            concept_code=str(row["concept_code"]),
                            domain_id=str(row["domain_id"]),
                            similarity_score=0.9,
                            confidence="HIGH",
                        ))
                    if result.results:
                        result.total = len(result.results)
                        logger.debug("SQLite FTS: %d results for '%s'", len(result.results), query)
                        conn.close()
                        return result
                except Exception:
                    pass

            # Step 2: Fallback to keyword matching (LIKE)
            word_query = f"%{q}%"
            cur.execute(
                "SELECT DISTINCT c.concept_id, c.concept_name, c.vocabulary_id, "
                "c.concept_code, c.domain_id "
                "FROM concept c "
                "LEFT JOIN concept_synonym cs ON cs.concept_id = c.concept_id "
                "WHERE (c.concept_name LIKE ? OR cs.concept_synonym_name LIKE ?) "
                + vocab_filter +
                " ORDER BY c.concept_name LIMIT ?",
                (word_query, word_query, limit)
            )
            for row in cur.fetchall():
                score = 0.8
                name_lower = str(row["concept_name"]).lower()
                if q in name_lower or name_lower in q:
                    score = 0.95
                result.results.append(ConceptResult(
                    concept_id=int(row["concept_id"]),
                    concept_name=str(row["concept_name"]),
                    vocabulary_id=str(row["vocabulary_id"]),
                    concept_code=str(row["concept_code"]),
                    domain_id=str(row["domain_id"]),
                    similarity_score=score,
                    confidence="HIGH" if score >= 0.9 else "MED",
                ))

            if result.results:
                result.results.sort(key=lambda r: r.similarity_score, reverse=True)
                result.results = result.results[:limit]
                result.total = len(result.results)
                logger.debug("SQLite LIKE: %d results for '%s'", len(result.results), query)
                conn.close()
                return result

            # Step 2b: Word-level keyword matching (split query into individual tokens)
            # Handles cases where the full phrase doesn't match but individual words do
            # e.g., "benign nevi of skin" won't match "Benign neoplasm of skin of trunk"
            stopwords = {"the", "a", "an", "of", "to", "in", "for", "with", "on", "and", "or", "by", "at", "from", "is", "are", "was", "were", "be", "been"}
            words = [w for w in re.split(r'[\s,;:-]+', q) if len(w) > 2 and w not in stopwords]
            if words:
                word_results = {}  # concept_id -> (row, match_count)
                for word in words:
                    word_like = f"%{word}%"
                    try:
                        cur.execute(
                            "SELECT DISTINCT c.concept_id, c.concept_name, c.vocabulary_id, "
                            "c.concept_code, c.domain_id "
                            "FROM concept c "
                            "LEFT JOIN concept_synonym cs ON cs.concept_id = c.concept_id "
                            "WHERE (c.concept_name LIKE ? OR cs.concept_synonym_name LIKE ?) "
                            + vocab_filter +
                            " ORDER BY c.concept_name LIMIT ?",
                            (word_like, word_like, limit)
                        )
                        for row in cur.fetchall():
                            cid = int(row["concept_id"])
                            if cid not in word_results:
                                word_results[cid] = (row, 0)
                            word_results[cid] = (row, word_results[cid][1] + 1)
                    except Exception:
                        continue

                for cid, (row, match_count) in word_results.items():
                    score = 0.7 + (match_count / max(len(words), 1)) * 0.25
                    if score > 0.95:
                        score = 0.95
                    result.results.append(ConceptResult(
                        concept_id=cid,
                        concept_name=str(row["concept_name"]),
                        vocabulary_id=str(row["vocabulary_id"]),
                        concept_code=str(row["concept_code"]),
                        domain_id=str(row["domain_id"]),
                        similarity_score=round(score, 3),
                        confidence="HIGH" if score >= 0.9 else ("MED" if score >= 0.75 else "LOW"),
                    ))

            conn.close()

            if result.results:
                result.results.sort(key=lambda r: r.similarity_score, reverse=True)
                result.results = result.results[:limit]
                result.total = len(result.results)
                logger.debug("SQLite word-match: %d results for '%s'", len(result.results), query)
                return result

        except Exception as e:
            logger.error("SQLite search error: %s", e)
            try:
                conn.close()
            except Exception:
                pass

        # Step 3: Fallback to static Python dictionary
        from search.icd10_database import search_with_vocabulary
        raw_results = search_with_vocabulary(query, vocabulary_ids, limit)

        for item in raw_results:
            result.results.append(ConceptResult.from_dict(item))

        result.total = len(result.results)
        if result.results:
            logger.debug("Static DB fallback: %d results for '%s'", len(result.results), query)
        else:
            logger.debug("Static DB: no results for '%s'", query)

        return result