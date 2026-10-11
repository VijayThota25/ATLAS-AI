"""Stochastic synthetic recovery experiment. Optional SimPy discrete-event runtime.
Assumptions are illustrative, not calibrated to real payment-provider data.
"""
import random
import statistics

STRATEGIES = {
    'backup_provider': {'lift': 0.25, 'latency_multiplier': 0.75},
    'bounded_retries': {'lift': 0.12, 'latency_multiplier': 0.90},
    'circuit_breaker': {'lift': 0.08, 'latency_multiplier': 0.65},
}


def experiment(incident, strategy, trials=1000, seed=42):
    if strategy not in STRATEGIES: raise ValueError('Unsupported strategy')
    if not isinstance(trials, int) or not 10 <= trials <= 100000:
        raise ValueError('trials must be between 10 and 100000')
    rng = random.Random(seed)
    baseline = incident['metrics']['payment_success_rate'] / 100
    assumption = STRATEGIES[strategy]
    recovered_probability = min(.999, baseline + assumption['lift'])
    before, after = [], []
    for _ in range(trials):
        before.append(int(rng.random() < baseline))
        after.append(int(rng.random() < recovered_probability))
    try:
        import simpy
        env = simpy.Environment()
        completed = []
        def request(i):
            yield env.timeout(incident['metrics']['average_latency_ms'] * assumption['latency_multiplier'] / 1000)
            completed.append(i)
        for i in range(min(trials, 200)):
            env.process(request(i))
        env.run()
        runtime = 'SIMPY_DISCRETE_EVENT'
        event_count = len(completed)
    except ImportError:
        runtime = 'MONTE_CARLO_ONLY_SIMPY_NOT_INSTALLED'
        event_count = 0
    return {
        'strategy': strategy, 'trials': trials, 'seed': seed,
        'observed_baseline_success_rate': round(100 * statistics.mean(before), 2),
        'observed_recovery_success_rate': round(100 * statistics.mean(after), 2),
        'estimated_improvement_pp': round(100 * (statistics.mean(after) - statistics.mean(before)), 2),
        'simulation_runtime': runtime, 'simulated_events': event_count,
        'assumptions': assumption,
        'disclaimer': 'Synthetic stochastic experiment; not a calibrated or validated prediction.'
    }
