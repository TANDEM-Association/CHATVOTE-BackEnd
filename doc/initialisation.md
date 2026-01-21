# Initialization Guide

This guide walks you step by step through installing and configuring the wahl.chat backend.

---

## Prerequisites

- **Python 3.11+** installed
- **Poetry** for dependency management
- **Git** to clone the repository
- Accounts on external services (see next section)

---

## 1. Install Poetry

Poetry is the Python dependency management tool used by the project.

### Linux / macOS / WSL
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Windows (PowerShell)
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Verify
```bash
poetry --version
# Poetry (version 1.7.0)
```

### Configuration
```bash
# Create virtual environments inside the project
poetry config virtualenvs.in-project true
```

---

## 2. Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-org/wahl-chat-backend.git
cd wahl-chat-backend

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

---

## 3. Configure External Services

### 3.1 OpenAI

**Steps**:
1. Create an account at https://platform.openai.com/
2. Go to **API Keys**: https://platform.openai.com/api-keys
3. Click **Create new secret key**
4. Name the key (e.g., "wahl-chat-backend")
5. Copy the key (format: `sk-proj-...`)
6. Add credits in **Billing** (minimum $5)

**Environment variable**:
```bash
OPENAI_API_KEY="sk-proj-..."
```

### 3.2 Pinecone

**Steps**:
1. Create an account at https://www.pinecone.io/
2. Create a new project
3. Go to **API Keys** in the dashboard
4. Copy the API key (format: `pcsk_...`)

**Environment variable**:
```bash
PINECONE_API_KEY="pcsk_..."
```

**Create the indexes**:
```python
# scripts/init_pinecone.py
from pinecone import Pinecone, ServerlessSpec
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Index 1: Party programs
pc.create_index(
    name="all-parties-index",
    dimension=3072,  # text-embedding-3-large
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)

# Index 2: Parliamentary votes
pc.create_index(
    name="justified-voting-behavior-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Index 3: Parliamentary questions
pc.create_index(
    name="parliamentary-questions-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

print("✓ Pinecone indexes created successfully")
```

**Run**:
```bash
poetry run python scripts/init_pinecone.py
```

### 3.3 Perplexity

**Steps**:
1. Create an account at https://www.perplexity.ai/
2. Go to **Settings** > **API**
3. Click **Generate API Key**
4. Copy the key (format: `pplx-...`)
5. Add credits (minimum $10)

**Environment variable**:
```bash
PERPLEXITY_API_KEY="pplx-..."
```

### 3.4 Google Gemini

**Steps**:
1. Go to https://aistudio.google.com/
2. Sign in with a Google account
3. Click **Get API Key**
4. Create or select a Google Cloud project
5. Copy the generated key (format: `AIza...`)

**Environment variable**:
```bash
GOOGLE_API_KEY="AIza..."
```

### 3.5 Azure OpenAI (Optional)

**Steps**:
1. Create an Azure account: https://azure.microsoft.com/
2. Request access to Azure OpenAI: https://aka.ms/oai/access
3. Create an **Azure OpenAI** resource in the Azure portal
4. Deploy the models:
   - `gpt-4o` (deployment name: "gpt-4o")
   - `gpt-4o-mini` (deployment name: "gpt-4o-mini")
5. Retrieve in **Keys and Endpoint**:
   - KEY 1 or KEY 2
   - Endpoint URL

