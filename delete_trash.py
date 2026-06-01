import sqlite3
import os

# HOME_DIR: C:\Users\saiha\.logichive
db_path = os.path.join(os.path.expanduser("~"), ".logichive", "data", "logichive.db")
print(f"Connecting to: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("DELETE FROM logichive_functions WHERE name = 'contains_secrets_scanner'")
conn.commit()
print("Deleted successfully.")
conn.close()
