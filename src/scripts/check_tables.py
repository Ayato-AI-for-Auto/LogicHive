#!/usr/bin/env python3
"""Check all tables in logichive.db and count rows."""
import sqlite3

db = r'C:\Users\saiha\.logichive\data\logichive.db'
conn = sqlite3.connect(db)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print('=== テーブル一覧 ===')
for t in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        print(f'  {t}: {count} rows')
    except Exception as e:
        print(f'  {t}: {e}')

conn.close()
