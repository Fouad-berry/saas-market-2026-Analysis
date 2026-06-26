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
    """Print a human-readable summary to stdout."""
    mc = marts["mart_category"]
    mp = marts["mart_pricing"]

    print("\n" + "═" * 60)
    print("  SAAS MARKET 2026 — PIPELINE SUMMARY")
    print("═" * 60)
    print(f"  Total tools analysed : {len(df_clean):,}")
    print(f"  Categories           : {df_clean['category'].nunique()}")
    print(f"  Verticals            : {', '.join(df_clean['vertical'].unique())}")
    print(f"  Free plan available  : {df_clean['free_plan'].mean() * 100:.1f}% of tools")
    print(f"  Average rating       : {df_clean['rating'].mean():.3f} / 5.0")
    print(f"  Avg features/tool    : {df_clean['features_count'].mean():.1f}")
    print()

    print("  TOP 5 CATEGORIES BY TOOL COUNT")
    print("  " + "-" * 40)
    for _, row in mc.head(5).iterrows():
        print(f"  {row['category']:<25} {row['tool_count']:>3} tools  avg ⭐ {row['avg_rating']}")
    print()

    print("  PRICING TIER BREAKDOWN")
    print("  " + "-" * 40)
    tier_totals = mp.groupby("pricing_tier")["tool_count"].sum().sort_values(ascending=False)
    total = tier_totals.sum()
    for tier, count in tier_totals.items():
        bar = "█" * int(count / total * 30)
        print(f"  {tier:<12} {bar:<30} {count:>3} ({count / total * 100:.0f}%)")
    print("═" * 60 + "\n")


def run_pipeline() -> None:
    start = time.perf_counter()
    logger.info("══ PIPELINE START ══")

    # Ensure output dirs exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MARTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Ingest ──────────────────────────────────────────────────
    logger.info("[1/4] Ingestion & validation")
    df_raw = load_and_validate(RAW_CSV)

    # ── Stage 2: Transform ───────────────────────────────────────────────
    logger.info("[2/4] Transformation")
    df_clean = transform(df_raw)

    # ── Stage 3: Load (write clean Parquet) ──────────────────────────────
    logger.info("[3/4] Loading clean data")
    write_parquet(df_clean, CLEAN_PARQUET)

    # ── Stage 4: Build & write marts ─────────────────────────────────────
    logger.info("[4/4] Building marts")
    marts = build_marts(df_clean)
    write_parquet(marts["mart_category"], MART_CATEGORY)
    write_parquet(marts["mart_pricing"], MART_PRICING)
    write_parquet(marts["mart_features"], MART_FEATURES)

    elapsed = time.perf_counter() - start
    logger.info(f"══ PIPELINE COMPLETE in {elapsed:.2f}s ══")
    print_summary(df_clean, marts)


if __name__ == "__main__":
    run_pipeline()
