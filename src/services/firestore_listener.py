# SPDX-FileCopyrightText: 2025 chatvote
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""
Firestore listener service.

Listens to changes in the parties collection and triggers manifesto indexation
when a party is added or modified.
"""

import asyncio
import logging
from typing import Optional, Callable

from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.watch import ChangeType

from src.firebase_service import db
from src.models.party import Party
from src.services.manifesto_indexer import index_party_manifesto

logger = logging.getLogger(__name__)

# Track which parties have been indexed to avoid duplicate work
_indexed_manifesto_urls: dict[str, str] = {}
_listener_unsubscribe: Optional[Callable] = None
_is_running = False
_main_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _on_parties_snapshot(doc_snapshots, changes, read_time) -> None:
    """
    Callback for Firestore listener on parties collection.

    Triggers indexation when a party is added or modified.
    Note: This runs in a separate thread, not the main asyncio event loop.
    """
    for change in changes:
        doc: DocumentSnapshot = change.document
        party_id = doc.id

        if change.type == ChangeType.REMOVED:
            logger.info(f"Party {party_id} was removed")
            # Optionally: delete from Qdrant
            if party_id in _indexed_manifesto_urls:
                del _indexed_manifesto_urls[party_id]
            continue

        # ADDED or MODIFIED
        try:
            party_data = doc.to_dict()
            if not party_data:
                continue

            # Remove party_id from data if present (we use doc.id as party_id)
            party_data.pop("party_id", None)
            party = Party(party_id=party_id, **party_data)
            manifesto_url = party.election_manifesto_url

            # Check if we need to re-index
            if not manifesto_url:
                logger.debug(f"Party {party_id} has no manifesto URL, skipping")
                continue

            # Only re-index if the manifesto URL changed
            if _indexed_manifesto_urls.get(party_id) == manifesto_url:
                logger.debug(f"Party {party_id} manifesto URL unchanged, skipping")
                continue

            action = "Added" if change.type == ChangeType.ADDED else "Modified"
            logger.info(
                f"{action} party detected: {party_id}, triggering indexation..."
            )

            # Schedule indexation in the main event loop (thread-safe)
            if _main_event_loop is not None:
                asyncio.run_coroutine_threadsafe(
                    _index_party_async(party), _main_event_loop
                )
            else:
                logger.warning(
                    f"No event loop available, skipping indexation for {party_id}"
                )

        except Exception as e:
            logger.error(f"Error processing party change for {party_id}: {e}")


async def _index_party_async(party: Party) -> None:
    """Index a party's manifesto asynchronously."""
    try:
        count = await index_party_manifesto(party)
        if count > 0:
            _indexed_manifesto_urls[party.party_id] = party.election_manifesto_url
            logger.info(f"Indexed {count} chunks for party {party.party_id}")
        else:
            logger.warning(f"No chunks indexed for party {party.party_id}")
    except Exception as e:
        logger.error(f"Failed to index party {party.party_id}: {e}")


def start_parties_listener(
    event_loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """
    Start listening to the parties collection in Firestore.

    Args:
        event_loop: The main asyncio event loop to use for async tasks.
                   If not provided, will try to get the running loop.

    This should be called once at application startup.
    """
    global _listener_unsubscribe, _is_running, _main_event_loop

    if _is_running:
        logger.warning("Parties listener is already running")
        return

    # Store reference to the event loop for thread-safe async execution
    _main_event_loop = event_loop

    logger.info("Starting Firestore listener for parties collection...")

    try:
        parties_ref = db.collection("parties")
        _listener_unsubscribe = parties_ref.on_snapshot(_on_parties_snapshot)
        _is_running = True
        logger.info("Firestore listener started successfully")
    except Exception as e:
        logger.error(f"Failed to start Firestore listener: {e}")
        raise


def stop_parties_listener() -> None:
    """Stop the Firestore listener."""
    global _listener_unsubscribe, _is_running, _main_event_loop

    if _listener_unsubscribe:
        _listener_unsubscribe()
        _listener_unsubscribe = None
        _is_running = False
        _main_event_loop = None
        logger.info("Firestore listener stopped")


def is_listener_running() -> bool:
    """Check if the listener is currently running."""
    return _is_running
