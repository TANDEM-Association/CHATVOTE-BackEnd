# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

import os
from pathlib import Path
from typing import Union, Optional
import logging

from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    VectorParams,
    Distance,
)
from src.models.party import Party

from src.utils import load_env, safe_load_api_key

from src.chatbot_async import rerank_documents, Responder

load_env()

logger = logging.getLogger(__name__)

BASE_PATH = Path(__file__).parent

# Get environment suffix
env = os.getenv("ENV", "dev")
env_suffix = f"_{env}" if env in ["prod", "dev"] else "_dev"

PARTY_INDEX_NAME = f"all_parties{env_suffix}"
VOTING_BEHAVIOR_INDEX_NAME = f"justified_voting_behavior{env_suffix}"
PARLIAMENTARY_QUESTIONS_INDEX_NAME = f"parliamentary_questions{env_suffix}"

# Embedding dimensions for different providers
GOOGLE_EMBEDDING_DIM = 768  # text-embedding-004
OPENAI_EMBEDDING_DIM = 3072  # text-embedding-3-large


def _get_embeddings() -> tuple[Embeddings, int]:
    """
    Get the embeddings model based on available API keys.
    Prefers Google Embeddings, falls back to OpenAI if available.
    Returns tuple of (embeddings, dimension).
    """
    google_api_key = safe_load_api_key("GOOGLE_API_KEY")
    openai_api_key = safe_load_api_key("OPENAI_API_KEY")

    if google_api_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        logger.info("Using Google Generative AI Embeddings")
        return (
            GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=google_api_key,
            ),
            GOOGLE_EMBEDDING_DIM,
        )

    if openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        logger.info("Using OpenAI Embeddings")
        return (
            OpenAIEmbeddings(
                model="text-embedding-3-large",
                openai_api_key=openai_api_key,
            ),
            OPENAI_EMBEDDING_DIM,
        )

    raise ValueError(
        "No embedding API key found. Please set GOOGLE_API_KEY or OPENAI_API_KEY."
    )


embed, EMBEDDING_DIM = _get_embeddings()

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY"),
)


def _ensure_collection_exists(collection_name: str) -> None:
    """
    Ensure a Qdrant collection exists, creating it if necessary.
    """
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            logger.info(f"Creating Qdrant collection: {collection_name}")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    )
                },
            )
            logger.info(f"Collection {collection_name} created successfully")
        else:
            logger.debug(f"Collection {collection_name} already exists")
    except Exception as e:
        logger.error(f"Error ensuring collection {collection_name} exists: {e}")
        raise


def _get_vector_store(collection_name: str) -> QdrantVectorStore:
    """
    Get or create a Qdrant vector store for the given collection.
    """
    _ensure_collection_exists(collection_name)
    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding=embed,
        vector_name="dense",
        content_payload_key="text",
    )


# Lazy initialization of vector stores
_qdrant_vector_store: Optional[QdrantVectorStore] = None
_voting_behavior_vector_store: Optional[QdrantVectorStore] = None
_parliamentary_questions_vector_store: Optional[QdrantVectorStore] = None


def get_qdrant_vector_store() -> QdrantVectorStore:
    global _qdrant_vector_store
    if _qdrant_vector_store is None:
        _qdrant_vector_store = _get_vector_store(PARTY_INDEX_NAME)
    return _qdrant_vector_store


def get_voting_behavior_vector_store() -> QdrantVectorStore:
    global _voting_behavior_vector_store
    if _voting_behavior_vector_store is None:
        _voting_behavior_vector_store = _get_vector_store(VOTING_BEHAVIOR_INDEX_NAME)
    return _voting_behavior_vector_store


def get_parliamentary_questions_vector_store() -> QdrantVectorStore:
    global _parliamentary_questions_vector_store
    if _parliamentary_questions_vector_store is None:
        _parliamentary_questions_vector_store = _get_vector_store(
            PARLIAMENTARY_QUESTIONS_INDEX_NAME
        )
    return _parliamentary_questions_vector_store


async def _identify_relevant_documents(
    vector_store: QdrantVectorStore,
    namespace: str,
    rag_query: str,
    n_docs: int = 5,
    score_threshold: float = 0.5,
) -> list[Document]:
    """
    Identify relevant documents based on the provided query and namespace.
    Uses direct Qdrant client to ensure all metadata is preserved.
    """
    # Get query vector
    query_vector = await embed.aembed_query(rag_query)

    # Create filter for the namespace
    filter_condition = Filter(
        must=[FieldCondition(key="namespace", match=MatchValue(value=namespace))]
    )

    # Search directly using Qdrant client to preserve all metadata
    # Note: Using sync client in async context - this might need optimization later
    search_result = qdrant_client.search(
        collection_name=vector_store.collection_name,
        query_vector=("dense", query_vector),
        limit=n_docs,
        with_payload=True,
        query_filter=filter_condition,
        score_threshold=score_threshold,
    )

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
        vector_store=get_qdrant_vector_store(),
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
        vector_store=get_qdrant_vector_store(),
        namespace=party.party_id,
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )

    # For now, return without external reranking since we're moving away from Pinecone
    # TODO: Implement alternative reranking if needed
    return relevant_docs[:5]  # Return top 5 documents


async def identify_relevant_docs_with_llm_based_reranking(
    responder: Responder,
    rag_query: str,
    chat_history: str,
    user_message: str,
    n_docs: int = 20,
    score_threshold: float = 0.5,
) -> list[Document]:
    relevant_docs = await _identify_relevant_documents(
        vector_store=get_qdrant_vector_store(),
        namespace=responder.party_id,
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
        vector_store=get_voting_behavior_vector_store(),
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
        vector_store=get_parliamentary_questions_vector_store(),
        namespace=namespace,
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )
