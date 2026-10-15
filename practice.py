import pandas as pd
import sqlite3

from build_lookup import categorical_columns, value_map
from test_nemetron import system_prompt_template

df=pd.read_excel('TmpDaywiseLedgerTrans (1).xlsx',sheet_name=0)

print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
print("columns found: ", list(df.columns))

df.rename(columns={
    'BranchName': 'branch_name',
    'BranchState': 'branch_state'

}, inplace=True)

df['branch_name']=df['branch_name'].str.title()
df['branch_name']=df['branch_name'].str.strip()

Threshold=50000000

df['is_suspicious']=(
(df['total_debit']>Threshold | df['total_credit']>Threshold)
)

text_columns = [
    'branch_name', 'branch_state', 'account_category',
    'account_subcategory', 'parent_group', 'account_group',
    'account_type', 'ledger_name'
]
for col in text_columns:
    df[col] = df[col].str.strip()


df.loc[df['total_debit']>Threshold,'total_debit']=0
df.loc[df["total_credit"] > Threshold, "total_credit"] = 0

df['document_date']=pd.to_datetime(df['document_date'],errors="coerce")
df['document_date']=df['document_date'].dt.strftime('%Y-%m-%d')

conn=sqlite3.connect("accounting.db")

df.to_sql(
    name='ledger_transactions',
    con=conn,
    if_exists='replace',
    index=True,
    index_label='id'
)
cursor=conn.cursor()
cursor.execute('Select * FROM ledger_transactions')

count=cursor.fetchone()[0]
print(f"total number of rows {count}")

conn.close()


import sqlite3

conn=sqlite3.connect("accounting.db")
cursor=conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
print(cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM ledger_transactions")
print(cursor.fetchone()[0])

cursor.execute("SELECT * FROM ledger_transactions LIMIT 5")
for row in cursor.fetchall():
    print(row)


import sqlite3
import json
from collections import defaultdict

categorical_columns=[
    'branch_name',
    'branch_state'
]

value_map=defaultdict(list)
conn=sqlite3.connect("accounting.db")
cursor=conn.cursor()
for col in categorical_columns:
    cursor.execute(f"""SELECT DISTINCT {col}
                       FROM ledger_transactions
                       WHERE {col} IS NOT NULL
                       """)

    for (value,) in cursor.fetchall():
        key=value.strip().lower()
        value_map[key].append({"column":col, "value":value})


import os
import json
import re
import time
from openai import OpenAI
with open('system_prompt.txt', 'r') as f:
    system_prompt_template=f.read()

with open('value_lookup.json','r') as








