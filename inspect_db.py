import sqlite3

conn = sqlite3.connect('accounting.db')
cursor = conn.cursor()

# Check schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
print(cursor.fetchone()[0])

# Check row count
cursor.execute("SELECT COUNT(*) FROM ledger_transactions")
print("Row count:", cursor.fetchone()[0])

# Peek at 5 rows
cursor.execute("SELECT * FROM ledger_transactions LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()