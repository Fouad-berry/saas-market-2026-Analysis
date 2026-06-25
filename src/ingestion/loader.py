"""
Ingestion layer — loads raw CSV and validates it with Great Expectations.

Entry point: `load_and_validate(path) -> pd.DataFrame`
"""

from pathlib import Path

import great_expectations as gx
import pandas as pd

from src.utils.config import EXPECTED_COLUMNS, PRICE_MAX, RATING_MAX, RATING_MIN
from src.utils.logger import logger

# ── Loader ────────────────────────────────────────────────────────────────────


def load_raw(path: Path) -> pd.DataFrame:
    """Read the raw CSV into a DataFrame with basic type hints."""
    logger.info(f"Loading raw data from {path}")
    df = pd.read_csv(
        path,
        dtype={
            "tool_name": str,
            "category": str,
            "vertical": str,
            "free_plan": bool,
            "website": str,
        },
    )
    logger.info(f"Loaded {len(df):,} rows x {len(df.columns)} columns")
    return df


# ── Schema check ─────────────────────────────────────────────────────────────


def validate_schema(df: pd.DataFrame) -> None:
    """Raise ValueError if expected columns are missing."""
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in source data: {missing}")
    logger.info("Schema validation passed ✓")


# ── Great Expectations suite ──────────────────────────────────────────────────


def run_ge_suite(df: pd.DataFrame) -> dict:
    """
    Run a lightweight Great Expectations validation suite (GE v1.x compatible).
    Returns a dict with pass/fail counts and any failed expectations.
    """
    logger.info("Running Great Expectations validation suite…")

    context = gx.get_context(mode="ephemeral")

    # GE v1.x fluent API
    ds = context.data_sources.add_pandas(name="saas_source")
    da = ds.add_dataframe_asset(name="saas_asset")
    batch_def = da.add_batch_definition_whole_dataframe("saas_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name="saas_suite")

    # ── Expectations ──────────────────────────────────────────────────────
    expectations = []

    for col in EXPECTED_COLUMNS:
        expectations.append(gx.expectations.ExpectColumnToExist(column=col))

    expectations += [
        gx.expectations.ExpectColumnValuesToBeUnique(column="tool_name"),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="rating", min_value=RATING_MIN, max_value=RATING_MAX, mostly=0.95
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="starting_price_usd", min_value=0.0, mostly=0.99
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="highest_plan_price_usd", min_value=0.0, max_value=PRICE_MAX, mostly=0.95
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="vertical", value_set=["Business", "AI", "Crypto"]
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(column="free_plan", value_set=[True, False]),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="plan_count", min_value=1, mostly=0.99
        ),
    ]

    for exp in expectations:
        suite.add_expectation(exp)

    # ── Validate ──────────────────────────────────────────────────────────
    results = batch.validate(suite)

    passed = sum(1 for r in results.results if r.success)
    failed = sum(1 for r in results.results if not r.success)
    failed_expectations = [
        {
            "expectation": r.expectation_config.type,
            "column": r.expectation_config.kwargs.get("column"),
            "result": r.result,
        }
        for r in results.results
        if not r.success
    ]

    logger.info(f"GE suite: {passed} passed, {failed} failed")
    if failed_expectations:
        for fe in failed_expectations:
            logger.warning(f"  FAILED — {fe['expectation']} on '{fe['column']}'")

    return {
        "passed": passed,
        "failed": failed,
        "failed_expectations": failed_expectations,
        "overall_success": results.success,
    }


# ── Public entry point ────────────────────────────────────────────────────────


def load_and_validate(path: Path) -> pd.DataFrame:
    """Load raw CSV, run schema + GE validation, return DataFrame."""
    df = load_raw(path)
    validate_schema(df)
    report = run_ge_suite(df)

    if not report["overall_success"]:
        logger.warning(
            f"Validation completed with {report['failed']} failed expectations. "
            "Pipeline will proceed with warnings."
        )
    else:
        logger.info("All GE expectations passed ✓")

    return df
