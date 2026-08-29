import sqlite3

db_path = 'agentpay.db'
con = sqlite3.connect(db_path)
cur = con.cursor()

# Count all tasks
cur.execute("SELECT COUNT(*) FROM tasks")
print('Total tasks:', cur.fetchone()[0])

# Identify test-polluted records by pattern
test_patterns = [
    'Giant Reward', 'Phase11', 'Phase12', 'Phase13', 'Phase14',
    'Phase15', 'Phase16', 'Phase17', 'Phase18', 'Phase 10', 'Phase 1',
    'E2E ', 'P11', 'Insuff', 'NLP-Worker-P11', 'high-bar',
    'Automated', 'Stress', 'test task', 'Test Task'
]

all_test_ids = set()
for pat in test_patterns:
    cur.execute("SELECT id, title, reward FROM tasks WHERE title LIKE ?", (f'%{pat}%',))
    rows = cur.fetchall()
    for r in rows:
        all_test_ids.add(r[0])
        print(f'  TEST: id={r[0]}, title={r[1]}, reward={r[2]}')

# Also find huge reward tasks (>500 AP)
cur.execute("SELECT id, title, reward FROM tasks WHERE reward > 500")
rows = cur.fetchall()
for r in rows:
    all_test_ids.add(r[0])
    print(f'  HUGE: id={r[0]}, title={r[1]}, reward={r[2]}')

print(f'\nTotal test-generated records to clean: {len(all_test_ids)}')
print(f'IDs: {sorted(all_test_ids)}')

# Show legitimate demo tasks
print('\nLegitimate (non-test) tasks to preserve:')
cur.execute("SELECT id, title, reward, status FROM tasks ORDER BY id")
all_tasks = cur.fetchall()
for t in all_tasks:
    if t[0] not in all_test_ids:
        print(f'  KEEP: id={t[0]}, title={t[1]}, reward={t[2]}, status={t[3]}')

# Show test agents too
cur.execute("SELECT COUNT(*) FROM agents WHERE name LIKE '%P11%' OR name LIKE '%Insuff%' OR name LIKE '%Worker-%' OR name LIKE '%E2E-%' OR name LIKE '%Verifier-P%' OR name LIKE '%Phase%'")
print(f'\nTest agents to check: {cur.fetchone()[0]}')
cur.execute("SELECT id, name, agent_type FROM agents WHERE name LIKE '%P11%' OR name LIKE '%Insuff%' OR name LIKE '%E2E-%' OR name LIKE '%Phase%'")
for r in cur.fetchall()[:20]:
    print(f'  TEST AGENT: id={r[0]}, name={r[1]}, type={r[2]}')

con.close()
