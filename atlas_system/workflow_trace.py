"""Read-only synthetic workflow tracing; no external calls or persistence."""
from engine import SCENARIOS, investigate
from agent_pipeline import detect, reason, recommend
from reliability_lab import FAULTS, simulate


def trace(scenario='provider_outage', fault='none'):
    if scenario not in SCENARIOS:
        raise ValueError('Unknown synthetic scenario')
    if fault not in FAULTS:
        raise ValueError('Unknown simulated fault')
    incident = investigate(scenario)  # No append_record or SQLite writes.
    steps = []
    state = detect(incident)
    steps.append({'step': 1, 'stage': 'DETECT', 'status': 'COMPLETE',
                  'detail': {'severity': state['severity'], 'evidence': state['evidence']}})
    reasoning = reason(state)
    state.update(reasoning)
    steps.append({'step': 2, 'stage': 'REASON', 'status': 'COMPLETE',
                  'detail': {'hypothesis': reasoning['hypothesis'], 'confidence': reasoning['confidence']}})
    recommendation = recommend(state)
    state.update(recommendation)
    steps.append({'step': 3, 'stage': 'RECOMMEND', 'status': 'COMPLETE',
                  'detail': {'strategy': recommendation['recommended_strategy'],
                             'requires_human_approval': True}})
    reliability = simulate(fault)
    steps.append({'step': 4, 'stage': 'RELIABILITY_CHECK',
                  'status': 'COMPLETE' if reliability['outcome'] != 'SAFE_FAILURE' else 'SAFE_FAILURE',
                  'detail': {'outcome': reliability['outcome'],
                             'attempt_count': reliability['attempt_count'],
                             'attempts': reliability['attempts']}})
    steps.append({'step': 5, 'stage': 'HUMAN_APPROVAL_GATE', 'status': 'AWAITING_HUMAN_REVIEW',
                  'detail': {'action_executed': False, 'requires_human_approval': True}})
    return {'version': '1.0', 'mode': 'READ_ONLY_SYNTHETIC_WORKFLOW_TRACE',
            'scenario': scenario, 'fault': fault, 'severity': incident['severity'],
            'orchestrator': 'DETERMINISTIC_STEP_TRACE_NOT_LANGGRAPH_EXECUTION',
            'steps': steps, 'reliability_outcome': reliability['outcome'],
            'requires_human_approval': True, 'action_executed': False,
            'data_persisted': False,
            'limitations': 'Offline synthetic trace. No live LLM, LangGraph graph execution, network calls, database writes or actual recovery.'}


def regression():
    checks = []
    for scenario in SCENARIOS:
        result = trace(scenario)
        checks.append({'case': 'scenario_' + scenario,
                       'passed': (len(result['steps']) == 5 and
                                  [s['stage'] for s in result['steps']] ==
                                  ['DETECT', 'REASON', 'RECOMMEND', 'RELIABILITY_CHECK', 'HUMAN_APPROVAL_GATE'] and
                                  result['action_executed'] is False and
                                  result['data_persisted'] is False)})
    for fault in FAULTS:
        result = trace('provider_outage', fault)
        checks.append({'case': 'fault_' + fault,
                       'passed': result['action_executed'] is False and
                                 result['requires_human_approval'] is True and
                                 result['steps'][-1]['status'] == 'AWAITING_HUMAN_REVIEW'})
    for label, kwargs in [('reject_unknown_scenario', {'scenario': 'invalid'}),
                          ('reject_unknown_fault', {'fault': 'invalid'})]:
        try:
            trace(**kwargs)
        except ValueError:
            passed = True
        else:
            passed = False
        checks.append({'case': label, 'passed': passed})
    return {'suite': 'v1.0-workflow-offline-1', 'total': len(checks),
            'passed': sum(x['passed'] for x in checks),
            'failed': sum(not x['passed'] for x in checks),
            'cases': checks,
            'limitations': 'Deterministic read-only checks; not evidence of production reliability or LLM factuality.'}
