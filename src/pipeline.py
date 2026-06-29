"""
Pipeline orchestrator — runs all stages end to end.

Usage:
    pip install -e .
    python -m src.pipeline
    python -m src.pipeline --input data/raw/saas-market-2026.csv --skip-validation
"""

import argparse
import sys
import time
from pathlib import Path

from src.analysis.marts import build_marts
from src.ingestion.loader import load_and_validate, load_raw
from src.transform.cleaner import transform
from src.utils.config import MARTS_DIR, PROCESSED_DIR, RAW_CSV
from src.utils.io import write_parquet
from src.utils.logger import STDOUT_SINK, logger


def log_summary(df_clean, marts: dict) -> None:
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


def run_pipeline(
    input_path: Path | None = None,
    output_dir: Path | None = None,
    skip_validation: bool = False,
) -> None:
    """Run the full ETL pipeline: ingest → transform → load → mart.

    Parameters
    ----------
    input_path : Path, optional
        Override input CSV path (default: RAW_CSV from config).
    output_dir : Path, optional
        Override output directory for marts (default: MARTS_DIR).
    skip_validation : bool
        Skip Great Expectations validation (fast mode).
    """
    start = time.perf_counter()
    logger.info("══ PIPELINE START ══")

    src = input_path or RAW_CSV
    out = output_dir or MARTS_DIR
    clean_dir = output_dir.parent if output_dir else PROCESSED_DIR
    clean_path = clean_dir / "saas_clean.parquet"

    try:
        out.mkdir(parents=True, exist_ok=True)
        clean_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[1/4] Ingestion & validation")
        df_raw = load_and_validate(src) if not skip_validation else load_raw(src)

        logger.info("[2/4] Transformation")
        df_clean = transform(df_raw)

        logger.info("[3/4] Loading clean data")
        write_parquet(df_clean, clean_path)

        logger.info("[4/4] Building marts")
        marts = build_marts(df_clean)
        write_parquet(marts["mart_category"], out / "mart_category.parquet")
        write_parquet(marts["mart_pricing"], out / "mart_pricing.parquet")
        write_parquet(marts["mart_features"], out / "mart_features.parquet")

        elapsed = time.perf_counter() - start
        logger.info(f"══ PIPELINE COMPLETE in {elapsed:.2f}s ══")
        log_summary(df_clean, marts)
    except Exception:
        logger.exception("Pipeline failed")
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="SaaS Market 2026 — Data engineering pipeline",
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=None,
        help="Input CSV path (default: config.RAW_CSV)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=None,
        help="Output directory for marts (default: config.MARTS_DIR)",
    )
    parser.add_argument(
        "--skip-validation", "-s",
        action="store_true",
        help="Skip Great Expectations validation",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        logger.remove(STDOUT_SINK)
        logger.add(sys.stdout, level="DEBUG")
    run_pipeline(
        input_path=args.input,
        output_dir=args.output_dir,
        skip_validation=args.skip_validation,
    )
