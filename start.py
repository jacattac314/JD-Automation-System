#!/usr/bin/env python3
"""
JD Automation System - One-Click Startup

Run this script to start everything:
    python start.py
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print startup banner."""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════╗
    ║          JD Automation System                     ║
    ║    Transform Job Descriptions into Projects       ║
    ╚═══════════════════════════════════════════════════╝
{Colors.END}""")

def check_python_version():
    """Check Python version."""
    print(f"{Colors.CYAN}[1/5]{Colors.END} Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"{Colors.GREEN}✓ Python {version.major}.{version.minor}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ Python 3.10+ required (found {version.major}.{version.minor}){Colors.END}")
        return False

def check_dependencies():
    """Check required dependencies."""
    print(f"{Colors.CYAN}[2/5]{Colors.END} Checking dependencies...", end=" ")
    required = ['fastapi', 'uvicorn', 'PyGithub']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.lower().replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"{Colors.YELLOW}Installing: {', '.join(missing)}{Colors.END}")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + missing)
        print(f"  {Colors.GREEN}✓ Dependencies installed{Colors.END}")
    else:
        print(f"{Colors.GREEN}✓ All dependencies available{Colors.END}")
    return True

def check_env_file():
    """Check for .env file."""
    print(f"{Colors.CYAN}[3/5]{Colors.END} Checking configuration...", end=" ")
    env_path = Path(".env")
    env_example = Path(".env.example")
    
    if env_path.exists():
        print(f"{Colors.GREEN}✓ .env file found{Colors.END}")
    elif env_example.exists():
        import shutil
        shutil.copy(env_example, env_path)
        print(f"{Colors.YELLOW}Created .env from template (configure API keys){Colors.END}")
    else:
        print(f"{Colors.YELLOW}No .env file (API keys can be set in UI){Colors.END}")
    return True

def create_directories():
    """Ensure required directories exist."""
    print(f"{Colors.CYAN}[4/5]{Colors.END} Setting up directories...", end=" ")
    dirs = ["data", "logs", "projects"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print(f"{Colors.GREEN}✓ Directories ready{Colors.END}")
    return True

def start_server():
    """Start the API server."""
    print(f"{Colors.CYAN}[5/5]{Colors.END} Starting API server...", end=" ")
    
    # Start server in background
    server_path = Path("api/server.py")
    if not server_path.exists():
        print(f"{Colors.RED}✗ Server file not found{Colors.END}")
        return None
    
    # Start uvicorn
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.server:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent)
    )
    
    # Wait for server to start
    time.sleep(2)
    
    if process.poll() is None:
        print(f"{Colors.GREEN}✓ Server running{Colors.END}")
        return process
    else:
        print(f"{Colors.RED}✗ Server failed to start{Colors.END}")
        return None

def open_browser():
    """Open browser to UI."""
    url = "http://127.0.0.1:8000/"
    print(f"\n{Colors.BOLD}Opening browser...{Colors.END}")
    print(f"  {Colors.CYAN}🌐 UI:{Colors.END} {url}")
    print(f"  {Colors.CYAN}📚 API Docs:{Colors.END} {url}docs")
    webbrowser.open(url)

def main():
    """Main entry point."""
    print_banner()
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Run checks
    if not check_python_version():
        sys.exit(1)
    
    check_dependencies()
    check_env_file()
    create_directories()
    
    process = start_server()
    if not process:
        print(f"\n{Colors.RED}Failed to start. Try running manually:{Colors.END}")
        print(f"  python -m uvicorn api.server:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    
    open_browser()
    
    print(f"""
{Colors.GREEN}{Colors.BOLD}✓ JD Automation System is running!{Colors.END}

{Colors.CYAN}Quick Start:{Colors.END}
  1. Go to Settings and enter your API keys
  2. Click "New Run" to start
  3. Paste a job description
  4. Watch the magic happen!

{Colors.YELLOW}Press Ctrl+C to stop the server{Colors.END}
""")
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}Shutting down...{Colors.END}")
        process.terminate()
        print(f"{Colors.GREEN}Goodbye!{Colors.END}")

if __name__ == "__main__":
    main()
