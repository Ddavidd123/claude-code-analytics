# Claude Code Analytics Platform

An end-to-end analytics platform that processes telemetry data from Claude Code sessions and transforms it into actionable insights through an interactive dashboard.

## 🎯 Project Overview

This platform consists of four main components:

1. **Data Generation** (`generate_fake_data.py`) - Synthetic telemetry data generator
2. **Data Processing** (`data_processor.py`) - ETL pipeline to normalize and aggregate data
3. **Analytics Engine** (`analytics.py`) - Compute insights and metrics
4. **Interactive Dashboard** (`dashboard.py`) - Streamlit visualization interface

## 🚀 Quick Start

### 1. Setup

```bash
# Navigate to project directory
cd claude-code-analytics

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Telemetry Data

```bash
# Generate synthetic data (default: 30 users, 500 sessions, 30 days)
python src/generate_fake_data.py

# Or generate larger dataset
python src/generate_fake_data.py --num-users 100 --num-sessions 5000 --days 60
```

**Output files:**
- `output/telemetry_logs.jsonl` - Raw telemetry events
- `output/employees.csv` - Employee directory

### 3. Run the Dashboard

```bash
streamlit run src/dashboard.py
```

The dashboard will open at `http://localhost:8501`

## 📊 Dashboard Features

### Overview Page
- **Key Metrics**: Total users, sessions, API calls, and costs
- **Performance Summary**: Essential system-level metrics

### Models Page
- Model usage distribution
- Cost analysis by model
- API call frequency per model
- Average duration per model

### Tools Page
- Tool usage frequency
- Tool acceptance rates
- Tool success rates
- Tool execution duration

### Users Page
- User segmentation by level (L1-L10)
- User distribution by engineering practice
- Geographic distribution of users
- Cost and usage patterns by segment

### Top Users Page
- Ranked users by cost
- Ranked users by API calls
- User metadata (level, sessions)

### Performance Page
- API latency metrics (avg, median, p95)
- Tool success rates
- Cache efficiency metrics
- System-level performance insights

### Errors Page
- Error frequency analysis
- Error distribution by type
- Error rate calculations

## 📁 Project Structure

```
claude-code-analytics/
├── data/
│   ├── raw/                    # Raw telemetry data
│   └── processed/              # Processed datasets
├── src/
│   ├── generate_fake_data.py   # Data generation
│   ├── data_processor.py       # ETL pipeline
│   ├── analytics.py            # Analytics engine
│   └── dashboard.py            # Streamlit dashboard
├── notebooks/                  # Jupyter notebooks (exploratory analysis)
├── output/                     # Generated data output
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Core Components

### generate_fake_data.py
Generates realistic synthetic telemetry based on real Claude Code usage patterns:
- **Models**: Haiku, Opus, Sonnet variants with realistic cost/performance profiles
- **Tools**: 17 different tool types with usage weights
- **Users**: 30+ synthetic employees with metadata (level, practice, location)
- **Sessions**: Multi-turn coding sessions with realistic event sequences

**Usage:**
```bash
python src/generate_fake_data.py [OPTIONS]
  --num-users 30      # Number of engineers
  --num-sessions 500  # Total sessions
  --days 30           # Time span
  --output-dir output # Output directory
  --seed 42           # Random seed
```

### data_processor.py
Transforms raw telemetry into analytics-ready datasets:
- **Normalization**: Converts nested JSON to structured tables
- **Enrichment**: Joins with employee metadata
- **Aggregation**: User-level metrics and statistics
- **Output**: CSV files for downstream analysis

**Usage:**
```python
from src.data_processor import process_telemetry

events_df, users_df = process_telemetry(
    telemetry_file="output/telemetry_logs.jsonl",
    employees_file="output/employees.csv"
)
```

### analytics.py
Generates comprehensive insights:
- Overall platform statistics
- Model usage analysis
- Tool usage patterns
- User segmentation
- Error analysis
- Performance metrics

**Usage:**
```python
from src.data_processor import process_telemetry
from src.analytics import TelemetryAnalytics, generate_insights

