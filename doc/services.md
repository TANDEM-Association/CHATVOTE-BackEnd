# Services and External APIs

This document details all external services used by wahl.chat and their role in the architecture.

---

## 1. LangChain

### Role
**LangChain** is the main LLM orchestration framework. It provides an abstraction to interact with different language models and manage processing chains.

### Usage in the Project
- **LLM orchestration**: Unified management of OpenAI, Azure OpenAI, and Google Gemini
- **Prompt chains**: Building complex prompts with templates
- **Memory management**: Conversation history
- **Pinecone integration**: Interface with the vector store

### Configuration

```python
# src/llms.py
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# OpenAI configuration example
openai_gpt_4o = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)
```

### Environment Variables
```bash
# No specific key for LangChain
# Uses keys from underlying services (OpenAI, Azure, Google)

# Optional: Tracing with LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://eu.api.smith.langchain.com"
LANGCHAIN_API_KEY="lsv2_pt_..."
LANGCHAIN_PROJECT="wahl-chat-prod"
```

### Documentation
- Official site: https://python.langchain.com/
- GitHub: https://github.com/langchain-ai/langchain

---

## 2. OpenAI

### Role
**OpenAI** provides GPT-4o and GPT-4o-mini models, used for response generation and natural language processing.

### Models Used

| Model | Usage | Temperature | Cost (1M tokens) |
|--------|-------|-------------|------------------|
| **gpt-4o** | Complex answers | 0.7 | $2.50 input / $10 output |
| **gpt-4o-mini** | Simple tasks | 0.7 | $0.15 input / $0.60 output |
| **gpt-4o-mini** (det) | Classification | 0.0 | $0.15 input / $0.60 output |
| **text-embedding-3-large** | Embeddings | N/A | $0.13 / 1M tokens |

### Configuration

```python
# src/llms.py
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# LLM for generation
openai_gpt_4o_mini = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=3,
)

# Embeddings for Pinecone
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY"),
    dimensions=3072
)
```

### Environment Variables
```bash
OPENAI_API_KEY="sk-proj-..."
```

### Get an API Key
1. Create an account at https://platform.openai.com/
2. Go to **API Keys**: https://platform.openai.com/api-keys
3. Click **Create new secret key**
4. Copy the key (it will only be shown once)
5. Add credits in **Billing**: https://platform.openai.com/account/billing

### Rate Limits
- **Tier 1** (new account): 500 RPM, 30,000 TPM
- **Tier 5** (after $1000 spent): 10,000 RPM, 30M TPM

### Documentation
- API Reference: https://platform.openai.com/docs/api-reference
- Pricing: https://openai.com/api/pricing/

---

## 3. Pinecone

### Role
**Pinecone** is the vector database used for RAG (Retrieval-Augmented Generation). It stores document embeddings and enables semantic search.

### Index Architecture

The project uses **3 distinct Pinecone indexes**:

#### 3.1 `all-parties-index`
**Content**: Election programs and party documents

**Namespaces**:
```
all-parties-index/
├── cdu          # CDU documents
├── spd          # SPD documents
├── gruene       # Grune documents
├── fdp          # FDP documents
├── linke        # Die Linke documents
├── afd          # AfD documents
├── bsw          # BSW documents
└── ...          # Other parties
```

**Usage**: Search for party positions on specific topics

#### 3.2 `justified-voting-behavior-index`
**Content**: Bundestag voting history with justifications

**Namespace**:
```
justified-voting-behavior-index/
└── vote_summary    # Parliamentary vote summaries
```

**Usage**: Analyze party voting behavior

#### 3.3 `parliamentary-questions-index`
**Content**: Parliamentary questions asked by MPs

**Namespaces**:
```
parliamentary-questions-index/
├── cdu-parliamentary-questions
├── spd-parliamentary-questions
├── gruene-parliamentary-questions
└── ...
```

**Usage**: Search questions asked by parties

### Configuration

```python
# src/vector_store_helper.py
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

# Initialization
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Main index
index = pc.Index("all-parties-index")
vector_store = PineconeVectorStore(
    index=index,
    embedding=OpenAIEmbeddings(model="text-embedding-3-large")
)

# Search within a namespace
results = await vector_store.asimilarity_search_with_relevance_scores(
    query="Position on climate",
    namespace="cdu",
    k=10,
    score_threshold=0.5
)
```

### Environment Variables
```bash
PINECONE_API_KEY="pcsk_..."
```

### Get an API Key
1. Create an account at https://www.pinecone.io/
2. Create a project
3. Go to **API Keys** in the dashboard
4. Copy the API key

### Create the Indexes

```python
# Initialization script
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="pcsk_...")

# Create the main index
pc.create_index(
    name="all-parties-index",
    dimension=3072,  # text-embedding-3-large
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)

# Create the votes index
pc.create_index(
    name="justified-voting-behavior-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Create the questions index
pc.create_index(
    name="parliamentary-questions-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

### Limits
- **Free plan**: 1 index, 100K vectors
- **Starter plan** ($70/month): 5 indexes, 2M vectors
- **Standard plan**: Unlimited

### Documentation
- Docs: https://docs.pinecone.io/
- Python SDK: https://docs.pinecone.io/guides/get-started/quickstart

---

## 4. Perplexity

### Role
**Perplexity** is used to generate external critical perspectives on party proposals. It performs real-time web searches and provides sourced analyses.

### Usage in the Project
- **Critical analysis**: Evaluate feasibility of proposals
- **External research**: Up-to-date information not in programs
- **Multiple sources**: Aggregate expert and media opinions

### Configuration

```python
# src/chatbot_async.py
from openai import AsyncOpenAI

