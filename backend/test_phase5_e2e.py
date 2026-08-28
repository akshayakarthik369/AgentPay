"""Quick E2E verification of Phase 5 agent API endpoints"""
import urllib.request, json, urllib.error, time

base = 'http://127.0.0.1:8000'

def get(url):
    try:
        resp = urllib.request.urlopen(url)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def post(url, data=None):
    body = json.dumps(data).encode() if data else b''
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

ok = 0
fail = 0

def check(label, condition, detail=''):
    global ok, fail
    if condition:
        print(f"  [PASS] {label}")
        ok += 1
    else:
        print(f"  [FAIL] {label} {detail}")
        fail += 1

print("\n=== Phase 5 Final E2E Verification ===\n")

# Core endpoints
s, r = get(f'{base}/api/health')
check("GET /api/health returns 200", s == 200)
check("Health status is 'ok'", r.get('status') == 'ok')

s, r = get(f'{base}/api/client/dashboard')
check("GET /api/client/dashboard returns 200", s == 200)
check("Dashboard has total_tasks", 'total_tasks' in r)

# Agents listing
s, r = get(f'{base}/api/agents')
check("GET /api/agents returns 200", s == 200)
check("At least 5 agents exist (5 seeded + maybe more)", len(r) >= 5, f"got {len(r)}")
check("All agents have agent_code", all('agent_code' in a for a in r))
check("All agents have capabilities list", all(isinstance(a.get('capabilities'), list) for a in r))

# Agent codes are sequential AG-1001...
codes = {a['agent_code'] for a in r}
check("AG-1001 exists (NLP-Agent-01)", 'AG-1001' in codes)
check("AG-1005 exists (Verify-Agent-01)", 'AG-1005' in codes)

# Filter by type
s, r = get(f'{base}/api/agents?agent_type=verifier')
check("GET /api/agents?agent_type=verifier returns 200", s == 200)
check("Verifier filter returns verifiers only", all(a['agent_type'] == 'verifier' for a in r))

# Filter by capability
s, r = get(f'{base}/api/agents?capability=NLP')
check("GET /api/agents?capability=NLP returns NLP-Agent-01", any(a['name'] == 'NLP-Agent-01' for a in r))

# Get individual agent
s, r = get(f'{base}/api/agents/1')
check("GET /api/agents/1 returns 200", s == 200)
check("Agent 1 has reputation_score field", 'reputation_score' in r)
check("Agent 1 has wallet_balance field", 'wallet_balance' in r)
check("Agent 1 has tasks_completed field", 'tasks_completed' in r)

# 404 test
s, r = get(f'{base}/api/agents/999999')
check("GET /api/agents/999999 returns 404", s == 404)

# Create agent with unique name
unique_name = f"E2E-Agent-{int(time.time())}"
s, r = post(f'{base}/api/agents', {
    'name': unique_name,
    'agent_type': 'worker',
    'description': 'Phase 5 E2E verification agent',
    'capabilities': ['NLP', 'Summarization'],
    'status': 'available'
})
check("POST /api/agents returns 201", s == 201, f"got {s}")
new_id = r.get('id')
new_code = r.get('agent_code', '')
check("New agent has agent_code starting AG-", new_code.startswith('AG-'), f"got {new_code}")

# Activate/deactivate
if new_id:
    s, r = post(f'{base}/api/agents/{new_id}/deactivate')
    check(f"POST /api/agents/{new_id}/deactivate returns 200", s == 200)
    check("Agent is_active=False after deactivate", r.get('is_active') == False)

    s, r = post(f'{base}/api/agents/{new_id}/activate')
    check(f"POST /api/agents/{new_id}/activate returns 200", s == 200)
    check("Agent is_active=True after activate", r.get('is_active') == True)

# Discoverable tasks
s, r = get(f'{base}/api/agents/1/discoverable-tasks')
check("GET /api/agents/1/discoverable-tasks returns 200", s == 200)
check("Discoverable tasks response has agent_code", 'agent_code' in r or 'agent_code' in r.get('agent', {}))
check("Discoverable tasks response has tasks list", isinstance(r.get('tasks'), list))

# Marketplace still works
s, r = get(f'{base}/api/marketplace/stats')
check("GET /api/marketplace/stats still returns 200", s == 200)

# Task endpoints still work
s, r = get(f'{base}/api/tasks')
check("GET /api/tasks still returns 200", s == 200)

print(f"\n{'='*45}")
print(f"Results: {ok} passed, {fail} failed")
print(f"Phase 5 Status: {'ALL PASS' if fail == 0 else 'SOME FAILURES'}")
print(f"{'='*45}")
