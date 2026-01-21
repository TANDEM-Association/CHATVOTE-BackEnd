#!/usr/bin/env python3
"""
Full initialization script for the wahl.chat project.

This script checks the configuration and initializes all services:
1. Check environment variables
2. Create Pinecone indexes
3. Initialize Firebase Firestore
4. Import German parties

Usage:
    poetry run python scripts/setup_all.py

    # With French parties
    poetry run python scripts/setup_all.py --france
"""

import os
import sys
from pathlib import Path

def check_env_vars():
    """Check that all environment variables are configured."""

    print("🔍 Checking environment variables...\n")

    required_vars = {
        "PINECONE_API_KEY": "Pinecone API key",
        "OPENAI_API_KEY": "OpenAI API key",
    }

    optional_vars = {
        "FIREBASE_CREDENTIALS_PATH": "Path to Firebase credentials",
        "PERPLEXITY_API_KEY": "Perplexity API key",
        "AZURE_OPENAI_API_KEY": "Azure OpenAI API key",
        "GOOGLE_API_KEY": "Google Gemini API key",
    }

    missing = []
    present = []

    # Required variables
    print("📋 Required variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var} : {'*' * 10}{value[-4:]}")
            present.append(var)
        else:
            print(f"  ❌ {var} : NOT CONFIGURED")
            missing.append(var)

    # Optional variables
    print("\n📋 Optional variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if var == "FIREBASE_CREDENTIALS_PATH":
                print(f"  ✓ {var} : {value}")
            else:
                print(f"  ✓ {var} : {'*' * 10}{value[-4:]}")
        else:
            print(f"  ⚠️  {var} : Not configured")

    # Check Firebase file
    firebase_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "wahl-chat-dev-firebase-adminsdk.json")
    print("\n📄 Firebase file:")
    if Path(firebase_path).exists():
        print(f"  ✓ {firebase_path} exists")
    else:
        print(f"  ❌ {firebase_path} does not exist")
        missing.append("FIREBASE_CREDENTIALS")

    print("\n" + "="*70)

    if missing:
        print(f"❌ {len(missing)} missing variable(s): {', '.join(missing)}")
        print("\n💡 To configure environment variables:")
        print("   1. Copy .env.example to .env")
        print("   2. Edit .env with your API keys")
        print("   3. Restart the Docker container")
        return False
    else:
        print("✅ All required variables are configured!")
        return True

def run_script(script_path: str, description: str):
    """Run a script and display the result."""

    print(f"\n{'='*70}")
    print(f"📝 {description}")
    print(f"{'='*70}\n")

    import subprocess

    result = subprocess.run(
        ["python", script_path],
        capture_output=False,
        text=True
    )

    if result.returncode == 0:
        print(f"\n✅ {description} : SUCCESS")
        return True
    else:
        print(f"\n❌ {description} : FAILED (code {result.returncode})")
        return False

def main():
    """Initialize all services."""

    import argparse

    parser = argparse.ArgumentParser(description="Full initialization for the wahl.chat project")
    parser.add_argument("--france", action="store_true", help="Also import French parties")
    parser.add_argument("--skip-check", action="store_true", help="Skip environment variable checks")

    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║           FULL INITIALIZATION OF THE WAHL.CHAT PROJECT               ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    # Check configuration
    if not args.skip_check:
        if not check_env_vars():
            print("\n⚠️  Incomplete configuration. Continue anyway? (y/N)")
            response = input().strip().lower()
            if response != 'y':
                print("\n❌ Initialization canceled.")
                return 1

    # Scripts to run
    scripts_dir = Path(__file__).parent

    scripts = [
        (scripts_dir / "init_pinecone.py", "Create Pinecone indexes"),
        (scripts_dir / "init_firestore.py", "Initialize Firebase Firestore"),
        (scripts_dir / "import_parties.py", "Import German parties"),
    ]

    if args.france:
        scripts.append(
            (scripts_dir / "france" / "import_french_parties.py", "Import French parties")
        )

    # Run scripts
    results = []
    for script_path, description in scripts:
        if script_path.exists():
            success = run_script(str(script_path), description)
            results.append((description, success))
        else:
            print(f"\n⚠️  Script {script_path.name} not found, skipped.")
            results.append((description, False))

    # Summary
    print("\n" + "="*70)
    print("📊 INITIALIZATION SUMMARY")
    print("="*70 + "\n")

    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"\n{'='*70}")
    print(f"Result: {success_count}/{total_count} steps succeeded")

    if success_count == total_count:
        print("\n✅ FULL INITIALIZATION SUCCEEDED!")
        print("\n🚀 Next steps:")
        print("   1. Import election programs:")
        print("      poetry run python scripts/import_programs.py --all")
        print("   2. Start the application:")
        print("      poetry run python src/main.py")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count} step(s) failed")
        print("\n💡 Check:")
        print("   - Environment variables (.env)")
        print("   - API keys (Pinecone, Firebase, OpenAI)")
        print("   - Internet connection")
        print("   - The logs above for more details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
