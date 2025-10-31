import os
import sqlite3
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

DB_DIR = r"\\nas3be\ITCrediti\DevMind"
DB_FILE = os.path.join(DB_DIR, "mcp_dashboard.db")

# Ensure directory exists
os.makedirs(DB_DIR, exist_ok=True)

# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
print(f"✅ Connected to SQLite DB: {DB_FILE}")

# ============================================================
# TABLE CREATION
# ============================================================

cursor.executescript("""
DROP TABLE IF EXISTS jira_dashboard;

CREATE TABLE jira_dashboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jira_number TEXT NOT NULL,
    jira_heading TEXT,
    assignee TEXT,
    created TEXT,
    priority TEXT,
    type TEXT,
    requirement_clarity TEXT,
    automation TEXT,
    analysis_code_gen_prompt TEXT,
    generated_code_file BLOB,         -- stores actual file binary data
    test_case_file BLOB,              -- stores actual test case file binary data
    decision TEXT DEFAULT 'PENDING',  -- APPROVED / REJECTED / PENDING
    deployment_prompt TEXT,
    last_updated TEXT
);
""")

print("✅ Table 'jira_dashboard' created successfully.")

# ============================================================
# SAMPLE DATA INSERTION
# ============================================================

# Sample file content as binary data
sample_sql_code = "CREATE TABLE CUSTOMER (ID NUMBER, NAME VARCHAR2(50));"
sample_test_code = """-- Test cases for CUSTOMER table
INSERT INTO CUSTOMER VALUES (1, 'John Doe');
INSERT INTO CUSTOMER VALUES (2, 'Jane Smith');
SELECT * FROM CUSTOMER;
DELETE FROM CUSTOMER WHERE ID = 1;"""

sample_accounts_code = "CREATE TABLE ACCOUNTS (ACC_ID NUMBER, BALANCE NUMBER);"
sample_accounts_test = """-- Test cases for ACCOUNTS table
INSERT INTO ACCOUNTS VALUES (1001, 1500.00);
INSERT INTO ACCOUNTS VALUES (1002, 2500.50);
SELECT * FROM ACCOUNTS WHERE BALANCE > 1000;
UPDATE ACCOUNTS SET BALANCE = 3000.00 WHERE ACC_ID = 1001;"""

sample_data = [
    (
        "JIRA-101",
        "Customer Database Creation", 
        "John Doe",
        datetime.now().strftime("%Y-%m-%d"),
        "High",
        "Story",
        "Clear",
        "Yes",
        "Create a customer table with ID and NAME columns for the new CRM system",
        sample_sql_code.encode('utf-8'),      # generated code file content as binary
        sample_test_code.encode('utf-8'),     # test case file content as binary
        "PENDING",
        "Deploy to development environment first",
        datetime.now().isoformat()
    ),
    (
        "JIRA-102",
        "Account Management System",
        "Jane Smith", 
        datetime.now().strftime("%Y-%m-%d"),
        "Medium",
        "Bug",
        "Unclear",
        "No",
        "Need clarification on account balance calculation logic",
        None,  # no generated code file yet
        None,  # no test case file yet
        "PENDING",
        "",
        datetime.now().isoformat()
    ),
    (
        "JIRA-103",
        "Financial Reporting Module",
        "Alex Lee",
        datetime.now().strftime("%Y-%m-%d"),
        "Low", 
        "Enhancement",
        "Clear",
        "Yes",
        "Create accounts table for financial reporting with balance tracking",
        sample_accounts_code.encode('utf-8'),     # generated code file content as binary
        sample_accounts_test.encode('utf-8'),     # test case file content as binary
        "APPROVED",
        "Ready for production deployment",
        datetime.now().isoformat()
    )
]

cursor.executemany("""
INSERT INTO jira_dashboard 
(jira_number, jira_heading, assignee, created, priority, type, requirement_clarity, automation, analysis_code_gen_prompt, generated_code_file, test_case_file, decision, deployment_prompt, last_updated)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", sample_data)

conn.commit()
print(f"✅ Inserted {len(sample_data)} sample records into 'jira_dashboard'.")

conn.close()
print("\n🎉 MCP Dashboard DB initialized successfully!")
