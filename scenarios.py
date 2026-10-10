
import random


SCENARIOS = {
    "healthy": {
        "payment_success_rate": 99.2,
        "average_latency_ms": 150,
        "failed_transactions": 5
    },

    "provider_outage": {
        "payment_success_rate": 42.5,
        "average_latency_ms": 4200,
        "failed_transactions": 1284
    },

    "latency_spike": {
        "payment_success_rate": 94.0,
        "average_latency_ms": 3500,
        "failed_transactions": 180
    },

    "retry_storm": {
        "payment_success_rate": 76.0,
        "average_latency_ms": 1800,
        "failed_transactions": 2400
    }
}


def generate_scenario():
    scenario_name = random.choice(list(SCENARIOS.keys()))

    return {
        "scenario": scenario_name,
        "metrics": SCENARIOS[scenario_name].copy()
    }


if __name__ == "__main__":
    scenario = generate_scenario()

    print("\nATLAS AI - SCENARIO GENERATOR")
    print("-----------------------------")
    print("Scenario:", scenario["scenario"])
    print("Metrics:", scenario["metrics"])
