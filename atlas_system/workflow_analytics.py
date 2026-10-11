"""Read-only aggregates for locally saved synthetic workflow traces."""
import json
from collections import Counter
from contextlib import closing
from atlas_store import connect


def summarize_workflows():
    with closing(connect()) as db:
        rows = db.execute('SELECT payload FROM workflow_traces ORDER BY id').fetchall()
    traces = [json.loads(row[0]) for row in rows]
    by_scenario = Counter()
    by_fault = Counter()
    by_severity = Counter()
    by_outcome = Counter()
    by_day = Counter()
    safety_anomalies = 0
    for trace in traces:
        by_scenario[str(trace.get('scenario', 'UNKNOWN'))] += 1
        by_fault[str(trace.get('fault', 'UNKNOWN'))] += 1
        by_severity[str(trace.get('severity', 'UNKNOWN'))] += 1
        by_outcome[str(trace.get('reliability_outcome', 'UNKNOWN'))] += 1
        created_at = trace.get('created_at')
        by_day[str(created_at)[:10] if created_at else 'UNKNOWN'] += 1
        if trace.get('requires_human_approval') is not True or trace.get('action_executed') is not False:
            safety_anomalies += 1
    return {
        'version': '1.2',
        'mode': 'LOCAL_SYNTHETIC_TRACE_ANALYTICS',
        'total_traces': len(traces),
        'by_scenario': dict(sorted(by_scenario.items())),
        'by_fault': dict(sorted(by_fault.items())),
        'by_severity': dict(sorted(by_severity.items())),
        'by_reliability_outcome': dict(sorted(by_outcome.items())),
        'by_utc_day': dict(sorted(by_day.items())),
        'safety': {
            'human_approval_required_count': sum(t.get('requires_human_approval') is True for t in traces),
            'no_action_executed_count': sum(t.get('action_executed') is False for t in traces),
            'anomaly_count': safety_anomalies,
        },
        'limitations': 'Aggregates locally persisted synthetic traces only. No real payments, recovery execution, live LLM calls, or production reliability claims.',
    }
