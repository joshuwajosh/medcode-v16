"""
MedCode AI Agent -- Beam-Search BFS Hierarchy Traversal
=========================================================
Iterative beam-search BFS over the ICD-10 hierarchy.
Starts from seed codes and expands parents/children, scoring each with the LLM.
"""

import heapq
import logging
from typing import Optional

logger = logging.getLogger('medcode.bfs')

from core.models import CodeCandidate, ExtractedClinicalData
from core.omop_client import OMOPClient
from core.config import (
    BEAM_WIDTH_BALANCED, BEAM_WIDTH_DEEP,
    BFS_MAX_DEPTH_BALANCED, BFS_MAX_DEPTH_DEEP,
    BFS_EXPLORE_THRESHOLD,
    BFS_MAX_ITERATIONS_BALANCED, BFS_MAX_ITERATIONS_DEEP,
)


class BFSHierarchyTraversal:
    """
    Beam-search BFS over medical code hierarchy.
    
    Starting from seed code candidates from semantic search, iteratively:
    1. Pops the highest-scoring candidate from the beam
    2. Gets its parent codes (broader) and child codes (more specific)
    3. Scores each with the LLM for relevance to the clinical context
    4. Keeps candidates above threshold in the beam
    5. Prunes beam to beam_width for next iteration
    """

    def __init__(self, omop_client: OMOPClient, llm_client):
        self.omop = omop_client
        self.llm = llm_client

    async def expand(
        self,
        seed_candidates: list[dict],
        clinical_context: str,
        mode: str = "balanced",
    ) -> list[CodeCandidate]:
        """
        Expand seed code candidates via beam-search BFS.
        Only expands ICD-10 codes (CPT codes have no hierarchy).
        
        Args:
            seed_candidates: List of dicts with 'code', 'name', and optionally 'score'
            clinical_context: The clinical context for LLM scoring
            mode: 'quick' (no BFS), 'balanced' (5-beam, 2-depth), 'deep' (10-beam, 3-depth)
            
        Returns:
            Expanded list of CodeCandidate objects
        """
        if mode == "quick":
            return await self._seeds_to_candidates(seed_candidates)

        # Separate ICD10 codes (expandable via hierarchy) from CPT/HCPCS (no hierarchy)
        icd_seeds = [s for s in seed_candidates if s.get("vocabulary", "ICD10CM") == "ICD10CM"]
        non_icd_seeds = [s for s in seed_candidates if s.get("vocabulary", "ICD10CM") != "ICD10CM"]

        # Non-ICD codes (CPT/HCPCS) are returned directly without hierarchy expansion
        expanded: list[CodeCandidate] = []
        for s in non_icd_seeds:
            c = CodeCandidate(
                code=s.get("code", ""),
                name=s.get("name", ""),
                vocabulary=s.get("vocabulary", "CPT"),
                similarity_score=s.get("score", 0),
            )
            if c.code and not any(ex.code == c.code for ex in expanded):
                expanded.append(c)

        beam_width = BEAM_WIDTH_BALANCED if mode == "balanced" else BEAM_WIDTH_DEEP
        max_iterations = BFS_MAX_ITERATIONS_BALANCED if mode == "balanced" else BFS_MAX_ITERATIONS_DEEP
        threshold = BFS_EXPLORE_THRESHOLD

        visited = set()
        
        # Priority queue: (-score, index, candidate_dict)
        beam = []
        for i, sc in enumerate(icd_seeds[:beam_width]):
            score = sc.get("score", 50)
            heapq.heappush(beam, (-score, i, sc))

        iteration = 0
        while beam and iteration < max_iterations:
            _, _, current = heapq.heappop(beam)
            code = current.get("code", "")

            if code in visited:
                continue
            visited.add(code)

            # Add to expanded list if not already there
            if not any(c.code == code for c in expanded):
                candidate = CodeCandidate(
                    code=code,
                    name=current.get("name", ""),
                    vocabulary=current.get("vocabulary", "ICD10CM"),
                    similarity_score=current.get("score", 0),
                    llm_score=current.get("llm_score", 0),
                )
                expanded.append(candidate)

            # Quick LLM score to decide if we should explore this branch
            relevance = await self._score_relevance(code, current.get("name", ""), clinical_context)

            if relevance >= threshold or mode == "deep":
                # Expand parents
                try:
                    parents = self.omop.get_parents("ICD10CM", code)
                    for p in parents[:3]:
                        if p.concept_code and p.concept_code not in visited:
                            heapq.heappush(beam, (
                                -relevance,
                                len(visited) + len(beam),
                                {"code": p.concept_code, "name": p.concept_name, "score": relevance},
                            ))
                except Exception:
                    pass

                # Expand children
                try:
                    children = self.omop.get_children("ICD10CM", code)
                    for c in children[:5]:
                        if c.concept_code and c.concept_code not in visited:
                            heapq.heappush(beam, (
                                -relevance,
                                len(visited) + len(beam),
                                {"code": c.concept_code, "name": c.concept_name, "score": relevance},
                            ))
                except Exception:
                    pass

            # Prune beam to beam_width
            while len(beam) > beam_width * 2:
                heapq.heappop(beam)

            iteration += 1

        logger.debug("%s mode -- explored %d codes in %d iterations", mode, len(expanded), iteration)
        return expanded

    async def _score_relevance(self, code: str, name: str, clinical_context: str) -> int:
        """Quick LLM call to score code relevance."""
        prompt = f"""Given this clinical context: {clinical_context[:200]}
        
ICD-10 code: {code} - {name}

Rate relevance 0-100:
- 0-20: Unrelated
- 21-40: Tangentially related
- 41-60: Moderately relevant
- 61-80: Relevant
- 81-100: Very relevant

Return ONLY a number 0-100."""

        try:
            raw = self.llm.call_llm(
                "You are a medical coding expert. Return ONLY a number 0-100.",
                prompt,
                max_tokens=10,
            )
            import re
            nums = re.findall(r"\d+", raw)
            if nums:
                return min(100, int(nums[0]))
        except Exception:
            pass
        return 50  # Neutral fallback

    async def _seeds_to_candidates(self, seeds: list[dict]) -> list[CodeCandidate]:
        """Convert seed dicts to CodeCandidate objects."""
        return [
            CodeCandidate(
                code=s.get("code", ""),
                name=s.get("name", ""),
                vocabulary=s.get("vocabulary", "ICD10CM"),
                similarity_score=s.get("score", 0),
            )
            for s in seeds
        ]
