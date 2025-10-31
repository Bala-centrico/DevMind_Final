"""
Secure Credentials Manager for Jira API
Handles reading credentials from external files
"""

import configparser
import os
import json
from typing import Optional, Dict, Any


class CredentialsManager:
    """Manages secure credential loading from various sources"""
    
    def __init__(self, credentials_file: str = None):
        """
        Initialize credentials manager with flexible path resolution
        
        Priority order for locating credentials:
        1. Explicit credentials_file parameter
        2. JIRA_CREDENTIALS_PATH environment variable (from MCP config)
        3. User's home directory: ~/.devmind/credentials.ini
        4. Current directory: ./credentials.ini (fallback for backward compatibility)
        
        Args:
            credentials_file: Optional explicit path to credentials file
        """
        self.credentials = {}
        
        # Resolve credentials file path
        self.credentials_file = self._resolve_credentials_path(credentials_file)
        
        # Try to load credentials from available sources
        self._load_credentials()
    
    def _resolve_credentials_path(self, explicit_path: str = None) -> str:
        """
        Resolve the credentials file path using priority order
        
        Args:
            explicit_path: Explicitly provided path (highest priority)
            
        Returns:
            str: Resolved path to credentials file
        """
        # Priority 1: Explicit path provided
        if explicit_path and os.path.exists(explicit_path):
            print(f"✅ Using explicit credentials path: {explicit_path}")
            return explicit_path
        
        # Priority 2: Environment variable (from MCP configuration)
        env_path = os.getenv('JIRA_CREDENTIALS_PATH')
        if env_path:
            if os.path.exists(env_path):
                print(f"✅ Using credentials from JIRA_CREDENTIALS_PATH: {env_path}")
                return env_path
            else:
                print(f"⚠️ JIRA_CREDENTIALS_PATH set but file not found: {env_path}")
        
        # Priority 3: User's home directory
        user_home_path = os.path.join(os.path.expanduser('~'), '.devmind', 'credentials.ini')
        if os.path.exists(user_home_path):
            print(f"✅ Using user credentials: {user_home_path}")
            return user_home_path
        
        # Priority 4: Current directory (backward compatibility)
        current_dir_path = "credentials.ini"
        if os.path.exists(current_dir_path):
            print(f"⚠️ Using credentials from current directory: {current_dir_path}")
            print(f"   Consider moving to user directory: {user_home_path}")
            return current_dir_path
        
        # No file found - return user home path as target for creation
        print(f"ℹ️ No credentials file found. Expected location: {user_home_path}")
        return user_home_path
    
    def _load_credentials(self):
        """Load credentials from available sources in order of preference"""
        # 1. Try to load from INI file
        if os.path.exists(self.credentials_file):
            self._load_from_ini()
            return
        
        # 2. Try to load from JSON file
        json_file = self.credentials_file.replace('.ini', '.json')
        if os.path.exists(json_file):
            self._load_from_json(json_file)
            return
        
        # 3. Try environment variables
        self._load_from_env()
    
    def _load_from_ini(self, ini_file: str = None):
        """Load credentials from INI configuration file"""
        try:
            file_to_load = ini_file or self.credentials_file
            if not os.path.exists(file_to_load):
                print(f"⚠️ Credentials file not found: {file_to_load}")
                return
            
            config = configparser.ConfigParser()
            config.read(file_to_load, encoding='utf-8')
            
            # Load Jira credentials
            if 'jira' in config:
                self.credentials.update({
                    'username': config.get('jira', 'username', fallback=None),
                    'password': config.get('jira', 'password', fallback=None),
                    'api_token': config.get('jira', 'api_token', fallback=None)
                })
            
            # Load Jira settings
            if 'jira_settings' in config:
                self.credentials.update({
                    'base_url': config.get('jira_settings', 'base_url', fallback='https://svil.bansel.it/jira'),
                    'verify_ssl': config.getboolean('jira_settings', 'verify_ssl', fallback=False),
                    'default_issue': config.get('jira_settings', 'default_issue', fallback='PH-198'),
                    'default_project': config.get('jira_settings', 'default_project', fallback='PH'),
                    'download_path': config.get('jira_settings', 'download_path', fallback=None)
                })
            
            print(f"✅ Loaded credentials from {file_to_load}")
            
        except Exception as e:
            print(f"⚠️ Error loading INI file: {e}")
            self._load_from_env()
    
    def _load_from_json(self, json_file: str):
        """Load credentials from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.credentials.update(data)
            print(f"✅ Loaded credentials from {json_file}")
        except Exception as e:
            print(f"⚠️ Error loading JSON file: {e}")
            self._load_from_env()
    
    def _load_from_env(self):
        """Load credentials from environment variables"""
        self.credentials.update({
            'username': os.getenv('JIRA_USERNAME'),
            'password': os.getenv('JIRA_PASSWORD'),
            'api_token': os.getenv('JIRA_API_TOKEN'),
            'base_url': os.getenv('JIRA_BASE_URL', 'https://svil.bansel.it/jira'),
            'verify_ssl': os.getenv('JIRA_VERIFY_SSL', 'False').lower() == 'true',
            'default_issue': os.getenv('DEFAULT_ISSUE_KEY', 'PH-198'),
            'default_project': os.getenv('DEFAULT_PROJECT_KEY', 'PH'),
            'download_path': os.getenv('JIRA_DOWNLOAD_PATH')
        })
        print("📝 Using environment variables for credentials")
    
    def get_username(self) -> Optional[str]:
        """Get Jira username"""
        return self.credentials.get('username')
    
    def get_password(self) -> Optional[str]:
        """Get Jira password"""
        return self.credentials.get('password')
    
    def get_api_token(self) -> Optional[str]:
        """Get Jira API token"""
        return self.credentials.get('api_token')
    
    def get_base_url(self) -> str:
        """Get Jira base URL"""
        return self.credentials.get('base_url', 'https://svil.bansel.it/jira')
    
    def get_verify_ssl(self) -> bool:
        """Get SSL verification setting"""
        return self.credentials.get('verify_ssl', False)
    
    def get_default_issue(self) -> str:
        """Get default issue key"""
        return self.credentials.get('default_issue', 'PH-198')
    
    def get_default_project(self) -> str:
        """Get default project key"""
        return self.credentials.get('default_project', 'PH')
    
    def get_download_path(self) -> Optional[str]:
        """Get default download path for attachments"""
        return self.credentials.get('download_path')
    
    def has_credentials(self) -> bool:
        """Check if valid credentials are available"""
        username = self.get_username()
        return username and (self.get_password() or self.get_api_token())
    
    def get_auth_method(self) -> str:
        """Get the authentication method being used"""
        if self.get_api_token():
            return "API Token"
        elif self.get_password():
            return "Password"
        else:
            return "None"
    
    def prompt_for_missing_credentials(self):
        """Prompt user for any missing credentials"""
        if not self.get_username():
            username = input("Enter Jira username: ").strip()
            if username:
                self.credentials['username'] = username
        
        if not self.get_api_token() and not self.get_password():
            print("\nChoose authentication method:")
            print("1. API Token (recommended)")
            print("2. Password")
            choice = input("Enter choice (1 or 2): ").strip()
            
            if choice == "1":
                api_token = input("Enter API token: ").strip()
                if api_token:
                    self.credentials['api_token'] = api_token
            else:
                import getpass
                password = getpass.getpass("Enter password: ")
                if password:
                    self.credentials['password'] = password
    
    def prompt_for_issue_key(self, allow_default=True):
        """
        Prompt user for issue key with optional default
        
        Args:
            allow_default (bool): Whether to show and allow default value
            
        Returns:
            str: The issue key to use
        """
        default_issue = self.get_default_issue()
        
        if allow_default and default_issue:
            user_input = input(f"Enter issue key (default: {default_issue}): ").strip()
            return user_input if user_input else default_issue
        else:
            while True:
                user_input = input("Enter issue key (e.g., PH-198): ").strip()
                if user_input:
                    return user_input
                print("❌ Issue key cannot be empty. Please try again.")
    
    def save_credentials_template(self, filename: str = "credentials.ini.template"):
        """Save a template credentials file"""
        template_content = """# Jira Credentials Configuration
