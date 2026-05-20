"""
Tests for the analysis / mart building layer.
"""

import pandas as pd
import pytest

from src.analysis.marts import (
    build_mart_category,
    build_mart_pricing,
    build_mart_features,
    build_marts,
)


def sample_df():
    return pd.DataFrame({
        "tool_name": ["Notion", "ClickUp", "Stripe", "Brex", "GPT-4"],
        "category": ["pm", "pm", "fintech", "fintech", "llm"],
        "vertical": ["Business", "Business", "Business", "Business", "AI"],
        "free_plan": [True, True, False, False, False],
        "starting_price_usd": [0.0, 5.0, 0.0, 50.0, 20.0],
        "highest_plan_price_usd": [18.0, 12.0, 99.0, 200.0, 120.0],
        "plan_count": [4, 4, 3, 2, 2],
        "rating": [4.7, 4.7, 4.5, 4.2, 4.8],
        "features_count": [32, 47, 15, 12, 20],
        "website": ["a.com"] * 5,
        "is_freemium": [False, True, False, False, False],
        "price_range_usd": [18.0, 7.0, 99.0, 150.0, 100.0],
        "price_per_feature_usd": [0.0, 0.11, 0.0, 4.17, 1.0],
        "log_highest_price": [2.94, 2.56, 4.60, 5.30, 4.80],
        "rating_tier": ["High", "High", "Mid", "Low", "High"],
        "features_tier": ["High", "High", "Low", "Low", "Mid"],
    })


class TestMartCategory:
    def test_one_row_per_category(self):
        df = sample_df()
        result = build_mart_category(df)
        assert result["category"].nunique() == result.shape[0]

    def test_tool_count_correct(self):
        df = sample_df()
        result = build_mart_category(df)
        pm_count = result.loc[result["category"] == "pm", "tool_count"].iloc[0]
        assert pm_count == 2

    def test_free_plan_pct_range(self):
        df = sample_df()
        result = build_mart_category(df)
        assert (result["free_plan_pct"] >= 0).all()
        assert (result["free_plan_pct"] <= 100).all()

    def test_expected_columns_present(self):
        result = build_mart_category(sample_df())
        for col in ["tool_count", "free_plan_pct", "avg_rating",
                    "median_starting_price", "dominant_vertical"]:
            assert col in result.columns


class TestMartPricing:
    def test_expected_tiers(self):
        result = build_mart_pricing(sample_df())
        valid = {"Free", "Budget", "Mid-Market", "Premium"}
        assert set(result["pricing_tier"]).issubset(valid)

    def test_share_pct_sums_to_100_per_vertical(self):
        result = build_mart_pricing(sample_df())
        for vertical, grp in result.groupby("vertical"):
            total = grp["share_pct"].sum()
            assert abs(total - 100.0) < 0.5, f"Vertical {vertical}: share_pct sums to {total}"

    def test_expected_columns_present(self):
        result = build_mart_pricing(sample_df())
        for col in ["vertical", "pricing_tier", "tool_count", "avg_rating", "share_pct"]:
            assert col in result.columns


class TestMartFeatures:
    def test_one_row_per_category(self):
        result = build_mart_features(sample_df())
        assert result["category"].nunique() == result.shape[0]

    def test_sorted_by_avg_features_descending(self):
        result = build_mart_features(sample_df())
        vals = result["avg_features"].tolist()
        assert vals == sorted(vals, reverse=True)

    def test_expected_columns_present(self):
        result = build_mart_features(sample_df())
        for col in ["avg_features", "avg_rating", "corr_features_rating"]:
            assert col in result.columns


class TestBuildMarts:
    def test_returns_three_keys(self):
        marts = build_marts(sample_df())
        assert set(marts.keys()) == {"mart_category", "mart_pricing", "mart_features"}

    def test_all_values_are_dataframes(self):
        marts = build_marts(sample_df())
        for name, df in marts.items():
            assert isinstance(df, pd.DataFrame), f"{name} is not a DataFrame"
