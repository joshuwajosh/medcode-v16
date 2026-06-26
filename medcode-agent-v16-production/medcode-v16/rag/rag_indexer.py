"""
RAG Indexer — MedCodeAI
========================
Builds an in-memory search index across all 14 RAG knowledge collections.
Provides vector-like similarity search using keyword overlap (no external embeddings).
"""

from __future__ import annotations
import logging
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger('medcode.rag_indexer')

from data.rag_models import (
    RetrievalSource, RAGContext, RAGResult,
    CMSDocument, NCCIEdit, CPTExample, CodingClinicEntry,
    SpecialtyCase, OperativeNote, CPCExamQuestion,
    AuditCase, ModifierCase, DenialCase, PayerRule,
    ProcedureTemplate, AnatomyEntry, BenchmarkTest,
)
from data.cms.cms_repository import get_cms_repository
from data.ncci.ncci_repository import get_ncci_repository
from data.cpt_examples.cpt_example_repository import get_cpt_example_repository
from data.coding_clinic.coding_clinic_repository import get_coding_clinic_repository
from data.specialty_cases.specialty_case_repository import get_specialty_case_repository
from data.operative_notes.operative_note_repository import get_operative_note_repository
from data.cpc_exam_bank.cpc_exam_repository import get_cpc_exam_repository
from data.audit_cases.audit_case_repository import get_audit_case_repository
from data.modifier_cases.modifier_case_repository import get_modifier_case_repository
from data.denial_cases.denial_case_repository import get_denial_case_repository
from data.payer_rules.payer_rule_repository import get_payer_rule_repository
from data.procedure_templates.procedure_template_repository import get_procedure_template_repository
from data.anatomy_reference.anatomy_repository import get_anatomy_repository
from data.benchmark_tests.benchmark_repository import get_benchmark_repository


@dataclass
class IndexedDocument:
    """A document in the RAG search index."""
    id: str
    source: RetrievalSource
    text: str
    keywords: List[str] = field(default_factory=list)
    specialty: str = ""
    codes: List[str] = field(default_factory=list)
    original: Any = None


