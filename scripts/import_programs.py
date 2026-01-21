#!/usr/bin/env python3
"""
Import election programs into Pinecone.

This script loads election programs (PDFs) and indexes them in Pinecone
for semantic search.

Usage:
    poetry run python scripts/import_programs.py --party cdu --pdf path/to/program.pdf
    poetry run python scripts/import_programs.py --all --data-dir data/programs/
"""

import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# Load environment variables
load_dotenv()

def import_party_program(party_id: str, pdf_path: str, index_name: str = "all-parties-index"):
    """
    Import an election program into Pinecone.

    Args:
        party_id: Party ID (e.g., "cdu", "spd")
        pdf_path: Path to the PDF file
        index_name: Pinecone index name
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    print(f"\n📄 Loading program for {party_id.upper()} from {pdf_path}...")

    # 1. Load the PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"  ✓ {len(documents)} pages loaded")

    # 2. Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    splits = text_splitter.split_documents(documents)
    print(f"  ✓ {len(splits)} chunks created")

    # 3. Add metadata
    for i, split in enumerate(splits):
        split.metadata["party_id"] = party_id
        split.metadata["source"] = pdf_path
        split.metadata["chunk_id"] = i

    # 4. Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(index_name)

    # 5. Create embeddings and index
    print(f"  📝 Indexing in Pinecone (namespace: {party_id})...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace=party_id
    )

    # Index in batches of 100
    batch_size = 100
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i+batch_size]
        vector_store.add_documents(batch)
        print(f"  ✓ Batch {i//batch_size + 1}/{(len(splits)-1)//batch_size + 1} indexed")

    print(f"✅ Program for {party_id.upper()} imported successfully ({len(splits)} chunks)")

def import_all_programs(data_dir: str):
    """
    Import all programs from a folder.

    Expected structure:
    data_dir/
        cdu/program.pdf
        spd/program.pdf
        ...
    """

    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Folder not found: {data_dir}")

    print(f"🔍 Searching for programs in {data_dir}...")

    # Iterate subfolders
    imported = 0
    for party_dir in data_path.iterdir():
        if not party_dir.is_dir():
            continue

        party_id = party_dir.name

        # Find a PDF file
        pdf_files = list(party_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"⚠️  No PDF found for {party_id}")
            continue

        # Take the first PDF found
        pdf_path = pdf_files[0]

        try:
            import_party_program(party_id, str(pdf_path))
            imported += 1
        except Exception as e:
            print(f"❌ Error importing {party_id}: {e}")

    print(f"\n✅ {imported} programs imported successfully!")

def main():
    parser = argparse.ArgumentParser(
        description="Import election programs into Pinecone"
    )
    parser.add_argument(
        "--party",
        type=str,
        help="Party ID (e.g., cdu, spd)"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to the PDF file"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import all programs from a folder"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/programs",
        help="Folder containing programs (default: data/programs)"
    )
    parser.add_argument(
        "--index",
        type=str,
        default="all-parties-index",
        help="Pinecone index name (default: all-parties-index)"
    )

    args = parser.parse_args()

    try:
        if args.all:
            import_all_programs(args.data_dir)
        elif args.party and args.pdf:
            import_party_program(args.party, args.pdf, args.index)
        else:
            parser.print_help()
            print("\n❌ Error: specify --party and --pdf, or --all")
            exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
