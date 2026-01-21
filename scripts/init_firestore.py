#!/usr/bin/env python3
"""
Initialize Firebase Firestore for wahl.chat.

This script initializes the base Firestore structure with required collections.

Usage:
    poetry run python scripts/init_firestore.py
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_firestore():
    """Initialize Firebase Firestore with the base structure."""

    # Path to credentials file
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "wahl-chat-dev-firebase-adminsdk.json")

    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"Firebase credentials file not found: {cred_path}\n"
            f"Download it from Firebase Console > Project Settings > Service Accounts"
        )

    # Initialize Firebase
    print(f"📝 Initializing Firebase with {cred_path}...")
    cred = credentials.Certificate(cred_path)

    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialized
        print("⚠️  Firebase already initialized")

    # Get Firestore reference
    db = firestore.client()

    # Create base collections
    collections = [
        "parties",
        "proposed_questions",
        "cached_answers",
        "llm_status",
        "chat_sessions"
    ]

    print("\n📚 Creating base collections...")
    for collection_name in collections:
        # Check if collection already exists
        docs = db.collection(collection_name).limit(1).get()

        if len(list(docs)) > 0:
            print(f"⚠️  Collection '{collection_name}' already exists")
        else:
            # Create a temporary document to initialize the collection
            # (Firestore does not create empty collections)
            doc_ref = db.collection(collection_name).document("_init")
            doc_ref.set({"initialized": True, "timestamp": firestore.SERVER_TIMESTAMP})
            print(f"✓ Collection '{collection_name}' created")

    print("\n✅ Firestore initialized successfully!")
    print("\nAvailable collections:")
    for collection in collections:
        print(f"  - {collection}")

    print("\n💡 Next steps:")
    print("  1. Run scripts/import_parties.py to import parties")
    print("  2. Run scripts/import_programs.py to import programs")

if __name__ == "__main__":
    try:
        init_firestore()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
