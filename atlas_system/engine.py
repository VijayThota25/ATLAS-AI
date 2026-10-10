"""Local-first synthetic payments investigation engine. No real payments or APIs."""
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCENARIOS = {
    'healthy': {'payment_success_rate': 99.2, 'average_latency_ms': 150, 'failed_transactions': 5},
    'provider_outage': {'payment_success_rate': 42.5, 'average_latency_ms': 4200, 'failed_transactions': 1284},
    'latency_spike': {'payment_success_rate': 94.0, 'average_latency_ms': 3500, 'failed_transactions': 180},
    'retry_storm': {'payment_success_rate': 76.0, 'average_latency_ms': 1800, 'failed_transactions': 2400},
}
DATA = Path(__file__).resolve().parent / 'data'
HISTORY = DATA / 'incidents.jsonl'
ACTIONS = DATA / 'actions.jsonl'

def classify(metrics):
    success, latency, failed = metrics['payment_success_rate'], metrics['average_latency_ms'], metrics['failed_transactions']
    reasons = []
    if success < 60: reasons.append('Critical drop in payment success rate')
    elif success < 90: reasons.append('Payment success rate below normal')
    if latency > 3000: reasons.append('Severe payment processing latency')
    elif latency > 1000: reasons.append('Elevated payment processing latency')
    if failed > 1000: reasons.append('High number of failed transactions')
    severity = 'CRITICAL' if success < 60 or latency > 3000 else 'HIGH' if success < 90 or latency > 1000 or failed > 1000 else 'HEALTHY'
    return severity, reasons

def investigate(name):
    if name not in SCENARIOS: raise ValueError('Unknown scenario')
    metrics = SCENARIOS[name].copy()
    severity, reasons = classify(metrics)
    causes = {
        'healthy': 'No abnormal behavior detected in synthetic metrics',
        'provider_outage': 'Synthetic upstream payment-provider availability degradation',
        'latency_spike': 'Synthetic high processing latency in provider calls',
        'retry_storm': 'Synthetic excessive retries amplifying failed transactions',
    }
    recommendation = {
        'healthy': 'No intervention required',
        'provider_outage': 'Evaluate routing traffic to a backup provider',
        'latency_spike': 'Evaluate circuit breaker and request timeouts',
        'retry_storm': 'Evaluate bounded retries and exponential backoff',
    }
    return {
        'incident_id': str(uuid.uuid4()),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'scenario': name,
        'environment': 'SIMULATION',
        'metrics': metrics,
        'severity': severity,
        'status': 'HEALTHY' if severity == 'HEALTHY' else 'DETECTED',
        'evidence': reasons,
        'hypothesis': causes[name],
        'recommendation': recommendation[name],
        'analysis_type': 'DETERMINISTIC_DEMO_NOT_LLM',
    }

def append_record(path, record):
    DATA.mkdir(exist_ok=True, parents=True)
    with path.open('a', encoding='utf-8') as f: f.write(json.dumps(record) + '\n')

def read_records(path, limit=50):
    if not path.exists(): return []
    with path.open(encoding='utf-8') as f:
        records = [json.loads(line) for line in f if line.strip()]
    return records[-limit:][::-1]

def create_incident(name=None):
    incident = investigate(name or random.choice(list(SCENARIOS)))
    append_record(HISTORY, incident)
    return incident

def simulate_recovery(incident, strategy):
    """Illustrative deterministic counterfactual, not a validated digital twin."""
    if strategy not in ('backup_provider', 'bounded_retries', 'circuit_breaker'):
        raise ValueError('Unsupported strategy')
    baseline = incident['metrics']['payment_success_rate']
    delta = {'backup_provider': 25.0, 'bounded_retries': 12.0, 'circuit_breaker': 8.0}[strategy]
    projected = round(min(99.9, baseline + delta), 1)
    return {'strategy': strategy, 'baseline_success_rate': baseline, 'projected_success_rate': projected,
            'improvement_percentage_points': round(projected - baseline, 1),
            'disclaimer': 'Illustrative synthetic estimate, not a calibrated simulation'}

def propose_action(incident, strategy):
    simulation = simulate_recovery(incident, strategy)
    proposal = {'action_id': str(uuid.uuid4()), 'incident_id': incident['incident_id'],
                'strategy': strategy, 'status': 'PENDING_HUMAN_APPROVAL',
                'simulation': simulation, 'environment': 'SIMULATION'}
    append_record(ACTIONS, proposal)
    return proposal

def approve_action(action_id):
    actions = read_records(ACTIONS, 100000)
    proposal = next((a for a in actions if a.get('action_id') == action_id and a.get('status') == 'PENDING_HUMAN_APPROVAL'), None)
    if not proposal: raise ValueError('No pending proposal found')
    result = {'action_id': action_id, 'incident_id': proposal['incident_id'],
              'status': 'SIMULATED_EXECUTION_COMPLETE', 'environment': 'SIMULATION',
              'timestamp': datetime.now(timezone.utc).isoformat(),
              'note': 'No external payment system was modified'}
    append_record(ACTIONS, result)
    return result
