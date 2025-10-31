"""
DevMind System - Complete Service Launcher
Date: October 31, 2025
Version: 1.0.0

This script starts all required services for the DevMind system:
1. Monitoring Service (Port 5002)
2. Backend API (Port 8001)
3. Dashboard (Port 3000)
"""

import subprocess
import time
import sys
import os
import signal
import socket
from pathlib import Path
from typing import List, Tuple, Optional

# ANSI Color codes for Windows
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Base paths
BASE_PATH = Path(r"C:\CentricoINshared\DevMind_Final")
BACKEND_PATH = BASE_PATH / "Backend"
SERVICES_PATH = BASE_PATH / "Services"
DASHBOARD_PATH = BASE_PATH / "Dashboard"

# Process tracking
processes: List[subprocess.Popen] = []

def print_header():
    """Print startup header"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  DevMind System - Complete Service Launcher{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_step(step: int, message: str):
    """Print step message"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}Step {step}: {message}{Colors.ENDC}")

def check_directory(path: Path, name: str) -> bool:
    """Check if directory exists"""
    if not path.exists():
        print_error(f"{name} directory not found at {path}")
        return False
    print_success(f"{name} directory found: {path}")
    return True

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def check_port_availability(port: int, service_name: str) -> bool:
    """Check if port is available"""
    if is_port_in_use(port):
        print_warning(f"Port {port} is already in use by another process")
        response = input(f"Do you want to continue anyway? (y/n): ").lower()
        if response != 'y':
            return False
    else:
        print_success(f"Port {port} is available for {service_name}")
    return True

def start_service(
    name: str, 
    command: List[str], 
    cwd: Path, 
    port: int,
    env: Optional[dict] = None
) -> bool:
    """Start a service in a new terminal window"""
    try:
        print_info(f"Starting {name} on port {port}...")
        
        # Create environment with NODE_OPTIONS for Dashboard
        service_env = os.environ.copy()
        if env:
            service_env.update(env)
        
        # Build environment string for cmd
        env_str = ""
        if env:
            for key, value in env.items():
                env_str += f"set {key}={value} && "
        
        # On Windows, use 'start' command to open new terminal
        if sys.platform == 'win32':
            # Prepare command for Windows
            cmd_str = ' '.join(command)
            
            # Build the full command string
            startup_cmd = f'cd /d "{cwd}" && echo === {name} === && {env_str}{cmd_str}'
            
            # Use subprocess to call 'start' with proper escaping
            # The /B flag starts without creating new window (we want window, so don't use it)
            full_command = f'start "{name}" cmd /k "{startup_cmd}"'
            
            # Execute using shell
            result = subprocess.run(
                full_command,
                shell=True,
                cwd=str(cwd),
                env=service_env
            )
            
            if result.returncode == 0:
                print_success(f"{name} terminal window opened successfully")
                return True
            else:
                print_error(f"Failed to open terminal for {name}")
                return False
        else:
            # For Unix-like systems
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                env=service_env
            )
            processes.append(process)
            print_success(f"{name} started successfully (PID: {process.pid})")
            return True
        
    except Exception as e:
        print_error(f"Failed to start {name}: {e}")
        return False

def cleanup_processes(signum=None, frame=None):
    """Cleanup function - note: processes run in separate windows"""
    print(f"\n\n{Colors.WARNING}Closing launcher...{Colors.ENDC}")
    print_info("Services are running in separate terminal windows")
    print_info("Close each terminal window to stop individual services")
    
    for process in processes:
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                print_info(f"Terminated process (PID: {process.pid})")
        except Exception as e:
            pass  # Ignore errors for detached processes
    
    sys.exit(0)

