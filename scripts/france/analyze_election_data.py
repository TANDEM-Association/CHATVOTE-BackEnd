#!/usr/bin/env python3
"""
Analyze 2024 legislative election data downloaded from data.gouv.fr.

This script reads and analyzes downloaded CSV files to extract statistics
and prepare data for Pinecone import.

Usage:
    poetry run python scripts/france/analyze_election_data.py --circonscriptions
    poetry run python scripts/france/analyze_election_data.py --candidats
    poetry run python scripts/france/analyze_election_data.py --stats
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime
from collections import Counter

# Directories
DATA_DIR = Path("data/elections_2024")
OUTPUT_DIR = Path("data/processed_elections_2024")

def setup_directories():
    """Create required directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def analyze_circonscriptions_tour1():
    """Analyze first-round results by constituency."""

    print("\n" + "="*70)
    print("📊 ANALYSIS OF RESULTS BY CONSTITUENCY - ROUND 1")
    print("="*70 + "\n")

    file_path = DATA_DIR / "resultats_tour1_circonscriptions_csv"

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print("   Run first: poetry run python scripts/france/download_opendata_elections.py --resultats-tour1")
        return

    print(f"📂 Reading file: {file_path.name}")

    # Read CSV with correct separator (semicolon)
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    print(f"✓ {len(rows)} rows loaded\n")

    if not rows:
        print("❌ No data found")
        return

    # Display columns
    print("📋 Available columns:")
    for i, col in enumerate(rows[0].keys(), 1):
        print(f"  {i}. {col}")

    # Statistics
    circonscriptions = set()
    departements = set()
    for row in rows:
        if 'Code de la circonscription' in row:
            circonscriptions.add(row['Code de la circonscription'])
        if 'Code du département' in row:
            departements.add(row['Code du département'])

    print(f"\n📊 Statistics:")
    print(f"  Number of constituencies: {len(circonscriptions)}")
    print(f"  Number of departments: {len(departements)}")

    # Show sample
    print(f"\n📄 Sample data (first 5 rows):")
    for i, row in enumerate(rows[:5], 1):
        print(f"\n  Row {i}:")
        for key, value in list(row.items())[:10]:  # Limit to 10 columns
            print(f"    {key}: {value}")

    # Save as JSON for analysis
    output_file = OUTPUT_DIR / "circonscriptions_tour1.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Data saved: {output_file}")

def analyze_circonscriptions_tour2():
    """Analyze second-round results by constituency."""

    print("\n" + "="*70)
    print("📊 ANALYSIS OF RESULTS BY CONSTITUENCY - ROUND 2")
    print("="*70 + "\n")

    file_path = DATA_DIR / "resultats_tour2_circonscriptions_csv"

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print("   Run first: poetry run python scripts/france/download_opendata_elections.py --resultats-tour2")
        return

    print(f"📂 Reading file: {file_path.name}")

    # Read CSV with correct separator (semicolon)
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    print(f"✓ {len(rows)} rows loaded\n")

    if not rows:
        print("❌ No data found")
        return

    # Display columns
    print("📋 Available columns:")
    for i, col in enumerate(rows[0].keys(), 1):
        print(f"  {i}. {col}")

    # Statistics
    circonscriptions = set()
    departements = set()
    for row in rows:
        if 'Code de la circonscription' in row:
            circonscriptions.add(row['Code de la circonscription'])
        if 'Code du département' in row:
            departements.add(row['Code du département'])

    print(f"\n📊 Statistics:")
    print(f"  Number of constituencies: {len(circonscriptions)}")
    print(f"  Number of departments: {len(departements)}")

    # Show sample
    print(f"\n📄 Sample data (first 5 rows):")
    for i, row in enumerate(rows[:5], 1):
        print(f"\n  Row {i}:")
        for key, value in list(row.items())[:10]:  # Limit to 10 columns
            print(f"    {key}: {value}")

    # Save as JSON for analysis
    output_file = OUTPUT_DIR / "circonscriptions_tour2.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Data saved: {output_file}")

