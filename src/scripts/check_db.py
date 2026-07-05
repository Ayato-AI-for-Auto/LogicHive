import sqlite3

db = sqlite3.connect("C:/Users/saiha/.logichive/data/logichive.db")
cur = db.cursor()

cur.execute("SELECT COUNT(*) FROM logichive_functions")
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM logichive_functions WHERE embedding IS NULL")
null_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM logichive_functions WHERE embedding = ''")
empty_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM logichive_functions WHERE embedding = '[]'")
bracket_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM logichive_functions WHERE embedding IS NOT NULL AND embedding != '' AND embedding != '[]'")
valid_count = cur.fetchone()[0]

print(f"Total: {total}")
print(f"  embedding IS NULL: {null_count}")
print(f"  embedding = '':    {empty_count}")
print(f"  embedding = '[]':  {bracket_count}")
print(f"  Valid embedding:   {valid_count}")

cur.execute("SELECT name, project, CASE WHEN embedding IS NULL THEN 'NULL' WHEN embedding = '' THEN 'EMPTY' WHEN embedding = '[]' THEN 'BRACKETS' ELSE 'HAS_EMBEDDING(' || LENGTH(embedding) || ')' END as status FROM logichive_functions ORDER BY status, name")
for row in cur.fetchall():
    print(f"  {row[0]:40s} {row[1]:15s} {row[2]}")

db.close()
