# ATLAS_V06_EVALUATIONS
# ATLAS_V05_OBSERVABILITY
# ATLAS_V04_STRUCTURED_ADVISORY
# ATLAS_V03_LOCAL_OLLAMA
"""Dependency-free HTTP API and local dashboard."""
import json
import time
from atlas_store import import_history, overview, record_operation, save_workflow_trace, workflow_history  # ATLAS_V11_PERSISTENCE
from evaluation_suite import run_and_record, history as evaluation_history
from live_evaluation import run_live  # ATLAS_V07_LIVE_EVALUATION
from evaluation_analytics import summarize  # ATLAS_V08_ANALYTICS
from reliability_lab import simulate as reliability_simulate, regression as reliability_regression  # ATLAS_V09_RELIABILITY
from workflow_trace import trace as workflow_trace, regression as workflow_regression  # ATLAS_V10_WORKFLOW
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
        elif path == '/api/health': self.respond(200, {'status': 'ok', 'mode': 'local_simulation', 'version': '1.1', 'investigation': 'LangGraph', 'recovery': 'SimPy', 'local_llm': 'Ollama optional structured advisory'})
        elif path == '/api/scenarios': self.respond(200, list(SCENARIOS))
        elif path == '/api/incidents': self.respond(200, read_records(HISTORY))
        elif path == '/api/actions': self.respond(200, read_records(ACTIONS))
        elif path == '/api/observability': self.respond(200, overview())
        elif path == '/api/evaluations': self.respond(200, evaluation_history())
        elif path == '/api/analytics': self.respond(200, summarize())
        elif path == '/api/reliability/regression': self.respond(200, reliability_regression())
        elif path == '/api/workflow/regression': self.respond(200, workflow_regression())
        elif path == '/api/workflow/history': self.respond(200, workflow_history())
        else: self.respond(404, {'error': 'Not found'})
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 10000: return self.respond(413, {'error': 'Request too large'})
            payload = json.loads(self.rfile.read(length) or b'{}')
            path = urlparse(self.path).path
            if path == '/api/workflow/trace':
                return self.respond(200, workflow_trace(payload.get('scenario', 'provider_outage'), payload.get('fault', 'none')))
            if path == '/api/workflow/trace/save':
                result = workflow_trace(payload.get('scenario', 'provider_outage'), payload.get('fault', 'none'))
                return self.respond(201, save_workflow_trace(result))
            if path == '/api/reliability/simulate':
                return self.respond(200, reliability_simulate(payload.get('fault', 'none')))
            if path == '/api/evaluations/live':
                return self.respond(200, run_live())
            if path == '/api/evaluations/run':
                return self.respond(200, run_and_record())
            if path == '/api/incidents':
                name = payload.get('scenario')
                if name is not None and name not in SCENARIOS: return self.respond(400, {'error': 'Invalid scenario'})
                return self.respond(201, create_incident(name))
            if path == '/api/llm-analysis':
                incident_id = payload.get('incident_id')
                if not isinstance(incident_id, str):
                    return self.respond(400, {'error': 'incident_id is required'})
                incident = next((x for x in read_records(HISTORY, 100000) if x['incident_id'] == incident_id), None)
                if incident is None:
                    return self.respond(404, {'error': 'Incident not found'})
                from structured_advisory import analyze_structured
                started = time.perf_counter()
                try:
                    advisory = analyze_structured(incident)
                    success = 'error' not in advisory
                except Exception:
                    record_operation('llm_analysis', (time.perf_counter()-started)*1000, False)
                    raise
                record_operation('llm_analysis', (time.perf_counter()-started)*1000, success)
                return self.respond(200, {'incident_id': incident_id, **advisory,
                    'disclaimer': 'Advisory hypothesis only. Not verified; cannot approve actions.'})
            if path == '/api/proposals':
                incident_id = payload.get('incident_id')
                incident = next((x for x in read_records(HISTORY, 100000) if x['incident_id'] == incident_id), None)
                if incident is None: return self.respond(404, {'error': 'Incident not found'})
                started = time.perf_counter()
                try:
                    proposal = propose_action(incident, payload.get('strategy'))
                except Exception:
                    record_operation('recovery_simulation', (time.perf_counter()-started)*1000, False)
                    raise
                record_operation('recovery_simulation', (time.perf_counter()-started)*1000, True)
                return self.respond(201, proposal)
            if path == '/api/approve':
                return self.respond(200, approve_action(payload.get('action_id')))
            return self.respond(404, {'error': 'Not found'})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            return self.respond(400, {'error': str(e)})

def main():
    imported = import_history(HISTORY, ACTIONS)
    print('ATLAS SQLite audit mirror ready; history rows scanned:', imported, flush=True)
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    print('ATLAS AI dashboard: http://127.0.0.1:8765', flush=True)
    print('Press Ctrl+C to stop.', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__': main()
