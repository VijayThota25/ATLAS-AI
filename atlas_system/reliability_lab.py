"""ATLAS v0.9: deterministic fault injection and bounded recovery simulation.

No Ollama calls, network access, production actions, or database writes.
"""
from dataclasses import dataclass

FAULTS = ('none', 'transient_timeout', 'persistent_timeout', 'malformed_response', 'tool_unavailable')
MAX_ATTEMPTS = 3

@dataclass(frozen=True)
class SimulatedFault(Exception):
    category: str
    retryable: bool


def _attempt(fault, number):
    if fault == 'transient_timeout' and number == 1:
        raise SimulatedFault('TIMEOUT', True)
    if fault == 'persistent_timeout':
        raise SimulatedFault('TIMEOUT', True)
    if fault == 'malformed_response':
        raise SimulatedFault('INVALID_MODEL_RESPONSE', False)
    if fault == 'tool_unavailable':
        raise SimulatedFault('TOOL_UNAVAILABLE', False)
    return {'status': 'VALIDATED_SYNTHETIC_ADVISORY', 'unverified': True}


def simulate(fault='none', max_attempts=MAX_ATTEMPTS):
    if fault not in FAULTS:
        raise ValueError('Unknown simulated fault')
    if type(max_attempts) is not int or not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise ValueError('max_attempts must be an integer from 1 to 3')
    attempts = []
    outcome = None
    for number in range(1, max_attempts + 1):
        try:
            _attempt(fault, number)
            attempts.append({'attempt': number, 'result': 'SUCCESS'})
            outcome = 'RECOVERED_AFTER_RETRY' if number > 1 else 'SUCCEEDED'
            break
        except SimulatedFault as error:
            attempts.append({'attempt': number, 'result': error.category,
                             'retryable': error.retryable})
            if not error.retryable or number == max_attempts:
                outcome = 'SAFE_FAILURE'
                break
    return {'version': '0.9', 'mode': 'DETERMINISTIC_FAULT_SIMULATION',
            'fault': fault, 'outcome': outcome, 'attempt_count': len(attempts),
            'max_attempts': max_attempts, 'attempts': attempts,
            'requires_human_approval': True, 'action_executed': False,
            'recovery_proposal': 'REQUIRES_HUMAN_REVIEW' if outcome == 'SAFE_FAILURE' else 'ADVISORY_ONLY',
            'limitations': ('Synthetic fault injection only; no real agent/tool outage, network calls, '
                            'live LLM validation, production recovery, or automated approval.')}


def regression():
    cases = []
    expected = {
        'none': ('SUCCEEDED', 1),
        'transient_timeout': ('RECOVERED_AFTER_RETRY', 2),
        'persistent_timeout': ('SAFE_FAILURE', 3),
        'malformed_response': ('SAFE_FAILURE', 1),
        'tool_unavailable': ('SAFE_FAILURE', 1),
    }
    for fault, (outcome, attempts) in expected.items():
        result = simulate(fault)
        cases.append({'case': fault, 'passed': (result['outcome'] == outcome and
                      result['attempt_count'] == attempts and
                      result['requires_human_approval'] is True and
                      result['action_executed'] is False),
                      'outcome': result['outcome'], 'attempt_count': result['attempt_count']})
    try:
        simulate('not_a_fault')
    except ValueError:
        rejected = True
    else:
        rejected = False
    cases.append({'case': 'reject_unknown_fault', 'passed': rejected})
    try:
        simulate('none', max_attempts=100)
    except ValueError:
        rejected = True
    else:
        rejected = False
    cases.append({'case': 'reject_unbounded_retries', 'passed': rejected})
    return {'suite': 'v0.9-reliability-offline-1', 'total': len(cases),
            'passed': sum(c['passed'] for c in cases),
            'failed': sum(not c['passed'] for c in cases), 'cases': cases,
            'limitations': 'Deterministic offline simulation, not production reliability evidence.'}