class RAGIndexer:
    """
    In-memory search index over all RAG knowledge collections.
    Uses token overlap scoring for retrieval (no external API calls).
    """

    def __init__(self):
        self._documents: List[IndexedDocument] = []
        self._initialized = False

    def initialize(self):
        """Load all data collections into the search index."""
        if self._initialized:
            return
        start = time.time()

        # Load CMS documents
        cms_repo = get_cms_repository()
        for doc in cms_repo.get_all():
            text = f"{doc.topic} {doc.content} {' '.join(doc.keywords)}"
            self._documents.append(IndexedDocument(
                id=doc.document_id, source=RetrievalSource.CMS,
                text=text, keywords=doc.keywords,
                specialty=doc.specialty, codes=doc.applies_to_codes,
                original=doc,
            ))

        # Load NCCI edits
        ncci_repo = get_ncci_repository()
        for edit in ncci_repo.get_all():
            text = f"{edit.code_a}/{edit.code_b} {edit.explanation}"
            self._documents.append(IndexedDocument(
                id=edit.edit_id, source=RetrievalSource.NCCI,
                text=text,
                codes=[edit.code_a, edit.code_b],
                original=edit,
            ))

        # Load CPT examples
        cpt_repo = get_cpt_example_repository()
        for ex in cpt_repo.get_all():
            text = f"{ex.specialty} {ex.procedure} {ex.clinical_note} {ex.coding_rationale} {' '.join(ex.common_mistakes)}"
            self._documents.append(IndexedDocument(
                id=ex.example_id, source=RetrievalSource.CPT_EXAMPLE,
                text=text, specialty=ex.specialty,
                codes=[ex.final_cpt] + ex.icd_codes,
                original=ex,
            ))

        # Load coding clinic entries
        clinic_repo = get_coding_clinic_repository()
        for entry in clinic_repo.get_all():
            text = f"{entry.question} {entry.clinical_scenario} {entry.official_answer} {entry.coding_rationale}"
            self._documents.append(IndexedDocument(
                id=entry.entry_id, source=RetrievalSource.CODING_CLINIC,
                text=text, codes=entry.applicable_codes,
                original=entry,
            ))

        # Load specialty cases
        sc_repo = get_specialty_case_repository()
        for case in sc_repo.get_all():
            text = f"{case.specialty} {case.clinical_note} {case.operative_report} {case.reasoning} {' '.join(case.common_errors)}"
            self._documents.append(IndexedDocument(
                id=case.case_id, source=RetrievalSource.SPECIALTY_CASE,
                text=text, specialty=case.specialty,
                original=case,
            ))

        # Load operative notes
        op_repo = get_operative_note_repository()
        for note in op_repo.get_all():
            text = f"{note.title} {note.specialty} {note.operative_note} {' '.join(note.key_findings)} {' '.join(note.procedure_steps)}"
            self._documents.append(IndexedDocument(
                id=note.note_id, source=RetrievalSource.OPERATIVE_NOTE,
                text=text, specialty=note.specialty,
                codes=[note.assigned_cpt],
                original=note,
            ))

        # Load CPC exam questions
        cpc_repo = get_cpc_exam_repository()
        for q in cpc_repo.get_all():
            text = f"{q.specialty} {q.question} {q.evidence} {q.reasoning} {' '.join(str(v) for v in q.distractor_analysis.values())}"
            self._documents.append(IndexedDocument(
                id=q.question_id, source=RetrievalSource.CPC_EXAM,
                text=text, specialty=q.specialty,
                codes=q.cpt_codes,
                original=q,
            ))

        # Load audit cases
        audit_repo = get_audit_case_repository()
        for case in audit_repo.get_all():
            text = f"{case.title} {case.scenario} {case.incorrect_coding} {case.correct_coding} {' '.join(case.audit_findings)} {case.corrective_action}"
            self._documents.append(IndexedDocument(
                id=case.audit_id, source=RetrievalSource.AUDIT_CASE,
                text=text, specialty=case.specialty,
                original=case,
            ))

        # Load modifier cases
        mod_repo = get_modifier_case_repository()
        for case in mod_repo.get_all():
            text = f"{case.title} {case.scenario} {case.reasoning} {case.accepted_outcome} {case.rejected_outcome}"
            self._documents.append(IndexedDocument(
                id=case.case_id, source=RetrievalSource.MODIFIER_CASE,
                text=text,
                codes=[case.modifier],
                original=case,
            ))

        # Load denial cases
        denial_repo = get_denial_case_repository()
        for d in denial_repo.get_all():
            text = f"{d.payer} {d.title} {d.denied_claim} {d.reason_for_denial} {d.required_correction}"
            self._documents.append(IndexedDocument(
                id=d.denial_id, source=RetrievalSource.DENIAL_CASE,
                text=text,
                original=d,
            ))

        # Load payer rules
        payer_repo = get_payer_rule_repository()
        for r in payer_repo.get_all():
            text = f"{r.payer} {r.title} {r.content} {' '.join(r.documentation_requirements)}"
            self._documents.append(IndexedDocument(
                id=r.rule_id, source=RetrievalSource.PAYER_RULE,
                text=text,
                codes=r.applicable_codes,
                original=r,
            ))

        # Load procedure templates
        proc_repo = get_procedure_template_repository()
        for t in proc_repo.get_all():
            text = f"{t.procedure_name} {t.specialty} {' '.join(t.procedure_signature_keywords)} {' '.join(t.required_evidence)} {' '.join(t.bundling_notes)}"
            self._documents.append(IndexedDocument(
                id=t.template_id, source=RetrievalSource.PROCEDURE_TEMPLATE,
                text=text, specialty=t.specialty,
                codes=[t.cpt_code] + t.alternative_cpts,
                original=t,
            ))

        # Load anatomy references
        anat_repo = get_anatomy_repository()
        for a in anat_repo.get_all():
            text = f"{a.body_system} {a.organ} {a.sub_organ} {' '.join(a.synonyms)} {a.description}"
            self._documents.append(IndexedDocument(
                id=a.entry_id, source=RetrievalSource.ANATOMY,
                text=text,
                codes=a.related_codes,
                original=a,
            ))

        # Load benchmarks
        bench_repo = get_benchmark_repository()
        for b in bench_repo.get_all():
            text = f"{b.category} {b.input_note} {b.reasoning}"
            self._documents.append(IndexedDocument(
                id=b.test_id, source=RetrievalSource.BENCHMARK,
                text=text,
                codes=[b.expected_cpt] + b.expected_icd,
                original=b,
            ))

        self._initialized = True
        elapsed = time.time() - start
        logger.info("Indexed %d documents in %.2fs", len(self._documents), elapsed)

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase, stripped tokens."""
        tokens = re.findall(r"[a-z0-9]+(?:[-/][a-z0-9]+)*", text.lower())
        return [t for t in tokens if len(t) >= 1]

    def _score_keyword_overlap(self, query_tokens: List[str], doc: IndexedDocument) -> float:
        """
        Score document relevance by keyword overlap.
        Normalized by query length to produce 0-1 score.
        """
        doc_tokens = set(self._tokenize(doc.text))
        query_set = set(query_tokens)
        if not query_set:
            return 0.0

        # Compute overlapping tokens
        overlap = query_set & doc_tokens

        # Factor in length ratio (prefer documents with closer length)
        query_len = len(query_set)
        doc_len = len(doc_tokens)
        len_ratio = min(query_len / max(doc_len, 1), 1.0)

        # Score = overlap fraction * length factor
        overlap_score = len(overlap) / len(query_set)
        return overlap_score * (0.7 + 0.3 * len_ratio)

    def retrieve(self, query: str, top_k: int = 10,
                 specialty: str = "",
                 source_filter: Optional[RetrievalSource] = None,
                 code_filter: str = "") -> RAGResult:
        """
        Retrieve relevant documents for a query.
        Returns RAGResult with ranked context sections.

        Args:
            query: The clinical query or note text
            top_k: Number of results per collection type
            specialty: Optional specialty filter
            source_filter: Optional source type filter
            code_filter: Optional code filter (e.g., "33533")
        """
        start = time.time()
        start_embed = time.time()
        query_tokens = self._tokenize(query)
        query_specialty = specialty.lower() if specialty else ""
        query_code = code_filter.replace(".", "")
        embed_time = time.time() - start_embed

        # Score all documents
        start_retrieve = time.time()
        scored: List[Tuple[float, IndexedDocument]] = []
        for doc in self._documents:
            # Apply filters
            if source_filter and doc.source != source_filter:
                continue
            if query_specialty and doc.specialty and query_specialty not in doc.specialty.lower():
                # Still allow low score, don't filter out entirely
                pass
            if query_code:
                has_code = any(query_code == c.replace(".", "") for c in doc.codes)
                if not has_code:
                    continue

            score = self._score_keyword_overlap(query_tokens, doc)
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[1].source.value if hasattr(x[1].source, 'value') else str(x[1].source))
        scored.sort(key=lambda x: x[0], reverse=True)
        retrieve_time = time.time() - start_retrieve

        # Build RAG context
        start_fusion = time.time()
        context = RAGContext()
        seen_ids = set()

        for score, doc in scored[:top_k * 5]:  # Take more than top_k for richer context
            if doc.id in seen_ids:
                continue
            seen_ids.add(doc.id)

            # Add to appropriate context section
            source_key = doc.source.value if hasattr(doc.source, 'value') else str(doc.source)
            if source_key == RetrievalSource.CMS.value and len(context.cms_documents) < top_k:
                if isinstance(doc.original, CMSDocument):
                    context.cms_documents.append(doc.original)
            elif source_key == RetrievalSource.NCCI.value and len(context.ncci_edits) < top_k:
                if isinstance(doc.original, NCCIEdit):
                    context.ncci_edits.append(doc.original)
            elif source_key == RetrievalSource.CPT_EXAMPLE.value and len(context.cpt_examples) < top_k:
                if isinstance(doc.original, CPTExample):
                    context.cpt_examples.append(doc.original)
            elif source_key == RetrievalSource.CODING_CLINIC.value and len(context.coding_clinic) < top_k:
                if isinstance(doc.original, CodingClinicEntry):
                    context.coding_clinic.append(doc.original)
            elif source_key == RetrievalSource.SPECIALTY_CASE.value and len(context.specialty_cases) < top_k:
                if isinstance(doc.original, SpecialtyCase):
                    context.specialty_cases.append(doc.original)
            elif source_key == RetrievalSource.OPERATIVE_NOTE.value and len(context.operative_notes) < top_k:
                if isinstance(doc.original, OperativeNote):
                    context.operative_notes.append(doc.original)
            elif source_key == RetrievalSource.CPC_EXAM.value and len(context.cpc_exam_questions) < top_k:
                if isinstance(doc.original, CPCExamQuestion):
                    context.cpc_exam_questions.append(doc.original)
            elif source_key == RetrievalSource.AUDIT_CASE.value and len(context.audit_cases) < top_k:
                if isinstance(doc.original, AuditCase):
                    context.audit_cases.append(doc.original)
            elif source_key == RetrievalSource.MODIFIER_CASE.value and len(context.modifier_cases) < top_k:
                if isinstance(doc.original, ModifierCase):
                    context.modifier_cases.append(doc.original)
            elif source_key == RetrievalSource.DENIAL_CASE.value and len(context.denial_cases) < top_k:
                if isinstance(doc.original, DenialCase):
                    context.denial_cases.append(doc.original)
            elif source_key == RetrievalSource.PAYER_RULE.value and len(context.payer_rules) < top_k:
                if isinstance(doc.original, PayerRule):
                    context.payer_rules.append(doc.original)
            elif source_key == RetrievalSource.PROCEDURE_TEMPLATE.value and len(context.procedure_templates) < top_k:
                if isinstance(doc.original, ProcedureTemplate):
                    context.procedure_templates.append(doc.original)
            elif source_key == RetrievalSource.ANATOMY.value and len(context.anatomy_references) < top_k:
                if isinstance(doc.original, AnatomyEntry):
                    context.anatomy_references.append(doc.original)
            elif source_key == RetrievalSource.BENCHMARK.value and len(context.benchmark_tests) < top_k:
                if isinstance(doc.original, BenchmarkTest):
                    context.benchmark_tests.append(doc.original)

        fusion_time = time.time() - start_fusion
        total_time = time.time() - start

        return RAGResult(
            query=query,
            context=context,
            embedding_time_ms=embed_time * 1000,
            retrieval_time_ms=retrieve_time * 1000,
            fusion_time_ms=fusion_time * 1000,
        )
