"""Explainable agent pipeline. LangGraph optional; no paid LLM required.
Ollama is optional and only accessed at localhost with an explicit opt-in.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import URLError


def detect(incident):
    metrics = incident['metrics']
    return {'severity': incident['severity'], 'evidence': incident['evidence'],
            'metrics': metrics, 'incident_id': incident['incident_id']}


def reason(state):
    m = state['metrics']
    if m['payment_success_rate'] < 60:
        hypothesis = 'Provider availability degradation is plausible; confirm using provider telemetry.'
    elif m['average_latency_ms'] > 3000:
        hypothesis = 'Upstream latency or saturation is plausible; inspect timeout traces.'
    elif m['failed_transactions'] > 1000:
        hypothesis = 'Retry amplification is plausible; inspect retry volume and idempotency.'
    else:
        hypothesis = 'No critical provider symptoms; continue monitoring.'
    return {'hypothesis': hypothesis, 'confidence': 'UNVERIFIED_HYPOTHESIS'}


def recommend(state):
    m = state['metrics']
    if m['payment_success_rate'] < 60: strategy = 'backup_provider'
    elif m['failed_transactions'] > 1000: strategy = 'bounded_retries'
    else: strategy = 'circuit_breaker'
    return {'recommended_strategy': strategy, 'requires_human_approval': True}


def investigate_agents(incident):
    """Use LangGraph if installed, otherwise explicit sequential agent steps."""
    try:
        from langgraph.graph import StateGraph, START, END
    except ImportError:
        state = detect(incident)
        state.update(reason(state))
        state.update(recommend(state))
        return {'orchestrator': 'SEQUENTIAL_FALLBACK_NOT_LANGGRAPH', **state}
    from typing import TypedDict, Any
    class State(TypedDict, total=False):
        incident: dict[str, Any]
        incident_id: str
        severity: str
        evidence: list[str]
        metrics: dict[str, Any]
        hypothesis: str
        confidence: str
        recommended_strategy: str
        requires_human_approval: bool
    graph = StateGraph(State)
    graph.add_node('detect', lambda s: detect(s['incident']))
    graph.add_node('reason', reason)
    graph.add_node('recommend', recommend)
    graph.add_edge(START, 'detect')
    graph.add_edge('detect', 'reason')
    graph.add_edge('reason', 'recommend')
    graph.add_edge('recommend', END)
    result = graph.compile().invoke({'incident': incident})
    result.pop('incident', None)
    return {'orchestrator': 'LANGGRAPH', **result}


def ask_local_llm(incident, model='llama3.2', endpoint='http://127.0.0.1:11434/api/generate'):
    """Optional local Ollama. Treat output as advisory, never authorize execution."""
    if endpoint != 'http://127.0.0.1:11434/api/generate':
        raise ValueError('Only local Ollama endpoint is permitted')
    prompt = ('Analyze these SYNTHETIC payment metrics. Give a cautious hypothesis and '
              'what evidence would verify it. Never claim certainty or execute actions.\n'
              + json.dumps({'scenario': incident['scenario'], 'metrics': incident['metrics']}))
    payload = json.dumps({'model': model, 'prompt': prompt, 'stream': False}).encode()
    req = Request(endpoint, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=35) as response:
            return {'analysis_type': 'LOCAL_OLLAMA_ADVISORY', 'response': json.load(response)['response']}
    except (URLError, TimeoutError, KeyError) as exc:
        return {'analysis_type': 'LOCAL_OLLAMA_UNAVAILABLE', 'error': str(exc)}
