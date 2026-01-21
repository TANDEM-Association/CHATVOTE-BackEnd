# Adaptation for the French System

This guide explains how to adapt wahl.chat for French elections.

---

## 1. French Electoral Context

### Election Types

The system can be adapted for:
- **Presidential elections** (2027)
- **Legislative elections** (2027)
- **European elections** (2024, 2029)
- **Regional/departmental elections**

### Electoral Calendar

```python
# Update in src/prompts.py
"""
## Legislative Elections 2027
First round date: [DATE]
Second round date: [DATE]
Reference URL: https://www.vie-publique.fr/elections
"""
```

---

## 2. French Political Parties

### 2.1 Main Parties

Replace in `src/models/structured_outputs.py`:

```python
class PartyID(StrEnum):
    # Left
    LFI = "lfi"                    # La France Insoumise
    PCF = "pcf"                    # Parti Communiste Francais
    PS = "ps"                      # Parti Socialiste
    EELV = "eelv"                  # Europe Ecologie Les Verts

    # Center
    RENAISSANCE = "renaissance"     # Renaissance (ex-LREM)
    MODEM = "modem"                # MoDem
    HORIZONS = "horizons"          # Horizons

    # Right
    LR = "lr"                      # Les Republicains
    UDI = "udi"                    # Union des Democrates et Independants

    # Far right
    RN = "rn"                      # Rassemblement National
    RECONQUETE = "reconquete"      # Reconquete

    # Other
    DLF = "dlf"                    # Debout la France

    # Neutral assistant
    VOTE_CHAT = "vote-chat"        # Name to adapt
```

### 2.2 Coalitions and Alliances

```python
# Nouvelle Union Populaire Ecologique et Sociale (NUPES)
NUPES_PARTIES = ["lfi", "ps", "eelv", "pcf"]

# Ensemble (presidential majority)
ENSEMBLE_PARTIES = ["renaissance", "modem", "horizons"]

# Right-wing union
DROITE_PARTIES = ["lr", "udi"]
```

### 2.3 Name Mapping

```python
# data/scripts/script_utils.py
def convert_party_short_hand_to_party_id(party_short_hand: str) -> str:
    mapping = {
        "La France Insoumise": "lfi",
        "LFI": "lfi",
        "Parti Socialiste": "ps",
        "PS": "ps",
        "Europe Ecologie Les Verts": "eelv",
        "EELV": "eelv",
        "Renaissance": "renaissance",
        "LREM": "renaissance",
        "La Republique En Marche": "renaissance",
        "Les Republicains": "lr",
        "LR": "lr",
        "Rassemblement National": "rn",
        "RN": "rn",
        "Front National": "rn",
        "FN": "rn",
        # ...
    }
    return mapping.get(party_short_hand, party_short_hand)
```

---

## 3. National Assembly

### 3.1 Vote Scraping

Adapt `data/scripts/scrape_voting_behavior.ipynb`:

```python
def scrape_voting_behavior_france(scrutin_id: str) -> Dict:
    """
    Scrape vote data from the National Assembly
    Source: https://www2.assemblee-nationale.fr/scrutins/
    """
    url = f"https://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/16/(num)/{scrutin_id}"

    # Parse the page
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract information
    vote_data = {
        "id": scrutin_id,
        "url": url,
        "date": extract_date(soup),
        "title": extract_title(soup),
        "description": extract_description(soup),
        "voting_results": {
            "overall": extract_overall_results(soup),
            "by_party": extract_party_results(soup)
        }
    }

    return vote_data
```

### 3.2 French Vote Structure

```python
# src/models/vote.py - To adapt
class VoteFrance(BaseModel):
    id: str                          # Vote number
    legislature: int                 # Legislature number (e.g., 16)
    url: str                         # assemblee-nationale.fr URL
    date: str                        # Vote date
    title: str                       # Vote title
    type: str                        # Type (public ballot, solemn, etc.)
    subject: str                     # Subject of the vote
    voting_results: VotingResults    # Results
    text_url: Optional[str]          # URL of the voted text
```

