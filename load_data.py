import pandas as pd
import sqlite3

# --- Step 1: Read the Excel file ---
# pandas reads the Excel sheet into a DataFrame — an in-memory table.
# sheet_name=0 means the first sheet (your file has only one).
df = pd.read_excel('TmpDaywiseLedgerTrans (1).xlsx', sheet_name=0)

print(f"Loaded {len(df)} rows and {len(df.columns)} columns from Excel.")
print("Columns found:", list(df.columns))

# --- Step 2: Rename columns to clean snake_case names ---
# This makes SQL queries cleaner and avoids quoting issues.
df.rename(columns={
    'BranchName':             'branch_name',
    'BranchState':            'branch_state',
    'DocumentDate':           'document_date',
    'AccountCategoryName':    'account_category',
    'AccountSubCategoryName': 'account_subcategory',
    'ParentGroupName':        'parent_group',
    'AccountGroupName':       'account_group',
    'AccountTypeName':        'account_type',
    'LedgerName':             'ledger_name',
    'TotalDebitAmount':       'total_debit',
    'TotalCreditAmount':      'total_credit'
}, inplace=True)



# --- Standardize casing for branch_name ---
# Found: 'gurgaon' and 'Gurgaon' are the same branch stored with
# inconsistent casing, causing GROUP BY to treat them as different branches.
df['branch_name'] = df['branch_name'].str.title()





# --- Strip leading/trailing whitespace from all text columns ---
# This fixes issues like 'PADUP VENTURES ' (trailing space) being
# treated as a different value than 'PADUP VENTURES'.
text_columns = [
    'branch_name', 'branch_state', 'account_category',
    'account_subcategory', 'parent_group', 'account_group',
    'account_type', 'ledger_name'
]
for col in text_columns:
    df[col] = df[col].str.strip()


THRESHOLD = 50_000_000

df["is_suspicious"] = (
    (df["total_debit"] > THRESHOLD) | (df["total_credit"] > THRESHOLD)
)

df.loc[df["total_debit"]  > THRESHOLD, "total_debit"]  = 0
df.loc[df["total_credit"] > THRESHOLD, "total_credit"] = 0








# --- Step 3: Convert dates to clean YYYY-MM-DD strings ---
# pandas reads Excel dates as Timestamp objects.
# SQLite wants them as plain strings.
# errors='coerce' turns anything unparseable into NaT (null date)
# instead of crashing.
df['document_date'] = pd.to_datetime(df['document_date'], errors='coerce')
df['document_date'] = df['document_date'].dt.strftime('%Y-%m-%d')

# --- Step 4: Fill NaN amounts with 0 ---
# If a debit or credit cell was blank in Excel, pandas reads it as NaN.
# SQLite will store NaN as NULL. For amounts, 0 is more useful than NULL.
df['total_debit']  = df['total_debit'].fillna(0)
df['total_credit'] = df['total_credit'].fillna(0)

# --- Step 5: Create (or connect to) the SQLite database ---
# If accounting.db doesn't exist, SQLite creates it.
# If it already exists, this just opens it.
conn = sqlite3.connect('accounting.db')

# --- Step 6: Write the DataFrame into a SQLite table ---
# if_exists='replace' drops and recreates the table each time you run this.
# This is safe during development — run the script again to reload clean data.
# index=True adds the auto-increment 'id' column (pandas index becomes a column).
# index_label='id' names that column 'id'.
df.to_sql(
    name='ledger_transactions',
    con=conn,
    if_exists='replace',
    index=True,
    index_label='id'
)

print(f"Written to accounting.db — table: ledger_transactions")

# --- Step 7: Verify the row count matches ---
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM ledger_transactions")
count = cursor.fetchone()[0]
print(f"Rows in database: {count}")

conn.close()
print("Done. Database connection closed.")
