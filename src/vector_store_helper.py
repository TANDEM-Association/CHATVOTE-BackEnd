# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import os
import logging
from pathlib import Path
from typing import Optional, Union

from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.models.party import Party

from src.utils import load_env, safe_load_api_key

from src.chatbot_async import rerank_documents

load_env()

logger = logging.getLogger(__name__)

BASE_PATH = Path(__file__).parent
EMBEDDING_SIZE = 3072  # Embedding sizes for the OpenAI models: https://platform.openai.com/docs/guides/embeddings#how-to-get-embeddings
EMBEDDING_MODEL = "text-embedding-3-large"

# Get environment suffix
env = os.getenv("ENV", "dev")
env_suffix = f"_{env}" if env in ["prod", "dev"] else "_dev"

PARTY_INDEX_NAME = f"all_parties{env_suffix}"
VOTING_BEHAVIOR_INDEX_NAME = f"justified_voting_behavior{env_suffix}"
PARLIAMENTARY_QUESTIONS_INDEX_NAME = f"parliamentary_questions{env_suffix}"

_qdrant_client: Optional[QdrantClient] = None
_embed: Optional[OpenAIEmbeddings] = None
_qdrant_config_warned = False
_qdrant_runtime_warned = False
_embed_warned = False


def _qdrant_enabled() -> bool:
    flag = os.getenv("QDRANT_ENABLED")
    if flag is None:
        return True
    return flag.strip().lower() in {"1", "true", "yes", "on"}


def _qdrant_url() -> str:
    url = os.getenv("QDRANT_URL", "").strip()
    if not url:
        return ""
    lowered = url.lower()
    if lowered.startswith("your_") or lowered.startswith("changeme"):
        return ""
    return url


def _ensure_qdrant_client() -> Optional[QdrantClient]:
    global _qdrant_client, _qdrant_config_warned, _qdrant_runtime_warned

    if not _qdrant_enabled():
        if not _qdrant_config_warned:
            logger.info("Qdrant is disabled via QDRANT_ENABLED; vector search is off.")
            _qdrant_config_warned = True
        return None

    url = _qdrant_url()
    if not url:
        if not _qdrant_config_warned:
            logger.info("QDRANT_URL is not set; vector search is off.")
            _qdrant_config_warned = True
        return None

    if _qdrant_client is not None:
        return _qdrant_client

    try:
        _qdrant_client = QdrantClient(
            url=url,
            api_key=os.getenv("QDRANT_API_KEY"),
        )
    except Exception:
        if not _qdrant_runtime_warned:
            logger.warning(
                "Qdrant client initialization failed; vector search is off.",
                exc_info=True,
            )
            _qdrant_runtime_warned = True
        return None

    return _qdrant_client


def _ensure_embed() -> Optional[OpenAIEmbeddings]:
    global _embed, _embed_warned

    if _embed is not None:
        return _embed

    api_key = safe_load_api_key("OPENAI_API_KEY")
    if not api_key:
        if not _embed_warned:
            logger.info("OPENAI_API_KEY is not set; vector search is off.")
            _embed_warned = True
        return None

    try:
        _embed = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=api_key)
    except Exception:
        if not _embed_warned:
            logger.warning(
                "OpenAI embeddings initialization failed; vector search is off.",
                exc_info=True,
            )
            _embed_warned = True
        return None

    return _embed


