"""ATLAS AI Phase 1, Step 9B: safely connect storage and add history viewing.

Run from any directory with: python atlas_automate.py
Place this file in the ATLAS-AI project root alongside main.py and storage.py.
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / 'main.py'
STORAGE = ROOT / 'storage.py'
HISTORY = ROOT / 'history.py'


def abort(message: str) -> None:
    print(f'ERROR: {message}')
    raise SystemExit(1)


def main() -> None:
    print('ATLAS AI | Phase 1, Step 9B automation')
    if not MAIN.is_file() or not STORAGE.is_file():
        abort('Place atlas_automate.py in ATLAS-AI beside main.py and storage.py.')

    original = MAIN.read_text(encoding='utf-8-sig')
    try:
        tree = ast.parse(original)
    except SyntaxError as exc:
        abort(f'main.py contains a syntax error on line {exc.lineno}. No files changed.')

    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if 'main' not in functions:
        abort('Cannot find def main() in main.py. No files changed.')

    main_fn = functions['main']
    has_save_call = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'save_incident'
        for node in ast.walk(main_fn)
    )
    # Require a top-level incident report print so the insertion point is unambiguous.
    candidates = []
    for node in main_fn.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Name) or call.func.id != 'print':
            continue
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and isinstance(n.func.value, ast.Name) and n.func.value.id == 'json'
               and n.func.attr == 'dumps' and n.args and isinstance(n.args[0], ast.Name)
               and n.args[0].id == 'incident' for n in ast.walk(call)):
            candidates.append(node)

    if not has_save_call and len(candidates) != 1:
        abort('Cannot safely identify the incident JSON print in main(). No files changed.')

    lines = original.splitlines(keepends=True)
    newline = '\r\n' if '\r\n' in original else '\n'
    changed = False
    if not has_save_call:
        target = candidates[0]
        indent = ' ' * target.col_offset
        lines.insert(target.end_lineno, f'{indent}save_incident(incident){newline}')
        changed = True

    revised = ''.join(lines)
    # Add import if missing. Insert immediately before the first top-level function.
    parsed = ast.parse(revised)
    imported = any(
        isinstance(node, ast.ImportFrom) and node.module == 'storage'
        and any(alias.name == 'save_incident' for alias in node.names)
        for node in parsed.body
    )
    if not imported:
        top_fns = [node for node in parsed.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not top_fns:
            abort('Cannot find a top-level function. No files changed.')
        new_lines = revised.splitlines(keepends=True)
        new_lines.insert(top_fns[0].lineno - 1, f'from storage import save_incident{newline}{newline}')
        revised = ''.join(new_lines)
        changed = True

    try:
        ast.parse(revised)
    except SyntaxError as exc:
        abort(f'Proposed edit is invalid on line {exc.lineno}. No files changed.')

    history_code = '''"""Read saved ATLAS synthetic incident reports without changing them."""\nimport json\nfrom storage import INCIDENTS_FILE\n\n\ndef show_history():\n    if not INCIDENTS_FILE.exists():\n        print("No saved incidents yet. Run python main.py first.")\n        return\n\n    print("ATLAS AI | SAVED INCIDENT HISTORY")\n    count = 0\n    with INCIDENTS_FILE.open("r", encoding="utf-8") as records:\n        for line_number, line in enumerate(records, 1):\n            if not line.strip():\n                continue\n            try:\n                incident = json.loads(line)\n            except json.JSONDecodeError:\n                print(f"Skipping invalid record on line {line_number}")\n                continue\n            count += 1\n            print(f"{count}. {incident.get('incident_type', 'UNKNOWN')} | "\n                  f"{incident.get('severity', 'UNKNOWN')} | "\n                  f"{incident.get('status', 'UNKNOWN')} | "\n                  f"{incident.get('incident_id', 'NO-ID')}")\n    print(f"Total saved records: {count}")\n\n\nif __name__ == "__main__":\n    show_history()\n'''
    if HISTORY.exists() and HISTORY.read_text(encoding='utf-8') != history_code:
        abort('history.py already exists with different content. No files changed.')

    if changed:
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = ROOT / f'main.py.backup_{stamp}'
        shutil.copy2(MAIN, backup)
        MAIN.write_text(revised, encoding='utf-8')
        print(f'Updated main.py (backup: {backup.name})')
    else:
        print('main.py already has the storage integration.')

    if not HISTORY.exists():
        HISTORY.write_text(history_code, encoding='utf-8')
        print('Created history.py')
    else:
        print('history.py is already up to date.')

    print('Checking Python syntax...')
    for path in (MAIN, STORAGE, HISTORY):
        ast.parse(path.read_text(encoding='utf-8-sig'))
    print('Syntax checks passed.')
    print('Running one synthetic incident...')
    result = subprocess.run([sys.executable, str(MAIN)], cwd=ROOT, text=True)
    if result.returncode:
        abort('main.py did not complete successfully. See output above; backup is available.')
    print('Showing saved history...')
    result = subprocess.run([sys.executable, str(HISTORY)], cwd=ROOT, text=True)
    if result.returncode:
        abort('history.py did not complete successfully. See output above.')
    print('ATLAS Phase 1 Step 9B automation completed successfully!')


if __name__ == '__main__':
    main()
