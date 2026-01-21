# Available Scripts

This document lists all available scripts in the wahl.chat project and what they do.

---

## 📋 Overview

The project contains **7 Python scripts** in 2 categories:
- **4 initialization scripts** for the German system
- **3 adaptation scripts** for the French system

All scripts are **documented**, **tested**, and **ready to use**.

---

## 🔧 Initialization Scripts

### 1. `scripts/init_pinecone.py`

**Purpose**: Creates the 3 Pinecone indexes required by the project

**Usage**:
```bash
poetry run python scripts/init_pinecone.py
```

**Indexes created**:
- `all-parties-index` (dimension: 3072, metric: cosine)
  - Party programs and documents
  - Namespace per party (cdu, spd, gruene, etc.)

- `justified-voting-behavior-index` (dimension: 3072, metric: cosine)
  - Bundestag voting behavior with justifications
  - Namespace per party

- `parliamentary-questions-index` (dimension: 3072, metric: cosine)
  - Parliamentary questions by party
  - Namespace format: `{party_id}-parliamentary-questions`

**Prerequisites**:
- Environment variable `PINECONE_API_KEY`

**Output**:
```
📝 Creating index 'all-parties-index'...
✓ Index 'all-parties-index' created successfully
📝 Creating index 'justified-voting-behavior-index'...
✓ Index 'justified-voting-behavior-index' created successfully
📝 Creating index 'parliamentary-questions-index'...
✓ Index 'parliamentary-questions-index' created successfully

✅ All Pinecone indexes are ready!
```

---

### 2. `scripts/init_firestore.py`

**Purpose**: Initializes Firebase Firestore with base collections

**Usage**:
```bash
poetry run python scripts/init_firestore.py
```

**Collections created**:
- `parties` - Political party data
- `proposed_questions` - Suggested questions
- `cached_answers` - Cached answers
- `llm_status` - LLM status and monitoring
- `chat_sessions` - User chat sessions

**Prerequisites**:
- Firebase credentials file: `wahl-chat-dev-firebase-adminsdk.json`
- Environment variable `FIREBASE_CREDENTIALS_PATH` (optional)

**Output**:
```
📝 Initializing Firebase with wahl-chat-dev-firebase-adminsdk.json...

📚 Creating base collections...
✓ Collection 'parties' created
✓ Collection 'proposed_questions' created
✓ Collection 'cached_answers' created
✓ Collection 'llm_status' created
✓ Collection 'chat_sessions' created

✅ Firestore initialized successfully!
```

---

### 3. `scripts/import_parties.py`

**Purpose**: Imports the 13 German political parties into Firestore

**Usage**:
```bash
poetry run python scripts/import_parties.py
```

**Imported parties**:
- CDU (Christlich Demokratische Union)
- SPD (Sozialdemokratische Partei)
- Grune (Bundnis 90/Die Grunen)
- FDP (Freie Demokratische Partei)
- Die Linke
- AfD (Alternative fur Deutschland)
- BSW (Bundnis Sahra Wagenknecht)
- Freie Wahler
- Volt Deutschland
- Tierschutzpartei
- Piratenpartei
- ODP (Okologisch-Demokratische Partei)
- dieBasis

**Data per party**:
- `party_id`: Unique identifier
- `name`: Short name
- `long_name`: Full name
- `description`: Description
- `website_url`: Official website
- `candidate`: Lead candidate
- `is_small_party`: Small party (boolean)

**Output**:
```
📝 Importing 13 political parties...

✓ Importing party 'CDU'...
✓ Importing party 'SPD'...
...

✅ 13 parties imported successfully!
```

---

### 4. `scripts/import_programs.py`

**Purpose**: Imports election programs (PDFs) into Pinecone

**Usage**:
```bash
# Import a specific program
poetry run python scripts/import_programs.py --party cdu --pdf data/programs/cdu/program.pdf

# Import all programs from a folder
poetry run python scripts/import_programs.py --all --data-dir data/programs/
```

**Options**:
- `--party`: Party ID (e.g., cdu, spd)
- `--pdf`: Path to the PDF file
- `--all`: Import all programs
- `--data-dir`: Folder containing programs (default: data/programs)
- `--index`: Pinecone index name (default: all-parties-index)

**Expected structure**:
```
data/programs/
├── cdu/
│   └── program.pdf
├── spd/
│   └── program.pdf
└── ...
```

**Process**:
1. Load the PDF with PyPDFLoader
2. Split into chunks (1000 chars, overlap 200)
3. Add metadata (party_id, source, chunk_id)
4. Generate embeddings (OpenAI text-embedding-3-large)
5. Index in Pinecone (namespace = party_id)

