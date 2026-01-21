#!/usr/bin/env python3
"""
Initialize Pinecone indexes for wahl.chat.

This script creates the 3 required indexes:
- all-parties-index: Party programs and documents
- justified-voting-behavior-index: Bundestag voting behavior
- parliamentary-questions-index: Parliamentary questions by party

Usage:
    poetry run python scripts/init_pinecone.py
"""

from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_pinecone_indexes():
    """Create the 3 Pinecone indexes required for wahl.chat."""

    # Initialize Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    pc = Pinecone(api_key=api_key)

    # Index configuration
    indexes_config = [
        {
            "name": "all-parties-index",
            "dimension": 3072,  # text-embedding-3-large
            "metric": "cosine",
            "description": "Party programs and documents"
        },
        {
            "name": "justified-voting-behavior-index",
            "dimension": 3072,
            "metric": "cosine",
            "description": "Bundestag voting behavior with justifications"
        },
        {
            "name": "parliamentary-questions-index",
            "dimension": 3072,
            "metric": "cosine",
            "description": "Parliamentary questions by party"
        }
    ]

    # Create each index
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    for config in indexes_config:
        index_name = config["name"]

        if index_name in existing_indexes:
            print(f"⚠️  Index '{index_name}' already exists, skipped")
            continue

        print(f"📝 Creating index '{index_name}'...")

        pc.create_index(
            name=index_name,
            dimension=config["dimension"],
            metric=config["metric"],
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print(f"✓ Index '{index_name}' created successfully")

    print("\n✅ All Pinecone indexes are ready!")
    print("\nAvailable indexes:")
    for idx in pc.list_indexes():
        print(f"  - {idx.name}")

if __name__ == "__main__":
    try:
        init_pinecone_indexes()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
