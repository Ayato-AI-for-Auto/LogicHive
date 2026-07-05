import sqlite3

db = sqlite3.connect("C:/Users/saiha/.logichive/data/logichive.db")
cur = db.cursor()

cur.execute("SELECT name, project, embedding FROM logichive_functions WHERE LENGTH(embedding) < 100 LIMIT 5")
for row in cur.fetchall():
    print(f"  {row[0]} ({row[1]}): embedding = {repr(row[2])}")

cur.execute("SELECT name, project, LENGTH(embedding) FROM logichive_functions WHERE LENGTH(embedding) >= 100 LIMIT 5")
for row in cur.fetchall():
    print(f"  {row[0]} ({row[1]}): LENGTH = {row[2]}")

db.close()
