"""
Migration script: Add missing columns to agents table (trust_status and any other new Phase fields).
Safe to run multiple times — uses IF NOT EXISTS checks via pragma.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'agentpay.db')

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

def migrate():
    print(f"Connecting to: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- agents table migrations ---
    agents_migrations = [
        ("trust_status", "ALTER TABLE agents ADD COLUMN trust_status TEXT NOT NULL DEFAULT 'trusted'"),
        ("risk_score",   "ALTER TABLE agents ADD COLUMN risk_score REAL NOT NULL DEFAULT 0.0"),
        ("violation_count", "ALTER TABLE agents ADD COLUMN violation_count INTEGER NOT NULL DEFAULT 0"),
        ("is_suspended", "ALTER TABLE agents ADD COLUMN is_suspended INTEGER NOT NULL DEFAULT 0"),
        ("suspension_reason", "ALTER TABLE agents ADD COLUMN suspension_reason TEXT"),
        ("last_violation_at", "ALTER TABLE agents ADD COLUMN last_violation_at TEXT"),
    ]

    for col, sql in agents_migrations:
        if not column_exists(cur, "agents", col):
            print(f"  Adding agents.{col} ...")
            cur.execute(sql)
            print(f"  [OK] agents.{col} added")
        else:
            print(f"  [OK] agents.{col} already exists")

    conn.commit()
    conn.close()
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
