"""
DevMind Unified MCP Server - Complete Integration
Combines all tools from Jira, Oracle Knowledge Base, and SVN servers into one comprehensive MCP server.

Tools included:
1. Jira API Tools (13 tools) - Complete Jira integration + Knowledge Base search + KB management
2. Oracle Standards Tools (2 tools) - Oracle development guidelines  
3. SVN Tools (4 tools) - Source control operations
4. SVN Path Tools (2 tools) - SVN path mapping and discovery

Total: 21 integrated tools for complete development workflow
"""

import asyncio
import configparser
import io
import json
import logging
import os
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import urllib3
from mcp.server.fastmcp import FastMCP
from requests.auth import HTTPBasicAuth

# Optional imports for document processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Set UTF-8 encoding for stdout and stderr
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("DevMind_Unified")

# Constants
DEFAULT_ISSUE_SUMMARY_SEPARATOR = "=" * 70
DEFAULT_DESCRIPTION_SEPARATOR = "-" * 60
DEFAULT_SVN_TIMEOUT = 30
DEFAULT_BASE_URL = "https://svn.bansel.it/h2o"
DB_DIR = r"\\nas3be\ITCrediti\DevMind"
ORACLE_STANDARDS_DB = os.path.join(DB_DIR, "oracle_standards.db")
JIRA_DASHBOARD_DB = os.path.join(DB_DIR, "mcp_dashboard.db")