def wait_for_startup(port: int, service_name: str, timeout: int = 30) -> bool:
    """Wait for a service to start listening on its port"""
    print_info(f"Waiting for {service_name} to start...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            print_success(f"{service_name} is now running on port {port}")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    
    print()
    print_warning(f"{service_name} did not start within {timeout} seconds")
    return False

def main():
    """Main function to start all services"""
    print_header()
    
    # Register cleanup handler
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)
    
    # Step 1: Verify directories
    print_step(1, "Verifying directory structure")
    
    if not check_directory(BASE_PATH, "DevMind_Final"):
        return
    if not check_directory(BACKEND_PATH, "Backend"):
        return
    if not check_directory(SERVICES_PATH, "Services"):
        return
    if not check_directory(DASHBOARD_PATH, "Dashboard"):
        return
    
    # Step 2: Check port availability
    print_step(2, "Checking port availability")
    
    ports = [
        (5002, "Monitoring Service"),
        (8001, "Backend API"),
        (3000, "Dashboard")
    ]
    
    for port, service in ports:
        if not check_port_availability(port, service):
            print_error(f"Cannot proceed - port {port} is required for {service}")
            return
    
    # Step 3: Start Monitoring Service
    print_step(3, "Starting Monitoring Service")
    monitoring_success = start_service(
        name="DevMind - Monitoring Service",
        command=['python', 'monitoring_service.py'],
        cwd=SERVICES_PATH,
        port=5002
    )
    
    if not monitoring_success:
        print_error("Failed to start Monitoring Service")
        return
    
    # Wait a bit for monitoring service to initialize
    time.sleep(2)
    
    # Step 4: Start Backend API
    print_step(4, "Starting Backend API")
    backend_success = start_service(
        name="DevMind - Backend API",
        command=['python', 'main.py'],
        cwd=BACKEND_PATH,
        port=8001
    )
    
    if not backend_success:
        print_error("Failed to start Backend API")
        return
    
    # Wait for backend to initialize
    time.sleep(2)
    
    # Step 5: Start Dashboard
    print_step(5, "Starting React Dashboard")
    dashboard_success = start_service(
        name="DevMind - Dashboard",
        command=['npm', 'start'],
        cwd=DASHBOARD_PATH,
        port=3000,
        env={'NODE_OPTIONS': '--openssl-legacy-provider'}
    )
    
    if not dashboard_success:
        print_error("Failed to start Dashboard")
        return
    
    # Step 6: Display status
    print_step(6, "Service Status Summary")
    print(f"\n{Colors.OKGREEN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}  All Services Started Successfully!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*60}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}📋 Service Endpoints:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Monitoring Service:{Colors.ENDC} http://localhost:5002")
    print(f"  {Colors.OKCYAN}• Backend API:{Colors.ENDC}        http://localhost:8001")
    print(f"  {Colors.OKCYAN}• Dashboard:{Colors.ENDC}          http://localhost:3000")
    
    print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  Note about VS Code Extension:{Colors.ENDC}")
    print(f"  The VS Code extension must be started manually:")
    print(f"  1. Open VS Code")
    print(f"  2. Extension should auto-start (port 8765)")
    print(f"  3. Check Output panel → 'Copilot Bridge'")
    
    print(f"\n{Colors.BOLD}🔍 Useful Commands:{Colors.ENDC}")
    print(f"  {Colors.OKBLUE}Check ports:{Colors.ENDC} netstat -ano | findstr \"5002 8001 3000\"")
    print(f"  {Colors.OKBLUE}API Health:{Colors.ENDC}  curl http://localhost:8001/health")
    print(f"  {Colors.OKBLUE}Monitor:{Colors.ENDC}     curl http://localhost:5002/api/health")
    
    # Wait a bit before opening browser
    print(f"\n{Colors.OKGREEN}Opening Dashboard in browser in 5 seconds...{Colors.ENDC}")
    time.sleep(5)
    
    # Open dashboard in browser
    try:
        if sys.platform == 'win32':
            os.system('start http://localhost:3000')
        elif sys.platform == 'darwin':
            os.system('open http://localhost:3000')
        else:
            os.system('xdg-open http://localhost:3000')
    except Exception as e:
        print_warning(f"Could not open browser automatically: {e}")
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ DevMind System is now running!{Colors.ENDC}")
    print(f"{Colors.WARNING}Press Ctrl+C to stop all services{Colors.ENDC}\n")
    
    # Keep script running
    try:
        while True:
            time.sleep(1)
            # Check if any process has died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print_error(f"Service process {i} (PID: {process.pid}) has stopped unexpectedly")
    except KeyboardInterrupt:
        cleanup_processes()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        cleanup_processes()
