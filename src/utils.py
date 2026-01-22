# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import os
from pathlib import Path
from typing import Optional, Union
import re
import logging

from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_core.documents import Document

from openai.types.chat import ChatCompletion
import xxhash

from src.models.chat import Message, Role
from src.models.party import Party
from src.models.assistant import CHATVOTE_ASSISTANT

BASE_DIR = Path(__file__).resolve().parent.parent
EXPECTED_API_NAME = "chatvote-api"

logger = logging.getLogger(__name__)


def load_env():
    """Charge les variables d'environnement depuis le fichier .env si API_NAME n'est pas déjà défini à la valeur attendue."""
    api_name = os.getenv("API_NAME")

    if api_name == EXPECTED_API_NAME:
        return

    if api_name is not None:
        raise ValueError(
            f"La variable d'environnement API_NAME est définie à '{api_name}' mais '{EXPECTED_API_NAME}' est attendu. "
            "Veuillez vérifier votre configuration."
        )

    env_path = BASE_DIR / ".env"
    if env_path.exists():
        print(f"Chargement des variables d'environnement depuis {env_path}...")
        load_dotenv(env_path, override=True)
        print(f"Variables d'environnement chargées depuis {env_path}.")

    api_name = os.getenv("API_NAME")
    if not api_name:
        raise ValueError(
            "La variable d'environnement API_NAME n'est pas définie. Veuillez la définir dans votre environnement ou fichier .env."
        )
    if api_name != EXPECTED_API_NAME:
        raise ValueError(
            f"La variable d'environnement API_NAME est définie à '{api_name}' mais '{EXPECTED_API_NAME}' est attendu. "
            "Veuillez vérifier votre configuration ou fichier .env."
        )


def safe_load_api_key(api_key: str) -> Optional[SecretStr]:
    key = os.getenv(api_key)
    if not key:
        return None
    return SecretStr(key)


def get_cors_allowed_origins(env: Optional[str]) -> Union[str, list[str]]:
    if env == "dev":
        return "*"
    else:
        return [
            "https://chatvote.fr",
            "https://embed.chatvote.fr",
            "https://pre-prod.chatvote.fr",
            "https://dev.chatvote.fr",
            "http://localhost:3000",
            "http://localhost:8080",
        ]


def build_chat_history_string(
    chat_history: list[Message],
    parties: list[Party],
    default_assistant_name=CHATVOTE_ASSISTANT.name,
) -> str:
    chat_history_string = ""
    for i, message in enumerate(chat_history):
        sender = ""
        if message.role == Role.USER:
            sender = "Utilisateur"
        else:
            sending_party = next(
                (party for party in parties if party.party_id == message.party_id),
                None,
            )
            if sending_party:
                sender = sending_party.name
            else:
                sender = default_assistant_name
        chat_history_string += f'{i + 1}. {sender}: "{message.content}"\n'
    return chat_history_string


def build_document_string_for_context(
    doc_num: int, doc: Document, doc_num_label="ID"
) -> str:
    return f"""{doc_num_label}: {doc_num}
- Nom du document: {doc.metadata.get("document_name", "inconnu")}
- Date de publication: {doc.metadata.get("document_publish_date", "inconnue")}
- Contenu: "{doc.page_content}"

"""


def build_party_str(party: Party):
    return f"""ID: {party.party_id}
- Nom court: {party.name}
- Nom complet: {party.long_name}
- Description: {party.description}
- Tête de liste pour les élections municipales: {party.candidate}
- Représenté au conseil municipal actuel: {party.is_already_in_parliament}
"""


def build_message_from_perplexity_response(response: ChatCompletion) -> Message:
    logger.debug(f"Processing raw perplexity response: {response}")
    # construct a source dict from response citations
    sources = []
    # type ignore because citations actually exists but is not typed
    for link in response.citations:  # type: ignore
        sources.append({"source": link})

    # postprocess perplexity response
    response_text = response.choices[0].message.content

    # give sources addition space before "[id]" -> " [id-1]" or "[id_1, id_2, ...]" --> " [id_1 - 1, id_2 - 1, ...]"
    def replacement(match):
        source_numbers = match.group(1).replace(", ", ",").split(",")
        new_ids = [int(num) - 1 for num in source_numbers]
        new_ids_str = ", ".join([str(num) for num in new_ids])
        # Return the modified string with a space in front
        return f" [{new_ids_str}]"

    # Match patterns like [1], [3], [5] or [1, 2, 3]
    sources_pattern = r"\[((\d+|(\d+, ))*)\]"
    response_text = re.sub(sources_pattern, replacement, response_text or "")
    logger.debug(f"Processed perplexity response text: {response_text}")

    return Message(role=Role.ASSISTANT, content=response_text, sources=sources)


def sanitize_references(text: str) -> str:
    # GPT 4o-mini sometimes references with [id1], [<1>], ... instead of [1]
    # This function sanitizes the references to [1], [2], ... by removing any non-numeric characters from the reference

    def sanitize_citatoin(match):
        content = match.group(1)
        cleaned_content = re.sub(r"[^0-9, ]", "", content)
        return f"[{cleaned_content}]"

    citations_pattern = r"\[(.*?)\]"

    sanitized_text = re.sub(citations_pattern, sanitize_citatoin, text)
    return sanitized_text


if __name__ == "__main__":
    text = """Die Grünen setzen sich für **gute Arbeit** und **faire Löhne** für Fabrikarbeiter ein. Sie wollen:

- **Faire Mindestlöhne**: Ein Mindestlohn von zunächst **15 Euro** im Jahr 2025, der auch für unter 18-Jährige gilt, um die Inflation auszugleichen. [id1]
- **Stärkung der Mitbestimmung**: Die betriebliche Mitbestimmung soll gestärkt werden, um Beschäftigten mehr Einfluss auf ihre Arbeitsbedingungen zu geben. [<2>]
- **Schutz vor Missbrauch**: Gegen Schein-Selbstständigkeit und den Missbrauch von Werkverträgen soll entschieden vorgegangen werden. [id2, id3]

Diese Maßnahmen zielen darauf ab, die Arbeitsbedingungen und die soziale Absicherung für Fabrikarbeiter zu verbessern.
"""
    sanitized_text = sanitize_references(text)
    print(sanitized_text)


def get_chat_history_hash_key(conversation_history_str: str) -> str:
    return xxhash.xxh64(conversation_history_str).hexdigest()
