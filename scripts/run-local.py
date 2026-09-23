"""Run both APIs locally with SQLite. Not a substitute for Kubernetes."""
import os
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
env = {**os.environ, 'DATABASE_MODE': 'sqlite',
       'SQLITE_DIRECTORY': str(root / '.local-data'),
       'FIELD_SERVICE_URL': 'http://127.0.0.1:8001',
       'ACTIVITY_SERVICE_URL': 'http://127.0.0.1:8002'}
processes = []
try:
    for module, port in [('fields', '8001'), ('activities', '8002')]:
        processes.append(subprocess.Popen([sys.executable, '-m', 'uvicorn',
            f'services.{module}.app:app', '--host', '127.0.0.1', '--port', port], cwd=root, env=env))
    print('FarmTrack: http://127.0.0.1:8001 — Ctrl+C to stop', flush=True)
    while all(p.poll() is None for p in processes):
        import time
        time.sleep(1)
finally:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        process.wait(timeout=10)
