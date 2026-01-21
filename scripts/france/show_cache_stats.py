#!/usr/bin/env python3
"""
Show cache and scraping log statistics.

This script displays information about cached HTML pages
and parsing logs from the National Assembly.

Usage:
    poetry run python scripts/france/show_cache_stats.py
    poetry run python scripts/france/show_cache_stats.py --scrutin 1
    poetry run python scripts/france/show_cache_stats.py --clear-cache
"""

import argparse
from pathlib import Path
import json
from datetime import datetime

CACHE_DIR = Path("data/cache/assemblee_nationale")
LOG_DIR = Path("data/logs/assemblee_nationale")

def get_file_size_human(size_bytes: int) -> str:
    """Convert a size in bytes to a readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def show_cache_stats():
    """Show cache statistics."""

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║              CACHE STATISTICS - NATIONAL ASSEMBLY                   ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    if not CACHE_DIR.exists():
        print("❌ Cache folder not found")
        print(f"   Expected path: {CACHE_DIR.absolute()}\n")
        return

    # List cache files
    cache_files = list(CACHE_DIR.glob("*.html"))

    if not cache_files:
        print("📭 No cached files\n")
        return

    print(f"📦 Cache folder: {CACHE_DIR.absolute()}")
    print(f"📊 Number of files: {len(cache_files)}\n")

    # Total size
    total_size = sum(f.stat().st_size for f in cache_files)
    print(f"💾 Total size: {get_file_size_human(total_size)}\n")

    # Group by legislature
    by_legislature = {}
    for f in cache_files:
        # Format: legislature_16_scrutin_1.html
        parts = f.stem.split('_')
        if len(parts) >= 4:
            legislature = parts[1]
            scrutin = parts[3]

            if legislature not in by_legislature:
                by_legislature[legislature] = []

            by_legislature[legislature].append({
                'scrutin': scrutin,
                'file': f,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime)
            })

    # Display by legislature
    print("📋 Files by legislature:\n")
    for legislature in sorted(by_legislature.keys()):
        files = by_legislature[legislature]
        total_leg_size = sum(f['size'] for f in files)

        print(f"  Legislature {legislature}:")
        print(f"    Ballots: {len(files)}")
        print(f"    Size: {get_file_size_human(total_leg_size)}")

        # Show 5 most recent
        recent = sorted(files, key=lambda x: x['modified'], reverse=True)[:5]
        print(f"    Latest ballots:")
        for f in recent:
            print(f"      - Ballot {f['scrutin']} ({get_file_size_human(f['size'])}) - {f['modified'].strftime('%Y-%m-%d %H:%M')}")
        print()

def show_log_stats():
    """Show log statistics."""

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║                LOG STATISTICS - PARSING                             ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    if not LOG_DIR.exists():
        print("❌ Log folder not found")
        print(f"   Expected path: {LOG_DIR.absolute()}\n")
        return

    # List log files
    log_files = list(LOG_DIR.glob("*.log"))

    if not log_files:
        print("📭 No log files\n")
        return

    print(f"📦 Log folder: {LOG_DIR.absolute()}")
    print(f"📊 Number of files: {len(log_files)}\n")

    # Total size
    total_size = sum(f.stat().st_size for f in log_files)
    print(f"💾 Total size: {get_file_size_human(total_size)}\n")

def show_scrutin_details(scrutin_id: str, legislature: int = 16):
    """Show details for a specific ballot."""

    print(f"╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║                                                                      ║")
    print(f"║           BALLOT DETAILS {scrutin_id} - LEGISLATURE {legislature}              ║")
    print(f"║                                                                      ║")
    print(f"╚══════════════════════════════════════════════════════════════════════╝\n")

    # Cache file
    cache_file = CACHE_DIR / f"legislature_{legislature}_scrutin_{scrutin_id}.html"
    log_file = LOG_DIR / f"legislature_{legislature}_scrutin_{scrutin_id}.log"

    print("📄 Cache file:")
    if cache_file.exists():
        size = cache_file.stat().st_size
        modified = datetime.fromtimestamp(cache_file.stat().st_mtime)
        print(f"  ✓ {cache_file.name}")
        print(f"    Size: {get_file_size_human(size)}")
        print(f"    Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"  ❌ Not found: {cache_file.name}")

    print("\n📝 Log file:")
    if log_file.exists():
        size = log_file.stat().st_size
        modified = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"  ✓ {log_file.name}")
        print(f"    Size: {get_file_size_human(size)}")
        print(f"    Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")

        # Display log content
        print(f"\n  Log content:")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                print(f"    {line.rstrip()}")
    else:
        print(f"  ❌ Not found: {log_file.name}")

    print()

def clear_cache():
    """Delete all cache files."""

    print("🗑️  Clearing cache...\n")

    if not CACHE_DIR.exists():
        print("❌ Cache folder not found\n")
        return

    cache_files = list(CACHE_DIR.glob("*.html"))

    if not cache_files:
        print("📭 No files to delete\n")
        return

    print(f"⚠️  You are about to delete {len(cache_files)} file(s) from cache.")
    response = input("Continue? (y/N) ")

    if response.lower() != 'y':
        print("❌ Canceled\n")
        return

    for f in cache_files:
        f.unlink()
        print(f"  ✓ Deleted: {f.name}")

    print(f"\n✅ {len(cache_files)} file(s) deleted\n")

def main():
    """Script entry point."""

    parser = argparse.ArgumentParser(
        description="Show cache and log statistics"
    )
    parser.add_argument(
        "--scrutin",
        type=str,
        help="Show details for a specific ballot"
    )
    parser.add_argument(
        "--legislature",
        type=int,
        default=16,
        help="Legislature number (default: 16)"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Delete all cache files"
    )
    parser.add_argument(
        "--logs-only",
        action="store_true",
        help="Show only log statistics"
    )

    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()
    elif args.scrutin:
        show_scrutin_details(args.scrutin, args.legislature)
    elif args.logs_only:
        show_log_stats()
    else:
        show_cache_stats()
        print()
        show_log_stats()

if __name__ == "__main__":
    main()
