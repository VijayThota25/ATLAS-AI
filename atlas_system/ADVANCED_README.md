# ATLAS AI advanced investigation and digital twin

This upgrade does not replace or modify the existing dashboard, server, or engine.

## Run the tests

```powershell
python -m unittest discover -s atlas_system -p "test_*.py" -v
```

## Enable LangGraph and SimPy (free packages)

```powershell
python -m pip install -r atlas_system/requirements-advanced.txt
python -m unittest discover -s atlas_system -p "test_*.py" -v
```

## Try the new modules

```powershell
cd atlas_system
python -c "from engine import investigate; from agent_pipeline import investigate_agents; print(investigate_agents(investigate('provider_outage')))"
python -c "from engine import investigate; from digital_twin import experiment; print(experiment(investigate('provider_outage'), 'backup_provider'))"
```

## Optional local LLM

`ask_local_llm` can call Ollama on localhost after you install Ollama and pull a model yourself.
No paid API key is required, but local models need memory and CPU/GPU resources.

## Limitations

Agent reasoning is still rule-based unless you explicitly call local Ollama. SimPy
uses illustrative fixed latency assumptions; experiments are not calibrated to
production payment data. Existing dashboard still uses v0.1 endpoints.