### 3.3 Parliamentary Groups

```python
# Groups in the National Assembly (16th legislature)
GROUPES_AN = {
    "RE": "renaissance",        # Renaissance
    "LFI-NUPES": "lfi",        # LFI-NUPES
    "RN": "rn",                # Rassemblement National
    "LR": "lr",                # Les Republicains
    "SOC": "ps",               # Socialists
    "ECOLO": "eelv",           # Ecologists
    "LIOT": "liot",            # Liberties, Independents, Overseas and Territories
    "HOR": "horizons",         # Horizons
    "GDR": "pcf",              # Democratic and Republican Left
    "NI": "non_inscrit",       # Non-attached MPs
}
```

---

## 4. Questions to Government

### 4.1 Data Sources

```python
# New sources for parliamentary questions
QUESTIONS_SOURCES = {
    "questions_ecrites": "https://questions.assemblee-nationale.fr/q16/",
    "questions_orales": "https://www.assemblee-nationale.fr/dyn/16/comptes-rendus/seance/",
    "questions_gouvernement": "https://videos.assemblee-nationale.fr/",
}
```

### 4.2 Question Scraping

```python
def scrape_questions_ecrites(depute_id: str, party_id: str):
    """
    Scrape written questions from an MP
    """
    url = f"https://questions.assemblee-nationale.fr/q16/auteur/{depute_id}"
    # Parse and extract questions
    # Index in Pinecone with namespace f"{party_id}-parliamentary-questions"
```

---

## 5. Prompt Translation

### 5.1 Main Prompt

```python
# src/prompts.py
party_response_system_prompt_template_str = """
# Role
You are a chatbot that provides citizens with sourced information
about the party {party_name} ({party_long_name}) for the 2027 legislative elections.

# Contextual information
## Legislative Elections 2027
First round date: [DATE]
Second round date: [DATE]
More information URL: https://www.vie-publique.fr/elections

## Party
Abbreviation: {party_name}
Full name: {party_long_name}
Description: {party_description}
Lead candidate: {party_candidate}
Website: {party_url}

## Current information
Date: {date}
Time: {time}

## Extracts from party documents you can use in your answers
{rag_context}

# Task
Generate an answer based on the contextual information and the provided guidelines.

{answer_guidelines}
"""
```

### 5.2 Answer Guidelines

```python
def get_chat_answer_guidelines(party_name: str, is_comparing: bool = False):
    if not is_comparing:
        comparison_handling = f"For comparisons or questions about other parties, politely state that you are only responsible for {party_name}. Mention that the user can create a chat with multiple parties via the homepage or navigation menu."
    else:
        comparison_handling = "For comparisons or questions about other parties, answer from the perspective of a neutral observer. Structure your response clearly."

    guidelines_str = f"""
## Guidelines for your answer
1. **Source-based**
    - For questions about the party program, rely exclusively on the provided context.
    - Focus on relevant information from the provided extracts.
    - You may answer general questions about the party using your own knowledge. Note that your knowledge only goes up to October 2023.
2. **Strict neutrality**
    - Do not evaluate party positions.
    - Avoid evaluative adjectives or phrasing.
    - Provide NO voting recommendations.
    - Use conditional phrasing when reporting statements (e.g., Mr. X notes that climate would be important.)
3. **Transparency**
    - Clearly state uncertainties.
    - Admit when you do not know something.
    - Distinguish between facts and interpretations.
    - Clearly mark answers based on your own knowledge and not the provided documents. Format these in italics and do not cite sources.
4. **Response style**
    - Respond in a sourced, concrete, and easily understandable way.
    - Provide precise figures and dates when available in the extracts.
    - Use informal address.
    - Citation style:
        - After each sentence, provide a list of integer source IDs used. The list must be inside brackets []. Example: [id] for one source or [id1, id2, ...] for multiple sources.
        - If you did not use any source for a sentence, do not cite sources and format the sentence in italics.
    - Response format:
        - Respond in Markdown.
        - Use line breaks, paragraphs, and lists to structure the response clearly.
        - Use bullets to organize your answers.
        - Bold keywords and the most important information.
    - Response length:
        - Keep your answer very short. Respond in 1-3 short sentences or bullet points.
        - If the user explicitly asks for more detail, you can provide longer answers.
        - The response should fit a chat format. Pay special attention to length.
    - Language:
        - Respond exclusively in French.
        - Use easy-to-understand French and briefly explain technical terms.
5. **Limits**
    - Actively state when:
        - Information may be outdated.
        - Facts are unclear.
        - A question cannot be answered neutrally.
        - Personal judgments are required.
    - {comparison_handling}
6. **Data protection**
    - Do NOT ask for voting intentions.
    - Do NOT ask for personal data.
    - You do not collect any personal data.
"""
    return guidelines_str
```

---

## 6. French Sources

### 6.1 Official Sources

```python
# src/prompts.py - perplexity_user_prompt
"""
Keywords: {party_name}, Legislative elections 2027, feasibility,
short-term effects, long-term effects, criticism, National Assembly,
Vie Publique, France Info, France TV, Le Monde, Le Figaro, Liberation,
INSEE, OFCE, France Strategie, CEVIPOF, Sciences Po, Fondation Jean Jaures,
Fondapol, Institut Montaigne, Terra Nova
"""
```

### 6.2 Source Mapping

| Type | Germany | France |
|------|-----------|--------|
| Civic education | bpb | Vie Publique |
| Public TV | ARD, ZDF | France TV, France Info |
| Quality press | FAZ, SZ | Le Monde, Le Figaro, Liberation |
| Economics | DIW, IW, ifo | INSEE, OFCE, France Strategie |
| Political science | - | CEVIPOF, Sciences Po |
| Think tanks | - | Fondapol, Institut Montaigne, Terra Nova, Fondation Jean Jaures |

---

## 7. Formats and Conventions

### 7.1 Date Format

```python
# German: Tag. Monat Jahr (23. Februar 2025)
# French: DD/MM/YYYY (23/02/2027)

def format_date_french(date_str: str) -> str:
    """Convert a date to French format"""
    from datetime import datetime
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d/%m/%Y")
```

### 7.2 Informal vs Formal Address

**Option 1: Informal (like German)**
```python
"Use informal address."
```

**Option 2: Formal (more formal)**
```python
"Use formal address."
```

Recommendation: **Informal** for a modern and accessible tone.

### 7.3 Typographic Conventions

```python
# Quotation marks
# German: "Text"
# French: « Texte »

# Non-breaking spaces
# Before: ; : ! ?
# Example: "Bonjour !"

# Capitalization
# Parties: Les Republicains, La France Insoumise
# Institutions: Assemblee Nationale, Senat
```

---

## 8. Electoral System

### 8.1 French Specifics

```python
# src/prompts.py - Add a section on the electoral system
"""
## French Electoral System
- **Two-round single-member majority vote** for legislative elections
- **577 MPs** elected in as many constituencies
- **First-round threshold**: 12.5% of registered voters to reach the second round
- **Term length**: 5 years
- **Parity**: Parity requirement on lists for some elections
"""
```

### 8.2 Electoral Compass

Replace references to Wahl-O-Mat:

```python
# src/prompts.py
"""
vote.chat Compass is an AI-based alternative to classic electoral compasses.
Users answer various political questions by stating whether they agree
or disagree with statements. At the end, they get an overview of the party
that best matches their political views.
"""
```

---

## 9. Data to Collect

### 9.1 Election Programs

Sources:
- Official party websites
- Legal deposit (BNF)
- Media (election dossiers)

Formats:
- Program PDFs
- Professions of faith
- Campaign speeches

### 9.2 National Assembly Votes

```python
# Collection script
def collect_votes_assemblee_nationale(legislature: int = 16):
    """
    Collect all ballots from a legislature
    """
    base_url = f"https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/{legislature}"

    # Parse the list of ballots
    # For each ballot, call scrape_voting_behavior_france()
    # Save to data/votes/
```

### 9.3 Parliamentary Questions

```python
def collect_questions_by_party(party_id: str):
    """
    Collect questions from MPs of a party
    """
    # 1. Get the list of MPs for the party
    # 2. For each MP, scrape their questions
    # 3. Index in Pinecone
```

---

## 10. Pinecone Configuration

### 10.1 New Namespaces

```python
# all-parties-index
namespaces = [
    "lfi",           # La France Insoumise
    "ps",            # Parti Socialiste
    "eelv",          # EELV
    "renaissance",   # Renaissance
    "modem",         # MoDem
    "lr",            # Les Republicains
    "rn",            # Rassemblement National
    # ...
]

# parliamentary-questions-index
namespaces = [
    "lfi-parliamentary-questions",
    "ps-parliamentary-questions",
    # ...
]
```

### 10.2 Import Script

```python
# scripts/import_french_data.py
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def import_party_program(party_id: str, pdf_path: str):
    """Import an election program into Pinecone"""

    # Load the PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)

    # Index in Pinecone
    embed = OpenAIEmbeddings(model="text-embedding-3-large")
    index = pc.Index("all-parties-index")
    vector_store = PineconeVectorStore(index=index, embedding=embed)
    vector_store.add_documents(splits, namespace=party_id)

    print(f"✓ Program for {party_id} imported ({len(splits)} chunks)")
```

---

## 11. Tests and Validation

### 11.1 Test Questions

Create a set of French questions:

```python
# tests/test_questions_france.py
TEST_QUESTIONS = [
    "What is LFI's position on the minimum wage?",
    "How does Renaissance plan to reform pensions?",
    "What does RN propose on immigration?",
    "What is EELV's environmental policy?",
    "How does LR want to reduce public debt?",
]
```

### 11.2 Response Validation

```python
def validate_french_response(response: str) -> bool:
    """Validate that a response follows French conventions"""
    checks = {
        "has_sources": "[" in response and "]" in response,
        "is_french": detect_language(response) == "fr",
        "is_neutral": not contains_opinion_words(response),
        "has_markdown": "**" in response or "*" in response,
    }
    return all(checks.values())
```

---

## 12. Migration Checklist

### Phase 1: Preparation
- [ ] Identify target elections (legislatives 2027)
- [ ] List parties to include
- [ ] Collect election programs
- [ ] Scrape National Assembly votes

### Phase 2: Translation
- [ ] Translate all system prompts
- [ ] Adapt terminology
- [ ] Modify formats (dates, citations)
- [ ] Update reference sources

### Phase 3: Data
- [ ] Create new Pinecone namespaces
- [ ] Import party programs
- [ ] Index parliamentary votes
- [ ] Add questions to government

### Phase 4: Code
- [ ] Update data models
- [ ] Adapt scrapers
- [ ] Modify party mappings
- [ ] Adjust prompts

### Phase 5: Tests
- [ ] Test with French questions
- [ ] Validate neutrality of responses
- [ ] Verify cited sources
- [ ] Test party comparisons

### Phase 6: Deployment
- [ ] Configure Firebase for France
- [ ] Deploy on a French domain
- [ ] Update documentation
- [ ] Train users

---

## 13. Useful Resources

### APIs and Open Data
- **data.gouv.fr**: French public data
- **NosDeputes.fr**: Parliamentary activity
- **Regards Citoyens**: Democratic transparency
- **National Assembly API**: Official data

### Documentation
- **Vie Publique**: https://www.vie-publique.fr
- **National Assembly**: https://www.assemblee-nationale.fr
- **Legifrance**: https://www.legifrance.gouv.fr

### Tools
- **BeautifulSoup**: Web scraping
- **Scrapy**: Scraping framework
- **pandas**: Data manipulation
- **spaCy**: French NLP

---

## 14. Project Name

Suggestions for the French name:
- **vote.chat** (direct equivalent)
- **election.chat**
- **citoyen.chat**
- **debat.chat**
- **programme.chat**

Check domain availability and adapt branding.

---

## Contact and Support

For any questions about the French adaptation:
- See the complete documentation in `/doc`
- Open an issue on GitHub
- Contact the original team: info@wahl.chat
