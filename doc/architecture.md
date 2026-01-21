# Technical Architecture

This document describes the technical architecture of the wahl.chat project.

---

## 1. Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Web/Mobile)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ WebSocket / HTTP
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Backend (Python/aiohttp)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ WebSocket    │  │ HTTP API     │  │ Chatbot      │          │
│  │ Handler      │  │ Endpoints    │  │ Logic        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Firebase    │    │   Pinecone    │    │     LLMs      │
│  (Firestore)  │    │  (Vectors)    │    │ (Multi-model) │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 2. Main Components

### 2.1 Web Application (aiohttp)

**File**: `src/aiohttp_app.py`

```python
# HTTP entry points
- GET  /health                    # Health check
- POST /api/swiper/answer         # Voting compass answer
- POST /api/parliamentary-question # Parliamentary question
```

**Features**:
- Async server (asyncio)
- CORS enabled for cross-origin requests
- Request validation with Pydantic
- Centralized error handling

### 2.2 WebSocket Application

**File**: `src/websocket_app.py`

```python
# WebSocket events
- init_chat_session              # Initialize a session
- user_message                   # User message
- request_summary                # Request a summary
- request_voting_behavior        # Request voting behavior
- request_pro_con_perspective    # Request a critical analysis
```

**Communication flow**:
```
Client                          Server
  │                               │
  ├─── init_chat_session ────────>│
  │<─── chat_session_initialized ─┤
  │                               │
  ├─── user_message ─────────────>│
  │<─── responding_parties ───────┤
  │<─── party_response_chunk ─────┤ (streaming)
  │<─── party_response_chunk ─────┤
  │<─── party_response_complete ──┤
  │<─── chat_response_complete ───┤
  │                               │
```

### 2.3 Chatbot Logic

**File**: `src/chatbot_async.py`

**Main functions**:

```python
# Answer generation
async def generate_streaming_chatbot_response(...)
    """Generate a streamed response for a party"""

async def generate_streaming_chatbot_comparing_response(...)
    """Generate a comparative response between parties"""

# Query improvement
async def generate_improvement_rag_query(...)
    """Improve the query for RAG"""

# Classification
async def get_question_targets_and_type(...)
    """Determine target parties and question type"""

# Analysis
async def generate_party_vote_behavior_summary(...)
    """Generate a voting behavior summary"""

async def generate_pro_con_perspective(...)
    """Generate a critical perspective (Perplexity)"""
```

---

## 3. Question Processing Flow

### 3.1 Full Workflow

```
1. Receive user question
   │
   ├─> 2. Determine target parties
   │      (deterministic LLM)
   │
   ├─> 3. Classify question type
   │      (comparison or single)
   │
   ├─> 4. For each party:
   │      │
   │      ├─> 4.1 Improve the RAG query
   │      │      (deterministic LLM)
   │      │
   │      ├─> 4.2 Search in Pinecone
   │      │      (embedding + similarity)
   │      │
   │      ├─> 4.3 Rerank documents
   │      │      (deterministic LLM)
   │      │
   │      ├─> 4.4 Generate the response
   │      │      (non-deterministic LLM, streaming)
   │      │
   │      └─> 4.5 Send to client (WebSocket)
   │
   ├─> 5. Generate title and quick replies
   │      (deterministic LLM)
   │
   └─> 6. Optional: Critical analysis (Perplexity)
          or voting behavior (Bundestag)
```

### 3.2 Code Example

```python
# 1. Receive
user_message = "What is the CDU position on climate?"

# 2. Determine target parties
targets = await get_question_targets_and_type(
    user_message=user_message,
    chat_history=chat_history,
    current_parties=["cdu", "spd"],
    all_parties=all_parties
)
# Result: ["cdu"]

# 3. Improve the query
improved_query = await generate_improvement_rag_query(
    party_name="CDU",
    user_message=user_message,
    chat_history=chat_history
)
# Result: "Position CDU Klimaschutz Klimapolitik CO2 Emissionen Energiewende"

# 4. RAG search
relevant_docs = await identify_relevant_docs_with_llm_based_reranking(
    party=cdu_party,
    rag_query=improved_query,
    chat_history=chat_history,
    user_message=user_message,
    n_docs=20,
    score_threshold=0.5
)

# 5. Generate response (streaming)
async for chunk in generate_streaming_chatbot_response(
    party=cdu_party,
    user_message=user_message,
    chat_history=chat_history,
    relevant_docs=relevant_docs
):
    # Send chunk to client via WebSocket
    await send_chunk(chunk)
```

---

## 4. LLM Management

### 4.1 Multi-LLM Strategy

**File**: `src/llms.py`

```python
# Preference-ordered list
NON_DETERMINISTIC_LLMS = [
    google_gemini_2_flash,      # Fast and free
    openai_gpt_4o_mini,         # Good price/performance
    azure_gpt_4o_mini,          # Azure fallback
    openai_gpt_4o,              # High quality
    azure_gpt_4o,               # Premium Azure fallback
]

DETERMINISTIC_LLMS = [
    google_gemini_2_flash_det,  # Temperature = 0
    openai_gpt_4o_mini_det,
    azure_gpt_4o_mini_det,
]
```

