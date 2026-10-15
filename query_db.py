# import sqlite3
#
# conn = sqlite3.connect('accounting.db')
# cursor = conn.cursor()
#
# # Query 1
# cursor.execute("""
#     SELECT branch_name,
#            SUM(total_debit) AS total_debit,
#            SUM(total_credit) AS total_credit
#     FROM ledger_transactions
#     GROUP BY branch_name
#     ORDER BY total_debit DESC
#     LIMIT 5
# """)
#
# for row in cursor.fetchall():
#     print(row)
#
# # Query 2
# cursor.execute("""
#     SELECT SUM(total_debit) AS total_indirect_expense
#     FROM ledger_transactions
#     WHERE branch_name = 'PADUP VENTURES'
#       AND account_subcategory = 'Indirect Expense'
# """)
#
# print(cursor.fetchone())
#
# # Query 3
# cursor.execute("""
#     SELECT ledger_name, SUM(total_credit) AS total_owed
#     FROM ledger_transactions
#     WHERE account_type = 'Vendor'
#     GROUP BY ledger_name
#     ORDER BY total_owed DESC
#     LIMIT 5
# """)
#
# for row in cursor.fetchall():
#     print(row)
#
#
# conn = sqlite3.connect('accounting.db')
# cursor = conn.cursor()
#
# cursor.execute("""
#     SELECT DISTINCT branch_name, TRIM(branch_name) AS cleaned, LENGTH(branch_name) AS raw_len
#     FROM ledger_transactions
#     WHERE branch_name LIKE 'PADUP%'
# """)
# for row in cursor.fetchall():
#     print(row)
#
# # Find all rows with abnormally large amounts (over 100 crore = 1,000,000,000)
# print("=== Rows with total_debit or total_credit over 100 crore ===")
# cursor.execute("""
#     SELECT id, branch_name, document_date, ledger_name, account_type, total_debit, total_credit
#     FROM ledger_transactions
#     WHERE total_debit > 1000000000 OR total_credit > 1000000000
#     ORDER BY total_debit DESC
# """)
# for row in cursor.fetchall():
#     print(row)
#
#
# cursor.execute("""
#     SELECT id, branch_name, document_date, ledger_name, account_type, account_category, total_debit, total_credit
#     FROM ledger_transactions
#     WHERE branch_name = 'ArjunMarg' AND document_date = '2025-01-17'
#     ORDER BY id
# """)
# for row in cursor.fetchall():
#     print(row)
#
# cursor.execute("""
#     SELECT id, branch_name, document_date, ledger_name, account_type, account_category, total_debit, total_credit
#     FROM ledger_transactions
#     WHERE branch_name = 'PADUP VENTURES' AND document_date IN ('2024-04-05','2024-04-06','2024-04-09','2024-04-11')
#     ORDER BY document_date, id
# """)
# for row in cursor.fetchall():
#     print(row)
#
# cursor.execute("""
#     SELECT id, branch_name, document_date, ledger_name, account_type, total_debit, total_credit
#     FROM ledger_transactions
#     WHERE total_debit > 10000000 OR total_credit > 10000000
#     ORDER BY
#         CASE WHEN total_debit > 10000000 THEN total_debit ELSE total_credit END ASC
# """)
# rows = cursor.fetchall()
# print(f"Total affected rows: {len(rows)}")
# for row in rows:
#     print(row)
#
# conn.close()  # only once, at the very end

# import sqlite3
#
# conn = sqlite3.connect('accounting.db')
# cursor = conn.cursor()
#
# cursor.execute("""
#     SELECT branch_name, COUNT(*)
#     FROM ledger_transactions
#     GROUP BY LOWER(TRIM(branch_name))
#     HAVING COUNT(DISTINCT branch_name) > 1
# """)
# for row in cursor.fetchall():
#     print(row)
#
# conn.close()

import json
import re


# def get_candidate_matches(question, lookup_path='value_lookup.json'):
#     with open(lookup_path, 'r') as f:
#         value_map = json.load(f)
#
#     question_lower = question.lower()
#     matches = {}
#
#     for key, candidates in value_map.items():
#         if len(key) < 3:
#             continue
#         # \b = word boundary. This ensures "del" matches "del" as a
#         # standalone word, but NOT as part of "delhi".
#         pattern = r'\b' + re.escape(key) + r'\b'
#         if re.search(pattern, question_lower):
#             matches[key] = candidates
#
#     return matches
#
#
# # --- Test it ---
# test_question = "What is the total credit for Sundry Debtors in Delhi?"
# result = get_candidate_matches(test_question)
# print(json.dumps(result, indent=2))

# import sqlite3
#
# conn = sqlite3.connect('accounting.db')
# cursor = conn.cursor()
#
# print("=== Q1: Total indirect expense for Padup Ventures ===")
# cursor.execute("""
#     SELECT SUM(total_debit - total_credit) AS total_indirect_expense
#     FROM ledger_transactions
#     WHERE branch_name = 'Padup Ventures'
#       AND account_subcategory = 'Indirect Expense'
#       AND account_category = 'Expense'
#       AND document_date BETWEEN '2010-01-01' AND '2026-12-31'
# """)
# print(cursor.fetchone())
#
# print("\n=== Q2: Top 5 customers by total debit ===")
# cursor.execute("""
#     SELECT ledger_name, SUM(total_debit) AS total_debit_amount
#     FROM ledger_transactions
#     WHERE account_type = 'Customer'
#       AND document_date BETWEEN '2010-01-01' AND '2026-12-31'
#     GROUP BY ledger_name
#     ORDER BY total_debit_amount DESC
#     LIMIT 5
# """)
# for row in cursor.fetchall():
#     print(row)
#
# conn.close()

import sqlite3

conn = sqlite3.connect('accounting.db')
cursor = conn.cursor()

print("=== Q1: Total indirect expense for Padup Ventures ===")
cursor.execute("""
    SELECT SUM(total_debit) - SUM(total_credit) AS total_indirect_expense
    FROM ledger_transactions
    WHERE branch_name = 'Padup Ventures'
      AND account_category = 'Expense'
      AND account_subcategory = 'Indirect Expense'
      AND document_date BETWEEN '2010-01-01' AND '2026-12-31'
""")
print(cursor.fetchone())

print("\n=== Q2: Top 5 customers by total debit ===")
cursor.execute("""
    SELECT ledger_name, SUM(total_debit) AS total_debit_amount
    FROM ledger_transactions
    WHERE account_type = 'Customer'
      AND document_date BETWEEN '2010-01-01' AND '2026-12-31'
    GROUP BY ledger_name
    ORDER BY total_debit_amount DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(row)

print("\n=== Q3: Total GST liability ===")
cursor.execute("""
    SELECT SUM(total_credit) - SUM(total_debit) AS total_gst_liability
    FROM ledger_transactions
    WHERE account_category = 'Liability'
      AND parent_group = 'GST'
      AND document_date BETWEEN '2010-01-01' AND '2026-12-31'
""")
print(cursor.fetchone())

conn.close()