import urllib.request, json, urllib.error

def get(url):
    resp = urllib.request.urlopen(url)
    return resp.status, json.loads(resp.read().decode())

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

base = 'http://127.0.0.1:8000'
print('=== PHASE 3 API VERIFICATION ===')

# 1. Health
s, r = get(f'{base}/api/health')
print(f'[1] GET /api/health -> {s} | {r}')

# 2. Create task (valid)
s, r = post(f'{base}/api/tasks', {
    'title': 'Autonomous Financial Audit Agent',
    'description': 'Audit Q3 financial transactions and produce discrepancy report with anomaly flags.',
    'category': 'Data Analysis',
    'required_capability': 'Financial Analysis / Anomaly Detection',
    'reward': 250,
    'deadline': '2026-12-31T23:59:59',
    'minimum_reputation': 85,
    'minimum_quality_score': 90
})
task_code = r.get('task_code')
task_id = r.get('id')
print(f'[2] POST /api/tasks (valid) -> {s} | task_code={task_code} id={task_id}')

# 3. List tasks
s, r = get(f'{base}/api/tasks')
print(f'[3] GET /api/tasks -> {s} | count={len(r)}')
for t in r:
    print(f'     {t["task_code"]} | {t["title"]} | status={t["status"]}')

# 4. Get single task
if task_id:
    s, r = get(f'{base}/api/tasks/{task_id}')
    print(f'[4] GET /api/tasks/{task_id} -> {s} | title={r.get("title")}')

# 5. 404 test
try:
    urllib.request.urlopen(f'{base}/api/tasks/999999')
    print('[5] GET /api/tasks/999999 -> ERROR: Expected 404 but got 200')
except urllib.error.HTTPError as e:
    body = json.loads(e.read().decode())
    print(f'[5] GET /api/tasks/999999 -> {e.code} | {body}')

# 6. Validation: negative reward
s, r = post(f'{base}/api/tasks', {
    'title': 'Bad Task', 'description': 'Test', 'category': 'NLP',
    'required_capability': 'NLP', 'reward': -10,
    'deadline': '2026-12-31T23:59:59', 'minimum_reputation': 80, 'minimum_quality_score': 85
})
detail = r.get('detail')
msg = detail[0]['msg'] if isinstance(detail, list) else str(r)
print(f'[6] POST reward=-10 -> {s} | {msg}')

# 7. Validation: reputation out of range
s, r = post(f'{base}/api/tasks', {
    'title': 'Bad Task', 'description': 'Test', 'category': 'NLP',
    'required_capability': 'NLP', 'reward': 100,
    'deadline': '2026-12-31T23:59:59', 'minimum_reputation': 150, 'minimum_quality_score': 85
})
detail = r.get('detail')
msg = detail[0]['msg'] if isinstance(detail, list) else str(r)
print(f'[7] POST rep=150 -> {s} | {msg}')

# 8. Dashboard with real data
s, r = get(f'{base}/api/client/dashboard')
print(f'[8] GET /api/client/dashboard -> {s} | {r}')
print()
print('All tests complete.')
