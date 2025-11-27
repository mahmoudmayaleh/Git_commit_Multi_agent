#!/usr/bin/env python3
"""
Quick Start Script

This script helps you get started quickly by checking dependencies
and guiding you through the setup process.
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_python_version():
    """Check if Python version is adequate."""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, you have {sys.version}")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_git():
    """Check if Git is installed."""
    print("Checking Git installation...")
    
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git not found. Please install Git.")
        return False


def check_dependencies():
    """Check if required Python packages are installed."""
    print("Checking Python dependencies...")
    
    required = [
        "GitPython",
        "requests",
        "python-dotenv",
        "transformers",
        "torch"
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def check_env_file():
    """Check if .env file exists."""
    print("Checking configuration...")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        print("❌ .env file not found")
        
        if env_example_path.exists():
            print("\nCreate .env file:")
            print("  copy .env.example .env")
            print("\nThen edit .env with your settings.")
        
        return False
    
    print("✓ .env file found")
    return True


def run_example():
    """Run the example script."""
    print("\nWould you like to run the example script? (y/n): ", end="")
    response = input().lower()
    
    if response in ['y', 'yes']:
        print("\nRunning example...")
        subprocess.run([sys.executable, "tests/example_usage.py"])


def main():
    """Main function."""
    print_header("Git Commit Writer Pipeline - Quick Start")
    
    checks = [
        ("Python Version", check_python_version),
        ("Git Installation", check_git),
        ("Python Dependencies", check_dependencies),
        ("Configuration File", check_env_file)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print_header("✓ All Checks Passed!")
        print("You're ready to use the pipeline!\n")
        print("Usage:")
        print("  1. Stage your changes:  git add .")
        print("  2. Run the pipeline:    python main.py")
        print("  3. Or run example:      python tests/example_usage.py")
        
        run_example()
    else:
        print_header("❌ Some Checks Failed")
        print("Please fix the issues above before using the pipeline.")
    
    print()


if __name__ == "__main__":
    main()
