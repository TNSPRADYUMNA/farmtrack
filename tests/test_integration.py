"""Real HTTP tests with two subprocesses and an isolated SQLite directory."""
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

class FarmTrackIntegration(unittest.TestCase):
    def test_workflow_failure_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            field_port, activity_port = free_port(), free_port()
            field_url, activity_url = f'http://127.0.0.1:{field_port}', f'http://127.0.0.1:{activity_port}'
            env = {**os.environ, 'DATABASE_MODE': 'sqlite', 'SQLITE_DIRECTORY': directory,
                   'FIELD_SERVICE_URL': field_url, 'ACTIVITY_SERVICE_URL': activity_url}
            processes = []
            def start(module, port):
                process = subprocess.Popen([sys.executable, '-m', 'uvicorn', f'services.{module}.app:app',
                    '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                processes.append(process)
                for _ in range(100):
                    if process.poll() is not None:
                        self.fail(f'{module} failed to start')
                    try:
                        if httpx.get(f'http://127.0.0.1:{port}/health/ready', trust_env=False).status_code == 200:
                            return process
                    except httpx.RequestError:
                        pass
                    time.sleep(.1)
                self.fail('Startup timeout')
            try:
                field_process = start('fields', field_port)
                start('activities', activity_port)
                with httpx.Client(base_url=field_url, trust_env=False) as client:
                    self.assertEqual(client.get('/').status_code, 200)
                    self.assertEqual(client.post('/api/fields', json={'name':'Bad','crop':'Rice','area_hectares':-1}).status_code, 422)
                    result = client.post('/api/fields', json={'name':"North's meadow",'crop':'Rice','area_hectares':2.5})
                    self.assertEqual(result.status_code, 201)
                    field = result.json()
                    payload = {'field_id':field['id'],'kind':'watering','due_date':'2026-10-01','notes':'Morning round'}
                    self.assertEqual(client.post('/api/activities', json={**payload,'field_id':str(uuid4())}).status_code, 404)
                    self.assertEqual(client.post('/api/activities', json={**payload,'kind':'invalid'}).status_code, 422)
                    result = client.post('/api/activities', json=payload)
                    self.assertEqual(result.status_code, 201)
                    activity = result.json()
                    self.assertEqual(len(client.get('/api/activities', params={'field_id':field['id']}).json()), 1)
                    path = '/api/activities/' + activity['id']
                    first = client.patch(path, json={'status':'completed'}).json()
                    second = client.patch(path, json={'status':'completed'}).json()
                    self.assertEqual(first['status'], 'completed')
                    self.assertEqual(first['completed_at'], second['completed_at'])
                    self.assertEqual(client.patch('/api/activities/'+str(uuid4()), json={'status':'completed'}).status_code, 404)
                    field_process.terminate(); field_process.wait(timeout=10)
                    result = httpx.post(activity_url+'/api/activities', json=payload, trust_env=False)
                    self.assertEqual(result.status_code, 503)
                    start('fields', field_port)
                    self.assertEqual(client.get('/api/fields/'+field['id']).status_code, 200)
                    self.assertEqual(len(client.get('/api/activities').json()), 1)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                for process in processes:
                    process.wait(timeout=10)

if __name__ == '__main__':
    unittest.main()
