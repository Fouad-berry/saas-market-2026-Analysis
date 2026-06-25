"""
Transform layer — cleans raw data and engineers new features.

Entry point: `transform(df) -> pd.DataFrame`
"""

import numpy as np
import pandas as pd

from src.utils.config import CATEGORICAL_COLUMNS
from src.utils.logger import logger

# ── 1. Null handling ──────────────────────────────────────────────────────────


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strategy per column:
    - starting_price_usd   → fill with 0 (free / unknown)
    - highest_plan_price_usd → fill with median per category
    - rating               → fill with global median
    """
    df = df.copy()

    # starting price: null means no paid plan found → treat as 0
    null_start = df["starting_price_usd"].isna().sum()
    df["starting_price_usd"] = df["starting_price_usd"].fillna(0.0)
    if null_start:
        logger.debug(f"Filled {null_start} null(s) in starting_price_usd with 0")

    # highest plan price: impute with category median
    null_high = df["highest_plan_price_usd"].isna().sum()
    cat_median = df.groupby("category")["highest_plan_price_usd"].transform("median")
    df["highest_plan_price_usd"] = df["highest_plan_price_usd"].fillna(cat_median)
    # fallback: global median for categories with all nulls
    global_median = df["highest_plan_price_usd"].median()
    df["highest_plan_price_usd"] = df["highest_plan_price_usd"].fillna(global_median)
    if null_high:
        logger.debug(f"Imputed {null_high} null(s) in highest_plan_price_usd (category median)")

    # rating: global median
    null_rating = df["rating"].isna().sum()
    df["rating"] = df["rating"].fillna(df["rating"].median())
    if null_rating:
        logger.debug(f"Imputed {null_rating} null(s) in rating (global median)")

    logger.info("Null handling complete ✓")
    return df


# ── 2. Type casting ───────────────────────────────────────────────────────────


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce correct dtypes and convert categoricals."""
    df = df.copy()

    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].astype("category")

    df["free_plan"] = df["free_plan"].astype(bool)
    df["plan_count"] = df["plan_count"].astype(int)
    df["features_count"] = df["features_count"].astype(int)
    df["starting_price_usd"] = df["starting_price_usd"].astype(float)
    df["highest_plan_price_usd"] = df["highest_plan_price_usd"].astype(float)
    df["rating"] = df["rating"].astype(float)

    logger.info("Type casting complete ✓")
    return df


# ── 3. Feature engineering ────────────────────────────────────────────────────


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    New columns:
    - price_range_usd        : highest - starting (spread of plans)
    - price_per_feature_usd  : starting_price / features_count (value proxy)
    - is_freemium            : free_plan AND starting_price > 0 (hybrid model)
    - rating_tier            : Low / Mid / High based on rating quartiles
    - features_tier          : Low / Mid / High based on features_count quartiles
    - log_highest_price      : log1p(highest_plan_price) for skewed-data analysis
    """
    df = df.copy()

    df["price_range_usd"] = (df["highest_plan_price_usd"] - df["starting_price_usd"]).clip(
        lower=0.0
    )

    df["price_per_feature_usd"] = np.where(
        df["features_count"] > 0,
        df["starting_price_usd"] / df["features_count"],
        0.0,
    ).round(4)

    df["is_freemium"] = df["free_plan"] & (df["starting_price_usd"] > 0)

    # rating tier (Low < p33, High >= p67)
    r33, r67 = df["rating"].quantile([0.33, 0.67])
    df["rating_tier"] = pd.cut(
        df["rating"],
        bins=[-np.inf, r33, r67, np.inf],
        labels=["Low", "Mid", "High"],
    )

    # features tier
    f33, f67 = df["features_count"].quantile([0.33, 0.67])
    df["features_tier"] = pd.cut(
        df["features_count"],
        bins=[-np.inf, f33, f67, np.inf],
        labels=["Low", "Mid", "High"],
    )

    df["log_highest_price"] = np.log1p(df["highest_plan_price_usd"])

    logger.info("Engineered 6 new features ✓")
    return df


# ── 4. Deduplication ──────────────────────────────────────────────────────────


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows, keep first occurrence."""
    before = len(df)
    df = df.drop_duplicates(subset=["tool_name"])
    dropped = before - len(df)
    if dropped:
        logger.warning(f"Dropped {dropped} duplicate tool_name(s)")
    else:
        logger.info("No duplicates found ✓")
    return df


# ── Public entry point ────────────────────────────────────────────────────────


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Full transformation pipeline."""
    logger.info("Starting transformation…")
    df = deduplicate(df)
    df = handle_nulls(df)
    df = cast_types(df)
    df = engineer_features(df)
    logger.info(f"Transformation complete — {len(df):,} rows, {len(df.columns)} columns ✓")
    return df
