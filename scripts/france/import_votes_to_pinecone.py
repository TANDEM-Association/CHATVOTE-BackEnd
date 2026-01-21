#!/usr/bin/env python3
"""
Import National Assembly votes into Pinecone.

This script imports votes collected from the National Assembly
into the Pinecone index 'justified-voting-behavior-index'.

Usage:
    poetry run python scripts/france/import_votes_to_pinecone.py
    poetry run python scripts/france/import_votes_to_pinecone.py --file data/votes/legislature_16.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict

# Add parent folder to path to import from src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def import_votes_to_pinecone(votes_file: str, index_name: str = "justified-voting-behavior-index"):
    """
    Import votes into Pinecone.

    Args:
        votes_file: Path to the JSON file with votes
        index_name: Pinecone index name
    """

    try:
        from pinecone import Pinecone
        from openai import OpenAI
        from scripts.france.utils import convert_groupe_to_party_id, format_date_french
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure dependencies are installed: poetry install")
        return False

    # Check environment variables
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not pinecone_api_key:
        print("❌ Environment variable PINECONE_API_KEY not found")
        return False

    if not openai_api_key:
        print("❌ Environment variable OPENAI_API_KEY not found")
        return False

    # Load votes
    print(f"📄 Loading votes from {votes_file}...")

    if not Path(votes_file).exists():
        print(f"❌ File {votes_file} not found")
        return False

    with open(votes_file, 'r', encoding='utf-8') as f:
        votes = json.load(f)

    print(f"  ✓ {len(votes)} votes loaded")

    # Initialize Pinecone
    print(f"\n📝 Connecting to Pinecone...")
    pc = Pinecone(api_key=pinecone_api_key)

    # Check that the index exists
    if index_name not in pc.list_indexes().names():
        print(f"❌ Index '{index_name}' not found in Pinecone")
        print("💡 Create the index first with: poetry run python scripts/init_pinecone.py")
        return False

    index = pc.Index(index_name)
    print(f"  ✓ Connected to index '{index_name}'")

    # Initialize OpenAI for embeddings
    print(f"\n📝 Initializing OpenAI...")
    client = OpenAI(api_key=openai_api_key)

    # Prepare documents for indexing
    print(f"\n📝 Preparing documents...")

    documents = []

    for vote in votes:
        scrutin_id = vote.get("scrutin_id", "")
        date = vote.get("date", "")
        title = vote.get("title", "")
        subject = vote.get("subject", "")
        vote_type = vote.get("type", "")

        # Results by group
        group_results = vote.get("group_results", {})

        # Create a document per parliamentary group
        for groupe, results in group_results.items():
            # Convert group to party_id
            party_id = convert_groupe_to_party_id(groupe)

            if not party_id:
                continue

            # Build document text
            text = f"""Ballot no. {scrutin_id} - {format_date_french(date)}
Title: {title}
Subject: {subject}
Type: {vote_type}

Parliamentary group: {groupe}
For: {results.get('pour', 0)}
Against: {results.get('contre', 0)}
Abstentions: {results.get('abstentions', 0)}
"""

            # Metadata
            metadata = {
                "party_id": party_id,
                "scrutin_id": scrutin_id,
                "date": date,
                "title": title[:500],  # Limit size
                "subject": subject[:500],
                "type": vote_type,
                "groupe": groupe,
                "pour": results.get('pour', 0),
                "contre": results.get('contre', 0),
                "abstentions": results.get('abstentions', 0),
                "source": "assemblee_nationale",
            }

            documents.append({
                "text": text,
                "metadata": metadata,
                "id": f"{party_id}-scrutin-{scrutin_id}"
            })

    print(f"  ✓ {len(documents)} documents prepared")

    # Generate embeddings and index
    print(f"\n📝 Generating embeddings and indexing...")

    batch_size = 100
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_num = i // batch_size + 1

        print(f"  📦 Batch {batch_num}/{total_batches} ({len(batch)} documents)...")

        # Generate embeddings
        texts = [doc["text"] for doc in batch]

        try:
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=texts
            )

            embeddings = [item.embedding for item in response.data]

            # Prepare vectors for Pinecone
            vectors = []
            for doc, embedding in zip(batch, embeddings):
                vectors.append({
                    "id": doc["id"],
                    "values": embedding,
                    "metadata": doc["metadata"]
                })

            # Index in Pinecone
            # Use the party namespace
            for vector in vectors:
                party_id = vector["metadata"]["party_id"]
                index.upsert(
                    vectors=[vector],
                    namespace=party_id
                )

            print(f"    ✓ Batch {batch_num}/{total_batches} indexed")

        except Exception as e:
            print(f"    ❌ Batch {batch_num} error: {e}")
            continue

    print(f"\n✅ {len(documents)} votes imported into Pinecone!")

    # Show stats
    print(f"\n📊 Index statistics:")
    stats = index.describe_index_stats()
    print(f"  Total vectors: {stats.total_vector_count}")
    print(f"  Namespaces: {len(stats.namespaces)}")
    for namespace, info in stats.namespaces.items():
        print(f"    - {namespace}: {info.vector_count} vectors")

    return True

def main():
    """Script entry point."""

    parser = argparse.ArgumentParser(
        description="Import National Assembly votes into Pinecone"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="data/votes/legislature_16.json",
        help="Path to the JSON file with votes"
    )
    parser.add_argument(
        "--index",
        type=str,
        default="justified-voting-behavior-index",
        help="Pinecone index name"
    )

    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║      IMPORTING NATIONAL ASSEMBLY VOTES INTO PINECONE                ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝\n")

    try:
        success = import_votes_to_pinecone(args.file, args.index)

        if success:
            print("\n✅ Import completed successfully!")
            return 0
        else:
            print("\n❌ Import failed")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