**Environment variables**:
```bash
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

---

## 4. Firebase Configuration

### 4.1 Create a Firebase Project

1. Go to https://console.firebase.google.com/
2. Click **Add project**
3. Name the project (e.g., "wahl-chat-dev")
4. Disable Google Analytics (optional)
5. Create the project

### 4.2 Enable Firestore

1. In the menu, go to **Firestore Database**
2. Click **Create database**
3. Choose **Production** or **Test** mode
4. Select a region (e.g., `europe-west1`)

### 4.3 Generate the Service Key

1. Go to **Project Settings** (⚙️)
2. **Service accounts** tab
3. Click **Generate new private key**
4. Download the JSON file
5. Rename to `wahl-chat-dev-firebase-adminsdk.json`
6. Place it at the project root

**⚠️ Important**: Never commit this file. It is in `.gitignore`.

### 4.4 Initialize Firestore

```python
# scripts/init_firestore.py
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("wahl-chat-dev-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Create base collections
parties_ref = db.collection("parties")
print("✓ Collection 'parties' created")

proposed_questions_ref = db.collection("proposed_questions")
print("✓ Collection 'proposed_questions' created")

print("✓ Firestore initialized successfully")
```

**Run**:
```bash
poetry run python scripts/init_firestore.py
```

---

## 5. Configure Environment Variables

### 5.1 Create the .env File

```bash
cp .env.example .env
```

### 5.2 Edit .env

```bash
# OpenAI
OPENAI_API_KEY="sk-proj-..."

# Pinecone
PINECONE_API_KEY="pcsk_..."

# Perplexity
PERPLEXITY_API_KEY="pplx-..."

# Google Gemini
GOOGLE_API_KEY="AIza..."

# Azure OpenAI (optional)
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Firebase
FIREBASE_CREDENTIALS_PATH="./wahl-chat-dev-firebase-adminsdk.json"

# LangSmith (optional - for monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://eu.api.smith.langchain.com"
LANGCHAIN_API_KEY="lsv2_pt_..."
LANGCHAIN_PROJECT="wahl-chat-dev"

# Application
DEBUG=true
PORT=8080
HOST=0.0.0.0
```

---

## 6. Import Data

### 6.1 Import Parties

```python
# scripts/import_parties.py
from src.firebase_service import db
from src.models.party import Party

parties = [
    {
        "party_id": "cdu",
        "name": "CDU",
        "long_name": "Christlich Demokratische Union",
        "description": "Center-right conservative party",
        "website_url": "https://www.cdu.de",
        "candidate": "Friedrich Merz",
        "election_manifesto_url": "https://...",
        "is_small_party": False,
        "is_already_in_parliament": True
    },
    # Add other parties...
]

for party_data in parties:
    db.collection("parties").document(party_data["party_id"]).set(party_data)
    print(f"✓ Party {party_data['name']} imported")
```

### 6.2 Import Election Programs

```python
# scripts/import_programs.py
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
import os

# Configuration
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("all-parties-index")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

def import_party_program(party_id: str, pdf_path: str):
    """Import an election program into Pinecone"""

    # Load the PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    splits = text_splitter.split_documents(documents)

    # Add metadata
    for i, doc in enumerate(splits):
        doc.metadata["party_id"] = party_id
        doc.metadata["chunk_id"] = i
        doc.metadata["source"] = pdf_path

    # Index in Pinecone
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace=party_id
    )
    vector_store.add_documents(splits)

    print(f"✓ Program for {party_id} imported ({len(splits)} chunks)")

# Import all programs
import_party_program("cdu", "data/programs/cdu_wahlprogramm.pdf")
import_party_program("spd", "data/programs/spd_wahlprogramm.pdf")
# ...
```

**Run**:
```bash
poetry run python scripts/import_programs.py
```

---

## 7. Run the Application

### 7.1 Development Mode

```bash
# With auto-reload
poetry run python -m src.aiohttp_app --debug

# The application starts at http://localhost:8080
```

### 7.2 Production Mode

```bash
poetry run python -m src.aiohttp_app --host 0.0.0.0 --port 8080
```

### 7.3 With Docker

```bash
# Build the image
docker build -t wahl-chat-backend:latest .

# Run the container
docker run -d \
  --name wahl-chat-api \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/wahl-chat-dev-firebase-adminsdk.json:/app/wahl-chat-dev-firebase-adminsdk.json:ro \
  wahl-chat-backend:latest
```

### 7.4 With Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f wahl-chat-api

# Stop
docker-compose down
```

---

## 8. Verify the Installation

### 8.1 Health Check

```bash
curl http://localhost:8080/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-02-15T10:30:00Z"
}
```

### 8.2 WebSocket Test

```python
# test_websocket.py
import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:8080/ws"

    async with websockets.connect(uri) as websocket:
        # Initialize session
        await websocket.send(json.dumps({
            "type": "init_chat_session",
            "data": {
                "party_ids": ["cdu"],
                "session_id": "test-session"
            }
        }))

        response = await websocket.recv()
        print("Init:", response)

        # Send a message
        await websocket.send(json.dumps({
            "type": "user_message",
            "data": {
                "message": "What is your position on climate?"
            }
        }))

        # Receive responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"{data['type']}: {data.get('data', {})}")

            if data['type'] == 'chat_response_complete':
                break

asyncio.run(test_chat())
```

**Run**:
```bash
poetry run python test_websocket.py
```

---

## 9. Troubleshooting

### Error: "OpenAI API key not found"

**Solution**:
```bash
# Check that the variable is defined
echo $OPENAI_API_KEY

# If empty, load the .env
export $(cat .env | xargs)
```

### Error: "Pinecone index not found"

**Solution**:
```bash
# Check that the indexes exist
poetry run python -c "from pinecone import Pinecone; import os; pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY')); print(pc.list_indexes())"

# If empty, create the indexes
poetry run python scripts/init_pinecone.py
```

### Error: "Firebase credentials not found"

**Solution**:
```bash
# Check that the file exists
ls -la wahl-chat-dev-firebase-adminsdk.json

# Check permissions
chmod 600 wahl-chat-dev-firebase-adminsdk.json
```

### Error: "Rate limit exceeded"

**Solution**:
- Wait a few minutes
- Check quotas in the service dashboards
- Upgrade to a higher tier if needed

---

## 10. Next Steps

- See [architecture.md](./architecture.md) to understand the system
- Read [services.md](./services.md) for API details
- See [systeme-allemand.md](./systeme-allemand.md) for the specifics
- Adapt for France with [adaptation-france.md](./adaptation-france.md)

---

## Support

For any questions:
- Open an issue on GitHub
- Contact: info@wahl.chat