**Output**:
```
📄 Loading program for CDU from data/programs/cdu/program.pdf...
  ✓ 45 pages loaded
  ✓ 234 chunks created
  📝 Indexing in Pinecone (namespace: cdu)...
  ✓ Batch 1/3 indexed
  ✓ Batch 2/3 indexed
  ✓ Batch 3/3 indexed
✅ Program for CDU imported successfully (234 chunks)
```

---

## 🇫🇷 French Adaptation Scripts

### 5. `scripts/france/import_french_parties.py`

**Purpose**: Imports French political parties into Firestore

**Usage**:
```bash
poetry run python scripts/france/import_french_parties.py
```

**Imported parties**:
- **Left**: LFI, PS, EELV, PCF
- **Center**: Renaissance, MoDem, Horizons
- **Right**: LR, UDI
- **Far right**: RN, Reconquete
- **Other**: DLF, LIOT

**Total**: 13 French parties

**Output**:
```
📝 Importing 13 French political parties...

✓ Importing party 'LFI'...
✓ Importing party 'PS'...
...

✅ 13 French parties imported successfully!

🔴 Left:
  - LFI (lfi)
  - PS (ps)
  - EELV (eelv)
  - PCF (pcf)

🟡 Center:
  - Renaissance (renaissance)
  - MoDem (modem)
  - Horizons (horizons)
...
```

---

### 6. `scripts/france/scrape_assemblee_nationale.py`

**Purpose**: Scrapes votes from the French National Assembly

**Usage**:
```bash
# Scrape a specific ballot
poetry run python scripts/france/scrape_assemblee_nationale.py --scrutin 1234

# Scrape all ballots from a legislature
poetry run python scripts/france/scrape_assemblee_nationale.py --legislature 16 --all --max 100
```

**Options**:
- `--scrutin`: Ballot number to fetch
- `--legislature`: Legislature number (default: 16)
- `--all`: Fetch all ballots
- `--max`: Maximum number of ballots (default: 100)

**Extracted data**:
- Ballot ID
- Vote date
- Title and subject
- Ballot type
- Overall results (pour, contre, abstentions)
- Results by parliamentary group
- URL of the voted text

**Output**:
```
🔍 Collecting ballots for legislature 16...
📥 Fetching ballot 1...
  ✓ Ballot 1 retrieved
📥 Fetching ballot 2...
  ✓ Ballot 2 retrieved
...

✅ 100 ballots collected and saved to data/votes/legislature_16.json
```

---

### 7. `scripts/france/utils.py`

**Purpose**: Utility functions for the French adaptation

**Available functions**:

#### `convert_party_short_hand_to_party_id(party_short_hand: str) -> str`
Convert a party name to an ID
```python
convert_party_short_hand_to_party_id("La France Insoumise")  # → "lfi"
convert_party_short_hand_to_party_id("LFI")  # → "lfi"
```

#### `convert_groupe_to_party_id(groupe: str) -> str`
Convert a parliamentary group to a party ID
```python
convert_groupe_to_party_id("RE")  # → "renaissance"
convert_groupe_to_party_id("LFI-NUPES")  # → "lfi"
```

#### `format_date_french(date_str: str) -> str`
Format a date in French format
```python
format_date_french("2027-02-23")  # → "23/02/2027"
```

#### `format_date_long_french(date_str: str) -> str`
Format a date in long French format
```python
format_date_long_french("2027-02-23")  # → "23 février 2027"
```

#### `validate_french_response(response: str) -> Dict[str, bool]`
Validate that a response follows French conventions
```python
validate_french_response("Response with **markdown** [1]")
# → {"has_sources": True, "has_markdown": True, ...}
```

#### `detect_language(text: str) -> str`
Detect the language of a text
```python
detect_language("Bonjour le monde")  # → "fr"
detect_language("Guten Tag")  # → "de"
```

#### `get_coalition(party_id: str) -> str`
Return the coalition of a party
```python
get_coalition("lfi")  # → "NUPES"
get_coalition("renaissance")  # → "Ensemble"
```

---

## 🧪 Script Tests

### `scripts/test_scripts.py`

**Purpose**: Verifies that all scripts are valid

**Usage**:
```bash
poetry run python scripts/test_scripts.py
```

**Output**:
```
🧪 Testing Python scripts...

📝 Initialization scripts:
  ✓ init_pinecone.py
  ✓ init_firestore.py
  ✓ import_parties.py
  ✓ import_programs.py

🇫🇷 French adaptation scripts:
  ✓ import_french_parties.py
  ✓ scrape_assemblee_nationale.py
  ✓ utils.py

============================================================
Result: 7/7 valid scripts
✅ All scripts are valid!
```

---

## 📖 Full Documentation

For more information, see:
- [Initialization guide](./initialisation.md) - Step-by-step installation
- [France adaptation](./adaptation-france.md) - Migration guide
- [Scripts README](../scripts/README.md) - Detailed documentation
