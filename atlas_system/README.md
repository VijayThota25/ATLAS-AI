# ATLAS AI — local-first simulation prototype

Run `python atlas_master.py` from the parent ATLAS-AI folder. It writes this application without overwriting your existing Phase 1 files.

## Included
- Four synthetic payment scenarios and deterministic severity classification
- Evidence-based rule-driven investigation (not a language model)
- JSONL local incident and action audit history
- Illustrative recovery counterfactuals (not SimPy or a calibrated digital twin)
- Human approval required for sandbox-only execution
- Dependency-free localhost HTTP API and interactive dashboard
- Python unittest checks

## Start again
From ATLAS-AI folder: `python atlas_system/server.py`
Open `http://127.0.0.1:8765`.

## Safety / limitations
Development-only local demo. Do not expose this server to the public internet; it has no authentication. No real payment providers are contacted. Metrics and recovery improvements are synthetic and illustrative. A production system would need a real database, security, calibrated simulation, LangGraph/model integration, monitoring, CI/CD and deployment hardening.
