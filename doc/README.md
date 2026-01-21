# wahl.chat Backend Project Documentation

## Overview

**wahl.chat** is an intelligent political chatbot initially developed for the 2025 German federal elections. The system enables citizens to engage with political party positions in a modern way and get answers to their questions, all backed by verifiable sources.

## Project Architecture

The project is built with the following technologies:
- **Python 3.11+** with Poetry for dependency management
- **aiohttp** for the async web server
- **Firebase** for database and storage
- **LangChain** for LLM orchestration
- **Pinecone** for vector storage (RAG)
- **OpenAI, Azure, Google Gemini** for language models
- **Perplexity** for enriched web search

## Folder Structure

```
wahl-chat-backend/
├── src/                    # Main source code
│   ├── aiohttp_app.py     # HTTP application
│   ├── websocket_app.py   # WebSocket application
│   ├── chatbot_async.py   # Chatbot logic
│   ├── llms.py            # LLM configuration
│   ├── prompts.py         # Prompt templates
│   ├── vector_store_helper.py  # Pinecone management
│   ├── firebase_service.py     # Firebase services
│   └── models/            # Data models
├── firebase/              # Firebase configuration
│   └── functions/         # Cloud Functions
├── data/                  # Data scripts
├── tests/                 # Unit tests
└── doc/                   # Documentation (this folder)
```

## Detailed Documentation

### 📚 Main Guides

1. [**Technical Architecture**](./architecture.md) - Overview of the system architecture
2. [**Services and APIs**](./services.md) - Details on LangChain, OpenAI, Pinecone, Perplexity, Azure, and Google
3. [**Initialization**](./initialisation.md) - Step-by-step installation and configuration guide

### 🌍 International Adaptation

4. [**German Specifics**](./systeme-allemand.md) - Features tied to the German political system
5. [**Adaptation for France**](./adaptation-france.md) - Complete guide to adapt the system to the French context

## Quick Start

1. **Install dependencies**
   ```bash
   poetry install
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the application**
   ```bash
   poetry run python -m src.aiohttp_app --debug
   ```

See [initialisation.md](./initialisation.md) for more details.

## Core Features

### 💬 Interactive Chat
- Real-time conversations via WebSocket
- Sourced and verifiable answers
- Multi-party support with comparisons

### 🔍 RAG (Retrieval-Augmented Generation)
- Semantic search across election programs
- Intelligent document reranking
- Precise citations with source numbers

### 🗳️ Political Analysis
- Parliamentary voting history
- Parliamentary questions
- External critical perspectives (Perplexity)

### 🤖 Multi-LLM
- Automatic fallback between models
- Cost optimization
- Real-time monitoring

## License

This project is licensed under **PolyForm Noncommercial 1.0.0** - non-commercial use only.

## Contact

For any questions: info@wahl.chat

---

## Quick Navigation

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | Diagrams and technical flows |
| [Services](./services.md) | External API configuration |
| [Initialization](./initialisation.md) | Installation and setup |
| [German System](./systeme-allemand.md) | Bundestag specifics |
| [France Adaptation](./adaptation-france.md) | Migration to the French system |
