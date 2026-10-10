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
