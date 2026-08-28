import urllib.request, json, urllib.error

base = 'http://127.0.0.1:8000'

def get(url):
    try:
        resp = urllib.request.urlopen(url)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def patch(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'}, method='PATCH')
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

print("=== PHASE 5 AGENT API VERIFICATION ===")

# 1. GET /api/agents (all)
s, r = get(f'{base}/api/agents')
print(f"[1] GET /api/agents -> {s}, count={len(r)}")
for a in r:
    print(f"     {a['agent_code']} | {a['name']} | type={a['agent_type']} | caps={a['capabilities']} | status={a['status']}")

# 2. POST a new agent
s, r = post(f'{base}/api/agents', {
    'name': 'Content-Agent-01',
    'agent_type': 'worker',
    'description': 'Generates SEO-optimized content for e-commerce products.',
    'capabilities': ['Content Generation']
})
print(f"\n[2] POST /api/agents -> {s}, code={r.get('agent_code')}, id={r.get('id')}")

# 3. GET /api/agents/1
s, r = get(f'{base}/api/agents/1')
print(f"[3] GET /api/agents/1 -> {s}, name={r.get('name')}, reputation={r.get('reputation_score')}")

# 4. GET /api/agents/999999 (404)
s, r = get(f'{base}/api/agents/999999')
print(f"[4] GET /api/agents/999999 -> {s} (Expected 404)")

# 5. GET /api/agents?capability=NLP
s, r = get(f'{base}/api/agents?capability=NLP')
print(f"[5] GET /api/agents?capability=NLP -> {s}, count={len(r)}, agents={[a['name'] for a in r]}")

# 6. GET /api/agents?status=available
s, r = get(f'{base}/api/agents?status=available')
print(f"[6] GET /api/agents?status=available -> {s}, count={len(r)}")

# 7. PATCH /api/agents/2 (update name & description)
s, r = patch(f'{base}/api/agents/2', {'description': 'Updated: Advanced research synthesis agent with multilingual support.'})
print(f"[7] PATCH /api/agents/2 -> {s}, desc={r.get('description')[:60]}...")

# 8. Deactivate agent
def post_no_body(url):
    req = urllib.request.Request(url, data=b'', headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

s, r = post_no_body(f'{base}/api/agents/3/deactivate')
print(f"[8] POST /api/agents/3/deactivate -> {s}, is_active={r.get('is_active')}")

# 9. discoverable-tasks for agent 1 (NLP-Agent-01)
s, r = get(f'{base}/api/agents/1/discoverable-tasks')
print(f"[9] GET /api/agents/1/discoverable-tasks -> {s}, tasks_found={len(r.get('tasks', []))}")
for t in r.get('tasks', []):
    print(f"     {t['task_code']} | {t['title']} | cap={t['required_capability']}")

# 10. discoverable-tasks for deactivated agent 3
s, r = get(f'{base}/api/agents/3/discoverable-tasks')
print(f"[10] GET /api/agents/3/discoverable-tasks (deactivated) -> {s}, tasks_found={len(r.get('tasks', []))} (expect 0)")

# 11. Re-activate agent 3
s, r = post_no_body(f'{base}/api/agents/3/activate')
print(f"[11] POST /api/agents/3/activate -> {s}, is_active={r.get('is_active')}")

print("\nAll Phase 5 backend verification tests completed.")
