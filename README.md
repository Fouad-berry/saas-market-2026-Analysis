# SaaS Market 2026 — Data Engineering Pipeline

A production-grade data engineering pipeline for analyzing the SaaS market landscape (2026), covering **330 tools** across **28 categories** and **3 verticals** (Business, AI, Crypto).

---

## Architecture

```
data/raw/                  ← Source CSV (ingestion)
    └── saas-market-2026.csv

data/processed/            ← Cleaned & validated data (Parquet)
    └── saas_clean.parquet

data/marts/                ← Analytical data marts (Parquet)
    ├── mart_category.parquet
    ├── mart_pricing.parquet
    └── mart_features.parquet

src/
    ├── pipeline.py        ← Orchestrator
    ├── ingestion/         ← Data loading & validation (Great Expectations)
    ├── transform/         ← Cleaning, type casting, feature engineering
    ├── analysis/          ← Aggregation & mart generation
    └── utils/             ← Logger, config, helpers

docs/
    └── architecture.md    ← Architecture documentation

notebooks/
    └── exploration.ipynb  ← EDA with Plotly visualizations

tests/                     ← Pytest unit + integration tests

pyproject.toml             ← Project metadata & tool config
```

---

## 📦 Dataset

| Field | Type | Description |
|---|---|---|
| `tool_name` | str | SaaS product name |
| `category` | str | Product category (28 unique) |
| `vertical` | str | Business / AI / Crypto |
| `free_plan` | bool | Has a free tier |
| `starting_price_usd` | float | Lowest paid plan price |
| `highest_plan_price_usd` | float | Enterprise plan price |
| `plan_count` | int | Number of pricing tiers |
| `rating` | float | User rating (0–5) |
| `features_count` | int | Number of tracked features |
| `website` | str | Official URL |

---

## 🚀 Quickstart

```bash
# 1. Clone & install
git clone https://github.com/YOUR_USERNAME/saas-market-2026-Analysis.git
cd saas-market-2026-Analysis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the full pipeline
python src/pipeline.py

# 3. Run tests
pytest tests/ -v

# 4. Open the notebook
jupyter lab notebooks/exploration.ipynb
```

---

## 🔄 Pipeline Steps

```
[1] INGEST      → Load raw CSV, validate schema & data quality
[2] TRANSFORM   → Clean nulls, cast types, engineer features
[3] LOAD        → Write clean Parquet to data/processed/
[4] MART        → Aggregate into 3 analytical marts & print summary
```

---

## 📊 Key Insights (sample)

- **330 tools** analyzed across 28 categories
- **~61%** of tools offer a free plan
- Average rating: **4.42 / 5**
- Highest price range: **$0.04 → $3,600/month**
- Top category by count: **LLM (25 tools)**

---

## 🧪 Tests

```bash
pytest tests/ -v --tb=short
```

Covers:
- Schema validation (column presence, types)
- Null handling logic
- Feature engineering correctness
- Mart aggregation accuracy

---

## ⚙️ CI/CD (planned)

GitHub Actions workflow (to be created) will run on every push to `main`:
1. Install dependencies
2. Run full pipeline
3. Run all tests
4. Upload processed artifacts

---

## 📁 File sizes

| File | Rows | Format |
|---|---|---|
| `data/raw/saas-market-2026.csv` | 330 | CSV |
| `data/processed/saas_clean.parquet` | 330 | Parquet |
| `data/marts/*.parquet` | varies | Parquet |

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| Data manipulation | Pandas, NumPy |
| Storage format | Apache Parquet (via PyArrow) |
| Data quality | Great Expectations |
| Visualization | Plotly, Matplotlib, Seaborn |
| Logging | Loguru |
| Configuration | Pydantic, python-dotenv |
| Testing | Pytest (with pytest-cov) |
| CI/CD | GitHub Actions (planned) |
| Notebooks | Jupyter Lab |

---

Réalisé par [FOUAD MOUTAIROU]
- My Linkedln: https://www.linkedin.com/in/fouad-moutairou-044460273/
- My Portfolio link: https://portfolio-fouad.netlify.app

## 📄 License

MIT
