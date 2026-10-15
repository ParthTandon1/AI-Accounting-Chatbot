import sqlite3
import json
from collections import defaultdict

conn = sqlite3.connect('accounting.db')
cursor = conn.cursor()

# These are the 8 columns whose values are "categorical" —
# i.e., a fixed-ish set of labels, not free-form numbers or dates.
categorical_columns = [
    'branch_name',
    'branch_state',
    'account_category',
    'account_subcategory',
    'parent_group',
    'account_group',
    'account_type',
    'ledger_name'
]

# value_map: lowercased value -> list of {"column": ..., "value": ...}
value_map = defaultdict(list)

for col in categorical_columns:
    cursor.execute(f"""
        SELECT DISTINCT {col}
        FROM ledger_transactions
        WHERE {col} IS NOT NULL 
    """)
    for (value,) in cursor.fetchall():
        key = value.strip().lower()
        value_map[key].append({"column": col, "value": value})

conn.close()

# --- Collision report ---
collisions = {k: v for k, v in value_map.items() if len(v) > 1}
print(f"Total distinct values across all columns: {len(value_map)}")
print(f"Values appearing in more than one column: {len(collisions)}")
print("\nSample collisions:")
for k, v in list(collisions.items())[:15]:
    print(f"  '{k}' -> {v}")

# --- Save full map to disk ---
with open('value_lookup.json', 'w') as f:
    json.dump(value_map, f, indent=2)

print("\nSaved to value_lookup.json")