"""SQLite audit mirror and local operation metrics. No external services."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parent / 'data' / 'atlas.db'

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute('PRAGMA busy_timeout=10000')
    conn.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, record_key TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(kind,record_key))')
    conn.execute('CREATE TABLE IF NOT EXISTS operations (id INTEGER PRIMARY KEY, operation TEXT NOT NULL, duration_ms REAL NOT NULL, success INTEGER NOT NULL, created_at TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS workflow_traces (id INTEGER PRIMARY KEY, trace_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)')
    return conn

def mirror(kind, record):
    if kind == 'incident':
        key = record['incident_id']
    else:
        key = record['action_id'] + ':' + record['status']
    with closing(connect()) as db, db:
        db.execute('INSERT OR IGNORE INTO records(kind,record_key,payload,created_at) VALUES (?,?,?,?)',
                   (kind, key, json.dumps(record), datetime.now(timezone.utc).isoformat()))

def import_history(incidents, actions):
    count = 0
    for kind, path in [('incident', incidents), ('action', actions)]:
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                mirror(kind, json.loads(line))
                count += 1
    return count

def record_operation(name, duration_ms, success):
    with closing(connect()) as db, db:
        db.execute('INSERT INTO operations(operation,duration_ms,success,created_at) VALUES (?,?,?,?)',
                   (name, round(duration_ms, 2), int(bool(success)), datetime.now(timezone.utc).isoformat()))

def overview():
    with closing(connect()) as db, db:
        rows = db.execute('SELECT kind, COUNT(*) FROM records GROUP BY kind').fetchall()
        operations = db.execute('SELECT operation, COUNT(*), ROUND(AVG(duration_ms),2), SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) FROM operations GROUP BY operation ORDER BY operation').fetchall()
    return {'storage': 'SQLITE_LOCAL_MIRROR', 'records': dict(rows),
            'operations': [{'operation': x[0], 'count': x[1], 'average_duration_ms': x[2], 'errors': x[3]} for x in operations],
            'limitations': 'Local audit mirror. JSONL remains the application source of truth. Metrics reflect operations recorded after v0.5.'}

# ATLAS_V11_PERSISTENCE
def save_workflow_trace(result):
    import uuid
    if result.get('action_executed') is not False or result.get('requires_human_approval') is not True or result.get('data_persisted') is not False:
        raise ValueError('Only safe read-only traces may be saved')
    saved = dict(result, trace_id=str(uuid.uuid4()), created_at=datetime.now(timezone.utc).isoformat(), data_persisted=True, mode='PERSISTED_SYNTHETIC_TRACE')
    saved['limitations'] = 'Local synthetic audit only. No real payments, recovery actions, live LLM or external calls.'
    with closing(connect()) as db, db:
        db.execute('INSERT INTO workflow_traces(trace_id,payload,created_at) VALUES (?,?,?)', (saved['trace_id'], json.dumps(saved), saved['created_at']))
    return saved

def workflow_history(limit=20):
    limit = max(1, min(int(limit), 100))
    with closing(connect()) as db, db:
        rows = db.execute('SELECT payload FROM workflow_traces ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [json.loads(row[0]) for row in rows]
