# wahl.chat Scripts

This folder contains all utility scripts to initialize and manage the wahl.chat project.

---

## 📋 Available Scripts

### Initialization

#### `init_pinecone.py`
Creates the 3 Pinecone indexes required by the project.

```bash
poetry run python scripts/init_pinecone.py
```

**Indexes created**:
- `all-parties-index` - Party programs and documents
- `justified-voting-behavior-index` - Bundestag voting behavior
- `parliamentary-questions-index` - Parliamentary questions

#### `init_firestore.py`
Initializes Firebase Firestore with base collections.

```bash
poetry run python scripts/init_firestore.py
```

**Collections created**:
- `parties` - Political party data
- `proposed_questions` - Suggested questions
- `cached_answers` - Cached answers
- `llm_status` - LLM status
- `chat_sessions` - Chat sessions

---

### Data Import

#### `import_parties.py`
Imports German political parties into Firestore.

```bash
poetry run python scripts/import_parties.py
```

**Imported parties**: CDU, SPD, Grune, FDP, Linke, AfD, BSW, etc.

#### `import_programs.py`
Imports election programs (PDFs) into Pinecone.

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

---

## 🇫🇷 Scripts for French Adaptation

Scripts to adapt the system to the French context are in the `france/` folder.

### `france/import_french_parties.py`
Imports French political parties into Firestore.

```bash
poetry run python scripts/france/import_french_parties.py
```

**Imported parties**: LFI, PS, EELV, Renaissance, LR, RN, etc.

### `france/scrape_assemblee_nationale.py`
Scrapes votes from the French National Assembly.

```bash
# Scrape a specific ballot
poetry run python scripts/france/scrape_assemblee_nationale.py --scrutin 1234

# Scrape all ballots from a legislature
poetry run python scripts/france/scrape_assemblee_nationale.py --legislature 16 --all --max 100
```

**Options**:
- `--scrutin`: Ballot number
- `--legislature`: Legislature number (default: 16)
- `--all`: Fetch all ballots
- `--max`: Maximum number of ballots (default: 100)

### `france/utils.py`
Utility functions for the French adaptation.

**Available functions**:
- `convert_party_short_hand_to_party_id()` - Convert a party name to an ID
- `convert_groupe_to_party_id()` - Convert a parliamentary group to a party ID
- `format_date_french()` - Format a date in French format
- `validate_french_response()` - Validate a French response
- `detect_language()` - Detect the language of a text
- `get_coalition()` - Return a party coalition

---

## 🔧 Other Scripts

### `create_jupyter_password.py`
Creates a password for Jupyter Notebook.

```bash
poetry run python scripts/create_jupyter_password.py
```

### `start_jupyter.sh`
Starts Jupyter Notebook.

```bash
./scripts/start_jupyter.sh
```

---

## 📖 Documentation

For more information, see the full documentation:
- [Initialization guide](../doc/initialisation.md)
- [Adaptation for France](../doc/adaptation-france.md)
- [Architecture](../doc/architecture.md)

---

## 🚀 Complete Installation Workflow

### For the German System

```bash
# 1. Create Pinecone indexes
poetry run python scripts/init_pinecone.py

# 2. Initialize Firestore
poetry run python scripts/init_firestore.py

# 3. Import German parties
poetry run python scripts/import_parties.py

# 4. Import election programs
poetry run python scripts/import_programs.py --all --data-dir data/programs/
```

### For French Adaptation

```bash
# 1. Create Pinecone indexes (if not already done)
poetry run python scripts/init_pinecone.py

# 2. Initialize Firestore (if not already done)
poetry run python scripts/init_firestore.py

# 3. Import French parties
poetry run python scripts/france/import_french_parties.py

# 4. Import French programs
poetry run python scripts/import_programs.py --all --data-dir data/programs_france/

# 5. Scrape National Assembly votes
poetry run python scripts/france/scrape_assemblee_nationale.py --legislature 16 --all --max 500
```

---

## ⚠️ Prerequisites

Before running these scripts, make sure you have:

1. **Installed dependencies**:
   ```bash
   poetry install
   ```

2. **Configured environment variables** in `.env`:
   - `PINECONE_API_KEY`
   - `OPENAI_API_KEY`
   - `FIREBASE_CREDENTIALS_PATH`

3. **Downloaded the Firebase credentials file**:
   - From Firebase Console > Project Settings > Service Accounts
   - Save as `wahl-chat-dev-firebase-adminsdk.json`

---

## 🐛 Troubleshooting

### Error: "PINECONE_API_KEY not found"
**Solution**: Verify the variable is defined in `.env`

### Error: "Firebase credentials not found"
**Solution**: Download the credentials file from Firebase Console

### Error: "Index already exists"
**Solution**: Expected. The script skips existing indexes automatically.

---

## 📞 Support

For any questions:
- See the [full documentation](../doc/)
- Open an issue on GitHub
- Contact: info@wahl.chat
