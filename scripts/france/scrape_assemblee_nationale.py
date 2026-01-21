#!/usr/bin/env python3
"""
Scrape National Assembly votes.

This script retrieves vote data from the French National Assembly
and structures it for indexing in Pinecone.

Usage:
    poetry run python scripts/france/scrape_assemblee_nationale.py --scrutin 1234
    poetry run python scripts/france/scrape_assemblee_nationale.py --legislature 16 --all
"""

import argparse
import json
from typing import Dict, List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
import time

# Cache and log configuration
CACHE_DIR = Path("data/cache/assemblee_nationale")
LOG_DIR = Path("data/logs/assemblee_nationale")

def setup_directories():
    """Create required directories for cache and logs."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_path(scrutin_id: str, legislature: int) -> Path:
    """Return the cache file path for a ballot."""
    return CACHE_DIR / f"legislature_{legislature}_scrutin_{scrutin_id}.html"

def get_log_path(scrutin_id: str, legislature: int) -> Path:
    """Return the log file path for a ballot."""
    return LOG_DIR / f"legislature_{legislature}_scrutin_{scrutin_id}.log"

def log_parsing(scrutin_id: str, legislature: int, message: str):
    """Record a parsing log message."""
    log_file = get_log_path(scrutin_id, legislature)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def scrape_voting_behavior_france(scrutin_id: str, legislature: int = 16, use_cache: bool = True) -> Dict:
    """
    Scrape vote data from the National Assembly.

    Args:
        scrutin_id: Ballot number
        legislature: Legislature number (default: 16)
        use_cache: Use cache if available (default: True)

    Returns:
        Dict with vote data
    """

    # Create directories if needed
    setup_directories()

    url = f"https://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/{legislature}/(num)/{scrutin_id}"
    cache_path = get_cache_path(scrutin_id, legislature)

    print(f"📥 Fetching ballot {scrutin_id}...")
    log_parsing(scrutin_id, legislature, f"Scraping start - URL: {url}")

    # Check cache
    html_content = None
    if use_cache and cache_path.exists():
        print(f"  💾 Loading from cache...")
        log_parsing(scrutin_id, legislature, "Loading from cache")
        with open(cache_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        # Download the page
        try:
            print(f"  🌐 Downloading from {url}...")
            log_parsing(scrutin_id, legislature, f"Downloading from {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            html_content = response.text

            # Save to cache
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Compute size and hash
            size_kb = len(html_content) / 1024
            content_hash = hashlib.md5(html_content.encode()).hexdigest()

            print(f"  ✓ Page downloaded ({size_kb:.1f} KB, hash: {content_hash[:8]})")
            log_parsing(scrutin_id, legislature, f"Page downloaded - Size: {size_kb:.1f} KB - Hash: {content_hash}")
            log_parsing(scrutin_id, legislature, f"Cache saved: {cache_path}")

            # Pause to avoid overloading the server
            time.sleep(0.5)

        except requests.RequestException as e:
            error_msg = f"Error fetching page: {e}"
            print(f"  ❌ {error_msg}")
            log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
            return None

    # Parse HTML
    log_parsing(scrutin_id, legislature, "Starting HTML parsing")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract information
    log_parsing(scrutin_id, legislature, "Extracting data...")

    date = extract_date(soup, scrutin_id, legislature)
    title = extract_title(soup, scrutin_id, legislature)
    vote_type = extract_type(soup, scrutin_id, legislature)
    subject = extract_subject(soup, scrutin_id, legislature)
    overall_results = extract_overall_results(soup, scrutin_id, legislature)
    party_results = extract_party_results(soup, scrutin_id, legislature)
    text_url = extract_text_url(soup, scrutin_id, legislature)

    vote_data = {
        "id": scrutin_id,
        "legislature": legislature,
        "url": url,
        "date": date,
        "title": title,
        "type": vote_type,
        "subject": subject,
        "voting_results": {
            "overall": overall_results,
            "by_party": party_results
        },
        "text_url": text_url
    }

    log_parsing(scrutin_id, legislature, f"Extraction finished - Date: {date}, Title: {title[:50] if title else 'N/A'}")
    log_parsing(scrutin_id, legislature, f"Overall results: {overall_results}")
    log_parsing(scrutin_id, legislature, f"Number of groups: {len(party_results) if party_results else 0}")

    return vote_data

def extract_date(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Optional[str]:
    """Extract the vote date."""
    try:
        date_elem = soup.find('div', class_='date-scrutin')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            log_parsing(scrutin_id, legislature, f"Date extracted: {date_text}")
            # Parse French date
            # Expected format: "Mardi 12 janvier 2024"
            return date_text
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Date element not found")
    except Exception as e:
        error_msg = f"Error extracting date: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
    return None

def extract_title(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Optional[str]:
    """Extract the ballot title."""
    try:
        title_elem = soup.find('h1', class_='title-scrutin')
        if title_elem:
            title = title_elem.get_text(strip=True)
            log_parsing(scrutin_id, legislature, f"Title extracted: {title}")
            return title
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Title element not found")
    except Exception as e:
        error_msg = f"Error extracting title: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
    return None

def extract_type(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Optional[str]:
    """Extract the ballot type."""
    try:
        type_elem = soup.find('div', class_='type-scrutin')
        if type_elem:
            vote_type = type_elem.get_text(strip=True)
            log_parsing(scrutin_id, legislature, f"Type extracted: {vote_type}")
            return vote_type
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Type element not found")
    except Exception as e:
        error_msg = f"Error extracting type: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
    return None

def extract_subject(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Optional[str]:
    """Extract the subject of the vote."""
    try:
        subject_elem = soup.find('div', class_='objet-scrutin')
        if subject_elem:
            subject = subject_elem.get_text(strip=True)
            log_parsing(scrutin_id, legislature, f"Subject extracted: {subject[:100]}...")
            return subject
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Subject element not found")
    except Exception as e:
        error_msg = f"Error extracting subject: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
    return None

def extract_overall_results(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Dict:
    """Extract overall results."""
    try:
        results = {
            "pour": 0,
            "contre": 0,
            "abstentions": 0,
            "non_votants": 0
        }

        # Look for results table
        result_table = soup.find('table', class_='resultats')
        if result_table:
            log_parsing(scrutin_id, legislature, "Results table found")
            rows = result_table.find_all('tr')
            log_parsing(scrutin_id, legislature, f"Number of rows in table: {len(rows)}")

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    try:
                        value = int(value)
                        if 'pour' in label:
                            results['pour'] = value
                        elif 'contre' in label:
                            results['contre'] = value
                        elif 'abstention' in label:
                            results['abstentions'] = value
                        elif 'non' in label and 'votant' in label:
                            results['non_votants'] = value
                    except ValueError:
                        pass

            log_parsing(scrutin_id, legislature, f"Overall results extracted: {results}")
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Results table not found")

        return results
    except Exception as e:
        error_msg = f"Error extracting overall results: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
        return {}

def extract_party_results(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Dict:
    """Extract results by parliamentary group."""
    try:
        party_results = {}

        # Look for results by group
        groups_section = soup.find('div', class_='groupes-politiques')
        if groups_section:
            log_parsing(scrutin_id, legislature, "Political groups section found")
            groups = groups_section.find_all('div', class_='groupe')
            log_parsing(scrutin_id, legislature, f"Number of groups found: {len(groups)}")

            for group in groups:
                group_name = group.find('h3')
                if group_name:
                    name = group_name.get_text(strip=True)

                    # Extract group votes
                    votes = {
                        "pour": 0,
                        "contre": 0,
                        "abstentions": 0,
                        "non_votants": 0
                    }

                    vote_details = group.find_all('span', class_='vote-count')
                    for detail in vote_details:
                        # Parse vote details
                        pass

                    party_results[name] = votes
                    log_parsing(scrutin_id, legislature, f"Group extracted: {name} - Votes: {votes}")

            log_parsing(scrutin_id, legislature, f"Total groups extracted: {len(party_results)}")
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Political groups section not found")

        return party_results
    except Exception as e:
        error_msg = f"Error extracting party results: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
        return {}

def extract_text_url(soup: BeautifulSoup, scrutin_id: str, legislature: int) -> Optional[str]:
    """Extract the URL of the voted text."""
    try:
        text_link = soup.find('a', class_='lien-texte')
        if text_link and text_link.get('href'):
            url = text_link['href']
            log_parsing(scrutin_id, legislature, f"Text URL extracted: {url}")
            return url
        else:
            log_parsing(scrutin_id, legislature, "WARNING: Text link not found")
    except Exception as e:
        error_msg = f"Error extracting text URL: {e}"
        print(f"⚠️  {error_msg}")
        log_parsing(scrutin_id, legislature, f"ERROR: {error_msg}")
    return None

def collect_votes_assemblee_nationale(legislature: int = 16, max_scrutins: int = 100, use_cache: bool = True):
    """
    Collect all ballots from a legislature.

    Args:
        legislature: Legislature number
        max_scrutins: Maximum number of ballots to fetch
        use_cache: Use cache if available
    """

    print(f"🔍 Collecting ballots for legislature {legislature}...")
    print(f"  Cache: {'enabled' if use_cache else 'disabled'}")
    print(f"  Cache folder: {CACHE_DIR}")
    print(f"  Logs folder: {LOG_DIR}\n")

    votes = []

    # Fetch ballots (adapt to actual site structure)
    for scrutin_id in range(1, max_scrutins + 1):
        vote_data = scrape_voting_behavior_france(str(scrutin_id), legislature, use_cache)

        if vote_data:
            votes.append(vote_data)
            print(f"  ✓ Ballot {scrutin_id} retrieved")
        else:
            print(f"  ⚠️  Ballot {scrutin_id} not found")

    # Create output folder if needed
    from pathlib import Path
    output_dir = Path("data/votes")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save data
    output_file = output_dir / f"legislature_{legislature}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(votes, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(votes)} ballots collected and saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Scrape National Assembly votes"
    )
    parser.add_argument(
        "--scrutin",
        type=str,
        help="Ballot number to fetch"
    )
    parser.add_argument(
        "--legislature",
        type=int,
        default=16,
        help="Legislature number (default: 16)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all ballots for the legislature"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=100,
        help="Maximum number of ballots to fetch (default: 100)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not use cache (download again)"
    )

    args = parser.parse_args()

    use_cache = not args.no_cache

    try:
        if args.all:
            collect_votes_assemblee_nationale(args.legislature, args.max, use_cache)
        elif args.scrutin:
            vote_data = scrape_voting_behavior_france(args.scrutin, args.legislature, use_cache)
            if vote_data:
                print(json.dumps(vote_data, ensure_ascii=False, indent=2))
        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
