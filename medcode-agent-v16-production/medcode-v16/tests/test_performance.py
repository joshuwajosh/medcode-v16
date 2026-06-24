"""
MedCode AI V19 - Performance Test Suite
"""
import sys, time, statistics, concurrent.futures
sys.path.insert(0, '.')
from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV15
from agents.clinical_note_parser import ClinicalNoteParser
from billing.claim_engine import get_claim_generator, get_claim_validator, get_denial_predictor
from billing.edi_837 import EDI837Generator
from billing.claim_tracker import ClaimTracker

TEST_NOTES = [
    ("CABG", "68yo male, CABG x3, LIMA to LAD, SVG to RCA with endarterectomy."),
    ("Cholecystectomy", "45yo female, laparoscopic cholecystectomy for cholelithiasis."),
    ("Pneumonia", "78yo male admitted with pneumonia, MRSA, sepsis."),
    ("Stroke", "75yo female, acute ischemic stroke, NIHSS 12, TPA given."),
    ("Diabetes", "55yo female, type 2 diabetes, HbA1c 7.2%."),
    ("Heart Failure", "68yo female, acute decompensated heart failure, BNP 1850."),
    ("Fracture", "78yo female, hip fracture, ORIF with cannulated screws."),
    ("Asthma", "28yo female, severe asthma exacerbation, nebulized albuterol."),
    ("CABG Radial", "71yo female, CABG x3 with radial artery graft."),
    ("Pre-eclampsia", "32yo female, severe pre-eclampsia, HELLP, C-section."),
    ("TAVR", "81yo female, aortic stenosis, TAVR transapical."),
    ("Hernia", "55yo male, inguinal hernia, mesh repair."),
    ("Colonoscopy", "60yo male, colonoscopy with polypectomy."),
    ("ERCP", "65yo male, ERCP stent exchange, chronic pancreatitis."),
    ("Knee Replacement", "68yo female, total knee arthroplasty."),
]

def run_case(pipeline, parser, name, note):
    t0 = time.time()
    pr = pipeline.run(note_text=note, note_id='perf')
    p_ms = (time.time()-t0)*1000
    t0 = time.time()
    pa = parser.parse(note)
    a_ms = (time.time()-t0)*1000
    return {'name':name, 'p_ms':p_ms, 'a_ms':a_ms, 'cpt':len(pr.cpt_codes), 'icd':len(pr.icd10_codes)}

def main():
    print('='*70)
    print('  MedCode AI V19 - Performance Test')
    print('='*70)
    pipeline = MedcodeDeterministicPipelineV15()
    parser = ClinicalNoteParser()
    print('\n  Warmup...')
    for n,note in TEST_NOTES[:3]: run_case(pipeline, parser, n, note)
    print('  Done.\n')

    # Single threaded
    print('  SINGLE-THREADED')
    print('  '+ '-'*60)
    results = []
    for name,note in TEST_NOTES:
        r = run_case(pipeline, parser, name, note)
        results.append(r)
        print('  %15s | Pipeline: %6.1fms | Parser: %5.1fms' % (name, r['p_ms'], r['a_ms']))
    pt = [r['p_ms'] for r in results]
    at = [r['a_ms'] for r in results]
    print('\n  Pipeline: avg=%.1fms med=%.1fms p95=%.1fms max=%.1fms' % (
        statistics.mean(pt), statistics.median(pt), sorted(pt)[int(len(pt)*0.95)], max(pt)))
    print('  Parser:   avg=%.1fms med=%.1fms p95=%.1fms max=%.1fms' % (
        statistics.mean(at), statistics.median(at), sorted(at)[int(len(at)*0.95)], max(at)))

    # Concurrent
    print('\n  CONCURRENT (5 workers)')
    print('  '+ '-'*60)
    tasks = [(n,note) for n,note in TEST_NOTES*3]
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(run_case, pipeline, parser, n, note) for n,note in tasks]
        results = [f.result() for f in concurrent.futures.as_completed(futs)]
    total = (time.time()-t0)*1000
    throughput = len(results)/(total/1000)
    pt = [r['p_ms'] for r in results]
    print('  Cases: %d | Time: %.0fms | Throughput: %.1f/sec' % (len(results), total, throughput))
    print('  Pipeline: avg=%.1fms p95=%.1fms max=%.1fms' % (
        statistics.mean(pt), sorted(pt)[int(len(pt)*0.95)], max(pt)))

    # Claim workflow
    print('\n  CLAIM WORKFLOW')
    print('  '+ '-'*60)
    gen = get_claim_generator(); val = get_claim_validator(); pred = get_denial_predictor()
    edi = EDI837Generator(); trk = ClaimTracker()
    times = []
    for i in range(10):
        t0=time.time()
        cl = gen.generate_claim(cpt_codes=[{'code':'47562','description':'Lap chole'}],
            icd_codes=[{'code':'K80.20','description':'Gallstones'}],
            patient_info={'name':'TEST','dob':'01/01/1980','sex':'M','insurance_id':'T1',
                         'payer':'Test','place_of_service':'22','dos':'06/21/2026'},
            provider_info={'npi':'1234567890','name':'DR TEST'})
        g=(time.time()-t0)*1000
        t0=time.time(); v=val.validate(cl); vl=(time.time()-t0)*1000
        t0=time.time(); d=pred.predict_denial(cl,v); dp=(time.time()-t0)*1000
        t0=time.time(); edi.generate_837p({'patient_name':cl.patient_name,
            'patient_dob':cl.patient_dob,'insurance_id':cl.insurance_id,
            'payer_name':cl.payer_name,'provider_npi':cl.provider_npi,
            'provider_name':cl.provider_name,'date_of_service':cl.date_of_service,
            'place_of_service':cl.place_of_service,
            'items':[{'cpt_code':i.cpt_code,'description':i.cpt_description,
                      'icd_codes':i.icd_codes,'charge':i.charge_amount} for i in cl.items],
            'total_charges':cl.total_charges}); e=(time.time()-t0)*1000
        t0=time.time(); trk.submit(claim_id=cl.claim_id,patient_name=cl.patient_name,
            payer_name=cl.payer_name,provider_npi=cl.provider_npi,
            total_charges=cl.total_charges,claim_type='professional'); tk=(time.time()-t0)*1000
        times.append(g+vl+dp+e+tk)
    print('  10 claims: avg=%.1fms p95=%.1fms max=%.1fms' % (
        statistics.mean(times), sorted(times)[8], max(times)))

    print('\n'+ '='*70)
    print('  PERFORMANCE TEST COMPLETE')
    print('='*70)

if __name__ == "__main__":
    main()
