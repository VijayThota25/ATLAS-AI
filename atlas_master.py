"""ATLAS AI one-command local bootstrap. Python 3.10+; standard library only.
Preserves existing project files and writes generated app under atlas_system/.
Usage: python atlas_master.py
"""
from pathlib import Path
import subprocess
import sys
import textwrap
import json

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'atlas_system'
FILES = {
'engine.py': r'''
"""Local-first synthetic payments investigation engine. No real payments or APIs."""
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCENARIOS = {
    'healthy': {'payment_success_rate': 99.2, 'average_latency_ms': 150, 'failed_transactions': 5},
    'provider_outage': {'payment_success_rate': 42.5, 'average_latency_ms': 4200, 'failed_transactions': 1284},
    'latency_spike': {'payment_success_rate': 94.0, 'average_latency_ms': 3500, 'failed_transactions': 180},
    'retry_storm': {'payment_success_rate': 76.0, 'average_latency_ms': 1800, 'failed_transactions': 2400},
}
DATA = Path(__file__).resolve().parent / 'data'
HISTORY = DATA / 'incidents.jsonl'
ACTIONS = DATA / 'actions.jsonl'

def classify(metrics):
    success, latency, failed = metrics['payment_success_rate'], metrics['average_latency_ms'], metrics['failed_transactions']
    reasons = []
    if success < 60: reasons.append('Critical drop in payment success rate')
    elif success < 90: reasons.append('Payment success rate below normal')
    if latency > 3000: reasons.append('Severe payment processing latency')
    elif latency > 1000: reasons.append('Elevated payment processing latency')
    if failed > 1000: reasons.append('High number of failed transactions')
    severity = 'CRITICAL' if success < 60 or latency > 3000 else 'HIGH' if success < 90 or latency > 1000 or failed > 1000 else 'HEALTHY'
    return severity, reasons

def investigate(name):
    if name not in SCENARIOS: raise ValueError('Unknown scenario')
    metrics = SCENARIOS[name].copy()
    severity, reasons = classify(metrics)
    causes = {
        'healthy': 'No abnormal behavior detected in synthetic metrics',
        'provider_outage': 'Synthetic upstream payment-provider availability degradation',
        'latency_spike': 'Synthetic high processing latency in provider calls',
        'retry_storm': 'Synthetic excessive retries amplifying failed transactions',
    }
    recommendation = {
        'healthy': 'No intervention required',
        'provider_outage': 'Evaluate routing traffic to a backup provider',
        'latency_spike': 'Evaluate circuit breaker and request timeouts',
        'retry_storm': 'Evaluate bounded retries and exponential backoff',
    }
    return {
        'incident_id': str(uuid.uuid4()),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'scenario': name,
        'environment': 'SIMULATION',
        'metrics': metrics,
        'severity': severity,
        'status': 'HEALTHY' if severity == 'HEALTHY' else 'DETECTED',
        'evidence': reasons,
        'hypothesis': causes[name],
        'recommendation': recommendation[name],
        'analysis_type': 'DETERMINISTIC_DEMO_NOT_LLM',
    }

def append_record(path, record):
    DATA.mkdir(exist_ok=True, parents=True)
    with path.open('a', encoding='utf-8') as f: f.write(json.dumps(record) + '\n')

def read_records(path, limit=50):
    if not path.exists(): return []
    with path.open(encoding='utf-8') as f:
        records = [json.loads(line) for line in f if line.strip()]
    return records[-limit:][::-1]

def create_incident(name=None):
    incident = investigate(name or random.choice(list(SCENARIOS)))
    append_record(HISTORY, incident)
    return incident

def simulate_recovery(incident, strategy):
    """Illustrative deterministic counterfactual, not a validated digital twin."""
    if strategy not in ('backup_provider', 'bounded_retries', 'circuit_breaker'):
        raise ValueError('Unsupported strategy')
    baseline = incident['metrics']['payment_success_rate']
    delta = {'backup_provider': 25.0, 'bounded_retries': 12.0, 'circuit_breaker': 8.0}[strategy]
    projected = round(min(99.9, baseline + delta), 1)
    return {'strategy': strategy, 'baseline_success_rate': baseline, 'projected_success_rate': projected,
            'improvement_percentage_points': round(projected - baseline, 1),
            'disclaimer': 'Illustrative synthetic estimate, not a calibrated simulation'}

def propose_action(incident, strategy):
    simulation = simulate_recovery(incident, strategy)
    proposal = {'action_id': str(uuid.uuid4()), 'incident_id': incident['incident_id'],
                'strategy': strategy, 'status': 'PENDING_HUMAN_APPROVAL',
                'simulation': simulation, 'environment': 'SIMULATION'}
    append_record(ACTIONS, proposal)
    return proposal

def approve_action(action_id):
    actions = read_records(ACTIONS, 100000)
    proposal = next((a for a in actions if a.get('action_id') == action_id and a.get('status') == 'PENDING_HUMAN_APPROVAL'), None)
    if not proposal: raise ValueError('No pending proposal found')
    result = {'action_id': action_id, 'incident_id': proposal['incident_id'],
              'status': 'SIMULATED_EXECUTION_COMPLETE', 'environment': 'SIMULATION',
              'timestamp': datetime.now(timezone.utc).isoformat(),
              'note': 'No external payment system was modified'}
    append_record(ACTIONS, result)
    return result
''',
'server.py': r'''
"""Dependency-free HTTP API and local dashboard."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from engine import SCENARIOS, HISTORY, ACTIONS, create_incident, read_records, propose_action, approve_action

HERE = Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def respond(self, code, value):
        body = json.dumps(value).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            body = (HERE / 'dashboard.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == '/api/health': self.respond(200, {'status': 'ok', 'mode': 'local_simulation'})
        elif path == '/api/scenarios': self.respond(200, list(SCENARIOS))
        elif path == '/api/incidents': self.respond(200, read_records(HISTORY))
        elif path == '/api/actions': self.respond(200, read_records(ACTIONS))
        else: self.respond(404, {'error': 'Not found'})
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 10000: return self.respond(413, {'error': 'Request too large'})
            payload = json.loads(self.rfile.read(length) or b'{}')
            path = urlparse(self.path).path
            if path == '/api/incidents':
                name = payload.get('scenario')
                if name is not None and name not in SCENARIOS: return self.respond(400, {'error': 'Invalid scenario'})
                return self.respond(201, create_incident(name))
            if path == '/api/proposals':
                incident_id = payload.get('incident_id')
                incident = next((x for x in read_records(HISTORY, 100000) if x['incident_id'] == incident_id), None)
                if incident is None: return self.respond(404, {'error': 'Incident not found'})
                return self.respond(201, propose_action(incident, payload.get('strategy')))
            if path == '/api/approve':
                return self.respond(200, approve_action(payload.get('action_id')))
            return self.respond(404, {'error': 'Not found'})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            return self.respond(400, {'error': str(e)})

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    print('ATLAS AI dashboard: http://127.0.0.1:8765', flush=True)
    print('Press Ctrl+C to stop.', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__': main()
''',
'dashboard.html': r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ATLAS AI | Mission Control</title><style>
:root{color-scheme:dark;font-family:Inter,Segoe UI,Arial,sans-serif;background:#0b1220;color:#eef4ff}
*{box-sizing:border-box}body{margin:0}header{padding:30px max(24px,7vw);border-bottom:1px solid #27334b;background:#111c2f}
small{color:#93a9c9;letter-spacing:.15em}h1{margin:8px 0;font-size:36px}h2{font-size:19px}
main{max-width:1250px;margin:auto;padding:28px 24px}section{background:#111c2f;border:1px solid #283753;border-radius:14px;padding:22px;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}.stat{background:#192840;padding:20px;border-radius:10px}
strong{font-size:25px;display:block;margin-top:6px}label{display:block;margin-bottom:8px;color:#aebfd8}
select,button{background:#253b5a;color:white;border:1px solid #456083;padding:12px;border-radius:8px;font-size:15px}
button{background:#2563eb;border-color:#2563eb;cursor:pointer}button:hover{background:#1d4ed8}button:disabled{opacity:.5}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#091321;border-radius:8px;padding:16px;max-height:390px;overflow:auto}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:end}.note{color:#aabbd5}.tag{color:#7dd3fc}
</style></head><body><header><small>LOCAL SIMULATION · NO LIVE PAYMENTS</small><h1>ATLAS AI / Mission Control</h1><p class="note">Synthetic incident detection, explainable investigation, recovery proposals and human approval.</p></header>
<main><div class="grid"><section class="stat">Incidents recorded<strong id="count">0</strong></section><section class="stat">Critical incidents<strong id="critical">0</strong></section><section class="stat">Pending actions<strong id="pending">0</strong></section></div>
<section><h2>1. Generate synthetic incident</h2><div class="row"><div><label for="scenario">Scenario</label><select id="scenario"><option value="">Random</option><option value="healthy">Healthy</option><option value="provider_outage">Provider outage</option><option value="latency_spike">Latency spike</option><option value="retry_storm">Retry storm</option></select></div><button onclick="generate()">Generate & investigate</button></div></section>
<section><h2>2. Incident investigation</h2><pre id="incident">Generate an incident to see evidence and investigation.</pre></section>
<section><h2>3. Recovery simulation & human approval</h2><div class="row"><div><label for="strategy">Recovery strategy</label><select id="strategy"><option value="backup_provider">Backup provider</option><option value="bounded_retries">Bounded retries</option><option value="circuit_breaker">Circuit breaker</option></select></div><button onclick="propose()">Simulate & propose</button><button id="approve" onclick="approve()" disabled>Approve sandbox action</button></div><pre id="proposal">Select an incident first. No real systems will be changed.</pre></section>
<section><h2>4. Recent incident history</h2><pre id="history">Loading...</pre></section>
<p class="note">Demo limitations: deterministic rule-based investigation; counterfactual projections are illustrative, not calibrated. Future phases can integrate LangGraph, SimPy, databases and production-grade security.</p></main>
<script>
let current=null,pending=null;
async function api(path,method='GET',data){let r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});let j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
function display(id,obj){document.getElementById(id).textContent=JSON.stringify(obj,null,2)}
async function refresh(){let [inc,acts]=await Promise.all([api('/api/incidents'),api('/api/actions')]);document.getElementById('count').textContent=inc.length;document.getElementById('critical').textContent=inc.filter(x=>x.severity==='CRITICAL').length;let completed=new Set(acts.filter(x=>x.status==='SIMULATED_EXECUTION_COMPLETE').map(x=>x.action_id));document.getElementById('pending').textContent=acts.filter(x=>x.status==='PENDING_HUMAN_APPROVAL'&&!completed.has(x.action_id)).length;display('history',inc.slice(0,10))}
async function generate(){try{current=await api('/api/incidents','POST',{scenario:document.getElementById('scenario').value||null});pending=null;document.getElementById('approve').disabled=true;display('incident',current);display('proposal','Select a strategy and click Simulate & propose');await refresh()}catch(e){alert(e.message)}}
async function propose(){if(!current)return alert('Generate an incident first');try{pending=await api('/api/proposals','POST',{incident_id:current.incident_id,strategy:document.getElementById('strategy').value});display('proposal',pending);document.getElementById('approve').disabled=false;await refresh()}catch(e){alert(e.message)}}
async function approve(){if(!pending)return;try{let result=await api('/api/approve','POST',{action_id:pending.action_id});display('proposal',result);pending=null;document.getElementById('approve').disabled=true;await refresh()}catch(e){alert(e.message)}}
refresh().catch(e=>display('history',{error:e.message}));
</script></body></html>''',
'test_engine.py': r'''
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import engine

class TestEngine(unittest.TestCase):
    def test_all_scenarios(self):
        expected = {'healthy':'HEALTHY','provider_outage':'CRITICAL','latency_spike':'CRITICAL','retry_storm':'HIGH'}
        for name, severity in expected.items():
            with self.subTest(name=name):
                result = engine.investigate(name)
                self.assertEqual(result['severity'], severity)
                self.assertEqual(result['environment'], 'SIMULATION')
    def test_storage(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'incidents.jsonl'
            with patch.object(engine, 'HISTORY', path):
                result = engine.create_incident('healthy')
                self.assertEqual(engine.read_records(path)[0]['incident_id'], result['incident_id'])
    def test_approval_gate(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'actions.jsonl'
            with patch.object(engine, 'ACTIONS', path):
                incident = engine.investigate('retry_storm')
                proposal = engine.propose_action(incident, 'bounded_retries')
                self.assertEqual(proposal['status'], 'PENDING_HUMAN_APPROVAL')
                completed = engine.approve_action(proposal['action_id'])
                self.assertEqual(completed['status'], 'SIMULATED_EXECUTION_COMPLETE')
    def test_invalid_strategy(self):
        with self.assertRaises(ValueError):
            engine.simulate_recovery(engine.investigate('healthy'), 'unknown')

if __name__ == '__main__': unittest.main()
''',
'README.md': r'''
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
'''
}

def main():
    if sys.version_info < (3, 10):
        print('Python 3.10 or newer is required.')
        sys.exit(1)
    APP.mkdir(exist_ok=True)
    created = []
    kept = []
    for name, contents in FILES.items():
        path = APP / name
        if path.exists():
            kept.append(name)
        else:
            path.write_text(textwrap.dedent(contents).lstrip(), encoding='utf-8')
            created.append(name)
    print('ATLAS master bootstrap')
    print('Created:', ', '.join(created) or 'none')
    if kept: print('Preserved existing:', ', '.join(kept))
    print('Your original main.py, detector.py, scenarios.py and storage.py were NOT changed.')
    print('Running automated tests...')
    result = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_engine.py'], cwd=APP)
    if result.returncode:
        print('Tests failed. Server not started. Review errors above.')
        sys.exit(result.returncode)
    print('Tests passed. Starting ATLAS Mission Control on http://127.0.0.1:8765', flush=True)
    print('Open that address in your browser. Press Ctrl+C in this terminal to stop.', flush=True)
    subprocess.run([sys.executable, str(APP / 'server.py')], cwd=APP)

if __name__ == '__main__':
    main()
