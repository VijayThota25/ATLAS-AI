"""ATLAS v0.6: repeatable, offline synthetic evaluation. No Ollama calls."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from atlas_store import DB
from engine import SCENARIOS, investigate
from structured_advisory import validate_report, evaluate_report

VERSION = 'v0.6-offline-1'

def sample_report():
    return {'hypothesis':'A synthetic upstream issue is plausible; verification is required.',
            'evidence_to_check':['Review synthetic provider telemetry'],
            'recommended_next_steps':['Inspect traces before any intervention'],
            'limitations':['No real provider telemetry is available']}

def run_checks():
    """A fixed regression suite; does not measure LLM accuracy or hallucination rate."""
    cases=[]
    def check(name, condition, detail):
        cases.append({'case':name,'passed':bool(condition),'detail':detail})
    expected={'healthy':'HEALTHY','provider_outage':'CRITICAL','latency_spike':'CRITICAL','retry_storm':'HIGH'}
    for scenario, severity in expected.items():
        incident=investigate(scenario)
        check('severity_'+scenario,incident['severity']==severity,
              'Expected severity '+severity+' for fixed synthetic metrics')
        result=validate_report(sample_report(),incident)
        check('metric_integrity_'+scenario,
              result['observed_metrics']==SCENARIOS[scenario],
              'Observed metrics must come from incident data, not the model')
        check('approval_gate_'+scenario,
              result['requires_human_approval'] is True and
              result['verification_status']=='UNVERIFIED_MODEL_HYPOTHESIS',
              'Advisory remains unverified and requires human approval')
    incident=investigate('provider_outage')
    try:
        validate_report({'hypothesis':'unsupported'},incident)
    except ValueError:
        invalid_rejected=True
    else:
        invalid_rejected=False
    check('reject_malformed_report',invalid_rejected,'Missing fields must be rejected')
    result=validate_report(sample_report(),incident)
    result['observed_metrics']['failed_transactions']=-999
    check('detect_metric_tampering',not evaluate_report(result,incident)['passed'],
          'Structural evaluator must detect changed source metrics')
    return {'suite':VERSION,'total':len(cases),'passed':sum(c['passed'] for c in cases),
            'failed':sum(not c['passed'] for c in cases),'cases':cases,
            'limitations':'Offline deterministic regression checks only; no live LLM generation, factuality, grounding, or hallucination-rate measurement.'}

def _connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB,timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS evaluation_runs (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, suite TEXT NOT NULL, passed INTEGER NOT NULL, failed INTEGER NOT NULL, report TEXT NOT NULL)')
    return db

def save_run(report):
    with closing(_connect()) as db:
        with db:
            cursor=db.execute('INSERT INTO evaluation_runs(created_at,suite,passed,failed,report) VALUES (?,?,?,?,?)',
                              (datetime.now(timezone.utc).isoformat(),report['suite'],report['passed'],report['failed'],json.dumps(report)))
            return cursor.lastrowid

def history(limit=20):
    limit=max(1,min(100,int(limit)))
    with closing(_connect()) as db:
        rows=db.execute('SELECT id,created_at,suite,passed,failed FROM evaluation_runs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [{'run_id':r[0],'timestamp':r[1],'suite':r[2],'passed':r[3],'failed':r[4]} for r in rows]

def run_and_record():
    report=run_checks()
    report['run_id']=save_run(report)
    return report
