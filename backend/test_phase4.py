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

print("=== PHASE 4 BACKEND VERIFICATION ===")

# Seed additional tasks if needed
tasks_to_seed = [
    {
        'title': 'AI Safety Red Teaming for LLMs',
        'description': 'Perform jailbreak testing and prompt injection vulnerability scans on model endpoints.',
        'category': 'Model Evaluation',
        'required_capability': 'AI Safety / Red Teaming',
        'reward': 300,
        'deadline': '2026-12-31T23:59:59',
        'minimum_reputation': 90,
        'minimum_quality_score': 95
    },
    {
        'title': 'Solidity Smart Contract Security Audit',
        'description': 'Audit escrow smart contracts for reentrancy and integer overflow vulnerabilities.',
        'category': 'Code Analysis',
        'required_capability': 'Code Analysis & Security',
        'reward': 500,
        'deadline': '2026-12-31T23:59:59',
        'minimum_reputation': 95,
        'minimum_quality_score': 90
    },
    {
        'title': 'Market Research: Multi-Agent Economic Systems',
        'description': 'Compile a 15-page comprehensive report on autonomous agent economies and micropayment protocols.',
        'category': 'Research',
        'required_capability': 'Research Synthesis',
        'reward': 75,
        'deadline': '2026-12-31T23:59:59',
        'minimum_reputation': 70,
        'minimum_quality_score': 80
    }
]

for t in tasks_to_seed:
    s, r = post(f'{base}/api/tasks', t)
    print(f"Seeded: {r.get('task_code')} ({r.get('title')}) -> status {s}")

# 1. GET /api/tasks (default)
s, r = get(f'{base}/api/tasks')
print(f"\n[1] GET /api/tasks -> {s}, total={r.get('total')}, page_size={r.get('page_size')}, items_count={len(r.get('items', []))}")

# 2. GET /api/tasks?status=open
s, r = get(f'{base}/api/tasks?status=open')
print(f"[2] GET /api/tasks?status=open -> {s}, total={r.get('total')}")

# 3. GET /api/tasks?category=NLP
s, r = get(f'{base}/api/tasks?category=NLP')
print(f"[3] GET /api/tasks?category=NLP -> {s}, total={r.get('total')}")

# 4. GET /api/tasks?search=sentiment
s, r = get(f'{base}/api/tasks?search=sentiment')
print(f"[4] GET /api/tasks?search=sentiment -> {s}, total={r.get('total')}, match={r.get('items')[0]['title'] if r.get('items') else 'None'}")

# 5. GET /api/tasks?min_reward=150
s, r = get(f'{base}/api/tasks?min_reward=150')
print(f"[5] GET /api/tasks?min_reward=150 -> {s}, total={r.get('total')}")

# 6. GET /api/tasks?sort_by=reward&sort_order=desc
s, r = get(f'{base}/api/tasks?sort_by=reward&sort_order=desc')
print(f"[6] GET /api/tasks?sort_by=reward&sort_order=desc -> {s}, top_reward={r.get('items')[0]['reward'] if r.get('items') else 'None'}")

# 7. GET /api/tasks?page=1&page_size=2
s, r = get(f'{base}/api/tasks?page=1&page_size=2')
print(f"[7] GET /api/tasks?page=1&page_size=2 -> {s}, items_returned={len(r.get('items', []))}, total_pages={r.get('total_pages')}")

# 8. Invalid pagination: page=0
s, r = get(f'{base}/api/tasks?page=0')
print(f"[8] GET /api/tasks?page=0 -> {s} (Expected 422)")

# 9. Invalid pagination: page_size=1000
s, r = get(f'{base}/api/tasks?page_size=1000')
print(f"[9] GET /api/tasks?page_size=1000 -> {s} (Expected 422)")

# 10. GET /api/marketplace/stats
s, r = get(f'{base}/api/marketplace/stats')
print(f"[10] GET /api/marketplace/stats -> {s}, stats={r}")

print("\nAll Phase 4 backend verification tests completed.")
