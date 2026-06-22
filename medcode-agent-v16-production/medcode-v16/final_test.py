import sys
sys.path.insert(0, '.')

from core.models import ClinicalNote, ExtractedClinicalData
from agents.orchestrator import AgentOrchestrator
from core.llm_client import LLMClient
from core.omop_client import OMOPClient
import asyncio
import time

# Initialize
llm = LLMClient()
omop = OMOPClient()
orchestrator = AgentOrchestrator(llm, omop)

# Dan Williams operative report
note_text = """Patient Name: Dan Williams
Date: 03/14/20XX
Anesthesia: General by LMA Surgeon: D. Smith, MD
Preoperative Diagnosis: Two benign skin lesions of right and left upper back. Postoperative Diagnosis: Two benign skin lesions of right and left upper back.
Operation Performed: Excision of two benign lesions on the right and left upper back.
Indication: The patient is a 45-year-old white female with two suspicious dark lesions on her back, which were biopsied and pathology reported them benign. She has had these lesions for many years and wants them removed.
Description of Procedure: The patient was placed in the prone position on the table. No sedation was given. Both areas of the right and left upper back were prepped and draped in sterile fashion with Betadine paint. The first area was located on the right upper back. This had a maximum diameter of 1 cm and a 3 mm margin on each side was planned. This was infiltrated with 1 percent Lidocaine with epinephrine. It was excised. The wound was then irrigated. Hemostasis was achieved. It was then closed with one layer using 5-0 Prolene. This area was covered with Steri-gauze and tape. The next lesion was located on the left upper back. This had a maximum diameter of 1.5 cm. This had a 4 mm margin designed. The area was infiltrated with 1% Lidocaine, followed by excision. It was also closed with one layer using 5-0 Prolene, gauzed, and taped. The patient tolerated this entire procedure with no complications and was sent home in stable condition."""

note = ClinicalNote(raw_text=note_text)

print('='*70)
print('FINAL TEST: DAN WILLIAMS OPERATIVE REPORT')
print('='*70)
print('Note length:', len(note_text), 'characters')
print()

# Run the full pipeline
start_time = time.time()
print('Running complete 5-agent pipeline...')
result = asyncio.run(orchestrator.run_pipeline(
    clinical_note=note,
    mode='balanced',
    vocabulary_ids=['ICD10CM', 'CPT'],
    fast_mode=False
))
elapsed = time.time() - start_time

print('')
print('Completed in {:.2f}s'.format(elapsed))
print('='*70)
print('RESULTS:')
print('='*70)
if result.primary_dx:
    print("Primary DX: {} - {}".format(result.primary_dx.code, result.primary_dx.name))
    print("Primary DX score: {}".format(result.primary_dx.llm_score))
else:
    print("Primary DX: None")

if result.secondary_dx:
    secondary_list = ['{} - {}'.format(c.code, c.name) for c in result.secondary_dx]
    print("Secondary DX: {}".format(', '.join(secondary_list)))
    secondary_scores = [str(c.llm_score) for c in result.secondary_dx]
    print("Secondary DX scores: {}".format(', '.join(secondary_scores)))
else:
    print("Secondary DX: None")

if result.procedures:
    procedure_list = ['{} - {}'.format(c.code, c.name) for c in result.procedures]
    print("Procedures: {}".format(', '.join(procedure_list)))
    procedure_scores = [str(c.llm_score) for c in result.procedures]
    print("Procedure scores: {}".format(', '.join(procedure_scores)))
else:
    print("Procedures: None")

print("Overall confidence: {:.1f}%".format(result.confidence_overall))
print("Needs human review: {}".format(result.needs_human_review))
if result.needs_human_review:
    print("Review reasons: {}".format(result.review_reasons))

print('')
print('EXPECTED (per MEDCODE_FIX_GUIDE.md):')
print('Primary DX: D23.5 - Benign neoplasm of skin of trunk')
print('Procedures: CPT 11402 (left 1.5cm lesion + 4mm margin each side = 2.3cm excised)')
print('          CPT 11401 -51 (right 1.0cm lesion + 3mm margin each side = 1.6cm excised)')
print('')
print('Let us see how close we got...')