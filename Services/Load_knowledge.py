import pandas as pd
import sqlite3

# Excel and SQLite paths
excel_file = "DevMind_JiraKnowledge_2025.xlsx"
sqlite_db = r"Z:\mcp_dashboard.db"  # <-- full path to your DB

# Read Excel
df = pd.read_excel(excel_file)
df = df.fillna("")  # fill empty cells with empty string

# Connect to SQLite
conn = sqlite3.connect(sqlite_db)
cursor = conn.cursor()

# Create table if not exists
create_table_sql = """
CREATE TABLE IF NOT EXISTS jira_kb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_id TEXT NOT NULL,
    module TEXT,
    requirement_description TEXT,
    solution_summary TEXT,
    key_objects TEXT,
    code_snippet TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
cursor.execute(create_table_sql)

# Insert rows
insert_sql = """
INSERT INTO jira_kb (
    jira_id, module, requirement_description, solution_summary, key_objects, code_snippet, notes
) VALUES (?, ?, ?, ?, ?, ?, ?);
"""

for _, row in df.iterrows():
    cursor.execute(insert_sql, (
        row["Jira_ID"],
        row["Module"],
        row["Requirement_Description"],
        row["Solution_Summary"],
        row["Key_Objects"],
        row.get("Code_Snippet", ""),
        row.get("Notes", "")
    ))

# Commit and close
conn.commit()
conn.close()

print(f"✅ All Jira tasks inserted into {sqlite_db} successfully!")
