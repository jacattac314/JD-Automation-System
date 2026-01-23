#!/usr/bin/env python3
"""
Bundle Python runtime and dependencies for Electron app distribution.

This script creates a standalone Python distribution that can be bundled
with the Electron app, so users don't need Python installed.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step, total, message):
    """Print formatted step message."""
    print(f"{Colors.CYAN}[{step}/{total}]{Colors.END} {message}")

def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def get_platform_info():
    """Get platform-specific information."""
    sys_platform = platform.system().lower()

    if sys_platform == 'windows':
        return {
            'name': 'windows',
            'python_exe': 'python.exe',
            'pip_exe': 'Scripts/pip.exe'
        }
    elif sys_platform == 'darwin':
        return {
            'name': 'macos',
            'python_exe': 'bin/python3',
            'pip_exe': 'bin/pip3'
        }
    else:  # Linux
        return {
            'name': 'linux',
            'python_exe': 'bin/python3',
            'pip_exe': 'bin/pip3'
        }

def check_python_version():
    """Ensure Python version is compatible."""
    print_step(1, 5, "Checking Python version...")

    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.10+ required (found {version.major}.{version.minor})")
        return False

def install_virtualenv():
    """Install virtualenv if not present."""
    print_step(2, 5, "Checking for virtualenv...")

    try:
        import virtualenv
        print_success("virtualenv available")
        return True
    except ImportError:
        print_warning("Installing virtualenv...")
        subprocess.run([sys.executable, "-m", "pip", "install", "virtualenv"], check=True)
        print_success("virtualenv installed")
        return True

def create_standalone_python(output_dir):
    """Create a standalone Python environment."""
    print_step(3, 5, "Creating standalone Python environment...")

    # Clean up existing directory
    if output_dir.exists():
        print_warning(f"Removing existing directory: {output_dir}")
        shutil.rmtree(output_dir)

    # Create virtual environment
    subprocess.run([
        sys.executable, "-m", "virtualenv",
        "--always-copy",  # Copy files instead of symlinking
        str(output_dir)
    ], check=True)

    print_success(f"Created virtual environment at {output_dir}")
    return True

def install_dependencies(venv_dir, platform_info):
    """Install project dependencies in the virtual environment."""
    print_step(4, 5, "Installing dependencies...")

    # Get pip path
    pip_path = venv_dir / platform_info['pip_exe']

    if not pip_path.exists():
        print_error(f"pip not found at {pip_path}")
        return False

    # Install requirements
    requirements_file = Path(__file__).parent.parent / "requirements.txt"

    if requirements_file.exists():
        print(f"  Installing from {requirements_file}...")
        subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
    else:
        print_warning("requirements.txt not found, installing core dependencies...")
        # Install core dependencies
        core_deps = [
            "fastapi",
            "uvicorn[standard]",
            "PyGithub",
            "python-dotenv",
            "google-generativeai",
            "anthropic"
        ]
        subprocess.run([str(pip_path), "install"] + core_deps, check=True)

    print_success("Dependencies installed")
    return True

def optimize_distribution(venv_dir):
    """Remove unnecessary files to reduce size."""
    print_step(5, 5, "Optimizing distribution size...")

    removed_size = 0

    # Patterns to remove
    patterns_to_remove = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.dist-info/RECORD",
        "**/test",
        "**/tests",
        "**/*.egg-info",
    ]

    for pattern in patterns_to_remove:
        for path in venv_dir.rglob(pattern):
            if path.is_file():
                size = path.stat().st_size
                path.unlink()
                removed_size += size
            elif path.is_dir():
                for file in path.rglob('*'):
                    if file.is_file():
                        removed_size += file.stat().st_size
                shutil.rmtree(path)

    # Convert bytes to MB
    removed_mb = removed_size / (1024 * 1024)
    print_success(f"Removed {removed_mb:.2f} MB of unnecessary files")

    return True

def main():
    """Main bundling process."""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════╗
║     Python Distribution Bundler                   ║
║     for JD Automation System                      ║
╚═══════════════════════════════════════════════════╝
{Colors.END}""")

    # Get platform info
    platform_info = get_platform_info()
    print(f"Platform: {Colors.BOLD}{platform_info['name']}{Colors.END}\n")

    # Output directory
    output_dir = Path(__file__).parent.parent / "python-dist"

    try:
        # Run bundling steps
        if not check_python_version():
            sys.exit(1)

        if not install_virtualenv():
            sys.exit(1)

        if not create_standalone_python(output_dir):
            sys.exit(1)

        if not install_dependencies(output_dir, platform_info):
            sys.exit(1)

        if not optimize_distribution(output_dir):
            sys.exit(1)

        # Calculate final size
        total_size = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
        total_mb = total_size / (1024 * 1024)

        print(f"""
{Colors.GREEN}{Colors.BOLD}
✓ Python distribution created successfully!{Colors.END}

{Colors.CYAN}Output directory:{Colors.END} {output_dir}
{Colors.CYAN}Total size:{Colors.END} {total_mb:.2f} MB

{Colors.YELLOW}Next steps:{Colors.END}
  1. Run: npm install
  2. Build app: npm run build
  3. Find installers in: dist/

{Colors.GREEN}Ready to build your Electron app!{Colors.END}
""")

    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
