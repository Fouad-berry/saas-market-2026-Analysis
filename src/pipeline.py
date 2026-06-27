"""
Pipeline orchestrator — runs all stages end to end.

Usage:
    pip install -e .
    python -m src.pipeline
"""

import time

from src.analysis.marts import build_marts
from src.ingestion.loader import load_and_validate
from src.transform.cleaner import transform
from src.utils.config import (
    CLEAN_PARQUET,
    MART_CATEGORY,
    MART_FEATURES,
    MART_PRICING,
    MARTS_DIR,
    PROCESSED_DIR,
    RAW_CSV,
)
from src.utils.io import write_parquet
from src.utils.logger import logger


def print_summary(df_clean, marts: dict) -> None:
    """Log a human-readable summary."""
    mc = marts["mart_category"]
    mp = marts["mart_pricing"]

    logger.info("══ PIPELINE SUMMARY ══")
    logger.info(f"Total tools analysed : {len(df_clean):,}")
    logger.info(f"Categories           : {df_clean['category'].nunique()}")
    logger.info(f"Verticals            : {', '.join(df_clean['vertical'].unique())}")
    logger.info(f"Free plan available  : {df_clean['free_plan'].mean() * 100:.1f}% of tools")
    logger.info(f"Average rating       : {df_clean['rating'].mean():.3f} / 5.0")
    logger.info(f"Avg features/tool    : {df_clean['features_count'].mean():.1f}")

    logger.info("TOP 5 CATEGORIES BY TOOL COUNT")
    for _, row in mc.head(5).iterrows():
        tier_name = row["category"]
        logger.info(f"  {tier_name:<25} {row['tool_count']:>3} tools  avg {row['avg_rating']}")

    logger.info("PRICING TIER BREAKDOWN")
    tier_totals = mp.groupby("pricing_tier")["tool_count"].sum().sort_values(ascending=False)
    total = tier_totals.sum()
    for tier, count in tier_totals.items():
        logger.info(f"  {tier:<12} {count:>3} ({count / total * 100:.0f}%)")


def run_pipeline() -> None:
    start = time.perf_counter()
    logger.info("══ PIPELINE START ══")

    try:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        MARTS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("[1/4] Ingestion & validation")
        df_raw = load_and_validate(RAW_CSV)

        logger.info("[2/4] Transformation")
        df_clean = transform(df_raw)

        logger.info("[3/4] Loading clean data")
        write_parquet(df_clean, CLEAN_PARQUET)

        logger.info("[4/4] Building marts")
        marts = build_marts(df_clean)
        write_parquet(marts["mart_category"], MART_CATEGORY)
        write_parquet(marts["mart_pricing"], MART_PRICING)
        write_parquet(marts["mart_features"], MART_FEATURES)

        elapsed = time.perf_counter() - start
        logger.info(f"══ PIPELINE COMPLETE in {elapsed:.2f}s ══")
        print_summary(df_clean, marts)
    except Exception:
        logger.exception("Pipeline failed")
        raise


if __name__ == "__main__":
    run_pipeline()