# ============================================================
# CREDENTIALS MANAGER
# ============================================================
class CredentialsManager:
    """Unified credentials manager for Jira and SVN"""
    
    def __init__(self, credentials_file: str = "credentials.ini"):
        self.credentials_file = self._resolve_credentials_path(credentials_file)
        self.config = configparser.ConfigParser()
        
        if self.credentials_file and os.path.exists(self.credentials_file):
            try:
                self.config.read(self.credentials_file, encoding='utf-8')
                logger.info(f"✅ Loaded credentials from: {self.credentials_file}")
            except Exception as e:
                logger.error(f"❌ Error reading credentials file: {e}")
    
    def _resolve_credentials_path(self, filename: str) -> Optional[str]:
        """Resolve credentials file path"""
        # Priority 1: Environment variable
        env_path = os.getenv('JIRA_CREDENTIALS_PATH') or os.getenv('SVN_CREDENTIALS_PATH')
        if env_path and os.path.exists(env_path):
            return env_path
        
        # Priority 2: User's home directory
        user_home_path = os.path.join(os.path.expanduser('~'), '.devmind', filename)
        if os.path.exists(user_home_path):
            return user_home_path
        
        # Priority 3: Script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            filename,
            os.path.join(script_dir, filename),
            os.path.join(os.path.dirname(script_dir), filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def has_credentials(self) -> bool:
        """Check if credentials file exists and has data"""
        return self.config.sections() and len(self.config.sections()) > 0
    
    # Jira credentials
    def get_base_url(self) -> str:
        return self.config.get('jira', 'base_url', fallback='')
    
    def get_username(self) -> str:
        return self.config.get('jira', 'username', fallback='')
    
    def get_api_token(self) -> str:
        return self.config.get('jira', 'api_token', fallback='')
    
    def get_password(self) -> str:
        return self.config.get('jira', 'password', fallback='')
    
    def get_verify_ssl(self) -> bool:
        return self.config.getboolean('jira', 'verify_ssl', fallback=False)
    
    def get_download_path(self) -> str:
        return self.config.get('jira', 'download_path', fallback='')
    
    # SVN credentials
    def get_svn_base_url(self) -> str:
        return self.config.get('svn', 'base_url', fallback=DEFAULT_BASE_URL)
    
    def get_svn_username(self) -> str:
        return self.config.get('svn', 'username', fallback='')
    
    def get_svn_password(self) -> str:
        return self.config.get('svn', 'password', fallback='')


# ============================================================
# JIRA API CLIENT
# ============================================================
class JiraAPI:
    """Jira REST API client with credentials management"""
    
    def __init__(self, credentials_manager: CredentialsManager, verify_ssl: Optional[bool] = None):
        self.creds = credentials_manager
        self.base_url = self.creds.get_base_url().rstrip('/')
        self.api_base = f"{self.base_url}/rest/api/2"
        self.verify_ssl = verify_ssl if verify_ssl is not None else self.creds.get_verify_ssl()
        
        username = self.creds.get_username()
        api_token = self.creds.get_api_token()
        password = self.creds.get_password()
        
        if api_token:
            self.auth = HTTPBasicAuth(username, api_token)
        elif password:
            self.auth = HTTPBasicAuth(username, password)
        else:
            raise ValueError("No valid credentials found")
        
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = self.verify_ssl
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """Get Jira issue details"""
        try:
            url = f"{self.api_base}/issue/{issue_key}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issue {issue_key}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test Jira connection"""
        try:
            url = f"{self.api_base}/myself"
            response = self.session.get(url)
            response.raise_for_status()
            return True
        except:
            return False
    
    def get_user_info(self) -> Optional[Dict]:
        """Get current user info"""
        try:
            url = f"{self.api_base}/myself"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def get_transitions(self, issue_key: str) -> Optional[list]:
        """Get available transitions"""
        try:
            url = f"{self.api_base}/issue/{issue_key}/transitions"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json().get('transitions', [])
        except:
            return None
    
    def transition_issue(self, issue_key: str, transition_id: str, comment: Optional[str] = None) -> bool:
        """Execute transition"""
        try:
            url = f"{self.api_base}/issue/{issue_key}/transitions"
            payload = {"transition": {"id": transition_id}}
            if comment:
                payload["update"] = {"comment": [{"add": {"body": comment}}]}
            response = self.session.post(url, data=json.dumps(payload))
            response.raise_for_status()
            return True
        except:
            return False
    
    def find_transition_by_name(self, issue_key: str, status_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Find transition by status name"""
        transitions = self.get_transitions(issue_key)
        if not transitions:
            return None, None
        
        for transition in transitions:
            to_status = transition.get('to', {}).get('name', '')
            if to_status.lower() == status_name.lower():
                return transition.get('id'), transition.get('name')
        
        for transition in transitions:
            to_status = transition.get('to', {}).get('name', '')
            if status_name.lower() in to_status.lower():
                return transition.get('id'), transition.get('name')
        
        return None, None
    
    def search_issues(self, jql_query: str, max_results: int = 50, start_at: int = 0) -> Optional[Dict]:
        """Search issues with JQL"""
        try:
            url = f"{self.api_base}/search"
            params = {
                'jql': jql_query,
                'maxResults': min(max_results, 100),
                'startAt': start_at,
                'fields': 'key,summary,status,assignee,priority,issuetype,created,updated'
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def get_attachments(self, issue_key: str) -> Optional[list]:
        """Get issue attachments"""
        try:
            url = f"{self.api_base}/issue/{issue_key}"
            params = {'fields': 'attachment'}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json().get('fields', {}).get('attachment', [])
        except:
            return None
    
    def download_attachment(self, attachment_url: str, attachment_filename: str) -> Optional[bytes]:
        """Download attachment"""
        try:
            headers = {'Accept': '*/*', 'User-Agent': 'DevMind-MCP-Client/1.0'}
            response = self.session.get(attachment_url, headers=headers, allow_redirects=True, timeout=30)
            
            if 'sso' in response.url.lower() or 'login' in response.url.lower() or response.status_code in [302, 401, 403]:
                logger.warning("SSO Authentication Required for attachment download")
                return None
            
            if response.status_code == 200:
                return response.content
            
            return None
        except:
            return None
    
    def get_latest_attachment(self, issue_key: str) -> Optional[Dict]:
        """Get latest attachment"""
        attachments = self.get_attachments(issue_key)
        if not attachments:
            return None
        return max(attachments, key=lambda x: x.get('created', ''))
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add comment to issue"""
        try:
            url = f"{self.api_base}/issue/{issue_key}/comment"
            payload = {"body": comment}
            response = self.session.post(url, data=json.dumps(payload))
            response.raise_for_status()
            return True
        except:
            return False
    
    def get_comments(self, issue_key: str) -> Optional[list]:
        """Get issue comments"""
        try:
            url = f"{self.api_base}/issue/{issue_key}/comment"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json().get('comments', [])
        except:
            return None
    
    def analyze_attachment_content(self, attachment_info: Dict, local_download_path: str = None) -> str:
        """Analyze attachment content"""
        try:
            if local_download_path is None:
                local_download_path = self.creds.get_download_path() or r"C:\Users\GBS05273\Downloads"
            
            filename = attachment_info.get('filename', 'Unknown')
            size = attachment_info.get('size', 0)
            content_type = attachment_info.get('mimeType', 'Unknown')
            created = attachment_info.get('created', 'Unknown')
            author = attachment_info.get('author', {}).get('displayName', 'Unknown')
            content_url = attachment_info.get('content', '')
            
            analysis = f"📎 Attachment Analysis: {filename}\n"
            analysis += f"{'=' * 60}\n"
            analysis += f"📊 Metadata:\n"
            analysis += f"  • File: {filename}\n"
            analysis += f"  • Size: {size:,} bytes ({size/1024:.1f} KB)\n"
            analysis += f"  • Type: {content_type}\n"
            analysis += f"  • Created: {created}\n"
            analysis += f"  • Author: {author}\n\n"
            
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            local_file_path = os.path.join(local_download_path, filename)
            
            if file_ext == 'docx' and DOCX_AVAILABLE:
                content = None
                if os.path.exists(local_file_path):
                    with open(local_file_path, 'rb') as f:
                        content = f.read()
                else:
                    content = self.download_attachment(content_url, filename)
                    if content and os.path.isdir(local_download_path):
                        with open(local_file_path, 'wb') as f:
                            f.write(content)
                
                if content:
                    doc = Document(io.BytesIO(content))
                    full_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                    document_text = "\n".join(full_text)
                    
                    preview_length = min(2000, len(document_text))
                    analysis += f"📄 Content Preview:\n{document_text[:preview_length]}\n"
                    if len(document_text) > preview_length:
                        analysis += f"... (truncated)\n"
            
            analysis += f"\n🔗 Download URL: {content_url}\n"
            return analysis
        except Exception as e:
            return f"❌ Error analyzing attachment: {str(e)}"


# ============================================================
# ORACLE STANDARDS KNOWLEDGE BASE
# ============================================================
class OracleStandardsKB:
    """Oracle Standards Knowledge Base"""
    
    def __init__(self, db_path: str = ORACLE_STANDARDS_DB):
        self.db_path = db_path
        self.connection = None
    
    def _connect(self) -> bool:
        try:
            if not os.path.exists(self.db_path):
                return False
            self.connection = sqlite3.connect(self.db_path)
            return True
        except:
            return False
    
    def _disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def analyze_standards(self, requirement: str = None) -> Dict[str, Any]:
        """Analyze Oracle standards"""
        if not self._connect():
            return {"error": "Could not connect to Oracle Standards database"}
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT procedure_name, description, parameters, usage_example 
                FROM oracle_standards 
                ORDER BY procedure_name
            """)
            standards = cursor.fetchall()
            
            result = {
                "title": "Oracle Development Standards Analysis",
                "svn_structure": {
                    "description": "SVN Repository Structure for Oracle Scripts",
                    "paths": {
                        "trunk": "trunk/DB/OraBE/WEBLOGIC_DBA/",
                        "branches": "branches/<branch_name>/DB/OraBE/WEBLOGIC_DBA/"
                    },
                    "folders": {
                        "upgrade": {"description": "DDL changes - tables, indexes, sequences"},
                        "view": {"description": "View definitions"},
                        "package": {"description": "Package specifications"},
                        "package_body": {"description": "Package bodies"},
                        "procedure": {"description": "Standalone procedures"},
                        "postinstall": {"description": "DML scripts - INSERT/UPDATE/DELETE"},
                        "grants": {"description": "Permission grants"},
                        "rollback": {"description": "Rollback scripts"}
                    }
                },
                "standard_procedures": {
                    "count": len(standards),
                    "procedures": [
                        {"name": std[0], "description": std[1], "parameters": std[2], "usage_example": std[3]}
                        for std in standards
                    ]
                },
                "naming_conventions": {
                    "tables": "{COMPONENT}_TR_{ENTITY}_DUMMY",
                    "sequences": "{COMPONENT}_SQ_{ENTITY_SHORT}_ID",
                    "indexes": "{COMPONENT}_IDX_{ENTITY_SHORT}_{COLUMN_SHORT}"
                }
            }
            
            return result
        except Exception as e:
            return {"error": f"Error analyzing standards: {str(e)}"}
        finally:
            self._disconnect()


# ============================================================
# JIRA DASHBOARD MANAGER
# ============================================================
class JiraDashboardManager:
    """Jira Dashboard Manager"""
    
    def __init__(self, db_path: str = JIRA_DASHBOARD_DB):
        self.db_path = db_path
        self.connection = None
    
    def _connect(self) -> bool:
        try:
            if not os.path.exists(self.db_path):
                return False
            self.connection = sqlite3.connect(self.db_path)
            return True
        except:
            return False
    
    def _disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def add_or_update_jira(self, jira_number: str, **kwargs) -> Dict[str, Any]:
        """Add or update Jira issue"""
        if not self._connect():
            return {"error": "Could not connect to database"}
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM jira_dashboard WHERE jira_number = ?", (jira_number,))
            exists = cursor.fetchone()
            
            current_time = datetime.now().isoformat()
            
            if exists:
                # Update logic
                update_fields = []
                update_values = []
                for key, value in kwargs.items():
                    if value is not None:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                if update_fields:
                    update_fields.append("last_updated = ?")
                    update_values.append(current_time)
                    update_values.append(jira_number)
                    sql = f"UPDATE jira_dashboard SET {', '.join(update_fields)} WHERE jira_number = ?"
                    cursor.execute(sql, update_values)
                    self.connection.commit()
                
                return {"status": "updated", "jira_number": jira_number}
            else:
                # Insert logic
                cursor.execute("""
                    INSERT INTO jira_dashboard 
                    (jira_number, jira_heading, assignee, created, priority, type, 
                     requirement_clarity, automation, comment, decision, status, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    jira_number,
                    kwargs.get('jira_heading'),
                    kwargs.get('assignee'),
                    datetime.now().strftime("%Y-%m-%d"),
                    kwargs.get('priority', 'Medium'),
                    kwargs.get('issue_type', 'Story'),
                    kwargs.get('requirement_clarity', 'Clear'),
                    kwargs.get('automation', 'No'),
                    kwargs.get('comment'),
                    kwargs.get('decision', 'PENDING'),
                    kwargs.get('status'),
                    current_time
                ))
                self.connection.commit()
                return {"status": "created", "jira_number": jira_number}
        except Exception as e:
            return {"error": str(e)}
        finally:
            self._disconnect()


# ============================================================
# SVN PATH MANAGER
# ============================================================
class SVNPathManager:
    """SVN Path Manager - Maps requirement types to SVN paths"""
    
    def __init__(self, db_path: str = JIRA_DASHBOARD_DB):
        self.db_path = db_path
        self.connection = None
    
    def _connect(self) -> bool:
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found: {self.db_path}")
                return False
            self.connection = sqlite3.connect(self.db_path, timeout=30.0)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def _disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
    
    def get_svn_path(self, component_name: str, requirement_type: str) -> Dict[str, Any]:
        """Get SVN path for a specific component and requirement type
        
        Args:
            component_name: Name of the component (e.g., 'FZGDPR')
            requirement_type: Type of requirement (e.g., 'table_creation', 'package_creation')
        
        Returns:
            Dictionary with SVN path information or error message
        """
        if not self._connect():
            return {"error": "Could not connect to SVN Path database"}
        
        try:
            cursor = self.connection.cursor()
            
            # Query for exact match
            query = """
            SELECT id, component_name, key, value 
            FROM svn_path
            WHERE component_name = ? AND key = ?
            """
            cursor.execute(query, (component_name, requirement_type))
            result = cursor.fetchone()
            
            if result:
                # Check if value contains multiple paths (like package_creation)
                svn_path_value = result[3]
                
                # Handle package_creation case which has spec and body paths
                if '\n' in svn_path_value:
                    paths = [p.strip() for p in svn_path_value.split('\n') if p.strip()]
                    return {
                        "component_name": result[1],
                        "requirement_type": result[2],
                        "svn_paths": paths,
                        "is_multi_path": True,
                        "full_paths": [f"{credentials.get_svn_base_url()}/{p}" for p in paths]
                    }
                else:
                    # Single path
                    return {
                        "component_name": result[1],
                        "requirement_type": result[2],
                        "svn_path": svn_path_value,
                        "is_multi_path": False,
                        "full_path": f"{credentials.get_svn_base_url()}/{svn_path_value}"
                    }
            else:
                # If exact match not found, try to find available types for this component
                cursor.execute("""
                    SELECT key FROM svn_path 
                    WHERE component_name = ?
                """, (component_name,))
                available_types = [row[0] for row in cursor.fetchall()]
                
                if available_types:
                    return {
                        "error": f"No SVN path found for component '{component_name}' and requirement type '{requirement_type}'",
                        "available_types": available_types,
                        "suggestion": f"Please use one of these requirement types: {', '.join(available_types)}"
                    }
                else:
                    return {
                        "error": f"Component '{component_name}' not found in SVN path database",
                        "suggestion": "Please check the component name or add it to the svn_path table"
                    }
        except Exception as e:
            logger.error(f"Error in get_svn_path: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            self._disconnect()
    
    def list_all_mappings(self, component_name: str = None) -> Dict[str, Any]:
        """List all SVN path mappings, optionally filtered by component
        
        Args:
            component_name: Optional component name to filter by
        
        Returns:
            Dictionary with all mappings or error message
        """
        if not self._connect():
            return {"error": "Could not connect to SVN Path database"}
        
        try:
            cursor = self.connection.cursor()
            
            if component_name:
                query = """
                SELECT component_name, key, value 
                FROM svn_path
                WHERE component_name = ?
                ORDER BY component_name, key
                """
                cursor.execute(query, (component_name,))
            else:
                query = """
                SELECT component_name, key, value 
                FROM svn_path
                ORDER BY component_name, key
                """
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            if results:
                mappings = []
                for row in results:
                    mappings.append({
                        "component": row[0],
                        "requirement_type": row[1],
                        "svn_path": row[2]
                    })
                
                return {
                    "total_mappings": len(mappings),
                    "filter": component_name if component_name else "all components",
                    "mappings": mappings
                }
            else:
                return {
                    "error": f"No mappings found" + (f" for component '{component_name}'" if component_name else ""),
                    "total_mappings": 0
                }
        except Exception as e:
            logger.error(f"Error in list_all_mappings: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            self._disconnect()


# ============================================================
# JIRA KNOWLEDGE BASE
# ============================================================
class JiraKnowledgeBase:
    """Jira Knowledge Base for similar requirement search"""
    
    def __init__(self, db_path: str = JIRA_DASHBOARD_DB):
        self.db_path = db_path
        self.connection = None
    
    def _connect(self) -> bool:
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found: {self.db_path}")
                return False
            # Use a timeout and check_same_thread=False for better concurrency
            self.connection = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False, isolation_level='DEFERRED')
            # Enable WAL mode for better concurrent access
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database {self.db_path}: {str(e)}")
            return False
    
    def _disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
    
    def get_similar_jira_entries(self, requirement_text: str, limit: int = 5) -> Dict[str, Any]:
        """
        Retrieve similar Jira entries from jira_kb table in mcp_dashboard.db
        
        Args:
            requirement_text: Text to search for in requirements, solutions, and key objects
            limit: Maximum number of results to return (default: 5)
        
        Returns:
            Dictionary with search results or error message
        """
        if not self._connect():
            return {"error": "Could not connect to Jira Knowledge Base"}
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT Jira_ID, Module, Requirement_Description, Solution_Summary, Key_Objects
            FROM jira_kb
            WHERE lower(Module) LIKE '%' || lower(?) || '%'
               OR lower(Requirement_Description) LIKE '%' || lower(?) || '%'
               OR lower(Solution_Summary) LIKE '%' || lower(?) || '%'
               OR lower(Key_Objects) LIKE '%' || lower(?) || '%'
            LIMIT ?
            """
            cursor.execute(query, (requirement_text, requirement_text, requirement_text, requirement_text, limit))
            results = cursor.fetchall()
            
            formatted = []
            for row in results:
                formatted.append({
                    "jira_id": row[0],
                    "module": row[1],
                    "requirement_description": row[2],
                    "solution_summary": row[3],
                    "key_objects": row[4]
                })
            
            return {
                "search_query": requirement_text,
                "results_count": len(formatted),
                "results": formatted
            }
        except Exception as e:
            return {"error": f"Error searching Jira KB: {str(e)}"}
        finally:
            self._disconnect()
    
    def get_latest_tmp_prompt(self, jira_number: str, prompt_type: str = "analysis") -> Dict[str, Any]:
        """
        Retrieve the latest row from jira_tmp_prompts table for a specific Jira issue
        
        Args:
            jira_number: Jira issue number (e.g., 'GDPR-58')
            prompt_type: Type of prompt to fetch - 'analysis', 'deployment', or 'both' (default: 'analysis')
        
        Returns:
            Dictionary with the latest prompt data or error message
        """
        if not self._connect():
            return {"error": "Could not connect to Jira Knowledge Base"}
        
        try:
            cursor = self.connection.cursor()
            
            # Validate prompt_type
            valid_types = ['analysis', 'deployment', 'both']
            if prompt_type.lower() not in valid_types:
                return {"error": f"Invalid prompt_type '{prompt_type}'. Must be one of: {', '.join(valid_types)}"}
            
            query = """
            SELECT jira_no, analysis_prompt, deployment_prompt
            FROM jira_tmp_prompts
            WHERE jira_no = ?
            ORDER BY rowid DESC
            LIMIT 1
            """
            cursor.execute(query, (jira_number,))
            result = cursor.fetchone()
            
            if result:
                response = {
                    "jira_number": result[0],
                    "created_at": None  # No created_at column in this table
                }
                
                # Add requested prompt(s) based on prompt_type
                if prompt_type.lower() == 'analysis':
                    response["analysis_prompt"] = result[1]
                elif prompt_type.lower() == 'deployment':
                    response["deployment_prompt"] = result[2]
                else:  # both
                    response["analysis_prompt"] = result[1]
                    response["deployment_prompt"] = result[2]
                
                return response
            else:
                return {"error": f"No records found for {jira_number} in jira_tmp_prompts table"}
        except Exception as e:
            return {"error": f"Error fetching tmp prompt: {str(e)}"}
        finally:
            self._disconnect()
    
    def get_jira_prompt(self, jira_number: str) -> Dict[str, Any]:
        """
        Retrieve the latest prompt entry from jira_prompts table
        
        Args:
            jira_number: Jira issue number (e.g., 'GDPR-58')
        
        Returns:
            Dictionary with prompt data or error message
        """
        if not self._connect():
            return {"error": "Could not connect to Jira Knowledge Base"}
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT p_id, jira_number, category, analysis_prompt, gen_code, 
                   gen_test_case, deployment_prompt, rewards
            FROM jira_prompts
            WHERE jira_number = ?
            ORDER BY p_id DESC
            LIMIT 1
            """
            cursor.execute(query, (jira_number,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "p_id": result[0],
                    "jira_number": result[1],
                    "category": result[2],
                    "analysis_prompt": result[3].decode('utf-8') if result[3] else None,
                    "gen_code": result[4].decode('utf-8') if result[4] else None,
                    "gen_test_case": result[5].decode('utf-8') if result[5] else None,
                    "deployment_prompt": result[6].decode('utf-8') if result[6] else None,
                    "rewards": result[7]
                }
            else:
                return {"error": f"No records found for {jira_number} in jira_prompts table"}
        except Exception as e:
            return {"error": f"Error fetching jira prompt: {str(e)}"}
        finally:
            self._disconnect()
    
    def insert_jira_prompt(self, jira_number: str, category: str = None, 
                          analysis_prompt: str = None, gen_code: str = None,
                          gen_test_case: str = None, deployment_prompt: str = None,
                          rewards: float = None) -> Dict[str, Any]:
        """
        Insert a new entry into jira_prompts table
        
        Args:
            jira_number: Jira issue number
            category: Category of the prompt
            analysis_prompt: Analysis prompt text (or file path)
            gen_code: Generated code text (or file path)
            gen_test_case: Generated test case text (or file path)
            deployment_prompt: Deployment prompt text
            rewards: Reward value
        
        Returns:
            Success message with inserted ID or error
        """
        if not self._connect():
            return {"error": "Could not connect to Jira Knowledge Base"}
        
        try:
            cursor = self.connection.cursor()
            
            # Helper function to read file content if path is provided, otherwise use the string
            def get_content(value):
                if not value:
                    return None
                # Check if it's a file path
                if isinstance(value, str) and (os.path.exists(value) or '\\' in value or '/' in value):
                    if os.path.exists(value):
                        try:
                            with open(value, 'r', encoding='utf-8') as f:
                                return f.read().encode('utf-8')
                        except:
                            # If file read fails, use the string as-is
                            return value.encode('utf-8')
                    else:
                        # File path doesn't exist, use as string
                        return value.encode('utf-8')
                # Not a file path, treat as string content
                return value.encode('utf-8')
            
            # Convert strings/file paths to BLOB (bytes) for BLOB columns
            analysis_blob = get_content(analysis_prompt)
            code_blob = get_content(gen_code)
            test_blob = get_content(gen_test_case)
            deployment_blob = get_content(deployment_prompt)
            
            query = """
            INSERT INTO jira_prompts (jira_number, category, analysis_prompt, gen_code,
                                     gen_test_case, deployment_prompt, rewards)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (jira_number, category, analysis_blob, code_blob,
                                  test_blob, deployment_blob, rewards))
            
            self.connection.commit()
            inserted_id = cursor.lastrowid
            
            return {
                "status": "success",
                "message": f"Successfully inserted prompt for {jira_number}",
                "p_id": inserted_id
            }
        except sqlite3.Error as e:
            logger.error(f"SQLite error in insert_jira_prompt: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error in insert_jira_prompt: {str(e)}\n{traceback.format_exc()}")
            return {"error": f"Error inserting jira prompt: {str(e)}"}
        finally:
            self._disconnect()
    
    def update_jira_prompt(self, jira_number: str, category: str = None,
                          analysis_prompt: str = None, gen_code: str = None,
                          gen_test_case: str = None, deployment_prompt: str = None,
                          rewards: float = None) -> Dict[str, Any]:
        """
        Update an existing entry in jira_prompts table (updates the latest record)
        
        Args:
            jira_number: Jira issue number
            category: Category of the prompt
            analysis_prompt: Analysis prompt text (or file path)
            gen_code: Generated code text (or file path)
            gen_test_case: Generated test case text (or file path)
            deployment_prompt: Deployment prompt text
            rewards: Reward value
        
        Returns:
            Success message or error
        """
        if not self._connect():
            return {"error": "Could not connect to Jira Knowledge Base"}
        
        try:
            cursor = self.connection.cursor()
            
            # Helper function to read file content if path is provided, otherwise use the string
            def get_content(value):
                if not value:
                    return None
                # Check if it's a file path
                if isinstance(value, str) and (os.path.exists(value) or '\\' in value or '/' in value):
                    if os.path.exists(value):
                        try:
                            with open(value, 'r', encoding='utf-8') as f:
                                return f.read().encode('utf-8')
                        except:
                            # If file read fails, use the string as-is
                            return value.encode('utf-8')
                    else:
                        # File path doesn't exist, use as string
                        return value.encode('utf-8')
                # Not a file path, treat as string content
                return value.encode('utf-8')
            
            # Build dynamic UPDATE query based on provided fields
            update_fields = []
            update_values = []
            
            if category is not None:
                update_fields.append("category = ?")
                update_values.append(category)
            
            if analysis_prompt is not None:
                update_fields.append("analysis_prompt = ?")
                update_values.append(get_content(analysis_prompt))
            
            if gen_code is not None:
                update_fields.append("gen_code = ?")
                update_values.append(get_content(gen_code))
            
            if gen_test_case is not None:
                update_fields.append("gen_test_case = ?")
                update_values.append(get_content(gen_test_case))
            
            if deployment_prompt is not None:
                update_fields.append("deployment_prompt = ?")
                update_values.append(get_content(deployment_prompt))
            
            if rewards is not None:
                update_fields.append("rewards = ?")
                update_values.append(rewards)
            
            if not update_fields:
                return {"error": "No fields provided to update"}
            
            # Get the latest p_id for this jira_number
            cursor.execute("SELECT p_id FROM jira_prompts WHERE jira_number = ? ORDER BY p_id DESC LIMIT 1", 
                          (jira_number,))
            result = cursor.fetchone()
            
            if not result:
                return {"error": f"No existing record found for {jira_number}. Use insert instead."}
            
            p_id = result[0]
            update_values.append(p_id)
            
            query = f"UPDATE jira_prompts SET {', '.join(update_fields)} WHERE p_id = ?"
            cursor.execute(query, update_values)
            
            self.connection.commit()
            
            return {
                "status": "success",
                "message": f"Successfully updated prompt for {jira_number}",
                "p_id": p_id,
                "updated_fields": len(update_fields)
            }
        except sqlite3.Error as e:
            logger.error(f"SQLite error in update_jira_prompt: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error in update_jira_prompt: {str(e)}\n{traceback.format_exc()}")
            return {"error": f"Error updating jira prompt: {str(e)}"}
        finally:
            self._disconnect()


# ============================================================
# SVN CLIENT
# ============================================================
class SVNClient:
    """SVN client for source control operations"""
    
    def __init__(self, credentials: CredentialsManager):
        self.creds = credentials
        self.base_url = credentials.get_svn_base_url()
        self.username = credentials.get_svn_username()
        self.password = credentials.get_svn_password()
    
    def _run_svn_command(self, command: list[str]) -> tuple[bool, str]:
        """Execute SVN command"""
        try:
            full_command = ["svn"] + command
            if self.username:
                full_command.extend(["--username", self.username])
            if self.password:
                full_command.extend(["--password", self.password])
            full_command.append("--trust-server-cert-failures=unknown-ca,cn-mismatch,expired,not-yet-valid,other")
            full_command.append("--non-interactive")
            
            result = subprocess.run(full_command, capture_output=True, text=True, timeout=DEFAULT_SVN_TIMEOUT, encoding='utf-8')
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip() or result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    def update_component(self, component: str) -> tuple[bool, str]:
        """Update specific component from SVN repository
        
        Note: This method is designed for local SVN working copies.
        For remote repository access (browsing only), no update is needed.
        """
        try:
            # Skip update for remote repository access - only needed for local working copies
            # When browsing SVN remotely, we directly access the latest version via URL
            return True, f"Using remote SVN access (no local update needed)"
        except Exception as e:
            return False, str(e)
    
    def commit_file(self, component: str, file_path: str, file_content: str, 
                   svn_path: str, commit_message: str) -> tuple[bool, str, Optional[str]]:
        """Commit file to SVN"""
        temp_dir = None
        try:
            # Update component first
            update_success, update_output = self.update_component(component)
            update_info = f"📥 SVN Update: {component}\n{update_output}\n\n" if update_success else f"⚠️ Update Warning: {update_output}\n\n"
            
            temp_dir = tempfile.mkdtemp()
            svn_url = f"{self.base_url}/{component}/{svn_path}"
            parent_url = os.path.dirname(svn_url).replace('\\', '/')
            file_name = os.path.basename(file_path)
            local_file = os.path.join(temp_dir, file_name)
            
            success, output = self._run_svn_command(["info", svn_url])
            file_exists = success
            
            success, output = self._run_svn_command(["checkout", "--depth", "files", parent_url, temp_dir])
            if not success:
                return False, f"Failed to checkout: {output}", None
            
            with open(local_file, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            if not file_exists:
                success, output = self._run_svn_command(["add", local_file])
                if not success:
                    return False, f"Failed to add: {output}", None
            
            success, output = self._run_svn_command(["commit", "-m", commit_message, local_file])
            if not success:
                return False, f"{update_info}Failed to commit: {output}", None
            
            revision = None
            if "Committed revision" in output:
                try:
                    revision = output.split("revision")[1].strip().rstrip('.').strip()
                except:
                    pass
            
            return True, f"{update_info}✅ File committed successfully!\n{output}", revision
        except Exception as e:
            return False, str(e), None
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    def get_file_version(self, component: str, svn_path: str, limit: int = 1) -> tuple[bool, str]:
        """Get file version info"""
        try:
            # Update component first
            update_success, update_output = self.update_component(component)
            update_info = f"📥 SVN Update: {component}\n{update_output}\n\n" if update_success else f"⚠️ Update Warning: {update_output}\n\n"
            
            svn_url = f"{self.base_url}/{component}/{svn_path}"
            success, output = self._run_svn_command(["log", "-l", str(limit), "-v", svn_url])
            if not success:
                return False, f"{update_info}Failed to get version: {output}"
            return True, f"{update_info}{output}"
        except Exception as e:
            return False, str(e)
    
    def get_latest_version(self, component: str, directory_path: str = "trunk/DB") -> tuple[bool, str]:
        """Get latest SVN version/revision for component directory"""
        try:
            # Update component first
            update_success, update_output = self.update_component(component)
            update_info = f"📥 SVN Update: {component}\n{update_output}\n\n" if update_success else f"⚠️ Update Warning: {update_output}\n\n"
            
            svn_url = f"{self.base_url}/{component}/{directory_path}"
            success, output = self._run_svn_command(["info", svn_url])
            if not success:
                return False, f"{update_info}Failed to get info: {output}"
            
            # Parse the output to extract revision and last changed info
            revision = "Unknown"
            last_changed_rev = "Unknown"
            last_changed_author = "Unknown"
            last_changed_date = "Unknown"
            
            for line in output.split('\n'):
                if line.startswith('Revision:'):
                    revision = line.split(':', 1)[1].strip()
                elif line.startswith('Last Changed Rev:'):
                    last_changed_rev = line.split(':', 1)[1].strip()
                elif line.startswith('Last Changed Author:'):
                    last_changed_author = line.split(':', 1)[1].strip()
                elif line.startswith('Last Changed Date:'):
                    last_changed_date = line.split(':', 1)[1].strip()
            
            report = f"{update_info}📌 Latest Version Info: {component}/{directory_path}\n"
            report += "=" * 70 + "\n"
            report += f"Current Revision: {revision}\n"
            report += f"Last Changed Revision: {last_changed_rev}\n"
            report += f"Last Changed Author: {last_changed_author}\n"
            report += f"Last Changed Date: {last_changed_date}\n"
            report += "=" * 70 + "\n"
            
            return True, report
        except Exception as e:
            return False, str(e)
    
    def analyze_directory_code(self, component: str, directory_path: str, 
                               file_extensions: list[str] = None, max_files: int = 20) -> tuple[bool, str]:
        """Analyze directory code"""
        try:
            # Update component first
            update_success, update_output = self.update_component(component)
            update_info = f"📥 SVN Update: {component}\n{update_output}\n\n" if update_success else f"⚠️ Update Warning: {update_output}\n\n"
            
            svn_url = f"{self.base_url}/{component}/{directory_path}"
            success, listing = self._run_svn_command(["list", "-R", svn_url])
            if not success:
                return False, f"{update_info}Failed to list directory: {listing}"
            
            files = [f.strip() for f in listing.split('\n') if f.strip() and not f.endswith('/')]
            if file_extensions:
                files = [f for f in files if any(f.endswith(ext) for ext in file_extensions)]
            
            if max_files > 0:
                files = files[:max_files]
            
            report = f"{update_info}🔍 Code Analysis: {component}/{directory_path}\n"
            report += "=" * 80 + "\n\n"
            
            for idx, file_path in enumerate(files, 1):
                file_url = f"{svn_url}/{file_path}"
                success, content = self._run_svn_command(["cat", file_url])
                if success:
                    report += f"\n📄 File {idx}: {file_path}\n"
                    report += "-" * 80 + "\n"
                    report += content + "\n"
                    report += "=" * 80 + "\n"
            
            return True, report
        except Exception as e:
            return False, str(e)


# ============================================================
# INITIALIZE GLOBAL INSTANCES
# ============================================================
credentials = CredentialsManager()
jira_api: Optional[JiraAPI] = None
oracle_kb = OracleStandardsKB()
jira_dashboard = JiraDashboardManager()
jira_kb = JiraKnowledgeBase()
svn_client = SVNClient(credentials)
svn_path_manager = SVNPathManager()


def get_jira_api() -> JiraAPI:
    """Get or initialize Jira API"""
    global jira_api
    if jira_api is None:
        jira_api = JiraAPI(credentials)
    return jira_api


def check_jira_auth() -> Optional[str]:
    """Check Jira authentication and return error message if failed, None if successful"""
    try:
        jira = get_jira_api()
        if not jira.test_connection():
            return "❌ Jira authentication failed. Please check your credentials in ~/.devmind/credentials.ini"
        return None
    except Exception as e:
        return f"❌ Jira connection error: {str(e)}\n\nPlease verify:\n1. Credentials file exists at ~/.devmind/credentials.ini\n2. Base URL, username, and password are correct\n3. Network connectivity to Jira server"


def format_issue_summary(issue_data: Optional[Dict]) -> str:
    """Format Jira issue summary"""
    if not issue_data:
        return "No issue data"
    
    fields = issue_data.get('fields', {})
    return f"""
{DEFAULT_ISSUE_SUMMARY_SEPARATOR}
Issue: {issue_data.get('key', 'Unknown')}
{DEFAULT_ISSUE_SUMMARY_SEPARATOR}
Summary: {fields.get('summary', 'No summary')}
Status: {fields.get('status', {}).get('name', 'Unknown')}
Priority: {fields.get('priority', {}).get('name', 'Unknown')}
Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}
Description: {fields.get('description', 'No description')}
{DEFAULT_ISSUE_SUMMARY_SEPARATOR}
"""


# ============================================================
# JIRA MCP TOOLS
# ============================================================

@mcp.tool()
def get_jira_issue(issue_key: str, format: str = "full") -> str:
    """Get Jira issue details with configurable format
    
    Args:
        issue_key: The Jira issue key (e.g., 'CMU-105')
        format: Output format - 'full' (default), 'summary', or 'raw'
            - 'full': Formatted detailed view with all fields
            - 'summary': Brief summary with key information
            - 'raw': Raw JSON data
    
    Returns:
        Formatted issue information based on the specified format
    """
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        issue_data = jira.get_issue(issue_key.strip())
        
        if not issue_data:
            return f"❌ Could not retrieve {issue_key}"
        
        # Handle different formats
        if format == "raw":
            return json.dumps(issue_data, indent=2)
        elif format == "summary":
            fields = issue_data.get('fields', {})
            return f"""📋 Issue: {issue_data.get('key')}
Title: {fields.get('summary')}
Status: {fields.get('status', {}).get('name')}
Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}
Priority: {fields.get('priority', {}).get('name')}"""
        else:  # default to 'full'
            return format_issue_summary(issue_data)
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def update_issue_status(issue_key: str, target_status: str, comment: str = None) -> str:
    """Update Jira issue status to any valid status (e.g., 'In Progress', 'Development Done', 'To Do', 'Done', etc.)
    
    Args:
        issue_key: The Jira issue key (e.g., 'CMU-105')
        target_status: The target status name (e.g., 'In Progress', 'Development Done', 'Done')
        comment: Optional comment to add when changing status
    
    Returns:
        Success or error message with status transition details
    """
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        issue_data = jira.get_issue(issue_key.strip())
        if not issue_data:
            return f"❌ Could not find {issue_key}"
        
        current_status = issue_data.get('fields', {}).get('status', {}).get('name', 'Unknown')
        if current_status.lower() == target_status.lower():
            return f"ℹ️ Issue {issue_key} is already in '{current_status}' status"
        
        transition_id, transition_name = jira.find_transition_by_name(issue_key, target_status)
        if not transition_id:
            # Get available transitions to help user
            transitions = jira.get_transitions(issue_key)
            available = [t.get('to', {}).get('name') for t in transitions] if transitions else []
            return f"❌ No transition found from '{current_status}' to '{target_status}'\n\nAvailable transitions: {', '.join(available)}"
        
        if jira.transition_issue(issue_key, transition_id, comment):
            comment_msg = f" with comment: '{comment}'" if comment else ""
            return f"✅ Status changed: {issue_key} from '{current_status}' → '{target_status}'{comment_msg}"
        return "❌ Transition failed"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def search_issues_by_assignee(assignee_name: str, max_results: int = 20, count_only: bool = False) -> str:
    """Search issues by assignee with optional count-only mode
    
    Args:
        assignee_name: The name of the assignee
        max_results: Maximum number of results to return (default: 20)
        count_only: If True, only return the count; if False, return full results
    
    Returns:
        Either count of issues or detailed list based on count_only parameter
    """
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        jql = f'assignee = "{assignee_name}"'
        results = jira.search_issues(jql, max_results if not count_only else 1)
        if not results:
            return f"❌ Search failed"
        
        total = results.get('total', 0)
        
        # Count-only mode
        if count_only:
            return f"📊 {assignee_name} has {total} issue{'s' if total != 1 else ''}"
        
        # Full results mode
        issues = results.get('issues', [])
        output = f"📋 Issues for {assignee_name}: {total} total\n{'='*60}\n"
        for issue in issues:
            key = issue.get('key')
            summary = issue.get('fields', {}).get('summary')
            status = issue.get('fields', {}).get('status', {}).get('name')
            output += f"🔹 {key}: {summary}\n   Status: {status}\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def search_issues_by_jql(jql_query: str, max_results: int = 20) -> str:
    """Search issues with custom JQL"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        results = jira.search_issues(jql_query, max_results)
        if not results:
            return "❌ Search failed"
        
        issues = results.get('issues', [])
        output = f"📋 JQL Results: {len(issues)} issues\n{'='*60}\n"
        for issue in issues:
            key = issue.get('key')
            summary = issue.get('fields', {}).get('summary')
            output += f"🔹 {key}: {summary}\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def add_comment_to_issue(issue_key: str, comment: str) -> str:
    """Add comment to Jira issue"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        if jira.add_comment(issue_key.strip(), comment):
            return f"✅ Comment added to {issue_key}"
        return "❌ Failed to add comment"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_issue_comments(issue_key: str, max_comments: int = 10) -> str:
    """Get issue comments"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        comments = jira.get_comments(issue_key.strip())
        if not comments:
            return f"💬 No comments for {issue_key}"
        
        output = f"💬 Comments for {issue_key}:\n{'='*60}\n"
        for idx, comment in enumerate(sorted(comments, key=lambda x: x.get('created', ''), reverse=True)[:max_comments], 1):
            author = comment.get('author', {}).get('displayName', 'Unknown')
            body = comment.get('body', '')
            output += f"{idx}. {author}: {body}\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def complete_attachment_analysis(issue_key: str, local_download_path: str = None) -> str:
    """Complete attachment analysis"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        attachments = jira.get_attachments(issue_key.strip())
        if not attachments:
            return f"📎 No attachments for {issue_key}"
        
        latest = jira.get_latest_attachment(issue_key)
        if not latest:
            return "❌ Could not get latest attachment"
        
        return jira.analyze_attachment_content(latest, local_download_path)
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def search_similar_jira_requirements(requirement_text: str, max_results: int = 5) -> str:
    """Search for similar Jira requirements in the knowledge base
    
    Args:
        requirement_text: Text to search for in requirement descriptions, solutions, and key objects
        max_results: Maximum number of similar entries to return (default: 5)
    
    Returns:
        List of similar Jira entries with their descriptions, solutions, and key objects
    """
    try:
        result = jira_kb.get_similar_jira_entries(requirement_text, max_results)
        
        if "error" in result:
            return f"❌ {result['error']}"
        
        if result['results_count'] == 0:
            return f"🔍 No similar requirements found for: '{requirement_text}'"
        
        output = f"🔍 Similar Requirements Found: {result['results_count']} matches\n"
        output += f"Search Query: '{requirement_text}'\n"
        output += "=" * 80 + "\n\n"
        
        for idx, entry in enumerate(result['results'], 1):
            output += f"📋 {idx}. {entry['jira_id']} - Module: {entry['module']}\n"
            output += "-" * 80 + "\n"
            output += f"📝 Requirement:\n{entry['requirement_description']}\n\n"
            output += f"💡 Solution:\n{entry['solution_summary']}\n\n"
            output += f"🔑 Key Objects:\n{entry['key_objects']}\n"
            output += "=" * 80 + "\n\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_latest_jira_tmp_prompt(jira_number: str, prompt_type: str = "analysis") -> str:
    """Get the latest prompt(s) from jira_tmp_prompts table for a specific Jira issue
    
    Args:
        jira_number: Jira issue number (e.g., 'GDPR-58', 'CMU-105')
        prompt_type: Type of prompt to fetch - 'analysis', 'deployment', or 'both' (default: 'analysis')
    
    Returns:
        The latest prompt(s) for the specified Jira issue based on prompt_type
    """
    try:
        result = jira_kb.get_latest_tmp_prompt(jira_number, prompt_type)
        
        if "error" in result:
            return f"❌ {result['error']}"
        
        output = f"📋 Latest Prompt for {result['jira_number']}\n"
        output += "=" * 80 + "\n"
        if result.get('created_at'):
            output += f"📅 Created: {result['created_at']}\n"
            output += "=" * 80 + "\n\n"
        
        # Display analysis prompt if requested
        if 'analysis_prompt' in result:
            output += "📊 ANALYSIS PROMPT:\n"
            output += "-" * 80 + "\n"
            output += f"{result['analysis_prompt']}\n"
            if 'deployment_prompt' in result:
                output += "\n" + "=" * 80 + "\n\n"
        
        # Display deployment prompt if requested
        if 'deployment_prompt' in result:
            output += "🚀 DEPLOYMENT PROMPT:\n"
            output += "-" * 80 + "\n"
            output += f"{result['deployment_prompt']}\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def add_to_jira_kb(
    jira_id: str,
    project: str,
    module: str,
    description: str,
    solution: str,
    key_objects: str,
    code: str
) -> str:
    """Add completed Jira issue to knowledge base for future reference
    
    Args:
        jira_id: Jira issue ID (e.g., 'CMU-105')
        project: Project name
        module: Module name
        description: Requirement description
        solution: Solution summary
        key_objects: Key objects involved (comma-separated)
        code: Code snippet or implementation details
    
    Returns:
        Success or error message
    """
    try:
        conn = sqlite3.connect(JIRA_DASHBOARD_DB)
        cur = conn.cursor()
        
        # Insert into jira_kb table
        cur.execute("""
            INSERT INTO jira_kb (jira_id, project_name, module, requirement_description,
                                 solution_summary, key_objects, code_snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (jira_id, project, module, description, solution, key_objects, code))
        
        conn.commit()
        conn.close()
        
        return f"✅ Successfully added {jira_id} to knowledge base\n📚 Project: {project}\n📦 Module: {module}"
    except sqlite3.IntegrityError:
        return f"⚠️ {jira_id} already exists in knowledge base. Use update if you need to modify it."
    except Exception as e:
        return f"❌ Error adding to knowledge base: {str(e)}"


# ============================================================
# JIRA PROMPTS TOOLS
# ============================================================

@mcp.tool()
def get_jira_prompt(jira_number: str) -> str:
    """Get the latest prompt entry from jira_prompts table
    
    Args:
        jira_number: Jira issue number (e.g., 'GDPR-58', 'CMU-105')
    
    Returns:
        Complete prompt information including analysis, generated code, test cases, and deployment details
    """
    try:
        result = jira_kb.get_jira_prompt(jira_number)
        
        if "error" in result:
            return f"❌ {result['error']}"
        
        output = f"📋 Jira Prompt for {result['jira_number']}\n"
        output += "=" * 80 + "\n"
        output += f"🆔 Prompt ID: {result['p_id']}\n"
        if result.get('category'):
            output += f"📂 Category: {result['category']}\n"
        if result.get('rewards') is not None:
            output += f"⭐ Rewards: {result['rewards']}\n"
        output += "=" * 80 + "\n\n"
        
        if result.get('analysis_prompt'):
            output += "📊 ANALYSIS PROMPT:\n"
            output += "-" * 80 + "\n"
            output += f"{result['analysis_prompt']}\n\n"
        
        if result.get('gen_code'):
            output += "💻 GENERATED CODE:\n"
            output += "-" * 80 + "\n"
            output += f"{result['gen_code']}\n\n"
        
        if result.get('gen_test_case'):
            output += "🧪 GENERATED TEST CASE:\n"
            output += "-" * 80 + "\n"
            output += f"{result['gen_test_case']}\n\n"
        
        if result.get('deployment_prompt'):
            output += "🚀 DEPLOYMENT PROMPT:\n"
            output += "-" * 80 + "\n"
            output += f"{result['deployment_prompt']}\n\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def insert_jira_prompt(
    jira_number: str,
    category: str = None,
    analysis_prompt: str = None,
    gen_code: str = None,
    gen_test_case: str = None,
    deployment_prompt: str = None,
    rewards: float = None
) -> str:
    """Insert a new prompt entry into jira_prompts table
    
    Args:
        jira_number: Jira issue number (e.g., 'GDPR-58', 'CMU-105')
        category: Category of the prompt (e.g., 'DDL', 'DML', 'Package')
        analysis_prompt: Analysis prompt text
        gen_code: Generated code (SQL, PL/SQL, etc.)
        gen_test_case: Generated test case code
        deployment_prompt: Deployment instructions or prompt
        rewards: Reward value for the prompt (numeric)
    
    Returns:
        Success message with inserted prompt ID
    """
    try:
        result = jira_kb.insert_jira_prompt(
            jira_number=jira_number,
            category=category,
            analysis_prompt=analysis_prompt,
            gen_code=gen_code,
            gen_test_case=gen_test_case,
            deployment_prompt=deployment_prompt,
            rewards=rewards
        )
        
        if "error" in result:
            return f"❌ {result['error']}"
        
        return f"✅ {result['message']}\n🆔 Prompt ID: {result['p_id']}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def update_jira_prompt(
    jira_number: str,
    category: str = None,
    analysis_prompt: str = None,
    gen_code: str = None,
    gen_test_case: str = None,
    deployment_prompt: str = None,
    rewards: float = None
) -> str:
    """Update an existing prompt entry in jira_prompts table (updates the latest record for the Jira number)
    
    Args:
        jira_number: Jira issue number (e.g., 'GDPR-58', 'CMU-105')
        category: Category of the prompt (e.g., 'DDL', 'DML', 'Package')
        analysis_prompt: Analysis prompt text
        gen_code: Generated code (SQL, PL/SQL, etc.)
        gen_test_case: Generated test case code
        deployment_prompt: Deployment instructions or prompt
        rewards: Reward value for the prompt (numeric)
    
    Returns:
        Success message with number of fields updated
    """
    try:
        result = jira_kb.update_jira_prompt(
            jira_number=jira_number,
            category=category,
            analysis_prompt=analysis_prompt,
            gen_code=gen_code,
            gen_test_case=gen_test_case,
            deployment_prompt=deployment_prompt,
            rewards=rewards
        )
        
        if "error" in result:
            return f"❌ {result['error']}"
        
        return f"✅ {result['message']}\n🆔 Prompt ID: {result['p_id']}\n📝 Updated {result['updated_fields']} field(s)"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ============================================================
