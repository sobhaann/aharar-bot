#!/usr/bin/env python
"""
Aharar Charity Bot - Implementation Verification Script

This script verifies that all components of the bot are properly installed
and configured.
"""

import sys
from pathlib import Path
import importlib.util


def check_python_version() -> bool:
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_files() -> bool:
    """Check if all required files exist."""
    required_files = [
        "main.py",
        "config.py",
        "database.py",
        "handlers.py",
        "scheduler.py",
        "models.py",
        "utils.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "README.md",
    ]

    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_exist = False

    return all_exist


def check_modules() -> bool:
    """Check if required Python modules can be imported."""
    required_modules = {
        "telegram": "python-telegram-bot",
        "pydantic": "pydantic",
        "pytz": "pytz",
        "openpyxl": "openpyxl",
        "reportlab": "reportlab",
    }

    all_available = True
    for module, package in required_modules.items():
        try:
            importlib.import_module(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_available = False

    return all_available


def check_env() -> bool:
    """Check .env file."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file - NOT FOUND (create from .env.example)")
        return False


def main() -> None:
    """Run all checks."""
    print("=" * 50)
    print("Aharar Charity Bot - Verification")
    print("=" * 50)

    print("\n📦 Checking Python version...")
    version_ok = check_python_version()

    print("\n📁 Checking required files...")
    files_ok = check_files()

    print("\n📚 Checking Python modules...")
    modules_ok = check_modules()

    print("\n🔐 Checking configuration...")
    env_ok = check_env()

    print("\n" + "=" * 50)
    if all([version_ok, files_ok, env_ok]):
        if modules_ok:
            print("✅ All checks passed! Bot is ready to run.")
            print("\nTo start the bot:")
            print("  1. Edit .env with your BOT_TOKEN and ADMIN_CHAT_ID")
            print("  2. Run: python main.py")
        else:
            print("⚠️  Missing Python packages.")
            print("Install them with: pip install -r requirements.txt")
    else:
        print("❌ Some checks failed. See details above.")
    print("=" * 50)


if __name__ == "__main__":
    main()