perplexity_client = AsyncOpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    base_url="https://api.perplexity.ai"
)

# API call
response = await perplexity_client.chat.completions.create(
    model="llama-3.1-sonar-large-128k-online",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)
```

### Environment Variables
```bash
PERPLEXITY_API_KEY="pplx-..."
```

### Get an API Key
1. Create an account at https://www.perplexity.ai/
2. Go to **Settings** > **API**
3. Generate a new API key
4. Add credits (minimum $10)

### Available Models
- **llama-3.1-sonar-large-128k-online**: Real-time web search
- **llama-3.1-sonar-small-128k-online**: Faster version
- Cost: ~$1 / 1M tokens

### Limits
- 50 requests per minute
- 60-second timeout per request

### Documentation
- API Docs: https://docs.perplexity.ai/

---

## 5. Azure OpenAI

### Role
**Azure OpenAI** provides the same models as OpenAI but hosted on Microsoft Azure infrastructure. Used as a **fallback** when OpenAI rate limits are hit.

### Configuration

```python
# src/llms.py
from langchain_openai import AzureChatOpenAI

azure_gpt_4o = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2024-08-01-preview",
    temperature=0.7,
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
```

### Environment Variables
```bash
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

### Get Access
1. Create an Azure account: https://azure.microsoft.com/
2. Request access to Azure OpenAI: https://aka.ms/oai/access
3. Create an Azure OpenAI resource in the portal
4. Deploy models (gpt-4o, gpt-4o-mini)
5. Retrieve the key and endpoint in **Keys and Endpoint**

### Benefits
- **Compliance**: Data hosted in Europe
- **SLA**: 99.9% availability guarantee
- **Separate quotas**: Independent from direct OpenAI

### Documentation
- Azure OpenAI: https://learn.microsoft.com/en-us/azure/ai-services/openai/

---

## 6. Google Gemini

### Role
**Google Gemini** (via Vertex AI or direct API) is used as the primary model for non-deterministic answers thanks to its strong price/performance ratio.

### Models Used
- **gemini-2.0-flash-exp**: Fast and free generation (preview)
- **gemini-1.5-flash**: Stable version

### Configuration

```python
# src/llms.py
from langchain_google_genai import ChatGoogleGenerativeAI

google_gemini_2_flash = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
```

### Environment Variables
```bash
GOOGLE_API_KEY="AIza..."
```

### Get an API Key
1. Go to https://aistudio.google.com/
2. Click **Get API Key**
3. Create or select a Google Cloud project
4. Copy the generated key

### Benefits
- **Free**: gemini-2.0-flash-exp is free in preview
- **Fast**: Very low latency
- **Multimodal**: Text, image, video support

### Limits
- 15 RPM (requests per minute) on the free tier
- 1M TPM (tokens per minute)

### Documentation
- Google AI Studio: https://ai.google.dev/
- API Reference: https://ai.google.dev/api/python/google/generativeai

---

## 7. Multi-LLM Strategy

### Fallback Order

The system tries LLMs in this order until it succeeds:

**For non-deterministic answers** (temperature > 0):
1. **Google Gemini 2.0 Flash** (free, fast)
2. **OpenAI GPT-4o-mini** (good value)
3. **Azure GPT-4o-mini** (fallback)
4. **OpenAI GPT-4o** (high quality)
5. **Azure GPT-4o** (premium fallback)

**For deterministic tasks** (temperature = 0):
1. **Google Gemini 2.0 Flash** (deterministic)
2. **OpenAI GPT-4o-mini** (deterministic)
3. **Azure GPT-4o-mini** (deterministic)

### Monitoring

```python
# src/llms.py
async def get_answer_from_llms(llms: list, system_prompt: str, user_prompt: str):
    for llm in llms:
        try:
            # Check capacity
            if not await check_llm_capacity(llm):
                continue

            # Call the LLM
            response = await llm.ainvoke([...])

            # Log success
            await log_llm_success(llm.name)
            return response.content

        except Exception as e:
            # Log failure and move to the next
            await log_llm_failure(llm.name, str(e))
            continue

    raise Exception("All LLMs failed")
```

---

## 8. Cost Comparison

| Service | Model | Input Cost (1M tokens) | Output Cost (1M tokens) | Notes |
|---------|--------|------------------------|-------------------------|-------|
| **Google** | gemini-2.0-flash-exp | Free | Free | Preview |
| **OpenAI** | gpt-4o-mini | $0.15 | $0.60 | Recommended |
| **OpenAI** | gpt-4o | $2.50 | $10.00 | High quality |
| **Azure** | gpt-4o-mini | $0.15 | $0.60 | Same price |
| **Azure** | gpt-4o | $2.50 | $10.00 | Same price |
| **Perplexity** | sonar-large | ~$1.00 | ~$1.00 | Web search |
| **OpenAI** | text-embedding-3-large | $0.13 | N/A | Embeddings |

**Monthly estimate** (10,000 requests/month):
- With Gemini as primary: **~$50-100/month**
- Without Gemini: **~$200-300/month**

---

## 9. Environment Variables Summary

```bash
# OpenAI
OPENAI_API_KEY="sk-proj-..."

# Pinecone
PINECONE_API_KEY="pcsk_..."

# Perplexity
PERPLEXITY_API_KEY="pplx-..."

# Azure OpenAI
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Google Gemini
GOOGLE_API_KEY="AIza..."

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://eu.api.smith.langchain.com"
LANGCHAIN_API_KEY="lsv2_pt_..."
LANGCHAIN_PROJECT="wahl-chat-prod"
```

---

## 10. Next Steps

See [initialisation.md](./initialisation.md) for the full installation and configuration guide.
