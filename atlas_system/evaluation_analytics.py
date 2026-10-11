"""ATLAS v0.8 read-only analytics from persisted evaluation reports."""
import json
import sqlite3
from contextlib import closing
from evaluation_suite import _connect


def summarize(limit=100):
    limit = max(1, min(500, int(limit)))
    with closing(_connect()) as db:
        rows = db.execute('SELECT id, created_at, suite, passed, failed, report FROM evaluation_runs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    runs = []
    scenarios = []
    for run_id, timestamp, suite, passed, failed, raw in reversed(rows):
        try:
            report = json.loads(raw)
        except (TypeError, ValueError):
            continue
        total = passed + failed
        item = {'run_id': run_id, 'timestamp': timestamp, 'suite': suite,
                'passed': passed, 'failed': failed, 'total': total,
                'pass_rate_pct': round(100 * passed / total, 2) if total else None}
        durations = [case['duration_ms'] for case in report.get('cases', [])
                     if isinstance(case, dict) and isinstance(case.get('duration_ms'), (int, float))
                     and not isinstance(case['duration_ms'], bool) and case['duration_ms'] >= 0]
        if durations:
            item['average_latency_ms'] = round(sum(durations) / len(durations), 2)
        runs.append(item)
        for case in report.get('cases', []):
            if not isinstance(case, dict) or 'scenario' not in case:
                continue
            duration = case.get('duration_ms')
            scenarios.append({'run_id': run_id, 'timestamp': timestamp, 'scenario': str(case['scenario']),
                              'passed': bool(case.get('passed')), 'duration_ms': duration if isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration >= 0 else None,
                              'flags': case.get('flags', []) if isinstance(case.get('flags'), list) else []})
    live = [r for r in runs if r['suite'].startswith('v0.7-live')]
    return {'version': '0.8', 'source': 'SQLITE_SAVED_EVALUATION_REPORTS',
            'run_count': len(runs), 'live_run_count': len(live),
            'runs': runs, 'scenario_measurements': scenarios,
            'limitations': ('Historical data only; no new LLM calls. Pass rates are proportions of existing deterministic or heuristic checks, '
                            'not factual accuracy. One live run is not a statistically meaningful trend. '
                            'Only the most recent requested runs are included.')}
