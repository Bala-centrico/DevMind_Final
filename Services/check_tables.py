import sqlite3

conn = sqlite3.connect(r'\\nas3be\ITCrediti\DevMind\mcp_dashboard.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in mcp_dashboard.db:")
for table in tables:
    print(f"  - {table[0]}")
    
    # Get schema for each table
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"    Columns:")
    for col in columns:
        print(f"      {col[1]} ({col[2]})")
    print()

conn.close()
