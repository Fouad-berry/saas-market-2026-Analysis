"""
Tests for the analysis / mart building layer.
"""

import pandas as pd

from src.analysis.marts import (
    build_mart_category,
    build_mart_features,
    build_mart_pricing,
    build_marts,
)


class TestMartCategory:
    def test_one_row_per_category(self, sample_df):
        result = build_mart_category(sample_df)
        assert result["category"].nunique() == result.shape[0]

    def test_tool_count_correct(self, sample_df):
        result = build_mart_category(sample_df)
        pm_count = result.loc[result["category"] == "pm", "tool_count"].iloc[0]
        assert pm_count == 2

    def test_free_plan_pct_range(self, sample_df):
        result = build_mart_category(sample_df)
        assert (result["free_plan_pct"] >= 0).all()
        assert (result["free_plan_pct"] <= 100).all()

    def test_expected_columns_present(self, sample_df):
        result = build_mart_category(sample_df)
        for col in [
            "tool_count",
            "free_plan_pct",
            "avg_rating",
            "median_starting_price",
            "dominant_vertical",
        ]:
            assert col in result.columns


class TestMartPricing:
    def test_expected_tiers(self, sample_df):
        result = build_mart_pricing(sample_df)
        valid = {"Free", "Budget", "Mid-Market", "Premium"}
        assert set(result["pricing_tier"]).issubset(valid)

    def test_share_pct_sums_to_100_per_vertical(self, sample_df):
        result = build_mart_pricing(sample_df)
        for _, grp in result.groupby("vertical"):
            total = grp["share_pct"].sum()
            assert abs(total - 100.0) < 0.5

    def test_expected_columns_present(self, sample_df):
        result = build_mart_pricing(sample_df)
        for col in ["vertical", "pricing_tier", "tool_count", "avg_rating", "share_pct"]:
            assert col in result.columns


class TestMartFeatures:
    def test_one_row_per_category(self, sample_df):
        result = build_mart_features(sample_df)
        assert result["category"].nunique() == result.shape[0]

    def test_sorted_by_avg_features_descending(self, sample_df):
        result = build_mart_features(sample_df)
        vals = result["avg_features"].tolist()
        assert vals == sorted(vals, reverse=True)

    def test_expected_columns_present(self, sample_df):
        result = build_mart_features(sample_df)
        for col in ["avg_features", "avg_rating", "corr_features_rating"]:
            assert col in result.columns

    def test_corr_is_within_range(self, sample_df):
        result = build_mart_features(sample_df)
        valid = result["corr_features_rating"].dropna()
        assert (valid >= -1.0).all()
        assert (valid <= 1.0).all()


class TestBuildMarts:
    def test_returns_three_keys(self, sample_df):
        marts = build_marts(sample_df)
        assert set(marts.keys()) == {"mart_category", "mart_pricing", "mart_features"}

    def test_all_values_are_dataframes(self, sample_df):
        marts = build_marts(sample_df)
        for name, df in marts.items():
            assert isinstance(df, pd.DataFrame), f"{name} is not a DataFrame"
