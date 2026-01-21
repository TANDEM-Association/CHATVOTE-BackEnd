#!/usr/bin/env python3
"""
Import political parties into Firestore.

This script imports data for German political parties into Firestore.

Usage:
    poetry run python scripts/import_parties.py
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# German party data for Bundestagswahl 2025
GERMAN_PARTIES = [
    {
        "party_id": "cdu",
        "name": "CDU",
        "long_name": "Christlich Demokratische Union Deutschlands",
        "description": "Conservative and Christian democratic party",
        "website_url": "https://www.cdu.de",
        "candidate": "Friedrich Merz",
        "election_manifesto_url": "https://www.cdu.de/regierungsprogramm",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    {
        "party_id": "spd",
        "name": "SPD",
        "long_name": "Sozialdemokratische Partei Deutschlands",
        "description": "Social democratic party",
        "website_url": "https://www.spd.de",
        "candidate": "Olaf Scholz",
        "election_manifesto_url": "https://www.spd.de/zukunftsprogramm",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    {
        "party_id": "gruene",
        "name": "Grune",
        "long_name": "Bundnis 90/Die Grunen",
        "description": "Green party",
        "website_url": "https://www.gruene.de",
        "candidate": "Robert Habeck",
        "election_manifesto_url": "https://www.gruene.de/wahlprogramm",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    {
        "party_id": "fdp",
        "name": "FDP",
        "long_name": "Freie Demokratische Partei",
        "description": "Liberal party",
        "website_url": "https://www.fdp.de",
        "candidate": "Christian Lindner",
        "election_manifesto_url": "https://www.fdp.de/wahlprogramm",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    {
        "party_id": "linke",
        "name": "Die Linke",
        "long_name": "Die Linke",
        "description": "Left-wing party",
        "website_url": "https://www.die-linke.de",
        "candidate": "Heidi Reichinnek / Jan van Aken",
        "election_manifesto_url": "https://www.die-linke.de/wahlprogramm",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    {
        "party_id": "afd",
        "name": "AfD",
        "long_name": "Alternative fur Deutschland",
        "description": "Nationalist right-wing party",
        "website_url": "https://www.afd.de",
        "candidate": "Alice Weidel",
        "election_manifesto_url": "https://www.afd.de/wahlprogramm",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    {
        "party_id": "bsw",
        "name": "BSW",
        "long_name": "Bundnis Sahra Wagenknecht",
        "description": "Conservative left party",
        "website_url": "https://www.bsw-vg.de",
        "candidate": "Sahra Wagenknecht",
        "election_manifesto_url": "https://www.bsw-vg.de/wahlprogramm",
        "is_small_party": False,
        "is_already_in_parliament": False
    },
    {
        "party_id": "fw",
        "name": "Freie Wahler",
        "long_name": "Freie Wahler",
        "description": "Centrist regionalist party",
        "website_url": "https://www.freiewaehler.eu",
        "candidate": "Hubert Aiwanger",
        "election_manifesto_url": "https://www.freiewaehler.eu/wahlprogramm",
        "is_small_party": True,
        "is_already_in_parliament": False
    },
    {
        "party_id": "volt",
        "name": "Volt",
        "long_name": "Volt Deutschland",
        "description": "Pro-European progressive party",
        "website_url": "https://www.voltdeutschland.org",
        "candidate": "Collective",
        "election_manifesto_url": "https://www.voltdeutschland.org/wahlprogramm",
        "is_small_party": True,
        "is_already_in_parliament": False
    },
    {
        "party_id": "tierschutzpartei",
        "name": "Tierschutzpartei",
        "long_name": "Partei Mensch Umwelt Tierschutz",
        "description": "Animal protection party",
        "website_url": "https://www.tierschutzpartei.de",
        "candidate": "Collective",
        "election_manifesto_url": "https://www.tierschutzpartei.de/wahlprogramm",
        "is_small_party": True,
        "is_already_in_parliament": False
    },
    {
        "party_id": "piraten",
        "name": "Piraten",
        "long_name": "Piratenpartei Deutschland",
        "description": "Pirate party for digital freedom",
        "website_url": "https://www.piratenpartei.de",
        "candidate": "Collective",
        "election_manifesto_url": "https://www.piratenpartei.de/wahlprogramm",
        "is_small_party": True,
        "is_already_in_parliament": False
    },
    {
        "party_id": "oedp",
        "name": "ODP",
        "long_name": "Okologisch-Demokratische Partei",
        "description": "Conservative green party",
        "website_url": "https://www.oedp.de",
        "candidate": "Collective",
        "election_manifesto_url": "https://www.oedp.de/wahlprogramm",
        "is_small_party": True,
        "is_already_in_parliament": False
    },
    {
        "party_id": "diebasis",
        "name": "dieBasis",
        "long_name": "Basisdemokratische Partei Deutschland",
        "description": "Direct democracy party",
        "website_url": "https://diebasis-partei.de",
        "candidate": "Collective",
        "election_manifesto_url": "https://diebasis-partei.de/wahlprogramm",
        "is_small_party": True,
        "is_already_in_parliament": False
    }
]

def import_parties():
    """Import political parties into Firestore."""

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

    print(f"📝 Importing {len(GERMAN_PARTIES)} political parties...\n")

    # Import each party
    for party in GERMAN_PARTIES:
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

    print(f"\n✅ {len(GERMAN_PARTIES)} parties imported successfully!")
    print("\nAvailable parties:")
    for party in GERMAN_PARTIES:
        print(f"  - {party['name']} ({party['party_id']})")

    print("\n💡 Next step:")
    print("  Run scripts/import_programs.py to import election programs")

if __name__ == "__main__":
    try:
        import_parties()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