events_df, users_df = process_telemetry(...)
analytics = TelemetryAnalytics(events_df, users_df)
insights = generate_insights(events_df, users_df)
```

### dashboard.py
Interactive Streamlit application for data exploration:
- Multi-page navigation system
- Real-time data loading and caching
- Interactive Plotly visualization
- Responsive layout

**Usage:**
```bash
streamlit run src/dashboard.py
```

## 🧠 How It Works (End‑to‑End Flow)

1. **Synthetic data generation**  
   - `generate_fake_data.py` stvara realistične Claude Code događaje (API pozivi, tool odluke/rezultati, user promptovi, greške) i `employees.csv` sa metapodacima o korisnicima (level, practice, location).  
   - Svi identifikatori i sadržaji su potpuno sintetički.

2. **ETL obrada i skladištenje**  
   - `process_telemetry` u `data_processor.py` čita ceo `output/telemetry_logs.jsonl`, pretvara u tabelarni format (`normalized_events.csv`) i agregira metrike po korisniku (`users_aggregated.csv`).  
   - CSV fajlovi u `data/processed/` služe kao analytics‑ready skladište (možeš ih direktno učitati u pandas, Excel, ili BI alat).

3. **Analytics engine**  
   - `TelemetryAnalytics` iz `analytics.py` računa:  
     - ukupnu upotrebu (broj korisnika, sesija, API poziva, tokena, trošak)  
     - raspodelu po modelima i alatima (cost, calls, duration, success/accept rate)  
     - segmente korisnika po nivou, praksi i lokaciji  
     - performanse (avg/median/p95 trajanje, cache hit ratio, tool success rate)  
     - greške (error rate, najčešće poruke) i top korisnike.

4. **Dashboard i API sloj**  
   - `dashboard.py` učitava podatke preko `process_telemetry(..., force_reprocess=True)` – pri svakom učitavanju ili klikom na **Refresh Data** pokreće se ceo ETL nad trenutnim stanjem `telemetry_logs.jsonl`.  
   - `api.py` izlaže iste podatke i insighte preko FastAPI endpointa (`/events`, `/users`, `/insights`, `/refresh`) za programatski pristup.

5. **Real‑time simulacija**  
   - `realtime.simulate_stream` kontinuirano dopisuje nove događaje u `output/telemetry_logs.jsonl`, imitirajući live telemetry stream.  
   - Kada je ovaj proces aktivan, dashboard i API pri svakom osvežavanju ponovo procesuiraju ceo log i tako “vide” nove događaje.

## 📊 Data Model

### Telemetry Events

| Event Type | Purpose | Key Fields |
|-----------|---------|-----------|
| `api_request` | Claude API calls | model, cost, tokens, duration |
| `tool_decision` | Tool invocation decision | tool, decision, source |
| `tool_result` | Tool execution result | tool, success, duration |
| `user_prompt` | User input | prompt_length |
| `api_error` | API errors | error, status_code |

### Employee Metadata

| Field | Description |
|-------|-------------|
| email | Employee email |
| full_name | Full name |
| practice | Engineering practice |
| level | Seniority (L1-L10) |
| location | Geographic location |

## 💡 Key Insights Provided

1. **Usage Patterns**: Which models and tools are most commonly used?
2. **Cost Analysis**: Cost distribution across models, users, and time periods
3. **Performance**: System latency, cache efficiency, success rates
4. **User Behavior**: Segmentation by level, practice, and location
5. **Error Patterns**: Common failures and error rates
6. **Top Users**: Power users and their usage patterns

## 📈 Example Workflows

### Analyze top spenders
```
Dashboard → Top Users → View users by cost
```

### Track tool efficiency
```
Dashboard → Tools → Check success rates and duration
```

### Model performance comparison
```
Dashboard → Models → Compare cost and latency across models
```

### User segmentation analysis
```
Dashboard → Users → View metrics grouped by level/practice
```

## 🔄 Complete Workflow

1. **Generate Data**
   ```bash
   python src/generate_fake_data.py --num-users 100 --num-sessions 5000 --days 60
   ```

2. **Process & Transform**
   - Data is automatically processed when dashboard loads
   - Outputs saved to `data/processed/`

3. **Explore & Analyze**
   ```bash
   streamlit run src/dashboard.py
   ```

5. **Real‑time Simulation** (optional)
   - Start the live stream generator in a separate shell:
     ```bash
     python -c "from src.realtime import simulate_stream; simulate_stream(Path('output/telemetry_logs.jsonl'))"
     ```
   - Sa pokrenutim generatorom:
     - **Dashboard**: klik na "Refresh Data" briše Streamlit cache i ponovo pokreće `process_telemetry(..., force_reprocess=True)`, pa se novi događaji uključuju u metrike.  
     - **API**: poziv na `POST /refresh` ponovo pokreće ETL i ažurira precompute‑ovane insighte u memoriji.

6. **Run API Service** (optional)
   - Launch the FastAPI process:
     ```bash
     uvicorn src.api:app --reload
     ```
   - Browse documentation at `http://localhost:8000/docs`.

