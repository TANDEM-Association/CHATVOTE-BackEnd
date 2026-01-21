# Specifics of the German Political System

This document details all project elements that are specific to the German political system and must be adapted for other countries.

---

## 1. Electoral Context

### Bundestagswahl 2025 (Federal Elections)

The project was designed for the **German federal elections on February 23, 2025**.

**References in code:**
```python
# src/prompts.py
"""
## Bundestagswahl 2025
Termin: 23. Februar 2025
URL fur weitere Informationen zur Wahl:
https://www.zdf.de/nachrichten/politik/deutschland/bundestagswahl-termin-kandidaten-umfrage-100.html
"""
```

**To adapt:**
- Election date
- Election type (presidential, legislative, etc.)
- Official reference URL
- Terminology (Bundestagswahl → legislative election)

---

## 2. German Political Parties

### 2.1 Party List

The system is configured for the following parties:

```python
# src/models/structured_outputs.py
class PartyID(StrEnum):
    AFD = "afd"              # Alternative fur Deutschland (far right)
    BSW = "bsw"              # Bundnis Sahra Wagenknecht (left)
    CDU = "cdu"              # Christlich Demokratische Union (center-right)
    FDP = "fdp"              # Freie Demokratische Partei (liberal)
    FREIE_WAEHLER = "fw"     # Freie Wahler (regionalist)
    GRUENE = "gruene"        # Bundnis 90/Die Grunen (green)
    LINKE = "linke"          # Die Linke (left)
    PIRATEN = "piraten"      # Piratenpartei (digital)
    SPD = "spd"              # Sozialdemokratische Partei (center-left)
    VOLT = "volt"            # Volt (pro-European)
    OEDP = "oedp"            # Okologisch-Demokratische Partei
    TIERSCHUTZPARTEI = "tierschutzpartei"  # Animal protection party
    WAHL_CHAT = "wahl-chat"  # Neutral assistant
```

### 2.2 Party Data Structure

```python
# src/models/party.py
class Party(BaseModel):
    party_id: str                    # Unique identifier
    name: str                        # Short name (e.g., "CDU")
    long_name: str                   # Full name
    description: str                 # Party description
    website_url: str                 # Official website
    candidate: str                   # Spitzenkandidat (lead candidate)
    election_manifesto_url: str      # Election program URL
    is_small_party: bool             # Small or major party
    is_already_in_parliament: bool   # Already in the Bundestag
```

### 2.3 Party Name Mapping

```python
# data/scripts/script_utils.py
def convert_party_short_hand_to_party_id(party_short_hand: str) -> str:
    mapping = {
        "CDU/CSU": "cdu",
        "CDU": "cdu",
        "SPD": "spd",
        "DIE LINKE.": "linke",
        "LINKE": "linke",
        "B90/GRUNE": "gruene",
        "GRUNE": "gruene",
        "FDP": "fdp",
        "AfD": "afd",
        "Volt": "volt",
        "BSW": "bsw",
        # ...
    }
```

**To adapt:**
- Replace with French parties (LR, PS, LREM/Renaissance, RN, LFI, EELV, etc.)
- Update descriptions and positioning
- Update URLs and candidates

---

## 3. Bundestag (German Parliament)

### 3.1 Parliamentary Vote Data

The system integrates voting history from the Bundestag.

**Data source:**
```python
# data/scripts/scrape_voting_behavior.ipynb
url = f"https://www.bundestag.de/parlament/plenum/abstimmung/abstimmung?id={vote_id}"
```

**Vote structure:**
```python
# src/models/vote.py
class Vote(BaseModel):
    id: str                          # Vote ID
    url: str                         # bundestag.de URL
    date: str                        # Vote date
    title: str                       # Vote title
    subtitle: Optional[str]          # Subtitle
    detail_text: Optional[str]       # Detailed text
    links: List[Link]                # Links to documents
    voting_results: VotingResults    # Results by party
    short_description: Optional[str] # Short description
    vote_category: Optional[str]     # Category (health, economy, etc.)
    submitting_parties: Optional[list[str]]  # Proposing parties
```