async def _identify_relevant_documents(
    collection_name: str,
    namespace: str,
    rag_query: str,
    n_docs: int = 5,
    score_threshold: float = 0.5,
) -> list[Document]:
    """
    Identify relevant documents based on the provided query and namespace.
    Uses direct Qdrant client to ensure all metadata is preserved.
    """
    global _embed_warned, _qdrant_runtime_warned

    if _qdrant_runtime_warned:
        return []

    qdrant_client = _ensure_qdrant_client()
    embed = _ensure_embed()
    if qdrant_client is None or embed is None:
        return []

    # Get query vector
    try:
        query_vector = await embed.aembed_query(rag_query)
    except Exception:
        if not _embed_warned:
            logger.warning("Embedding query failed; vector search is off.", exc_info=True)
            _embed_warned = True
        return []

    # Create filter for the namespace
    filter_condition = Filter(
        must=[FieldCondition(key="namespace", match=MatchValue(value=namespace))]
    )

    # Search directly using Qdrant client to preserve all metadata
    # Note: Using sync client in async context - this might need optimization later
    try:
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=("dense", query_vector),
            limit=n_docs,
            with_payload=True,
            query_filter=filter_condition,
            score_threshold=score_threshold,
        )
    except Exception:
        if not _qdrant_runtime_warned:
            logger.warning("Qdrant search failed; vector search is off.", exc_info=True)
            _qdrant_runtime_warned = True
        return []

    # Create LangChain Documents manually to preserve all metadata
    documents = []
    for point in search_result:
        if point.payload is None:
            continue

        # Extract content from text field
        content = point.payload.get("text", "")

        # Extract metadata (everything except text)
        metadata = {k: v for k, v in point.payload.items() if k != "text"}

        # Create Document with proper content and metadata
        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)

    return documents


async def identify_relevant_docs(
    party: Party,
    rag_query: str,
    n_docs: int = 5,
    score_threshold: float = 0.5,
) -> list[Document]:
    return await _identify_relevant_documents(
        collection_name=PARTY_INDEX_NAME,
        namespace=party.party_id,
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )


# relevant docs with reranking
async def identify_relevant_docs_with_reranking(
    party: Party,
    rag_query: str,
    n_docs: int = 20,
    score_threshold: float = 0.5,
) -> list[Document]:
    relevant_docs = await _identify_relevant_documents(
        collection_name=PARTY_INDEX_NAME,
        namespace=party.party_id,
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )

    # For now, return without external reranking since we're moving away from Pinecone
    # TODO: Implement alternative reranking if needed
    return relevant_docs[:5]  # Return top 5 documents


async def identify_relevant_docs_with_llm_based_reranking(
    party: Party,
    rag_query: str,
    chat_history: str,
    user_message: str,
    n_docs: int = 20,
    score_threshold: float = 0.5,
) -> list[Document]:
    relevant_docs = await _identify_relevant_documents(
        collection_name=PARTY_INDEX_NAME,
        namespace=party.party_id,
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )

    # Note: We lose the score information when using direct Qdrant search
    # If score sorting is critical, we could modify _identify_relevant_documents
    # to return scores as well

    if len(relevant_docs) >= 5:
        # get indices of relevant docs
        relevant_docs = await rerank_documents(
            relevant_docs=relevant_docs,
            user_message=user_message,
            chat_history=chat_history,
        )
        return relevant_docs
    else:
        return relevant_docs


async def identify_relevant_votes(
    rag_query: str, n_docs: int = 5, score_threshold: float = 0.5
) -> list[Document]:
    """
    Identify relevant votes based on the provided query.

    :param rag_query: The query to search for relevant documents.
    :param n_docs: The number of documents to return.
    :param score_threshold: The score threshold for the similarity search.
    :return: A list of relevant documents.
    """
    return await _identify_relevant_documents(
        collection_name=VOTING_BEHAVIOR_INDEX_NAME,
        namespace="vote_summary",
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )


async def identify_relevant_parliamentary_questions(
    party: Union[Party, str],
    rag_query: str,
    n_docs: int = 5,
    score_threshold: float = 0.7,
) -> list[Document]:
    """
    Identify relevant parliamentary questions based on the provided query and party.
    """
    namespace = f"{party.party_id if isinstance(party, Party) else party}-parliamentary-questions"
    return await _identify_relevant_documents(
        collection_name=PARLIAMENTARY_QUESTIONS_INDEX_NAME,
        namespace=namespace,
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )
