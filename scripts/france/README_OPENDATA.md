# Using Open Data - 2024 Legislative Elections

This guide explains how to use the official data from the 2024 French legislative elections published on data.gouv.fr.

## 📚 Data Sources

The data comes from the official datasets of the French Ministry of the Interior published on data.gouv.fr:

### Election results

1. **First round (June 30, 2024)**
   - URL: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/
   - Formats: CSV, XLSX
   - Levels: Constituencies, Departments, Regions, Municipalities, Polling stations

2. **Second round (July 7, 2024)**
   - URL: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-2nd-tour/
   - Formats: CSV, XLSX
   - Levels: Constituencies, Departments, Regions, Municipalities, Polling stations

### Candidate lists

3. **First-round candidates**
   - URL: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-liste-des-candidats-du-1er-tour/
   - Formats: CSV, XLSX

4. **Second-round candidates**
   - URL: https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-liste-des-candidats-du-2nd-tour/
   - Formats: CSV, XLSX

## 🚀 Usage

### 1. Download the data

```bash
# Download all datasets
poetry run python scripts/france/download_opendata_elections.py --all

# Download only first-round results
poetry run python scripts/france/download_opendata_elections.py --resultats-tour1

# Download only second-round results
poetry run python scripts/france/download_opendata_elections.py --resultats-tour2

# Download only first-round candidates
poetry run python scripts/france/download_opendata_elections.py --candidats-tour1

# Download only second-round candidates
poetry run python scripts/france/download_opendata_elections.py --candidats-tour2

# Download only CSV files
poetry run python scripts/france/download_opendata_elections.py --all --format csv

# Force re-download (no cache)
poetry run python scripts/france/download_opendata_elections.py --all --no-cache
```

### 2. Analyze the data

```bash
# Analyze results by constituency
poetry run python scripts/france/analyze_election_data.py --circonscriptions

# Analyze candidate list
poetry run python scripts/france/analyze_election_data.py --candidats

# Generate overall statistics
poetry run python scripts/france/analyze_election_data.py --stats

# Run all analyses
poetry run python scripts/france/analyze_election_data.py --all
```

### 3. View cache statistics

```bash
# Show cache statistics
poetry run python scripts/france/show_cache_stats.py

# Clear cache
poetry run python scripts/france/show_cache_stats.py --clear-cache
```

## 📁 File Structure

```
data/
├── elections_2024/                    # Downloaded data
│   ├── resultats_tour1_circonscriptions_csv
│   ├── resultats_tour1_circonscriptions_xlsx
│   ├── resultats_tour1_departements_csv
│   ├── resultats_tour1_regions_csv
│   ├── resultats_tour2_circonscriptions_csv
│   ├── resultats_tour2_circonscriptions_xlsx
│   ├── candidats_tour1_france_entiere_csv
│   ├── candidats_tour1_france_entiere_xlsx
│   └── ...
├── processed_elections_2024/          # Processed data
│   ├── circonscriptions_tour1.json
│   ├── circonscriptions_tour2.json
│   ├── candidats_tour1.json
│   └── stats.json
├── cache/
│   └── opendata/                      # Download cache
│       ├── 5163f2e3-1362-4c35-89a0-1934bb74f2d9
│       ├── 41ed46cd-77c2-4ecc-b8eb-374aa953ca39
│       └── ...
└── logs/
    └── opendata/                      # Download logs
        ├── resultats_tour1_circonscriptions_csv.log
        ├── resultats_tour2_circonscriptions_csv.log
        └── ...
```

## 📊 Data Format

### Results by constituency (CSV)

Main columns:
- `Code du departement`
- `Libelle du departement`
- `Code de la circonscription`
- `Libelle de la circonscription`
- `Inscrits`
- `Abstentions`
- `Votants`
- `Blancs`
- `Nuls`
- `Exprimes`
- Results by candidate/label

### Candidate list (CSV)

Main columns:
- `Code du departement`
- `Code de la circonscription`
- `N° de panneau`
- `Nom`
- `Prenom`
- `Sexe`
- `Date de naissance`
- `Code de la nuance`
- `Libelle de la nuance`
- `Nom du binome`
- `Prenom du binome`

## 🔄 Comparison with Scraping

### Open Data Advantages

✅ **Official data** - Directly from the Ministry of the Interior  
✅ **Complete data** - All geographic levels  
✅ **Structured data** - Standardized CSV/XLSX format  
✅ **No scraping** - No blocking risk  
✅ **Stable API** - Permanent URLs  
✅ **Updates** - Final and verified data  

### Drawbacks

❌ **Limited historical data** - Only 2024 elections  
❌ **No parliamentary ballots** - Only election results  
❌ **Fixed format** - Structure imposed by the Ministry  

## 🎯 Next Steps

1. **Import into Pinecone**
   - Create a script to vectorize results
   - Import into the `justified-voting-behavior-index`

2. **Data enrichment**
   - Add programs of elected candidates
   - Link with parliamentary groups

3. **Advanced analysis**
   - Calculate victory margins
   - Identify key constituencies
   - Analyze vote transfers

## 📝 Usage Examples

### Download and analyze first-round results

```bash
# 1. Download data
poetry run python scripts/france/download_opendata_elections.py --resultats-tour1 --format csv

# 2. Analyze data
poetry run python scripts/france/analyze_election_data.py --circonscriptions

# 3. View statistics
poetry run python scripts/france/analyze_election_data.py --stats
```

### Full workflow

```bash
# 1. Download all data
poetry run python scripts/france/download_opendata_elections.py --all --format csv

# 2. Analyze all data
poetry run python scripts/france/analyze_election_data.py --all

# 3. View cache statistics
poetry run python scripts/france/show_cache_stats.py
```

## 🔗 Useful Links

- [data.gouv.fr](https://www.data.gouv.fr/)
- [data.gouv.fr API](https://www.data.gouv.fr/api/1/)
- [API documentation](https://guides.data.gouv.fr/publier-des-donnees/guide-data.gouv.fr/api/reference)
- [Open Licence 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/)

## 📄 License

The data is published under the [Open Licence 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/) by the French Ministry of the Interior.

You are free to:
- Reproduce, copy, publish, and transmit the data
- Share and redistribute the data
- Adapt, modify, extract, and transform the data
- Use the data commercially

Provided that you:
- Mention the data source
- Mention the date of last update