# Copy this file to 'credentials.ini' and fill in your actual credentials
# DO NOT commit the actual credentials.ini file to version control

[jira]
username = your-username-here
password = your-password-here
# api_token = your-api-token-here  # Use this instead of password (recommended)

[jira_settings]
base_url = https://svil.bansel.it/jira
verify_ssl = False
default_issue = PH-198
default_project = PH
download_path = C:\\Users\\GBS05273\\Downloads
"""
        with open(filename, 'w') as f:
            f.write(template_content)
        print(f"📄 Created credentials template: {filename}")
    
    def display_credentials_status(self):
        """Display current credentials status (without showing actual values)"""
        print("\n📊 Credentials Status:")
        print(f"Username: {'✅ Set' if self.get_username() else '❌ Missing'}")
        print(f"Password: {'✅ Set' if self.get_password() else '❌ Missing'}")
        print(f"API Token: {'✅ Set' if self.get_api_token() else '❌ Missing'}")
        print(f"Auth Method: {self.get_auth_method()}")
        print(f"Base URL: {self.get_base_url()}")
        print(f"SSL Verify: {self.get_verify_ssl()}")
        print(f"Has Valid Credentials: {'✅ Yes' if self.has_credentials() else '❌ No'}")


def create_sample_credentials():
    """Create sample credential files for demonstration"""
    
    # Create INI format
    ini_content = """# Jira Credentials Configuration
# This file contains sensitive information - DO NOT commit to version control

[jira]
username = GBS05273
password = Aug@2025
# api_token = your-api-token-here  # Uncomment and use instead of password

[jira_settings]
base_url = https://svil.bansel.it/jira
verify_ssl = False
default_issue = PH-198
default_project = PH
"""
    
    # Create JSON format alternative
    json_content = {
        "username": "GBS05273",
        "password": "Aug@2025",
        "base_url": "https://svil.bansel.it/jira",
        "verify_ssl": False,
        "default_issue": "PH-198",
        "default_project": "PH"
    }
    
    with open("credentials.ini", "w") as f:
        f.write(ini_content)
    
    with open("credentials.json", "w") as f:
        json.dump(json_content, f, indent=2)
    
    print("✅ Created sample credential files:")
    print("  - credentials.ini (INI format)")
    print("  - credentials.json (JSON format)")


if __name__ == "__main__":
    # Demo usage
    print("Jira Credentials Manager Demo")
    print("=" * 30)
    
    # Test credentials manager
    creds = CredentialsManager()
    creds.display_credentials_status()
    
    if not creds.has_credentials():
        print("\n⚠️ Missing credentials, prompting user...")
        creds.prompt_for_missing_credentials()
        creds.display_credentials_status()