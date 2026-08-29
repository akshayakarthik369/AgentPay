import sqlite3
con = sqlite3.connect('agentpay.db')
cur = con.cursor()

cur.execute('SELECT COUNT(*) FROM tasks WHERE reward > 1000')
print('Tasks with reward > 1000 AP:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM tasks WHERE title LIKE '%Giant%' OR title LIKE '%Phase11%' OR title LIKE '%Phase 10%'")
print('Test-named tasks remaining:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM agents')
print('Total agents:', cur.fetchone()[0])

print('\nAll agents:')
cur.execute('SELECT id, name, agent_type, status FROM agents ORDER BY id')
for r in cur.fetchall():
    print(' AGENT:', r)

print('\nAll tasks:')
cur.execute('SELECT id, title, reward, status FROM tasks ORDER BY id')
for r in cur.fetchall():
    print(' TASK:', r)

con.close()
