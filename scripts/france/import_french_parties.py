#!/usr/bin/env python3
"""
Import French political parties into Firestore.

This script imports data for French political parties into Firestore
for the 2027 legislative elections.

Usage:
    poetry run python scripts/france/import_french_parties.py
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# French party data for the 2027 legislative elections
FRENCH_PARTIES = [
    # Left
    {
        "party_id": "lfi",
        "name": "LFI",
        "long_name": "La France Insoumise",
        "description": "Radical left party",
        "website_url": "https://lafranceinsoumise.fr",
        "candidate": "Jean-Luc Mélenchon",
        "is_small_party": False
    },
    {
        "party_id": "ps",
        "name": "PS",
        "long_name": "Parti Socialiste",
        "description": "Social democratic party",
        "website_url": "https://www.parti-socialiste.fr",
        "candidate": "Olivier Faure",
        "is_small_party": False
    },
    {
        "party_id": "eelv",
        "name": "EELV",
        "long_name": "Europe Écologie Les Verts",
        "description": "Green party",
        "website_url": "https://www.eelv.fr",
        "candidate": "Marine Tondelier",
        "is_small_party": False
    },
    {
        "party_id": "pcf",
        "name": "PCF",
        "long_name": "Parti Communiste Français",
        "description": "Communist party",
        "website_url": "https://www.pcf.fr",
        "candidate": "Fabien Roussel",
        "is_small_party": False
    },

    # Center
    {
        "party_id": "renaissance",
        "name": "Renaissance",
        "long_name": "Renaissance",
        "description": "Centrist liberal party (ex-LREM)",
        "website_url": "https://www.renaissance-en-marche.fr",
        "candidate": "Emmanuel Macron / Gabriel Attal",
        "is_small_party": False
    },
    {
        "party_id": "modem",
        "name": "MoDem",
        "long_name": "Mouvement Démocrate",
        "description": "Centrist party",
        "website_url": "https://www.modem.fr",
        "candidate": "François Bayrou",
        "is_small_party": False
    },
    {
        "party_id": "horizons",
        "name": "Horizons",
        "long_name": "Horizons",
        "description": "Center-right party",
        "website_url": "https://www.horizons.fr",
        "candidate": "Édouard Philippe",
        "is_small_party": False
    },

    # Right
    {
        "party_id": "lr",
        "name": "LR",
        "long_name": "Les Républicains",
        "description": "Conservative right-wing party",
        "website_url": "https://www.republicains.fr",
        "candidate": "Éric Ciotti / Laurent Wauquiez",
        "is_small_party": False
    },
    {
        "party_id": "udi",
        "name": "UDI",
        "long_name": "Union des Démocrates et Indépendants",
        "description": "Center-right party",
        "website_url": "https://www.udi.fr",
        "candidate": "Collective",
        "is_small_party": True
    },

    # Far right
    {
        "party_id": "rn",
        "name": "RN",
        "long_name": "Rassemblement National",
        "description": "Nationalist far-right party",
        "website_url": "https://www.rassemblementnational.fr",
        "candidate": "Marine Le Pen / Jordan Bardella",
        "is_small_party": False
    },
    {
        "party_id": "reconquete",
        "name": "Reconquête",
        "long_name": "Reconquête",
        "description": "Far-right party",
        "website_url": "https://www.reconquete.fr",
        "candidate": "Éric Zemmour",
        "is_small_party": False
    },

    # Other
    {
        "party_id": "dlf",
        "name": "DLF",
        "long_name": "Debout la France",
        "description": "Sovereigntist right-wing party",
        "website_url": "https://www.debout-la-france.fr",
        "candidate": "Nicolas Dupont-Aignan",
        "is_small_party": True
    },
    {
        "party_id": "liot",
        "name": "LIOT",
        "long_name": "Libertés, Indépendants, Outre-mer et Territoires",
        "description": "Centrist parliamentary group",
        "website_url": "",
        "candidate": "Collective",
        "is_small_party": True
    }
]

def import_french_parties():
    """Import French political parties into Firestore."""

    # Path to credentials file
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "wahl-chat-dev-firebase-adminsdk.json")

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}")

    # Initialize Firebase
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialized
        pass

    # Get Firestore reference
    db = firestore.client()

    print(f"📝 Importing {len(FRENCH_PARTIES)} French political parties...\n")

    # Import each party
    for party in FRENCH_PARTIES:
        party_id = party["party_id"]

        # Check if the party already exists
        doc_ref = db.collection("parties").document(party_id)
        existing = doc_ref.get()

        if existing.exists:
            print(f"⚠️  Party '{party['name']}' already exists, updating...")
        else:
            print(f"✓ Importing party '{party['name']}'...")

        # Add/update the party
        doc_ref.set(party)

    print(f"\n✅ {len(FRENCH_PARTIES)} French parties imported successfully!")
    print("\nAvailable parties:")

    # Display by category
    print("\n🔴 Left:")
    for party in FRENCH_PARTIES:
        if party["party_id"] in ["lfi", "ps", "eelv", "pcf"]:
            print(f"  - {party['name']} ({party['party_id']})")

    print("\n🟡 Center:")
    for party in FRENCH_PARTIES:
        if party["party_id"] in ["renaissance", "modem", "horizons"]:
            print(f"  - {party['name']} ({party['party_id']})")

    print("\n🔵 Right:")
    for party in FRENCH_PARTIES:
        if party["party_id"] in ["lr", "udi"]:
            print(f"  - {party['name']} ({party['party_id']})")

    print("\n⚫ Far right:")
    for party in FRENCH_PARTIES:
        if party["party_id"] in ["rn", "reconquete"]:
            print(f"  - {party['name']} ({party['party_id']})")

    print("\n⚪ Other:")
    for party in FRENCH_PARTIES:
        if party["party_id"] in ["dlf", "liot"]:
            print(f"  - {party['name']} ({party['party_id']})")

    print("\n💡 Next steps:")
    print("  1. Collect election programs")
    print("  2. Run scripts/import_programs.py to index them")
    print("  3. Scrape National Assembly votes")

if __name__ == "__main__":
    try:
        import_french_parties()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