**Results by party:**
```python
class VotingResultsByParty(BaseModel):
    party: str              # Party ID
    members: int            # Number of MPs
    yes: int                # Yes votes
    no: int                 # No votes
    abstain: int            # Abstentions
    not_voted: int          # Not voting
    justification: str | None  # Vote justification
```

### 3.2 Pinecone Index for Votes

```python
# src/vector_store_helper.py
VOTING_BEHAVIOR_INDEX_NAME = "justified-voting-behavior-index"

async def identify_relevant_votes(
    rag_query: str,
    n_docs: int = 5,
    score_threshold: float = 0.5
) -> list[Document]:
    """Search for relevant Bundestag votes"""
    return await _identify_relevant_documents(
        vector_store=voting_behavior_vector_store,
        namespace="vote_summary",
        rag_query=rag_query,
        n_docs=n_docs,
        score_threshold=score_threshold,
    )
```

**To adapt:**
- Scrape data from the French National Assembly
- Adapt vote structure (public ballots)
- Modify vote categories
- Update source URLs

---

## 4. Parliamentary Questions

### 4.1 Questions Index

```python
# src/vector_store_helper.py
PARLIAMENTARY_QUESTIONS_INDEX_NAME = "parliamentary-questions-index"

async def identify_relevant_parliamentary_questions(
    party: Union[Party, str],
    rag_query: str,
    n_docs: int = 5,
    score_threshold: float = 0.7,
) -> list[Document]:
    """Parliamentary questions by party"""
    namespace = f"{party.party_id}-parliamentary-questions"
    # ...
```

**To adapt:**
- French questions to government
- Written/oral questions
- Interpellations
- Source: questions.assemblee-nationale.fr

---

## 5. German Prompts

### 5.1 Prompt Language

**All system prompts are in German**:

```python
# src/prompts.py
party_response_system_prompt_template_str = """
# Rolle
Du bist ein Chatbot, der Burger:innen quellenbasierte Informationen
zur Partei {party_name} ({party_long_name}) fur die Bundestagswahl 2025 gibt.

# Hintergrundinformationen
## Bundestagswahl 2025
Termin: 23. Februar 2025
...
"""
```

**Elements to translate:**
- All system prompts
- Answering instructions
- Neutrality guidelines
- Citation format
- Error messages

### 5.2 Specific Terminology

| German | English |
|----------|----------|
| Bundestagswahl | Federal election |
| Bundestag | Federal parliament |
| Spitzenkandidat*In | Lead candidate |
| Wahlprogramm | Election program |
| Abstimmung | Vote / ballot |
| Fraktion | Parliamentary group |
| Koalition | Coalition |
| Opposition | Opposition |
| Regierung | Government |
| Burger:innen | Citizens |

### 5.3 Response Format

Responses use German conventions:

```python
# src/prompts.py
"""
- Spreche Nutzer:innen mit Du an.  # Informal address
- Zitierstil: [id] fur eine Quelle  # Citations
- Nutze das gangige deutsche Datenformat (Tag. Monat Jahr)  # Date format
"""
```

**To adapt:**
- Formal vs informal address in French
- French date format (DD/MM/YYYY)
- French typographic conventions

---

## 6. Sources and References

### 6.1 German Journalistic Sources

```python
# src/prompts.py - perplexity_user_prompt
"""
Schlusselworter: {party_name}, Bundestagswahl 2025, Machbarkeit,
kurzfristige Effekte, langfristige Effekte, Kritik, Bundestag,
bpb, ARD, ZDF, FAZ, SZ,
Deutsches Institut fur Wirtschaftsforschung (DIW),
Institut der deutschen Wirtschaft (IW),
Leibniz-Zentrum fur Europaische Wirtschaftsforschung (ZEW),
Institut fur Wirtschaftsforschung (ifo),
Institut fur Wirtschaftsforschung (IfW)
"""
```

