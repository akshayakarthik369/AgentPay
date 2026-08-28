"""
Comprehensive Automated Test Suite for Phase 7 — Task Bidding & Agent Selection.
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
    body = json.dumps(data).encode() if data is not None else b''
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def patch(url, data=None):
    body = json.dumps(data).encode() if data is not None else b''
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='PATCH')
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

print("\n=== Phase 7 Bidding & Selection Verification ===\n")

# 1. Verify health
s, r = get(f'{base}/api/health')
check("GET /api/health returns 200", s == 200)

ts = int(time.time())
future_deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

# 2. Setup Test Task (Reward 200 AP, Required: NLP)
s_t, task = post(f'{base}/api/tasks', {
    'title': f'Sentiment Bidding Test Task {ts}',
    'description': 'Analyze customer feedback dataset.',
    'category': 'NLP',
    'required_capability': 'NLP',
    'reward': 200.0,
    'deadline': future_deadline,
    'minimum_reputation': 75,
    'minimum_quality_score': 80
})
check("Created Task for Bidding Test", s_t == 201)
task_id = task['id']
check("Initial Task status is 'open'", task['status'] == 'open')

# 3. Setup 3 Eligible Agents (NLP) and 1 Ineligible Agent (Code Analysis only)
s_a1, agent1 = post(f'{base}/api/agents', {
    'name': f'NLP-Bidder-A-{ts}',
    'agent_type': 'worker',
    'description': 'NLP specialist A.',
    'capabilities': ['NLP', 'Sentiment Analysis'],
    'status': 'available'
})
s_a2, agent2 = post(f'{base}/api/agents', {
    'name': f'NLP-Bidder-B-{ts}',
    'agent_type': 'worker',
    'description': 'NLP specialist B.',
    'capabilities': ['NLP', 'Summarization'],
    'status': 'available'
})
s_a3, agent3 = post(f'{base}/api/agents', {
    'name': f'NLP-Bidder-C-{ts}',
    'agent_type': 'worker',
    'description': 'NLP specialist C.',
    'capabilities': ['NLP'],
    'status': 'available'
})
s_a4, agent_ineligible = post(f'{base}/api/agents', {
    'name': f'Code-Ineligible-{ts}',
    'agent_type': 'worker',
    'description': 'Only code analysis.',
    'capabilities': ['Code Analysis'],
    'status': 'available'
})
check("Created 4 test agents", all(s == 201 for s in [s_a1, s_a2, s_a3, s_a4]))

# 4. Test Bid Submission & Match Gate
# Ineligible agent (<60% match) attempt
s, err = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent_ineligible['id'],
    'bid_amount': 150.0,
    'estimated_completion_minutes': 45,
    'proposal': 'Attempting bid with low match.'
})
check("Low match score (<60%) rejected with 400", s == 400)

# Bid amount > task.reward attempt
s, err = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent1['id'],
    'bid_amount': 250.0, # reward is 200
    'estimated_completion_minutes': 45,
    'proposal': 'Bid exceeding reward budget.'
})
check("Bid exceeding reward rejected with 400", s == 400)

# Valid Bid 1 by Agent 1
s, bid1 = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent1['id'],
    'bid_amount': 160.0,
    'estimated_completion_minutes': 30,
    'proposal': 'High speed NLP analysis with 30m turnaround.'
})
check("POST /api/bids returns 201 for valid bid", s == 201)
check("Bid has auto-generated BD-code", bid1.get('bid_code', '').startswith('BD-'))
check("Bid status is 'pending'", bid1.get('status') == 'pending')

# Check Task status transitioned to 'bidding'
s, updated_task = get(f'{base}/api/tasks/{task_id}')
check("Task status automatically transitioned 'open' -> 'bidding'", updated_task.get('status') == 'bidding')

# Duplicate Pending Bid Attempt by Agent 1
s, err = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent1['id'],
    'bid_amount': 150.0,
    'estimated_completion_minutes': 30,
    'proposal': 'Duplicate attempt.'
})
check("Duplicate pending bid rejected with 409 Conflict", s == 409)

# Valid Bid 2 by Agent 2 (Lower price, higher time)
s, bid2 = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent2['id'],
    'bid_amount': 140.0,
    'estimated_completion_minutes': 60,
    'proposal': 'Budget friendly comprehensive NLP parsing.'
})
check("POST /api/bids created second bid", s == 201)

# Valid Bid 3 by Agent 3 (Full price, medium time)
s, bid3 = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent3['id'],
    'bid_amount': 200.0,
    'estimated_completion_minutes': 45,
    'proposal': 'Standard execution at full reward.'
})
check("POST /api/bids created third bid", s == 201)

# 5. Test Ranked Bids for Task (GET /api/tasks/{task_id}/bids)
s, task_bids = get(f'{base}/api/tasks/{task_id}/bids')
check("GET /api/tasks/{task_id}/bids returns 200", s == 200)
bids_list = task_bids.get('bids', [])
check("Task has 3 bids returned", len(bids_list) == 3)
check("Bids are sorted descending by selection_score", all(bids_list[i]['selection_score'] >= bids_list[i+1]['selection_score'] for i in range(len(bids_list)-1)))
check("Ranked bids include explainability reasons", all(len(b['reasons']) > 0 for b in bids_list))

# 6. Test Agent Bid History (GET /api/agents/{agent_id}/bids)
s, agent_bids = get(f'{base}/api/agents/{agent1["id"]}/bids')
check("GET /api/agents/{agent_id}/bids returns 200", s == 200)
check("Agent 1 has 1 bid in history", len(agent_bids.get('bids', [])) == 1)

# 7. Test Bid Update (PATCH /api/bids/{bid_id})
s, updated_bid1 = patch(f'{base}/api/bids/{bid1["id"]}', {
    'bid_amount': 150.0,
    'estimated_completion_minutes': 25,
    'proposal': 'Updated proposal: expedited 25m turnaround.'
})
check("PATCH /api/bids/{id} returns 200", s == 200)
check("Updated bid amount is 150.0", updated_bid1.get('bid_amount') == 150.0)
check("Selection score recalculated after update", updated_bid1.get('selection_score') >= bid1.get('selection_score', 0))

# 8. Test Bid Withdrawal (POST /api/bids/{bid_id}/withdraw)
s, withdrawn_bid3 = post(f'{base}/api/bids/{bid3["id"]}/withdraw')
check("POST /api/bids/{id}/withdraw returns 200", s == 200)
check("Bid status is 'withdrawn'", withdrawn_bid3.get('status') == 'withdrawn')

# Verify withdrawn bid is filtered or excluded from pending
s, task_pending_bids = get(f'{base}/api/tasks/{task_id}/bids?status=pending')
check("Pending bids filter excludes withdrawn bid", len(task_pending_bids.get('bids', [])) == 2)

# 9. Test Winner Selection & Atomic Assignment
# Select Bid 1 (Agent 1) as winner
s, sel_res = post(f'{base}/api/tasks/{task_id}/select-bid/{bid1["id"]}')
check("POST /api/tasks/{task_id}/select-bid/{bid_id} returns 200", s == 200)
check("Selection message indicates success", "accepted" in sel_res.get('message', '').lower())
check("Response confirms assigned_agent_id", sel_res.get('assigned_agent_id') == agent1['id'])

# Check Task state after selection
s, assigned_task = get(f'{base}/api/tasks/{task_id}')
check("Task status is now 'assigned'", assigned_task.get('status') == 'assigned')
check("Task assigned_agent_id is set to winning agent", assigned_task.get('assigned_agent_id') == agent1['id'])
check("Task selected_bid_id is set to winning bid", assigned_task.get('selected_bid_id') == bid1['id'])

# Check Winning Bid status is 'accepted'
s, winning_bid = get(f'{base}/api/bids/{bid1["id"]}')
check("Winning bid status is 'accepted'", winning_bid.get('status') == 'accepted')

# Check Competing Bid 2 status is 'rejected'
s, rejected_bid2 = get(f'{base}/api/bids/{bid2["id"]}')
check("Competing bid status is 'rejected'", rejected_bid2.get('status') == 'rejected')

# Check Winning Agent status is 'busy'
s, winning_agent = get(f'{base}/api/agents/{agent1["id"]}')
check("Winning agent status is now 'busy'", winning_agent.get('status') == 'busy')

# 10. Test Double Selection / Assigned Conflict Protection
s, err = post(f'{base}/api/tasks/{task_id}/select-bid/{bid2["id"]}')
check("Selecting bid on already assigned task returns 409 Conflict", s == 409)

# Submitting new bid on assigned task should fail
s, err = post(f'{base}/api/bids', {
    'task_id': task_id,
    'agent_id': agent3['id'],
    'bid_amount': 100.0,
    'estimated_completion_minutes': 30,
    'proposal': 'Attempting to bid on assigned task.'
})
check("Bidding on assigned task returns 400 Bad Request", s == 400)

# Updating rejected/accepted bid should fail
s, err = patch(f'{base}/api/bids/{bid1["id"]}', {'bid_amount': 120.0})
check("Updating accepted bid returns 400 Bad Request", s == 400)

print(f"\n{'='*50}")
print(f"Results: {ok} passed, {fail} failed")
print(f"Phase 7 Status: {'ALL PASS' if fail == 0 else 'SOME FAILURES'}")
print(f"{'='*50}")
