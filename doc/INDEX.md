# wahl.chat Documentation Index

Complete documentation for the wahl.chat backend project - more than 2,600 lines of technical documentation.

---

## 📖 Reading Guide

### To Get Started
1. Start with [README.md](./README.md) for an overview
2. Follow [initialisation.md](./initialisation.md) to install the project
3. See [services.md](./services.md) to configure the APIs

### To Understand
4. Read [architecture.md](./architecture.md) to understand how it works
5. Explore [systeme-allemand.md](./systeme-allemand.md) for the specifics

### To Adapt
6. Follow [adaptation-france.md](./adaptation-france.md) for the migration

---

## 📚 Detailed Contents

### [README.md](./README.md) - 112 lines
**Project overview**

- Introduction to the wahl.chat project
- High-level architecture
- Folder structure
- Quick start
- Core features
- Links to other documents

**Best for**: Getting up to speed quickly

---

### [services.md](./services.md) - 487 lines
**Services and External APIs**

#### Contents:
1. **LangChain** - LLM orchestration framework
2. **OpenAI** - GPT-4o models and embeddings
3. **Pinecone** - Vector database (3 indexes)
4. **Perplexity** - Web search and critical analysis
5. **Azure OpenAI** - Fallback and EU compliance
6. **Google Gemini** - Primary (free) model
7. **Multi-LLM strategy** - Fallback order
8. **Cost comparison** - Detailed table
9. **Environment variables** - Full configuration

#### Key points:
- Configuration of each service
- How to obtain API keys
- Limits and quotas
- Cost estimates (~$50-100/month)

**Best for**: Configuring external services

---

### [initialisation.md](./initialisation.md) - 546 lines
**Complete Installation Guide**

#### Contents:
1. **Prerequisites** - Python, Poetry, Git
2. **Poetry installation** - Linux, macOS, Windows
3. **Clone and install** - Dependencies
4. **Service configuration** - Step by step
   - OpenAI (API key, credits)
   - Pinecone (create 3 indexes)
   - Perplexity (API key)
   - Google Gemini (free API)
   - Azure OpenAI (optional)
5. **Firebase configuration** - Firestore, service key
6. **Environment variables** - .env file
7. **Data import** - Parties, programs
8. **Run** - Dev, prod, Docker
9. **Verification** - Health check, tests
10. **Troubleshooting** - Solutions to common errors

#### Provided scripts:
- `scripts/init_pinecone.py` - Create indexes
- `scripts/init_firestore.py` - Firebase initialization
- `scripts/import_parties.py` - Party import
- `scripts/import_programs.py` - Program import

**Best for**: Installing and configuring the project end to end

---

### [architecture.md](./architecture.md) - 438 lines
**Detailed Technical Architecture**

#### Contents:
1. **Overview** - Architecture diagram
2. **Main components**
   - Web application (aiohttp)
   - WebSocket application
   - Chatbot logic
3. **Processing flow** - Full workflow for a question
4. **LLM management** - Multi-LLM strategy, fallback
5. **RAG system** - Retrieval-Augmented Generation
6. **Database** - Firestore structure
7. **Deployment** - Docker, Docker Compose

#### Diagrams:
- Global architecture
- WebSocket flow
- Processing workflow
- RAG pipeline

#### Code examples:
- LLM management
- Vector search
- Document reranking
- Response streaming

**Best for**: Understanding the internal mechanics

---

### [systeme-allemand.md](./systeme-allemand.md) - 426 lines
**Specifics of the German Political System**

#### Contents:
1. **Electoral context** - Bundestagswahl 2025
2. **Political parties** - 13 configured parties
3. **Bundestag** - Parliamentary votes
4. **Parliamentary questions** - Pinecone index
5. **German prompts** - All templates
6. **Sources and references** - German media
7. **Electoral system** - Zweitstimme, Erststimme
8. **Government and coalitions** - Ampelkoalition
9. **Structured data** - Firebase, Pinecone
10. **Adaptation checklist** - For other countries

#### Terminology:
| German | English |
|----------|----------|
| Bundestagswahl | Federal election |
| Bundestag | Federal parliament |
| Spitzenkandidat | Lead candidate |
| Wahlprogramm | Election program |
| Abstimmung | Vote / ballot |

#### German sources:
- bpb (Bundeszentrale fur politische Bildung)
- ARD, ZDF (public TV)
- FAZ, SZ (press)
- DIW, ifo, IW (economic institutes)

**Best for**: Understanding what to adapt

---

### [adaptation-france.md](./adaptation-france.md) - 624 lines
**Complete Adaptation Guide for France**

#### Contents:
1. **Electoral context** - Legislative elections 2027
2. **French political parties** - LFI, PS, EELV, Renaissance, LR, RN...
3. **National Assembly** - Vote scraping
4. **Questions to government** - French sources
5. **Prompt translation** - All templates in French
6. **French sources** - Media and institutes
7. **Formats and conventions** - Dates, quotes, capitalization
8. **Electoral system** - Two-round single-member districts
9. **Data to collect** - Programs, votes, questions
10. **Pinecone configuration** - New namespaces
11. **Tests and validation** - Test questions
12. **Migration checklist** - 6 detailed phases
13. **Useful resources** - APIs, documentation, tools
14. **Project name** - Suggestions (vote.chat, election.chat...)

#### Source mapping:
| Type | Germany | France |
|------|-----------|--------|
| Civic education | bpb | Vie Publique |
| Public TV | ARD, ZDF | France TV, France Info |
| Press | FAZ, SZ | Le Monde, Le Figaro |
| Economics | DIW, ifo | INSEE, OFCE |
| Political science | - | CEVIPOF, Sciences Po |

#### Provided scripts:
- National Assembly scraping
- French program import
- Parliamentary question collection
- French answer validation

**Best for**: Adapting the system for France

---

## 🎯 Use Cases

### I want to install the project
1. [README.md](./README.md) - Overview
2. [initialisation.md](./initialisation.md) - Full installation
3. [services.md](./services.md) - API configuration

### I want to understand the code
1. [architecture.md](./architecture.md) - Technical architecture
2. [services.md](./services.md) - Services used
3. Source code in `/src`

### I want to adapt for France
1. [systeme-allemand.md](./systeme-allemand.md) - Understand the specifics
2. [adaptation-france.md](./adaptation-france.md) - Migration guide
3. [initialisation.md](./initialisation.md) - Reinitialize with new data

### I want to contribute
1. [README.md](./README.md) - Overview
2. [architecture.md](./architecture.md) - Understand the architecture
3. [systeme-allemand.md](./systeme-allemand.md) - Elements to preserve

---

## 📊 Statistics

- **Total**: 2633 lines of documentation
- **6 markdown files**
- **Coverage**: Installation, architecture, services, adaptation
- **Languages**: English (documentation), German (original prompts)

---

## 🔗 Quick Links

### Core documentation
- [README.md](./README.md) - Start here
- [initialisation.md](./initialisation.md) - Installation
- [architecture.md](./architecture.md) - Technical

### Adaptation
- [systeme-allemand.md](./systeme-allemand.md) - Specifics
- [adaptation-france.md](./adaptation-france.md) - France migration

### Configuration
- [services.md](./services.md) - External APIs
- `.env.example` - Configuration template

---

## 📞 Support

- **Email**: info@wahl.chat
- **GitHub**: Open an issue
- **Documentation**: This `/doc` folder

---

**Last updated**: November 9, 2024
