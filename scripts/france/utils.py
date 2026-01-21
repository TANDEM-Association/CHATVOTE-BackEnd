#!/usr/bin/env python3
"""
Utilities for the French adaptation.

This module contains helper functions for adapting the system
to the French political context.
"""

from datetime import datetime
from typing import Dict

# Mapping of French party names
PARTY_NAME_MAPPING = {
    # La France Insoumise
    "La France Insoumise": "lfi",
    "LFI": "lfi",
    "France Insoumise": "lfi",

    # Parti Socialiste
    "Parti Socialiste": "ps",
    "PS": "ps",
    "Socialiste": "ps",

    # Europe Ecologie Les Verts
    "Europe Écologie Les Verts": "eelv",
    "EELV": "eelv",
    "Les Verts": "eelv",
    "Écologistes": "eelv",

    # Parti Communiste Francais
    "Parti Communiste Français": "pcf",
    "PCF": "pcf",
    "Communiste": "pcf",

    # Renaissance
    "Renaissance": "renaissance",
    "La République En Marche": "renaissance",
    "LREM": "renaissance",
    "En Marche": "renaissance",
    "LaREM": "renaissance",

    # MoDem
    "Mouvement Démocrate": "modem",
    "MoDem": "modem",
    "Modem": "modem",

    # Horizons
    "Horizons": "horizons",

    # Les Republicains
    "Les Républicains": "lr",
    "LR": "lr",
    "Républicains": "lr",
    "UMP": "lr",  # Former name

    # UDI
    "Union des Démocrates et Indépendants": "udi",
    "UDI": "udi",

    # Rassemblement National
    "Rassemblement National": "rn",
    "RN": "rn",
    "Front National": "rn",  # Former name
    "FN": "rn",

    # Reconquete
    "Reconquête": "reconquete",
    "Reconquete": "reconquete",

    # Debout la France
    "Debout la France": "dlf",
    "DLF": "dlf",

    # LIOT
    "Libertés, Indépendants, Outre-mer et Territoires": "liot",
    "LIOT": "liot",
}

# Mapping of parliamentary groups to parties
GROUPE_TO_PARTY = {
    "RE": "renaissance",           # Renaissance
    "LFI-NUPES": "lfi",           # LFI-NUPES
    "RN": "rn",                   # Rassemblement National
    "LR": "lr",                   # Les Republicains
    "SOC": "ps",                  # Socialists
    "ECOLO": "eelv",              # Ecologists
    "LIOT": "liot",               # LIOT
    "HOR": "horizons",            # Horizons
    "GDR": "pcf",                 # Democratic and Republican Left
    "MODEM": "modem",             # MoDem
    "NI": "non_inscrit",          # Non-attached
}

def convert_party_short_hand_to_party_id(party_short_hand: str) -> str:
    """
    Convert a party name (short or long) to a party ID.

    Args:
        party_short_hand: Party name (e.g., "LFI", "La France Insoumise")

    Returns:
        Party ID (e.g., "lfi")
    """
    return PARTY_NAME_MAPPING.get(party_short_hand, party_short_hand.lower())

def convert_groupe_to_party_id(groupe: str) -> str:
    """
    Convert a parliamentary group to a party ID.

    Args:
        groupe: Parliamentary group name (e.g., "RE", "LFI-NUPES")

    Returns:
        Party ID (e.g., "renaissance", "lfi")
    """
    return GROUPE_TO_PARTY.get(groupe, groupe.lower())

def format_date_french(date_str: str) -> str:
    """
    Convert a date to French format.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        Date in French format (DD/MM/YYYY)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def format_date_long_french(date_str: str) -> str:
    """
    Convert a date to long French format.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        Date in long French format (e.g., "23 février 2027")
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        # French month names
        mois = [
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"
        ]

        jour = date_obj.day
        mois_nom = mois[date_obj.month - 1]
        annee = date_obj.year

        return f"{jour} {mois_nom} {annee}"
    except ValueError:
        return date_str

def validate_french_response(response: str) -> Dict[str, bool]:
    """
    Validate that a response follows French conventions.

    Args:
        response: Response to validate

    Returns:
        Dict with validation results
    """
    checks = {
        "has_sources": "[" in response and "]" in response,
        "has_markdown": "**" in response or "*" in response,
        "not_empty": len(response.strip()) > 0,
        "reasonable_length": 10 < len(response) < 5000,
    }

    return checks

def detect_language(text: str) -> str:
    """
    Detect the language of a text (simplified).

    Args:
        text: Text to analyze

    Returns:
        Language code ("fr", "de", "en", "unknown")
    """
    # French indicator words
    french_words = ["le", "la", "les", "de", "du", "des", "un", "une", "et", "est", "sont"]

    # German indicator words
    german_words = ["der", "die", "das", "und", "ist", "sind", "ein", "eine"]

    # English indicator words
    english_words = ["the", "and", "is", "are", "a", "an"]

    text_lower = text.lower()

    french_count = sum(1 for word in french_words if f" {word} " in text_lower)
    german_count = sum(1 for word in german_words if f" {word} " in text_lower)
    english_count = sum(1 for word in english_words if f" {word} " in text_lower)

    if french_count > german_count and french_count > english_count:
        return "fr"
    elif german_count > french_count and german_count > english_count:
        return "de"
    elif english_count > french_count and english_count > german_count:
        return "en"
    else:
        return "unknown"

def contains_opinion_words(text: str) -> bool:
    """
    Check whether a text contains opinion words.

    Args:
        text: Text to analyze

    Returns:
        True if the text contains opinion words
    """
    opinion_words = [
        "excellent", "mauvais", "terrible", "génial", "nul",
        "parfait", "catastrophique", "formidable", "horrible",
        "je pense", "je crois", "à mon avis", "selon moi"
    ]

    text_lower = text.lower()
    return any(word in text_lower for word in opinion_words)

# French coalitions
NUPES_PARTIES = ["lfi", "ps", "eelv", "pcf"]
ENSEMBLE_PARTIES = ["renaissance", "modem", "horizons"]
DROITE_PARTIES = ["lr", "udi"]

def get_coalition(party_id: str) -> str:
    """
    Return the coalition for a party.

    Args:
        party_id: Party ID

    Returns:
        Coalition name or "Independent"
    """
    if party_id in NUPES_PARTIES:
        return "NUPES"
    elif party_id in ENSEMBLE_PARTIES:
        return "Ensemble"
    elif party_id in DROITE_PARTIES:
        return "Right"
    else:
        return "Independent"