7. **Export Insights** (optional)
   - CSV files available in `data/processed/`
   - Can be imported to other BI tools

## 🤖 LLM Usage Log

### Tools Used

- **Claude / Claude Code (unutar Cursor‑a)** za generisanje koda, refaktorisanje i dokumentaciju.
- (Opcionalno) **ChatGPT / GitHub Copilot** za manje fragmente koda i podsetnik na bibliotečke API‑je.

### Kako su LLM‑ovi korišćeni

- **Arhitektura i dizajn**  
  - Korišćen LLM da predloži arhitekturu end‑to‑end platforme (data generation → ETL → analytics → dashboard → API) i razdvajanje odgovornosti po modulima.

- **Generisanje koda**  
  - Početne verzije sledećih modula su generisane ili skeletonizovane pomoću LLM‑ova i zatim ručno dorađene:  
    - `generate_fake_data.py` – generator sintetičkih događaja sa realističnim distribucijama modela, alata i grešaka.  
    - `data_processor.py` – ETL pipeline (učitavanje JSONL, normalizacija, agregacija, zapis u CSV).  
    - `analytics.py` – izračunavanje svih metrika (usage, cost, performance, errors, segmenti korisnika).  
    - `dashboard.py` – Streamlit višestranični dashboard sa Plotly grafovima.  
    - `api.py` i `realtime.py` – FastAPI servis i demonstracija ingestije u realnom vremenu.

- **Dokumentacija i UX copy**  
  - Struktura ovog `README.md`, opisi komponenti i uputstva za pokretanje su inicijalno generisani LLM‑om, a zatim prilagođeni stvarnom projektu.

### Primeri promptova

- *"Design an ETL pipeline in Python that reads Claude Code telemetry from a JSONL log, normalizes events into a flat table, aggregates metrics per user, and writes analytics-ready CSVs. Use pandas and keep it efficient for large files."*  
- *"Create a Streamlit dashboard for this telemetry dataset with pages for Overview, Models, Tools, Users, Top Users, Performance, and Errors. Use Plotly for charts and show key metrics as cards."*  
- *"Write a minimal FastAPI service that exposes endpoints to fetch normalized events, aggregated users, and a precomputed insights dictionary."*

### Validacija AI‑generisanog koda

- **Statička validacija**  
  - Ručni review koda koji je LLM predložio (čitajljivost, tipovi, performanse) i pojednostavljivanje gde je bio previše kompleksan.

- **Runtime validacija**  
  - Pokretanje kompletnog flow‑a na lokalnoj mašini: generisanje podataka → procesiranje → dashboard → API i poređenje očekivanih i stvarnih metrika (npr. broj korisnika, sesija, tokena).  
  - Popravke bug‑ova u parsiranju, grupisanju i edge case‑ovima na osnovu stvarnih rezultata.

- **Iterativno poboljšanje**  
  - Korišćenje LLM‑a za objašnjenje i prilagođavanje pandas groupby/agg logike tako da analitika odgovori na pitanja iz zadatka (token usage po roli, peak times, ponašanje alata).

## 📝 Notes

- All user identifiers are synthetic
- Prompt contents are redacted in telemetry
- Data generation uses configurable random seeds for reproducibility
- Dashboard requires internet for Plotly rendering

## 🤝 Contributing

This is a technical assignment for the internship program. Modifications should maintain:
- Data generation realism
- ETL pipeline accuracy
- Dashboard usability

## 📄 License

Internal use only.
