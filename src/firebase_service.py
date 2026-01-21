# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import os
from typing import Optional
from pathlib import Path
import firebase_admin
from firebase_admin import firestore, credentials, firestore_async

from src.models.chat import CachedResponse
from src.models.party import Party
from src.utils import load_env

load_env()

DEFAULT_DEV_CREDENTIALS = "wahl-chat-dev-firebase-adminsdk.json"
DEFAULT_PROD_CREDENTIALS = "wahl-chat-firebase-adminsdk.json"


def _resolve_credentials_path() -> Path:
    custom_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if custom_path:
        return Path(custom_path)
    filename = (
        DEFAULT_PROD_CREDENTIALS if os.getenv("ENV") == "prod" else DEFAULT_DEV_CREDENTIALS
    )
    return Path(filename)


credentials_path = _resolve_credentials_path()

# If the credentials file does not exist, use the application default credentials
if credentials_path.exists():
    cred = credentials.Certificate(credentials_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()

db = firestore.client()

async_db = firestore_async.client()


async def aget_parties() -> list[Party]:
    """
    Fetch all parties from Firebase.
    Filters out invalid documents that do not contain required fields.
    """
    parties = async_db.collection("parties").stream()
    valid_parties = []

    async for party_doc in parties:
        party_data = party_doc.to_dict()

        # Check that the document contains required fields
        required_fields = ['party_id', 'name', 'long_name', 'description',
                          'website_url', 'candidate', 'election_manifesto_url']

        if all(field in party_data for field in required_fields):
            try:
                valid_parties.append(Party(**party_data))
            except Exception as e:
                print(f"⚠️  Error loading party {party_doc.id}: {e}")
        else:
            print(
                f"⚠️  Skipping invalid document: {party_doc.id} - Missing fields: "
                f"{[f for f in required_fields if f not in party_data]}"
            )

    return valid_parties


async def aget_party_by_id(party_id: str) -> Optional[Party]:
    party_ref = async_db.collection("parties").document(party_id)
    party = await party_ref.get()
    if party.exists:
        return Party(**party.to_dict())
    return None


async def aget_proposed_questions_for_party(party_id: str) -> list[str]:
    questions = async_db.collection(f"proposed_questions/{party_id}/questions").stream()
    return [question.get("content") async for question in questions]


async def aget_cached_answers_for_party(
    party_id: str, cache_key: str
) -> list[CachedResponse]:
    cached_answers = async_db.collection(
        f"cached_answers/{party_id}/{cache_key}"
    ).stream()
    return [
        CachedResponse(**cached_answer.to_dict())
        async for cached_answer in cached_answers
    ]


async def awrite_cached_answer_for_party(
    party_id: str, cache_key: str, cached_answer: CachedResponse
) -> None:
    cached_answer_ref = async_db.collection(
        f"cached_answers/{party_id}/{cache_key}"
    ).document()
    await cached_answer_ref.set(cached_answer.model_dump())


async def awrite_llm_status(is_at_rate_limit: bool) -> None:
    llm_status_ref = async_db.collection("system_status").document("llm_status")
    await llm_status_ref.set({"is_at_rate_limit": is_at_rate_limit})