# ORACLE STANDARDS TOOLS
# ============================================================

@mcp.tool()
def analyze_oracle_standards(requirement: str = None) -> str:
    """Analyze Oracle development standards"""
    try:
        result = oracle_kb.analyze_standards(requirement)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def add_or_update_jira_dashboard(
    jira_number: str,
    jira_heading: str = None,
    assignee: str = None,
    priority: str = None,
    issue_type: str = None,
    requirement_clarity: str = None,
    automation: str = None,
    comment: str = None,
    decision: str = None,
    status: str = None
) -> str:
    """Add or update Jira in dashboard"""
    try:
        result = jira_dashboard.add_or_update_jira(
            jira_number=jira_number,
            jira_heading=jira_heading,
            assignee=assignee,
            priority=priority,
            issue_type=issue_type,
            requirement_clarity=requirement_clarity,
            automation=automation,
            comment=comment,
            decision=decision,
            status=status
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ============================================================
# SVN TOOLS
# ============================================================

@mcp.tool()
def commit_file_to_svn(
    component: str,
    file_path: str,
    file_content: str,
    svn_path: str,
    commit_message: str
) -> str:
    """Commit file to SVN"""
    try:
        success, message, revision = svn_client.commit_file(component, file_path, file_content, svn_path, commit_message)
        if success:
            return f"{message}\n📌 Revision: {revision}" if revision else message
        return f"❌ {message}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_committed_file_version(component: str, svn_path: str, history_limit: int = 5) -> str:
    """Get file version and history"""
    try:
        success, info = svn_client.get_file_version(component, svn_path, history_limit)
        return info
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_latest_component_version(
    component: str,
    repo_path: str = "trunk",
    db_subdirectory: str = ""
) -> str:
    """Get latest SVN version/revision of component DB directory (fast, no code analysis)"""
    try:
        directory_path = f"{repo_path}/DB/{db_subdirectory}" if db_subdirectory else f"{repo_path}/DB"
        success, version_info = svn_client.get_latest_version(component, directory_path)
        return version_info
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def analyze_db_code_logic(
    component: str,
    repo_path: str = "trunk",
    db_subdirectory: str = "",
    max_files: int = 0
) -> str:
    """Analyze database code logic"""
    try:
        directory_path = f"{repo_path}/DB/{db_subdirectory}" if db_subdirectory else f"{repo_path}/DB"
        success, analysis = svn_client.analyze_directory_code(
            component, directory_path, file_extensions=['.sql', '.SQL'], max_files=max_files
        )
        return analysis
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ============================================================
# SVN PATH TOOLS
# ============================================================

@mcp.tool()
def get_svn_path_for_requirement(component_name: str, requirement_type: str) -> str:
    """Get SVN path for a specific component and requirement type
    
    This tool retrieves the correct SVN repository path based on the component name 
    and the type of requirement (e.g., table_creation, package_creation, etc.).
    
    Args:
        component_name: Name of the component (e.g., 'FZGDPR', 'AnticipoFatture')
        requirement_type: Type of requirement, one of:
            - table_creation: DDL for creating tables
            - table_alter: DDL for altering tables
            - table_update: DML for updating table data
            - table_insert: DML for inserting data
            - table_delete: DML for deleting data
            - table_grants: Database permission grants
            - view_creation: View definitions
            - procedure_creation: Standalone procedures
            - package_creation: Package specifications and bodies
    
    Returns:
        Formatted SVN path information including full URL(s) for the requirement
    
    Examples:
        get_svn_path_for_requirement("FZGDPR", "table_creation")
        -> Returns: FZGDPR/DB/OraBE/WEBLOGIC_DBA/upgrade
        
        get_svn_path_for_requirement("FZGDPR", "package_creation")
        -> Returns multiple paths for spec and body
    """
    try:
        result = svn_path_manager.get_svn_path(component_name, requirement_type)
        
        if "error" in result:
            output = f"❌ {result['error']}\n"
            if "available_types" in result:
                output += f"\n📋 Available requirement types for '{component_name}':\n"
                for req_type in result['available_types']:
                    output += f"  • {req_type}\n"
            if "suggestion" in result:
                output += f"\n💡 {result['suggestion']}\n"
            return output
        
        # Handle multi-path results (e.g., package_creation with spec and body)
        if result.get('is_multi_path'):
            output = f"📂 SVN Paths for {result['component_name']} - {result['requirement_type']}\n"
            output += "=" * 80 + "\n"
            output += f"⚠️ This requirement type has multiple paths:\n\n"
            for idx, path in enumerate(result['svn_paths'], 1):
                output += f"{idx}. {path}\n"
            output += "\n" + "=" * 80 + "\n"
            output += "🔗 Full URLs:\n"
            for idx, full_path in enumerate(result['full_paths'], 1):
                output += f"{idx}. {full_path}\n"
            return output
        else:
            # Single path result
            output = f"📂 SVN Path for {result['component_name']} - {result['requirement_type']}\n"
            output += "=" * 80 + "\n"
            output += f"📁 Path: {result['svn_path']}\n"
            output += f"🔗 Full URL: {result['full_path']}\n"
            output += "=" * 80 + "\n"
            return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def list_svn_path_mappings(component_name: str = None) -> str:
    """List all SVN path mappings, optionally filtered by component
    
    This tool displays all configured SVN path mappings from the database.
    Useful for discovering available requirement types and their corresponding paths.
    
    Args:
        component_name: Optional component name to filter results (e.g., 'FZGDPR')
                       If not provided, lists all mappings for all components
    
    Returns:
        Formatted list of all SVN path mappings
    
    Examples:
        list_svn_path_mappings()  # Lists all mappings
        list_svn_path_mappings("FZGDPR")  # Lists only FZGDPR mappings
    """
    try:
        result = svn_path_manager.list_all_mappings(component_name)
        
        if "error" in result:
            return f"❌ {result['error']}"
        
        output = f"📋 SVN Path Mappings - {result['filter'].upper()}\n"
        output += "=" * 80 + "\n"
        output += f"Total Mappings: {result['total_mappings']}\n"
        output += "=" * 80 + "\n\n"
        
        current_component = None
        for mapping in result['mappings']:
            if mapping['component'] != current_component:
                if current_component is not None:
                    output += "\n"
                current_component = mapping['component']
                output += f"🔷 Component: {mapping['component']}\n"
                output += "-" * 80 + "\n"
            
            output += f"  📌 {mapping['requirement_type']:<25} → {mapping['svn_path']}\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ============================================================
# ADDITIONAL JIRA TOOLS (from original file)
# ============================================================

@mcp.tool()
def count_issues_by_assignee(assignee_name: str) -> str:
    """Count issues by assignee (DEPRECATED: Use search_issues_by_assignee with count_only=True)"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        jql = f'assignee = "{assignee_name}"'
        results = jira.search_issues(jql, max_results=1)
        if not results:
            return "❌ Search failed"
        
        total = results.get('total', 0)
        return f"📊 {assignee_name} has {total} issue{'s' if total != 1 else ''}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_jira_issue_raw(issue_key: str) -> str:
    """Get raw JSON of Jira issue (DEPRECATED: Use get_jira_issue with format='raw')"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        issue_data = jira.get_issue(issue_key.strip())
        return json.dumps(issue_data, indent=2) if issue_data else f"❌ Could not retrieve {issue_key}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_jira_user_info() -> str:
    """Get current Jira user info"""
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        user_info = jira.get_user_info()
        if user_info:
            return f"""👤 User: {user_info.get('displayName')}
Username: {user_info.get('name')}
Email: {user_info.get('emailAddress')}"""
        return "❌ Could not get user info"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_issue_transitions(issue_key: str, detailed: bool = False) -> str:
    """Get available transitions for issue with optional detailed information
    
    Args:
        issue_key: The Jira issue key
        detailed: If True, show full details with IDs; if False, show simple list
    
    Returns:
        List of available transitions in simple or detailed format
    """
    # Check authentication first
    auth_error = check_jira_auth()
    if auth_error:
        return auth_error
    
    try:
        jira = get_jira_api()
        transitions = jira.get_transitions(issue_key.strip())
        if not transitions:
            return f"❌ No transitions found for {issue_key}"
        
        # Detailed format
        if detailed:
            output = f"🔄 Transitions for {issue_key}:\n{'='*50}\n"
            for t in transitions:
                output += f"ID: {t.get('id')} | {t.get('name')} → {t.get('to', {}).get('name')}\n"
            return output
        
        # Simple format
        issue_data = jira.get_issue(issue_key.strip())
        current_status = issue_data.get('fields', {}).get('status', {}).get('name', 'Unknown') if issue_data else 'Unknown'
        output = f"📋 {issue_key} - Current: {current_status}\nAvailable transitions:\n"
        for idx, t in enumerate(transitions, 1):
            output += f"{idx}. {t.get('to', {}).get('name')}\n"
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    logger.info("🚀 Starting DevMind Unified MCP Server")
    logger.info("📦 Tools: 21 (Jira: 13, Oracle: 2, SVN: 4, SVN Path: 2)")
    logger.info("✨ Optimized and consolidated for production use")
    mcp.run()
