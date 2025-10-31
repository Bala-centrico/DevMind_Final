"""
Script to check the svn_path table structure and data
"""
import sqlite3
import os

DB_PATH = r"\\nas3be\ITCrediti\DevMind\mcp_dashboard.db"

def check_svn_path_table():
    """Check svn_path table structure and data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get table schema
        print("=" * 80)
        print("SVN_PATH TABLE SCHEMA")
        print("=" * 80)
        cursor.execute("PRAGMA table_info(svn_path)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[1]} | Type: {col[2]} | Not Null: {col[3]} | PK: {col[5]}")
        
        # Get sample data
        print("\n" + "=" * 80)
        print("SAMPLE DATA FROM SVN_PATH")
        print("=" * 80)
        cursor.execute("SELECT * FROM svn_path LIMIT 15")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(svn_path)")
        col_names = [col[1] for col in cursor.fetchall()]
        print(" | ".join(col_names))
        print("-" * 80)
        
        for row in rows:
            print(" | ".join(str(val) for val in row))
        
        print("\n" + "=" * 80)
        print(f"Total rows in svn_path: {len(rows)}")
        print("=" * 80)
        
        conn.close()
        print("\n✅ Check completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
    else:
        check_svn_path_table()