def analyze_candidats_tour1():
    """Analyze the first-round candidate list."""

    print("\n" + "="*70)
    print("📊 ANALYSIS OF CANDIDATES - ROUND 1")
    print("="*70 + "\n")

    file_path = DATA_DIR / "candidats_tour1_france_entiere_csv"

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print("   Run first: poetry run python scripts/france/download_opendata_elections.py --candidats-tour1")
        return

    print(f"📂 Reading file: {file_path.name}")

    # Read CSV with correct separator (semicolon)
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    print(f"✓ {len(rows)} candidates loaded\n")

    if not rows:
        print("❌ No data found")
        return

    # Display columns
    print("📋 Available columns:")
    for i, col in enumerate(rows[0].keys(), 1):
        print(f"  {i}. {col}")

    # Statistics
    circonscriptions = set()
    for row in rows:
        if 'Code de la circonscription' in row:
            circonscriptions.add(row['Code de la circonscription'])

    print(f"\n📊 Statistics:")
    print(f"  Number of candidates: {len(rows)}")
    print(f"  Number of constituencies: {len(circonscriptions)}")

    # Statistics by party
    if 'Libellé de la nuance' in rows[0]:
        nuances = Counter(row['Libellé de la nuance'] for row in rows)
        print(f"\n📊 Distribution by political label (Top 10):")
        for nuance, count in nuances.most_common(10):
            print(f"  {nuance}: {count} candidates")

    # Show sample
    print(f"\n📄 Sample data (first 5 candidates):")
    for i, row in enumerate(rows[:5], 1):
        print(f"\n  Candidate {i}:")
        for key, value in list(row.items())[:10]:  # Limit to 10 columns
            print(f"    {key}: {value}")

    # Save as JSON for analysis
    output_file = OUTPUT_DIR / "candidats_tour1.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Data saved: {output_file}")

def generate_stats():
    """Generate overall statistics on the data."""

    print("\n" + "="*70)
    print("📊 OVERALL STATISTICS")
    print("="*70 + "\n")

    stats = {
        "timestamp": datetime.now().isoformat(),
        "files": {},
        "summary": {}
    }

    # Check available files
    files_to_check = [
        ("resultats_tour1_circonscriptions_csv", "First round results - constituencies"),
        ("resultats_tour2_circonscriptions_csv", "Second round results - constituencies"),
        ("candidats_tour1_france_entiere_csv", "First round candidates"),
        ("candidats_tour2_france_entiere_csv", "Second round candidates"),
    ]

    for filename, description in files_to_check:
        file_path = DATA_DIR / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            stats["files"][filename] = {
                "description": description,
                "exists": True,
                "size_mb": round(size_mb, 2),
                "path": str(file_path)
            }
            print(f"✓ {description}")
            print(f"  File: {filename}")
            print(f"  Size: {size_mb:.2f} MB\n")
        else:
            stats["files"][filename] = {
                "description": description,
                "exists": False
            }
            print(f"❌ {description}")
            print(f"  File: {filename} (not found)\n")

    # Save stats
    stats_file = OUTPUT_DIR / "stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"✅ Statistics saved: {stats_file}")

def main():
    """Script entry point."""

    parser = argparse.ArgumentParser(
        description="Analyze 2024 legislative election data"
    )
    parser.add_argument(
        "--circonscriptions",
        action="store_true",
        help="Analyze results by constituency (round 1 and 2)"
    )
    parser.add_argument(
        "--candidats",
        action="store_true",
        help="Analyze the candidate list"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Generate overall statistics"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all analyses"
    )

    args = parser.parse_args()

    # Create directories
    setup_directories()

    try:
        if args.all:
            analyze_circonscriptions_tour1()
            analyze_circonscriptions_tour2()
            analyze_candidats_tour1()
            generate_stats()
        else:
            if args.circonscriptions:
                analyze_circonscriptions_tour1()
                analyze_circonscriptions_tour2()
            if args.candidats:
                analyze_candidats_tour1()
            if args.stats:
                generate_stats()

            if not any([args.circonscriptions, args.candidats, args.stats]):
                parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
