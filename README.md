# ATLAS AI

**Autonomous Trust, Learning & Action Simulation Engine**

ATLAS AI is a local-first Python prototype for investigating synthetic payment incidents, analyzing potential root causes, simulating recovery strategies, and archiving evaluated investigation reports.

**Current release:** v1.6

[View System Architecture](docs/architecture.md)

## Architecture

Synthetic Payment Scenarios
    |
    v
Detection and Classification
    |
    v
Investigation Workflow
    |
    v
Deterministic Root-Cause Analysis
    |
    v
Synthetic Recovery Simulation
    |
    v
Report Evaluation and Safety Checks
    |
    v
Explicit Investigation Archive
    |
    v
SQLite Persistence and Local Dashboard

## Features

- Synthetic payment incident detection and classification
- Explainable, rule-driven investigation
- Optional LangGraph orchestration with sequential fallback
- Optional SimPy recovery simulation with Monte Carlo fallback
- Local Ollama advisory integration
- SQLite investigation history
- Workflow observability and analytics
- Deterministic root-cause hypotheses
- Incident comparison and report evaluation
- JSON export and explicit investigation archiving
- Automated Python regression tests

## Technology

- Python 3.12
- LangGraph 1.2.14 (optional)
- SimPy 4.1.2 (optional)
- SQLite
- HTML and JavaScript
- Python unittest

## Quick Start

Clone the repository:

    git clone https://github.com/VijayThota25/ATLAS-AI.git
    cd ATLAS-AI

Install optional dependencies:

    python -m pip install -r requirements.txt

Start the server:

    python atlas_system/server.py

Open the dashboard:

http://127.0.0.1:8765

## Testing

Run:

    python -m unittest discover -s atlas_system -p "test_*.py" -v

The ATLAS AI v2.0 development branch passed 71 automated regression tests.

The test suite covers deterministic investigation workflows, scenario validation,
API responses, report evaluation, archive integrity, and safety constraints.
## Demonstration

1. Open the local dashboard.
2. Select synthetic incident scenarios.
3. Run an investigation.
4. Review root-cause findings and recovery simulations.
5. Compare two incidents.
6. Evaluate the comparison report.
7. Explicitly save the evaluated investigation.
8. Browse archive history and export JSON.

## Safety and Limitations

ATLAS AI is a development-only simulation prototype.

- No real payment providers are contacted.
- No real financial transactions are executed.
- Incident data and recovery metrics are synthetic.
- Root-cause findings are unverified hypotheses.
- Human approval controls are simulated.
- The local HTTP server has no authentication.
- Do not expose the server to the public internet.
- The system is not production-ready financial infrastructure.

## Roadmap

- v1.0: Investigation workflow
- v1.1: SQLite persistence
- v1.2: Workflow observability
- v1.3: Deterministic root-cause analysis
- v1.4: Incident comparison
- v1.5: Report evaluation and export
- v1.6: Investigation archive
- v1.7: Documentation, reliability and demo readiness
- v1.8: API reliability tests and SHA-256 archive integrity checks
- v1.9: Premium Mission Control dashboard, visual incident comparison, metric deltas, evaluation scorecard and investigation archive summary
- v2.0: One-click synthetic investigation orchestration, premium investigation status cards, visual execution timeline, structured root-cause evidence cards, and scenario comparison reporting.

## ATLAS AI v2.0 — Autonomous Investigation

ATLAS AI v2.0 introduces a one-click, deterministic investigation
workflow for synthetic payment incidents.

### Capabilities

- Compare two predefined synthetic incident scenarios.
- Generate deterministic root-cause hypotheses.
- Evaluate investigation reports using seven quality checks.
- Display investigation status and execution safety indicators.
- Visualize workflow stages and execution durations.
- Review supporting evidence, alternative explanations, and missing evidence.
- Compare payment success rates, processing latency, and failed transactions.

### Investigation API

Endpoint:

POST /api/investigations/run

Example request:

{
  "scenario_a": "provider_outage",
  "scenario_b": "healthy"
}

The API returns investigation status, execution stages,
scenario comparisons, root-cause hypotheses, and report evaluation results.

### Safety Boundaries

- Uses predefined synthetic payment scenarios only.
- Does not contact live payment providers.
- Does not execute real payment transactions or recovery actions.
- Does not automatically archive investigation results.
- Requires human review of investigation findings.
- Root-cause hypotheses are not verified causal conclusions.
- The local server is not authenticated and must not be publicly exposed.

The term "autonomous" refers to automated investigation orchestration,
not autonomous remediation or production decision-making.

## License

See LICENSE.