### 4.2 Fallback Function

```python
async def get_answer_from_llms(
    llms: list[LLM],
    system_prompt: str,
    user_prompt: str,
    session_id: str
) -> str:
    """
    Try each LLM in order until success
    """
    for llm in llms:
        try:
            # Check capacity
            if not await check_llm_capacity(llm):
                continue

            # Call the LLM
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Mark as success
            await awrite_llm_status(session_id, llm.name, "success")
            return response.content

        except Exception as e:
            # Mark as failure and move on
            await awrite_llm_status(session_id, llm.name, "error")
            logger.warning(f"LLM {llm.name} failed: {e}")
            continue

    raise Exception("All LLMs failed")
```

### 4.3 Capacity Monitoring

```python
# Per-minute capacities
CAPACITY_GEMINI_2_FLASH = 108
CAPACITY_GPT_4O_OPENAI_TIER_5 = 3759
CAPACITY_GPT_4O_AZURE = 112
CAPACITY_GPT_4O_MINI_OPENAI_TIER_5 = 4054
CAPACITY_GPT_4O_MINI_AZURE = 108

async def check_llm_capacity(llm: LLM) -> bool:
    """Check whether the LLM has available capacity"""
    # Count calls in the last minute
    recent_calls = await count_recent_calls(llm.name, window=60)
    return recent_calls < llm.capacity
```

---

## 5. RAG System (Retrieval-Augmented Generation)

### 5.1 RAG Architecture

```
User question
    │
    ├─> Query improvement (LLM)
    │   "climate" → "climate climate change CO2 emissions environmental policy"
    │
    ├─> Embedding generation (OpenAI)
    │   Text → Vector [3072 dimensions]
    │
    ├─> Search in Pinecone
    │   Cosine similarity → Top 20 documents
    │
    ├─> Reranking (LLM)
    │   Sort by real relevance → Top 5 documents
    │
    └─> Response generation (LLM)
        Context + Question → Sourced answer
```

### 5.2 Implementation

**File**: `src/vector_store_helper.py`

```python
async def identify_relevant_docs_with_llm_based_reranking(
    party: Party,
    rag_query: str,
    chat_history: str,
    user_message: str,
    n_docs: int = 20,
    score_threshold: float = 0.5,
) -> list[Document]:
    """
    Search with LLM reranking
    """
    # 1. Vector search
    relevant_docs_with_scores = await pinecone_vector_store.asimilarity_search_with_relevance_scores(
        rag_query,
        namespace=party.party_id,
        k=n_docs,
        score_threshold=score_threshold,
    )

    # 2. Sort by score
    relevant_docs_with_scores = sorted(
        relevant_docs_with_scores,
        key=lambda x: x[1],
        reverse=True
    )

    # 3. Rerank with LLM
    reranked_docs = await rerank_documents(
        documents=[doc for doc, _ in relevant_docs_with_scores],
        chat_history=chat_history,
        user_message=user_message
    )

    # 4. Return top 5
    return reranked_docs[:5]
```

---

## 6. Database (Firebase)

### 6.1 Firestore Structure

```
firestore/
├── parties/
│   ├── {party_id}/
│   │   ├── name: string
│   │   ├── long_name: string
│   │   ├── description: string
│   │   ├── website_url: string
│   │   ├── candidate: string
│   │   ├── election_manifesto_url: string
│   │   └── is_small_party: boolean
│   │
├── proposed_questions/
│   ├── {party_id}/
│   │   └── questions/
│   │       └── {question_id}/
│   │           ├── question: string
│   │           └── category: string
│   │
├── cached_answers/
│   ├── {party_id}/
│   │   └── answers/
│   │       └── {question_hash}/
│   │           ├── question: string
│   │           ├── answer: string
│   │           └── timestamp: timestamp
│   │
└── llm_status/
    └── {session_id}/
        └── {llm_name}/
            ├── status: string
            └── timestamp: timestamp
```

---

## 7. Deployment

### 7.1 Docker

**File**: `Dockerfile`

```dockerfile
FROM python:3.11.3-slim

# Install Poetry
RUN pip install poetry

# Copy dependencies
COPY pyproject.toml poetry.lock /app/
WORKDIR /app

# Install dependencies
RUN poetry install --no-root

# Copy code
COPY . /app/

# Run the application
CMD ["poetry", "run", "python", "-m", "src.aiohttp_app", "--host", "0.0.0.0", "--port", "8080"]
```

### 7.2 Docker Compose

**File**: `docker-compose.yml`

```yaml
version: "3.8"

services:
  wahl-chat-api:
    build: .
    image: wahl-chat-backend:latest
    env_file: .env
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - ./wahl-chat-dev-firebase-adminsdk.json:/app/wahl-chat-dev-firebase-adminsdk.json:ro
    networks:
      - traefik-public
```

---

## Additional Resources

- [Services and APIs](./services.md)
- [Initialization guide](./initialisation.md)
- [German specifics](./systeme-allemand.md)
- [France adaptation](./adaptation-france.md)
