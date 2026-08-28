"""
Automated Comprehensive Test Suite for Phase 6 — Agent Capability Matching & Task Ranking.
Tests all factor scoring, deterministic mapping, explainability reasons, ranking endpoints,
reverse matching, and boundary conditions.
"""
import urllib.request, json, urllib.error, time
from datetime import datetime, timezone, timedelta

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

print("\n=== Phase 6 Matching & Ranking Verification ===\n")

# 1. Verify health & existing core endpoints
s, r = get(f'{base}/api/health')
check("GET /api/health is ok", s == 200 and r.get('status') == 'ok')

# 2. Create test tasks with exact, related, and unrelated capabilities
ts = int(time.time())
future_deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
expired_deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

# Task A: Exact NLP task
s_t1, t_exact = post(f'{base}/api/tasks', {
    'title': f'NLP Sentiment Analysis Task {ts}',
    'description': 'Analyze sentiment for 100 customer reviews.',
    'category': 'NLP',
    'required_capability': 'NLP',
    'reward': 150.0,
    'deadline': future_deadline,
    'minimum_reputation': 80,
    'minimum_quality_score': 85
})
check("Created Task A (Exact NLP)", s_t1 == 201)

# Task B: Related capability task (Summarization)
s_t2, t_related = post(f'{base}/api/tasks', {
    'title': f'Text Summarization Task {ts}',
    'description': 'Summarize long legal document.',
    'category': 'NLP',
    'required_capability': 'Summarization',
    'reward': 200.0,
    'deadline': future_deadline,
    'minimum_reputation': 75,
    'minimum_quality_score': 70
})
check("Created Task B (Related Summarization)", s_t2 == 201)

# Task C: Unrelated capability task (Code Analysis)
s_t3, t_unrelated = post(f'{base}/api/tasks', {
    'title': f'Smart Contract Audit {ts}',
    'description': 'Perform OWASP static analysis.',
    'category': 'Engineering',
    'required_capability': 'Code Analysis',
    'reward': 300.0,
    'deadline': future_deadline,
    'minimum_reputation': 90,
    'minimum_quality_score': 90
})
check("Created Task C (Unrelated Code Analysis)", s_t3 == 201)

# Task D: Create with future deadline then simulate expiration
s_t4, t_expired = post(f'{base}/api/tasks', {
    'title': f'Expired Market Research {ts}',
    'description': 'Historical data gathering.',
    'category': 'Research',
    'required_capability': 'NLP',
    'reward': 100.0,
    'deadline': future_deadline,
    'minimum_reputation': 60,
    'minimum_quality_score': 60
})
check("Created Task D", s_t4 == 201)

# Update Task D in DB to have expired deadline
from database import SessionLocal
from app.models.task import Task as TaskModel
_db = SessionLocal()
try:
    _t = _db.query(TaskModel).filter(TaskModel.id == t_expired['id']).first()
    if _t:
        _t.deadline = datetime.now(timezone.utc) - timedelta(days=2)
        _db.commit()
finally:
    _db.close()


# 3. Create a test Agent with only NLP capability
s_a1, a_nlp = post(f'{base}/api/agents', {
    'name': f'NLP-Specialist-{ts}',
    'agent_type': 'worker',
    'description': 'Expert in NLP.',
    'capabilities': ['NLP'],
    'status': 'available'
})
check("Created Agent NLP-Specialist", s_a1 == 201)
agent_id = a_nlp['id']

# 4. Test Single Match Endpoint: Exact Match (Agent with NLP vs Task with NLP)
s, m_exact = get(f'{base}/api/agents/{agent_id}/match/{t_exact["id"]}')
check("GET /api/agents/{agent_id}/match/{task_id} returns 200", s == 200)
check("Exact match capability score is 100", m_exact.get('capability_score') == 100.0, f"got {m_exact.get('capability_score')}")
check("Exact match is eligible", m_exact.get('eligible') == True)
check("Exact match overall score is >= 85", m_exact.get('overall_score') >= 85.0, f"got {m_exact.get('overall_score')}")
check("Exact match level is excellent or strong", m_exact.get('match_level') in ('excellent', 'strong'))
check("Explainability reasons contain 'Exact capability match'", any('Exact capability match' in r for r in m_exact.get('reasons', [])))

# 5. Test Single Match Endpoint: Related Match (Agent with NLP vs Task with Summarization)
s, m_rel = get(f'{base}/api/agents/{agent_id}/match/{t_related["id"]}')
check("GET related match returns 200", s == 200)
check("Related capability score is 70", m_rel.get('capability_score') == 70.0, f"got {m_rel.get('capability_score')}")
check("Explainability reasons contain 'Related capability match'", any('Related capability match' in r for r in m_rel.get('reasons', [])))

# 6. Test Single Match Endpoint: Unrelated Match (Agent with NLP vs Task with Code Analysis)
s, m_unrel = get(f'{base}/api/agents/{agent_id}/match/{t_unrelated["id"]}')
check("GET unrelated match returns 200", s == 200)
check("Unrelated capability score is 0", m_unrel.get('capability_score') == 0.0, f"got {m_unrel.get('capability_score')}")
check("Explainability reasons contain 'No match for required capability'", any('No match' in r for r in m_unrel.get('reasons', [])))

# 7. Test Single Match Endpoint: Expired Task
s, m_exp = get(f'{base}/api/agents/{agent_id}/match/{t_expired["id"]}')
check("GET expired match returns 200", s == 200)
check("Expired task has eligible=False", m_exp.get('eligible') == False)
check("Explainability reasons note deadline expired", any('expired' in r.lower() for r in m_exp.get('reasons', [])))

# 8. Test Discoverable Tasks Ranking (GET /api/agents/{agent_id}/discoverable-tasks)
s, disc = get(f'{base}/api/agents/{agent_id}/discoverable-tasks')
check("GET /api/agents/{agent_id}/discoverable-tasks returns 200", s == 200)
matches = disc.get('matches', [])
check("Matches list is not empty", len(matches) > 0)
check("Matches are sorted descending by overall_score", all(matches[i]['overall_score'] >= matches[i+1]['overall_score'] for i in range(len(matches)-1)))
check("Expired task is excluded from discoverable matches", not any(m['task']['id'] == t_expired['id'] for m in matches))

# 9. Test min_score parameter on discoverable tasks
s, disc_filtered = get(f'{base}/api/agents/{agent_id}/discoverable-tasks?min_score=80')
check("GET discoverable tasks with min_score returns 200", s == 200)
check("All filtered matches have overall_score >= 80", all(m['overall_score'] >= 80.0 for m in disc_filtered.get('matches', [])))

# 10. Test limit parameter on discoverable tasks
s, disc_limited = get(f'{base}/api/agents/{agent_id}/discoverable-tasks?limit=1')
check("GET discoverable tasks with limit=1 returns at most 1 item", s == 200 and len(disc_limited.get('matches', [])) <= 1)

# 11. Test Inactive Agent cannot discover tasks
post(f'{base}/api/agents/{agent_id}/deactivate')
s, disc_inactive = get(f'{base}/api/agents/{agent_id}/discoverable-tasks')
check("Deactivated agent receives 0 discoverable matches", s == 200 and len(disc_inactive.get('matches', [])) == 0)
post(f'{base}/api/agents/{agent_id}/activate')

# 12. Test Reverse Matching (GET /api/tasks/{task_id}/matching-agents)
s, rev = get(f'{base}/api/tasks/{t_exact["id"]}/matching-agents')
check("GET /api/tasks/{task_id}/matching-agents returns 200", s == 200)
agents_ranked = rev.get('agents', [])
check("Reverse matching returns list of agents", len(agents_ranked) > 0)
check("Reverse matching agents sorted descending by overall_score", all(agents_ranked[i]['overall_score'] >= agents_ranked[i+1]['overall_score'] for i in range(len(agents_ranked)-1)))

# Top agent for NLP task should be an agent with NLP capability
top_agent = agents_ranked[0]
check("Top matching agent has high capability score (100 or 70)", top_agent['capability_score'] >= 70.0)

# 13. Test 404 error cases
s, _ = get(f'{base}/api/agents/{agent_id}/match/999999')
check("Invalid task match returns 404", s == 404)

s, _ = get(f'{base}/api/tasks/999999/matching-agents')
check("Invalid task in reverse matching returns 404", s == 404)

print(f"\n{'='*50}")
print(f"Results: {ok} passed, {fail} failed")
print(f"Phase 6 Status: {'ALL PASS' if fail == 0 else 'SOME FAILURES'}")
print(f"{'='*50}")
