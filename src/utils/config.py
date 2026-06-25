"""
Central configuration for the SaaS Market Pipeline.
All paths and constants are defined here to avoid magic strings.
"""

from pathlib import Path

# ── Root ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]

# ── Data directories ─────────────────────────────────────────────────────────
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MARTS_DIR = ROOT_DIR / "data" / "marts"

# ── Source files ─────────────────────────────────────────────────────────────
RAW_CSV = RAW_DIR / "saas-market-2026.csv"

# ── Output files ─────────────────────────────────────────────────────────────
CLEAN_PARQUET = PROCESSED_DIR / "saas_clean.parquet"
MART_CATEGORY = MARTS_DIR / "mart_category.parquet"
MART_PRICING = MARTS_DIR / "mart_pricing.parquet"
MART_FEATURES = MARTS_DIR / "mart_features.parquet"

# ── Schema ───────────────────────────────────────────────────────────────────
EXPECTED_COLUMNS = [
    "tool_name",
    "category",
    "vertical",
    "free_plan",
    "starting_price_usd",
    "highest_plan_price_usd",
    "plan_count",
    "rating",
    "features_count",
    "website",
]

NUMERIC_COLUMNS = [
    "starting_price_usd",
    "highest_plan_price_usd",
    "plan_count",
    "rating",
    "features_count",
]

CATEGORICAL_COLUMNS = ["category", "vertical"]

# ── Business rules ───────────────────────────────────────────────────────────
RATING_MIN = 0.0
RATING_MAX = 5.0
PRICE_MAX = 10_000.0  # sanity cap for outlier detection
