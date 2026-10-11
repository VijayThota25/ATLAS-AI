"""Read-only, deterministic explanation of synthetic payment metrics."""
from engine import SCENARIOS, classify

SIGNALS = (
    ('payment_success_rate', 'Payment success rate', '%'),
    ('average_latency_ms', 'Average latency', ' ms'),
    ('failed_transactions', 'Failed transactions', ''),
)

HYPOTHESES = {
    'healthy': (
        'No significant anomaly in the provided synthetic snapshot',
        ['Short-lived intermittent faults', 'Unobserved downstream issues'],
        ['Longer observation window', 'Provider error-rate time series'],
        ['Continue monitoring synthetic metrics; no intervention indicated'],
    ),
    'provider_outage': (
        'Possible upstream payment-provider availability degradation',
        ['Network connectivity degradation', 'Internal service saturation'],
        ['Provider health and status telemetry', 'Distributed traces and timeout/error breakdown', 'Network connectivity measurements'],
        ['Correlate provider status with request failures', 'Inspect request traces before considering failover'],
    ),
    'latency_spike': (
        'Possible upstream processing latency or saturation',
        ['Internal queue buildup', 'Network latency or packet loss'],
        ['Latency percentiles and distributed traces', 'Queue depth and saturation metrics', 'Network timing breakdown'],
        ['Compare upstream and internal latency', 'Inspect timeout and circuit-breaker telemetry'],
    ),
    'retry_storm': (
        'Possible retry amplification contributing to failed transactions',
        ['Upstream instability triggering retries', 'Client retry misconfiguration'],
        ['Retry-attempt distribution and original request counts', 'Idempotency-key and duplicate-request logs', 'Upstream error codes'],
        ['Inspect retry budgets and backoff behavior', 'Review idempotency handling before considering configuration changes'],
    ),
}

def analyze(scenario):
    """Generate a hypothetical RCA from a named built-in synthetic scenario.

    Does not read/write persistent records, call external services, or execute actions.
    """
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        raise ValueError('Unknown synthetic scenario')
    metrics = dict(SCENARIOS[scenario])
    severity, triggered = classify(metrics)
    primary, alternatives, gaps, next_steps = HYPOTHESES[scenario]
    evidence = [{'metric': key, 'label': label, 'value': metrics[key],
                 'display': f'{label}: {metrics[key]}{unit}'}
                for key, label, unit in SIGNALS]
    return {
        'version': '1.3', 'mode': 'DETERMINISTIC_SYNTHETIC_RCA',
        'scenario': scenario, 'severity': severity,
        'primary_hypothesis': primary, 'confidence': 'UNVERIFIED_HYPOTHESIS',
        'supporting_evidence': evidence, 'triggered_rules': list(triggered),
        'alternative_explanations': list(alternatives),
        'missing_evidence': list(gaps), 'investigation_steps': list(next_steps),
        'requires_human_approval': True, 'action_executed': False,
        'data_persisted': False,
        'limitations': ('Rule-based interpretation of fixed synthetic metrics only. '
                        'Not causal proof, real payment telemetry, a live LLM analysis, '
                        'or authorization to execute recovery actions.'),
    }
