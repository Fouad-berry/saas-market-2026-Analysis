"""
Analysis layer — builds 3 analytical data marts from the clean dataset.

Marts:
  mart_category  : category-level aggregations (pricing, ratings, features)
  mart_pricing   : pricing tier distribution per vertical
  mart_features  : feature richness vs. rating correlation by category

Entry point: `build_marts(df) -> dict[str, pd.DataFrame]`
"""

import numpy as np
import pandas as pd

from src.utils.logger import logger

# ── Mart 1: Category summary ──────────────────────────────────────────────────


def build_mart_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per category.
    Columns: tool_count, free_plan_pct, avg_rating, median_starting_price,
             median_highest_price, avg_features, avg_plan_count,
             freemium_pct, vertical_mix
    """
    agg = (
        df.groupby("category", observed=True)
        .agg(
            tool_count=("tool_name", "count"),
            free_plan_pct=("free_plan", lambda x: round(x.mean() * 100, 1)),
            avg_rating=("rating", lambda x: round(x.mean(), 3)),
            median_starting_price=("starting_price_usd", "median"),
            median_highest_price=("highest_plan_price_usd", "median"),
            avg_features=("features_count", lambda x: round(x.mean(), 1)),
            avg_plan_count=("plan_count", lambda x: round(x.mean(), 1)),
            freemium_pct=("is_freemium", lambda x: round(x.mean() * 100, 1)),
        )
        .reset_index()
    )

    # Dominant vertical per category
    dominant_vertical = (
        df.groupby(["category", "vertical"], observed=True)
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .drop_duplicates("category")
        .set_index("category")["vertical"]
    )
    agg["dominant_vertical"] = agg["category"].map(dominant_vertical)
    agg = agg.sort_values("tool_count", ascending=False).reset_index(drop=True)

    logger.info(f"mart_category built — {len(agg)} rows ✓")
    return agg


# ── Mart 2: Pricing tiers ─────────────────────────────────────────────────────


def build_mart_pricing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pricing tier analysis per vertical.
    Tiers: Free (0), Budget (0<p<=20), Mid (20<p<=100), Premium (>100)
    """

    df = df.copy()
    bins = [-np.inf, 0, 20, 100, np.inf]
    labels = ["Free", "Budget", "Mid-Market", "Premium"]
    df["pricing_tier"] = pd.cut(df["starting_price_usd"], bins=bins, labels=labels, right=True)
    df["pricing_tier"] = df["pricing_tier"].fillna("Free")

    agg = (
        df.groupby(["vertical", "pricing_tier"], observed=True)
        .agg(
            tool_count=("tool_name", "count"),
            avg_rating=("rating", lambda x: round(x.mean(), 3)),
            avg_features=("features_count", lambda x: round(x.mean(), 1)),
            median_price=("starting_price_usd", "median"),
        )
        .reset_index()
    )

    # Add % within vertical
    total_per_vertical = agg.groupby("vertical")["tool_count"].transform("sum")
    agg["share_pct"] = (agg["tool_count"] / total_per_vertical * 100).round(1)

    # Ordered tiers for readability
    tier_order = {"Free": 0, "Budget": 1, "Mid-Market": 2, "Premium": 3}
    agg["tier_order"] = agg["pricing_tier"].map(tier_order)
    agg = (
        agg.sort_values(["vertical", "tier_order"])
        .drop(columns="tier_order")
        .reset_index(drop=True)
    )

    logger.info(f"mart_pricing built — {len(agg)} rows ✓")
    return agg


# ── Mart 3: Features vs. rating ───────────────────────────────────────────────


def build_mart_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature richness vs. rating correlation, by category.
    Useful to detect whether more features correlates with higher ratings.
    """
    agg = (
        df.groupby("category", observed=True)
        .agg(
            tool_count=("tool_name", "count"),
            avg_features=("features_count", lambda x: round(x.mean(), 2)),
            median_features=("features_count", "median"),
            max_features=("features_count", "max"),
            avg_rating=("rating", lambda x: round(x.mean(), 3)),
            std_rating=("rating", lambda x: round(x.std(), 3)),
            corr_features_rating=(
                "features_count",
                lambda x: (
                    round(x.corr(df.loc[x.index, "rating"]), 3) if len(x) > 2 else float("nan")
                ),
            ),
        )
        .reset_index()
    )

    agg = agg.sort_values("avg_features", ascending=False).reset_index(drop=True)

    logger.info(f"mart_features built — {len(agg)} rows ✓")
    return agg


# ── Public entry point ────────────────────────────────────────────────────────


def build_marts(df: pd.DataFrame) -> dict:
    """Build all three marts and return them as a dict."""
    logger.info("Building analytical marts…")
    return {
        "mart_category": build_mart_category(df),
        "mart_pricing": build_mart_pricing(df),
        "mart_features": build_mart_features(df),
    }
