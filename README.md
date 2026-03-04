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

4. **Export Insights** (optional)
   - CSV files available in `data/processed/`
   - Can be imported to other BI tools

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
