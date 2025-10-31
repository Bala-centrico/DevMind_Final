"""
Jira Dashboard To-Do Insert Script

This script connects to Jira, fetches all "To Do" issues assigned to "B Balakrishnan",
and inserts them into the mcp_dashboard.db SQLite database.

Database: \\nas3be\ITCrediti\DevMind\mcp_dashboard.db
Table: jira_dashboard
"""

import os
import sys
import sqlite3
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import urllib3

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credentials_manager import CredentialsManager

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# CONFIGURATION
# ============================================================

DB_DIR = r"\\nas3be\ITCrediti\DevMind"
DB_FILE = os.path.join(DB_DIR, "mcp_dashboard.db")
ASSIGNEE_NAME = "B Balakrishnan"
STATUS_FILTER = "To Do"

# ============================================================
# JIRA API CLIENT
# ============================================================

class JiraClient:
    """Simple Jira API client for fetching issues"""
    
    def __init__(self, credentials_manager):
        """Initialize Jira client with credentials"""
        self.creds = credentials_manager
        self.base_url = self.creds.get_base_url().rstrip('/')
        self.api_base = f"{self.base_url}/rest/api/2"
        self.verify_ssl = self.creds.get_verify_ssl()
        
        # Setup authentication
        username = self.creds.get_username()
        api_token = self.creds.get_api_token()
        password = self.creds.get_password()
        
        if api_token:
            self.auth = HTTPBasicAuth(username, api_token)
        elif password:
            self.auth = HTTPBasicAuth(username, password)
        else:
            raise ValueError("No valid credentials found")
    
    def search_issues(self, jql, max_results=50):
        """
        Search for issues using JQL
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            List of issues or None if error
        """
        try:
            url = f"{self.api_base}/search"
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,assignee,created,priority,issuetype,status'
            }
            
            response = requests.get(
                url,
                auth=self.auth,
                params=params,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('issues', [])
            else:
                print(f"❌ Error searching issues: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception searching issues: {str(e)}")
            return None

# ============================================================
# DATABASE OPERATIONS
# ============================================================

def ensure_status_column(cursor):
    """
    Ensure the status column exists in jira_dashboard table.
    If it doesn't exist, add it.
    Also ensures jira_number has a unique index to prevent duplicates.
    """
    try:
        # Check if status column exists
        cursor.execute("PRAGMA table_info(jira_dashboard)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in columns:
            print("⚠️ Status column not found, adding it...")
            cursor.execute("ALTER TABLE jira_dashboard ADD COLUMN status TEXT")
            print("✅ Status column added successfully")
        else:
            print("✅ Status column already exists")
        
        # Check if unique index exists on jira_number
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_jira_number_unique'
        """)
        index_exists = cursor.fetchone()
        
        if not index_exists:
            print("⚠️ Unique index not found on jira_number, creating it...")
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_jira_number_unique 
                ON jira_dashboard(jira_number)
            """)
            print("✅ Unique index created successfully (prevents duplicate jira_numbers)")
        else:
            print("✅ Unique index on jira_number already exists")
            
    except Exception as e:
        print(f"❌ Error ensuring database schema: {str(e)}")
        raise

def insert_or_update_jira_issue(cursor, issue_data):
    """
    Insert a Jira issue in the database ONLY if it doesn't already exist.
    If the jira_number already exists, skip it (no update, no duplicate).
    
    Args:
        cursor: Database cursor
        issue_data: Dictionary containing issue data
        
    Returns:
        'inserted' if new record inserted, 'skipped' if already exists, 'error' if failed
    """
    try:
        # Check if issue already exists
        cursor.execute(
            "SELECT id FROM jira_dashboard WHERE jira_number = ?",
            (issue_data['jira_number'],)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Issue already exists - skip it
            print(f"  ⏭️  Skipped (already exists): {issue_data['jira_number']}")
            return 'skipped'
        else:
            # Insert new record only
            cursor.execute("""
                INSERT INTO jira_dashboard (
                    jira_number, jira_heading, assignee, created,
                    priority, type, status, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue_data['jira_number'],
                issue_data['jira_heading'],
                issue_data['assignee'],
                issue_data['created'],
                issue_data['priority'],
                issue_data['type'],
                issue_data['status'],
                issue_data['last_updated']
            ))
            print(f"  ✅ Inserted: {issue_data['jira_number']}")
            return 'inserted'
        
    except Exception as e:
        print(f"  ❌ Error processing {issue_data.get('jira_number', 'Unknown')}: {str(e)}")
        return 'error'

def parse_jira_issue(issue):
    """
    Parse Jira issue JSON into a dictionary for database insertion
    
    Args:
        issue: Jira issue JSON object
        
    Returns:
        Dictionary with parsed issue data
    """
    fields = issue.get('fields', {})
    
    # Extract assignee
    assignee_obj = fields.get('assignee', {})
    assignee = assignee_obj.get('displayName', 'Unassigned') if assignee_obj else 'Unassigned'
    
    # Extract priority
    priority_obj = fields.get('priority', {})
    priority = priority_obj.get('name', 'Unknown') if priority_obj else 'Unknown'
    
    # Extract issue type
    issuetype_obj = fields.get('issuetype', {})
    issue_type = issuetype_obj.get('name', 'Unknown') if issuetype_obj else 'Unknown'
    
    # Extract status
    status_obj = fields.get('status', {})
    status = status_obj.get('name', 'Unknown') if status_obj else 'Unknown'
    
    # Extract created date
    created = fields.get('created', '')
    if created:
        # Convert ISO format to simple date format
        try:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
            created = created_dt.strftime('%Y-%m-%d')
        except:
            created = created.split('T')[0] if 'T' in created else created
    
    return {
        'jira_number': issue.get('key', 'Unknown'),
        'jira_heading': fields.get('summary', 'No Summary'),
        'assignee': assignee,
        'created': created,
        'priority': priority,
        'type': issue_type,
        'status': status,
        'last_updated': datetime.now().isoformat()
    }

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution function"""
    print("=" * 70)
    print("JIRA DASHBOARD TO-DO INSERT SCRIPT")
    print("=" * 70)
    print(f"Database: {DB_FILE}")
    print(f"Assignee: {ASSIGNEE_NAME}")
    print(f"Status Filter: {STATUS_FILTER}")
    print("=" * 70)
    print()
    
    # Initialize credentials manager
    try:
        print("📝 Loading Jira credentials...")
        creds = CredentialsManager("credentials.ini")
        print(f"✅ Credentials loaded successfully")
        print(f"   Base URL: {creds.get_base_url()}")
        print(f"   Username: {creds.get_username()}")
        print()
    except Exception as e:
        print(f"❌ Error loading credentials: {str(e)}")
        return 1
    
    # Initialize Jira client
    try:
        print("🔗 Connecting to Jira...")
        jira = JiraClient(creds)
        print("✅ Jira client initialized")
        print()
    except Exception as e:
        print(f"❌ Error initializing Jira client: {str(e)}")
        return 1
    
    # Search for issues
    try:
        print(f"🔍 Searching for issues...")
        jql = f'assignee = "{ASSIGNEE_NAME}" AND status = "{STATUS_FILTER}"'
        print(f"   JQL: {jql}")
        print()
        
        issues = jira.search_issues(jql, max_results=50)
        
        if issues is None:
            print("❌ Failed to fetch issues from Jira")
            return 1
        
        if not issues:
            print(f"ℹ️ No issues found for assignee '{ASSIGNEE_NAME}' with status '{STATUS_FILTER}'")
            return 0
        
        print(f"✅ Found {len(issues)} issue(s)")
        print()
        
    except Exception as e:
        print(f"❌ Error searching for issues: {str(e)}")
        return 1
    
    # Connect to database
    try:
        print("💾 Connecting to database...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"✅ Connected to database: {DB_FILE}")
        print()
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return 1
    
    # Ensure status column exists
    try:
        ensure_status_column(cursor)
        conn.commit()
        print()
    except Exception as e:
        print(f"❌ Error ensuring database schema: {str(e)}")
        conn.close()
        return 1
    
    # Insert issues (skip if already exist)
    try:
        print(f"📥 Processing {len(issues)} issue(s)...")
        print()
        
        inserted_count = 0
        skipped_count = 0
        error_count = 0
        
        for issue in issues:
            issue_data = parse_jira_issue(issue)
            result = insert_or_update_jira_issue(cursor, issue_data)
            
            if result == 'inserted':
                inserted_count += 1
            elif result == 'skipped':
                skipped_count += 1
            elif result == 'error':
                error_count += 1
        
        # Commit changes
        conn.commit()
        print()
        print("=" * 70)
        print("📊 PROCESSING SUMMARY:")
        print("=" * 70)
        print(f"  Total Issues Found:     {len(issues)}")
        print(f"  ✅ Newly Inserted:      {inserted_count}")
        print(f"  ⏭️  Skipped (Existing): {skipped_count}")
        print(f"  ❌ Errors:              {error_count}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error processing issues: {str(e)}")
        conn.rollback()
        return 1
    finally:
        conn.close()
        print("💾 Database connection closed")
    
    print()
    print("=" * 70)
    print("✅ SCRIPT COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
