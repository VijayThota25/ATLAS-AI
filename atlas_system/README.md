# ATLAS AI — Technical Architecture

## Overview

ATLAS AI is a local-first, synthetic payment incident investigation prototype.

The system combines deterministic investigation logic, optional LangGraph orchestration, stochastic recovery experiments, report evaluation, and SQLite-based investigation archiving.

It is not a production payment processing or autonomous recovery system.

## Architecture

1. Synthetic incident generation and classification
2. Detection and evidence collection
3. Rule-based reasoning and recovery recommendations
4. Synthetic recovery experimentation
5. Deterministic root-cause analysis
6. Incident comparison and report evaluation
7. Explicit investigation archiving
8. Local dashboard and SQLite persistence

## Core Modules

| Module | Responsibility |
|---|---|
| engine.py | Synthetic scenarios and incident classification |
| agent_pipeline.py | Detection, reasoning and recommendation |
| digital_twin.py | Monte Carlo and optional SimPy experiments |
| workflow_trace.py | Deterministic workflow traces and regression checks |
| atlas_store.py | SQLite persistence |
| root_cause.py | Deterministic root-cause hypotheses |
| incident_comparison.py | Synthetic incident comparison |
| report_evaluator.py | Report evaluation |
| investigation_archive.py | Investigation archive storage and retrieval |
| server.py | Local HTTP API and dashboard delivery |

## Agent Orchestration

The optional LangGraph workflow contains three nodes:

    START
      |
    detect
      |
    reason
      |
    recommend
      |
     END

The nodes use deterministic Python rules.

If LangGraph cannot be imported, the same stages execute sequentially.

The reasoning output is an unverified hypothesis, not a confirmed root cause.

## Recovery Simulation

Supported strategies:

- backup_provider
- bounded_retries
- circuit_breaker

The experiment uses seeded Monte Carlo trials to estimate synthetic payment success-rate changes.

Default parameters:

- Trials: 1000
- Random seed: 42
- Accepted trial range: 10–100000

When SimPy is installed, it additionally simulates request completion delays for up to 200 events.

SimPy timing results do not determine the Monte Carlo success-rate estimates.

All improvements are illustrative and are not calibrated against real payment-provider telemetry.

## Optional Local LLM

The Ollama advisory integration uses:

    http://127.0.0.1:11434/api/generate

It is optional and restricted to the local endpoint.

LLM responses are advisory and cannot authorize real-world execution.

## Investigation Archive

The v1.6 archive supports:

- Explicitly saving an evaluated synthetic investigation
- SQLite persistence
- Retrieving archived reports by ID
- Listing investigation history
- Downloading archived JSON
- Rejecting saves when the current report has not passed evaluation

Archiving data is not equivalent to executing a recovery action.

## Run Locally

From the project root:

    python atlas_system/server.py

Open:

    http://127.0.0.1:8765

Optional dependencies:

    python -m pip install -r requirements.txt

Verified development runtime: Python 3.12.6.

## Testing

Run the unit tests:

    python -m unittest discover -s atlas_system -p "test_*.py" -v

The v1.6 release passed 48 automated tests and 11 workflow regression checks.

## Security and Limitations

- All payment incidents and metrics are synthetic.
- No real payment transactions are executed.
- Human approval is represented through simulation controls.
- The HTTP server is intended for localhost only.
- The API does not provide production authentication.
- Root-cause hypotheses require independent verification.
- Recovery estimates are not production forecasts.
- The system must not be exposed to the public internet.
