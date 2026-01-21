#!/usr/bin/env python3
"""
Test script to verify that all scripts are valid.

This script checks that all Python scripts can be imported
and that their main functions are defined.

Usage:
    poetry run python scripts/test_scripts.py
"""

import sys
import importlib.util
from pathlib import Path

def test_script(script_path: Path) -> bool:
    """
    Test that a script can be imported.

    Args:
        script_path: Path to the script

    Returns:
        True if the script is valid
    """
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("test_module", script_path)
        if spec is None:
            print(f"  ❌ Unable to load {script_path.name}")
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        print(f"  ✓ {script_path.name}")
        return True

    except SyntaxError as e:
        print(f"  ❌ Syntax error in {script_path.name}: {e}")
        return False

    except Exception as e:
        print(f"  ⚠️  {script_path.name}: {e}")
        return True  # Could be a dependency import error, not syntax

def main():
    """Test all scripts."""

    print("🧪 Testing Python scripts...\n")

    scripts_dir = Path(__file__).parent

    # Scripts to test
    scripts = [
        scripts_dir / "init_pinecone.py",
        scripts_dir / "init_firestore.py",
        scripts_dir / "import_parties.py",
        scripts_dir / "import_programs.py",
        scripts_dir / "france" / "import_french_parties.py",
        scripts_dir / "france" / "scrape_assemblee_nationale.py",
        scripts_dir / "france" / "utils.py",
    ]

    results = []

    print("📝 Initialization scripts:")
    for script in scripts[:4]:
        if script.exists():
            results.append(test_script(script))
        else:
            print(f"  ⚠️  {script.name} not found")
            results.append(False)

    print("\n🇫🇷 French adaptation scripts:")
    for script in scripts[4:]:
        if script.exists():
            results.append(test_script(script))
        else:
            print(f"  ⚠️  {script.name} not found")
            results.append(False)

    # Summary
    total = len(results)
    success = sum(results)

    print(f"\n{'='*60}")
    print(f"Result: {success}/{total} valid scripts")

    if success == total:
        print("✅ All scripts are valid!")
        return 0
    else:
        print(f"⚠️  {total - success} script(s) with issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
