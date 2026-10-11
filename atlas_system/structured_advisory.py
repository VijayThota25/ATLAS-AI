"""Local structured LLM advisory; synthetic data only; never authorizes actions."""
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ENDPOINT = 'http://127.0.0.1:11434/api/generate'
FIELDS = ('hypothesis', 'evidence_to_check', 'recommended_next_steps', 'limitations')

def validate_report(report, incident):
    if not isinstance(report, dict):
        raise ValueError('AI response must be a JSON object')
    if not isinstance(report.get('hypothesis'), str) or not 10 <= len(report['hypothesis']) <= 1500:
        raise ValueError('Invalid hypothesis')
    for key in FIELDS[1:]:
        values = report.get(key)
        if not isinstance(values, list) or not 1 <= len(values) <= 8 or any(not isinstance(v, str) or not 3 <= len(v) <= 350 for v in values):
            raise ValueError('Invalid '+key)
    observed = incident['metrics']
    return {
        'analysis_type': 'LOCAL_OLLAMA_STRUCTURED_ADVISORY',
        'hypothesis': report['hypothesis'],
        'observed_metrics': {key: observed[key] for key in ('payment_success_rate','average_latency_ms','failed_transactions')},
        'evidence_to_check': report['evidence_to_check'],
        'recommended_next_steps': report['recommended_next_steps'],
        'limitations': report['limitations'],
        'verification_status': 'UNVERIFIED_MODEL_HYPOTHESIS',
        'requires_human_approval': True,
        'disclaimer': 'Synthetic incident. AI suggestions are not verified facts and cannot authorize recovery.'
    }

def evaluate_report(result, incident):
    """Deterministic structural/metric checks, NOT a factual accuracy score."""
    expected = incident['metrics']
    checks = {
        'advisory_only': result.get('verification_status') == 'UNVERIFIED_MODEL_HYPOTHESIS',
        'human_approval_required': result.get('requires_human_approval') is True,
        'observed_metrics_match': result.get('observed_metrics') == {k:expected[k] for k in ('payment_success_rate','average_latency_ms','failed_transactions')},
        'evidence_checks_present': bool(result.get('evidence_to_check')),
        'limitations_present': bool(result.get('limitations')),
    }
    return {'checks': checks, 'passed': all(checks.values()),
            'note': 'Checks schema and source-metric integrity only; does not establish truth, grounding, or hallucination rate.'}

def analyze_structured(incident, model='llama3.2'):
    prompt = ('You are a cautious investigator of SYNTHETIC payment-system incidents. '
              'Return a JSON object with exactly these fields: '
              'hypothesis (string), evidence_to_check (array of strings), '
              'recommended_next_steps (array of strings), limitations (array of strings). '
              'Do not claim root cause is confirmed. Do not suggest executing any action. '
              'Distinguish observations from speculation. Use short, clear sentences. '
              'Incident data: ' + json.dumps({'scenario': incident['scenario'], 'metrics': incident['metrics']}))
    request = Request(ENDPOINT, data=json.dumps({'model':model,'prompt':prompt,'stream':False,'format':'json',
        'options':{'temperature':0}}).encode('utf-8'), headers={'Content-Type':'application/json'})
    try:
        with urlopen(request, timeout=90) as response:
            payload = json.load(response)
        raw = json.loads(payload['response'])
        result = validate_report(raw, incident)
        result['evaluation'] = evaluate_report(result, incident)
        return result
    except (URLError, TimeoutError, HTTPError, KeyError, json.JSONDecodeError, ValueError) as exc:
        return {'analysis_type':'LOCAL_OLLAMA_STRUCTURED_UNAVAILABLE',
                'error':str(exc), 'verification_status':'NO_VALID_ADVISORY',
                'requires_human_approval':True,
                'disclaimer':'No validated advisory was generated. No actions were taken.'}
