"""
Setup script for JD Automation System.
Helps users get started quickly.
"""

import os
import sys
from pathlib import Path
import subprocess

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_python_version():
    """Check if Python version is adequate."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
        return False

def check_git():
    """Check if git is installed."""
    print("📦 Checking Git installation...")
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("   ✗ Git not found")
    return False

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    dirs = ["data", "logs", "projects"]
    for dir_name in dirs:
        path = Path(dir_name)
        path.mkdir(exist_ok=True)
        print(f"   ✓ {dir_name}/")

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    print("   This may take a few minutes...\n")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("\n   ✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("\n   ✗ Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file if it doesn't exist."""
    print("⚙️  Setting up configuration...")
    
    env_path = Path(".env")
    env_example = Path(".env.example")
    
    if env_path.exists():
        print("   ℹ️  .env file already exists")
        return
    
    if env_example.exists():
        import shutil
        shutil.copy(env_example, env_path)
        print("   ✓ Created .env from template")
        print("   ⚠️  Remember to add your API keys to .env")
    else:
        print("   ✗ .env.example not found")

def run_tests():
    """Run basic tests."""
    print("🧪 Running tests...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✓ All tests passed")
            return True
        else:
            print("   ⚠️  Some tests failed (this may be OK if APIs aren't configured)")
            return True  # Don't fail setup
    except Exception as e:
        print(f"   ℹ️  Could not run tests: {e}")
        return True  # Don't fail setup

def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete! 🎉")
    
    print("Next steps:")
    print()
    print("1. Configure your API keys:")
    print("   python -m cli.main setup")
    print()
    print("2. Try the demo (no API keys needed):")
    print("   python demo.py")
    print()
    print("3. Run your first automation:")
    print("   python -m cli.main run --jd-file examples/sample_jd.txt")
    print()
    print("4. View documentation:")
    print("   - README.md - Project overview")
    print("   - QUICKSTART.md - Usage guide")
    print("   - ARCHITECTURE.md - Design details")
    print()
    print("Need help? Check the documentation or open an issue!")
    print()

def main():
    """Run setup."""
    print_header("JD Automation System - Setup")
    
    print("This script will set up your environment.\n")
    
    # Check prerequisites
    if not check_python_version():
        print("\n❌ Setup failed: Python 3.10+ required")
        return 1
    
    if not check_git():
        print("\n⚠️  Warning: Git not found. You'll need it for GitHub integration.")
    
    print()
    
    # Create directories
    create_directories()
    print()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        return 1
    print()
    
    # Create .env
    create_env_file()
    print()
    
    # Run tests
    run_tests()
    print()
    
    # Show next steps
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