**German sources:**
- **bpb**: Bundeszentrale fur politische Bildung
- **ARD, ZDF**: Public TV
- **FAZ**: Frankfurter Allgemeine Zeitung
- **SZ**: Suddeutsche Zeitung
- **DIW, IW, ZEW, ifo, IfW**: Economic research institutes

**Replace with French sources:**
- **Vie Publique** (vie-publique.fr)
- **France TV, France Info**
- **Le Monde, Le Figaro, Liberation**
- **INSEE, OFCE, France Strategie**
- **CEVIPOF, Sciences Po**

---

## 7. Electoral System

### 7.1 German Specifics

The German system uses:
- **Zweitstimme** (second vote): Vote for a party (proportional)
- **Erststimme** (first vote): Vote for a candidate (majoritarian)
- **5% Hurdle**: 5% threshold to enter the Bundestag
- **Uberhangmandate**: Overhang seats

### 7.2 Wahl-O-Mat

The project is inspired by the German **Wahl-O-Mat**:

```python
# src/prompts.py
"""
wahl.chat Swiper ist eine KI-gestutzte Alternative zum klassischen Wahl-O-Mat.
"""
```

**To adapt:**
- Reference the French system (no official equivalent)
- Explain the concept of an "electoral compass"

---

## 8. Government and Coalitions

### 8.1 Government Detection

```python
# data/scripts/add_additional_data.ipynb
if parse_german_date(vote["date"]) > datetime(2021, 12, 7):
    # Coalition SPD-FDP-Grune (Ampelkoalition)
    clean_submitting_parties.append("SPD")
    clean_submitting_parties.append("FDP")
    clean_submitting_parties.append("GRUNE")
else:
    # Grand coalition CDU-SPD
    clean_submitting_parties.append("CDU")
    clean_submitting_parties.append("SPD")
```

**To adapt:**
- Dates of French governments
- Majority composition
- Coalition logic

---

## 9. Structured Data

### 9.1 Firebase Collections

```
firestore/
├── parties/                    # Political parties
│   ├── cdu/
│   ├── spd/
│   └── ...
├── proposed_questions/         # Suggested questions by party
│   ├── afd/questions/
│   ├── cdu/questions/
│   └── ...
└── sources/                    # Source documents
    ├── cdu/
    │   └── programme.pdf
    └── ...
```

### 9.2 Pinecone Namespaces

```
all-parties-index:
├── cdu                         # CDU documents
├── spd                         # SPD documents
├── gruene                      # Grune documents
└── ...

justified-voting-behavior-index:
└── vote_summary                # Bundestag vote summaries

parliamentary-questions-index:
├── cdu-parliamentary-questions
├── spd-parliamentary-questions
└── ...
```

---

## 10. Adaptation Checklist

To adapt the system to another country:

### Data
- [ ] Replace the party list
- [ ] Scrape parliamentary votes
- [ ] Collect election programs
- [ ] Import parliamentary questions

### Configuration
- [ ] Update election dates
- [ ] Adapt reference URLs
- [ ] Modify journalistic sources
- [ ] Change research institutes

### Code
- [ ] Translate all prompts
- [ ] Adapt terminology
- [ ] Modify formats (dates, citations)
- [ ] Update data models

### Pinecone
- [ ] Recreate indexes with new data
- [ ] Adapt namespaces
- [ ] Reindex all documents

### Tests
- [ ] Test with local questions
- [ ] Verify answer relevance
- [ ] Validate cited sources

---

## Resources

- **Bundestag**: https://www.bundestag.de
- **Wahl-O-Mat**: https://www.wahl-o-mat.de
- **bpb**: https://www.bpb.de
- **Abgeordnetenwatch**: https://www.abgeordnetenwatch.de

For France, see [adaptation-france.md](./adaptation-france.md).
