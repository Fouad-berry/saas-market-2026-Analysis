# Pipeline Architecture

## Data flow

```
CSV (raw)
    │
    ▼
┌─────────────────────────────────────────────┐
│  INGESTION  src/ingestion/loader.py          │
│  • load_raw()         — pd.read_csv          │
│  • validate_schema()  — column check         │
│  • run_ge_suite()     — Great Expectations   │
└───────────────────────┬─────────────────────┘
                        │  pd.DataFrame (raw)
                        ▼
┌─────────────────────────────────────────────┐
│  TRANSFORM  src/transform/cleaner.py         │
│  • deduplicate()      — drop dup tool_names  │
│  • handle_nulls()     — median imputation    │
│  • cast_types()       — enforce dtypes       │
│  • engineer_features()— 6 new columns        │
└───────────────────────┬─────────────────────┘
                        │  pd.DataFrame (clean)
                        ▼
┌─────────────────────────────────────────────┐
│  LOAD  src/utils/io.py                       │
│  • write_parquet()   → data/processed/       │
└───────────────────────┬─────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────┐
│  ANALYSIS  src/analysis/marts.py             │
│  • build_mart_category()                     │
│  • build_mart_pricing()                      │
│  • build_mart_features()                     │
│  write_parquet() × 3 → data/marts/           │
└─────────────────────────────────────────────┘
```

## Engineered features

| Column | Formula | Purpose |
|---|---|---|
| `price_range_usd` | `highest - starting` | Plan spread |
| `price_per_feature_usd` | `starting / features_count` | Value proxy |
| `is_freemium` | `free_plan AND starting > 0` | Hybrid model flag |
| `rating_tier` | Tertile bins (Low/Mid/High) | Segment by quality |
| `features_tier` | Tertile bins (Low/Mid/High) | Segment by richness |
| `log_highest_price` | `log1p(highest_plan_price)` | Normalise skewed distribution |

## Null strategy

| Column | Strategy | Rationale |
|---|---|---|
| `starting_price_usd` | Fill → 0 | No paid plan found |
| `highest_plan_price_usd` | Category median, fallback global median | Keeps within segment range |
| `rating` | Global median | Small gap, safe imputation |

## Data marts

### mart_category
One row per category. Aggregates: tool count, free-plan %, avg rating, median prices, avg features, dominant vertical.

### mart_pricing
Pricing tier breakdown (Free / Budget / Mid-Market / Premium) per vertical. Includes share % within vertical.

### mart_features
Feature richness vs. rating analysis per category. Includes Pearson correlation between `features_count` and `rating` within each category.