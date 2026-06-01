import sqlite3
import os
db_path = os.path.join(os.path.expanduser("~"), ".logichive", "data", "logichive.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM logichive_functions")
print(cursor.fetchall())
conn.close()
