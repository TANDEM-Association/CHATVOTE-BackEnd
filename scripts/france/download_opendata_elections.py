#!/usr/bin/env python3
"""
Download official 2024 legislative election data from data.gouv.fr.

This script uses the official data.gouv.fr API to download data
from the 2024 French legislative elections (first and second rounds).

Sources:
- First round results: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/
- Second round results: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-2nd-tour/
- First round candidates: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-liste-des-candidats-du-1er-tour/
- Second round candidates: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-liste-des-candidats-du-2nd-tour/

Usage:
    poetry run python scripts/france/download_opendata_elections.py --all
    poetry run python scripts/france/download_opendata_elections.py --resultats-tour1
    poetry run python scripts/france/download_opendata_elections.py --candidats-tour1
"""

import argparse
import requests
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime
import hashlib

# Dataset configuration with direct URLs
DATASETS = {
    "resultats_tour1": {
        "name": "First round results",
        "resources": {
            "circonscriptions_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/20240710-171413/resultats-definitifs-par-circonscriptions-legislatives.csv",
            "departements_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/20240710-171330/resultats-definitifs-par-departements.csv",
            "regions_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/20240710-171318/resultats-definitifs-par-regions.csv",
            "communes_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/20240711-075056/resultats-definitifs-par-communes.csv",
        }
    },
    "resultats_tour2": {
        "name": "Second round results",
        "resources": {
            "circonscriptions_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-2nd-tour/20240710-170728/resultats-definitifs-par-circonscription.csv",
            "departements_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-2nd-tour/20240710-170553/resultats-definitifs-par-departement.csv",
            "regions_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-2nd-tour/20240710-170536/resultats-definitifs-par-region.csv",
            "communes_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-2nd-tour/20240710-170606/resultats-definitifs-par-commune.csv",
        }
    },
    "candidats_tour1": {
        "name": "First round candidates",
        "resources": {
            "france_entiere_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-liste-des-candidats-du-1er-tour/20240628-172440/legislatives-2024-candidatures-france-entiere-tour-1-2024-06-28.csv",
        }
    },
    "candidats_tour2": {
        "name": "Second round candidates",
        "resources": {
            "france_entiere_csv": "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-liste-des-candidats-du-2nd-tour/20240705-172440/legislatives-2024-candidatures-france-entiere-tour-2-2024-07-05.csv",
        }
    }
}

# Output directories
DATA_DIR = Path("data/elections_2024")
CACHE_DIR = Path("data/cache/opendata")
LOG_DIR = Path("data/logs/opendata")

def setup_directories():
    """Create required directories."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_download(dataset_name: str, resource_name: str, message: str):
    """Record a log message."""
    log_file = LOG_DIR / f"{dataset_name}_{resource_name}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def get_file_hash(file_path: Path) -> str:
    """Compute SHA1 hash of a file."""
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()

def download_resource(download_url: str, dataset_name: str, resource_name: str, use_cache: bool = True) -> Path:
    """
    Download a resource from data.gouv.fr.

    Args:
        download_url: Direct URL to the CSV file
        dataset_name: Dataset name (for logs)
        resource_name: Resource name (for file name)
        use_cache: Use cache if available

    Returns:
        Path to the downloaded file
    """

    # Output file name
    output_file = DATA_DIR / f"{dataset_name}_{resource_name}"
    # Use URL hash as cache name
    url_hash = hashlib.md5(download_url.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{url_hash}.csv"

    print(f"📥 Downloading: {dataset_name} - {resource_name}")
    log_download(dataset_name, resource_name, f"Download start - URL: {download_url}")

    # Check cache
    if use_cache and cache_file.exists():
        print(f"  💾 Loading from cache...")
        log_download(dataset_name, resource_name, "Loading from cache")

        # Copy from cache
        import shutil
        shutil.copy(cache_file, output_file)

        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ File loaded from cache ({size_mb:.2f} MB)")
        log_download(dataset_name, resource_name, f"File loaded from cache - Size: {size_mb:.2f} MB")

        return output_file

    # Download from direct URL
    try:
        print(f"  🌐 Downloading from data.gouv.fr...")
        log_download(dataset_name, resource_name, f"Downloading from {download_url}")

        # Download file
        print(f"  📦 Downloading file...")
        file_response = requests.get(download_url, stream=True, timeout=60)
        file_response.raise_for_status()

        # Save file
        total_size = 0
        with open(output_file, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        size_mb = total_size / (1024 * 1024)
        file_hash = get_file_hash(output_file)

        print(f"  ✓ File downloaded ({size_mb:.2f} MB, hash: {file_hash[:8]})")
        log_download(dataset_name, resource_name, f"File downloaded - Size: {size_mb:.2f} MB - Hash: {file_hash}")

        # Save to cache
        import shutil
        shutil.copy(output_file, cache_file)
        log_download(dataset_name, resource_name, f"Cache saved: {cache_file}")

        return output_file

    except requests.RequestException as e:
        error_msg = f"Download error: {e}"
        print(f"  ❌ {error_msg}")
        log_download(dataset_name, resource_name, f"ERROR: {error_msg}")
        raise

def download_dataset(dataset_key: str, use_cache: bool = True, format_filter: str = None):
    """
    Download all resources for a dataset.

    Args:
        dataset_key: Dataset key in DATASETS
        use_cache: Use cache if available
        format_filter: Filter by format (csv, xlsx, etc.)
    """

    dataset = DATASETS[dataset_key]
    print(f"\n{'='*70}")
    print(f"📊 Dataset: {dataset['name']}")
    print(f"{'='*70}\n")

    downloaded_files = []

    for resource_name, download_url in dataset['resources'].items():
        # Filter by format if requested
        if format_filter:
            if format_filter not in resource_name:
                continue

        try:
            file_path = download_resource(download_url, dataset_key, resource_name, use_cache)
            downloaded_files.append(file_path)
        except Exception as e:
            print(f"  ⚠️  Download failed: {e}")

    print(f"\n✅ {len(downloaded_files)} file(s) downloaded for {dataset['name']}\n")

    return downloaded_files

def main():
    """Script entry point."""

    parser = argparse.ArgumentParser(
        description="Download official 2024 legislative election data"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all datasets"
    )
    parser.add_argument(
        "--resultats-tour1",
        action="store_true",
        help="Download first round results"
    )
    parser.add_argument(
        "--resultats-tour2",
        action="store_true",
        help="Download second round results"
    )
    parser.add_argument(
        "--candidats-tour1",
        action="store_true",
        help="Download first round candidate list"
    )
    parser.add_argument(
        "--candidats-tour2",
        action="store_true",
        help="Download second round candidate list"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "xlsx"],
        help="Filter by file format"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not use cache (download again)"
    )

    args = parser.parse_args()

    # Create directories
    setup_directories()

    use_cache = not args.no_cache

    print(f"\n🔍 Downloading 2024 legislative election data")
    print(f"  Cache: {'enabled' if use_cache else 'disabled'}")
    print(f"  Output directory: {DATA_DIR.absolute()}")
    print(f"  Cache directory: {CACHE_DIR.absolute()}")
    print(f"  Logs directory: {LOG_DIR.absolute()}\n")

    try:
        if args.all:
            for dataset_key in DATASETS.keys():
                download_dataset(dataset_key, use_cache, args.format)
        else:
            if args.resultats_tour1:
                download_dataset("resultats_tour1", use_cache, args.format)
            if args.resultats_tour2:
                download_dataset("resultats_tour2", use_cache, args.format)
            if args.candidats_tour1:
                download_dataset("candidats_tour1", use_cache, args.format)
            if args.candidats_tour2:
                download_dataset("candidats_tour2", use_cache, args.format)

            if not any([args.resultats_tour1, args.resultats_tour2, args.candidats_tour1, args.candidats_tour2]):
                parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
