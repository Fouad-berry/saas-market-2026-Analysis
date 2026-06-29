"""
Tests for the transform / cleaning layer.
"""

import numpy as np
import pandas as pd
import pytest

from src.transform.cleaner import (
    cast_types,
    deduplicate,
    engineer_features,
    handle_nulls,
    transform,
)


class TestHandleNulls:
    def test_no_nulls_remaining(self, base_df):
        df = handle_nulls(base_df)
        assert df["starting_price_usd"].isna().sum() == 0
        assert df["highest_plan_price_usd"].isna().sum() == 0
        assert df["rating"].isna().sum() == 0

    def test_starting_price_null_filled_with_zero(self, base_df):
        df = base_df
        df.loc[0, "starting_price_usd"] = np.nan
        result = handle_nulls(df)
        assert result.loc[0, "starting_price_usd"] == 0.0

    def test_rating_filled_with_median(self, base_df):
        df = base_df
        result = handle_nulls(df)
        assert result["rating"].isna().sum() == 0
        assert result.loc[1, "rating"] == pytest.approx(4.55)

    def test_handle_nulls_empty_df(self):
        cols = ["category", "starting_price_usd", "highest_plan_price_usd", "rating"]
        empty = pd.DataFrame(columns=cols)
        result = handle_nulls(empty)
        assert len(result) == 0

    def test_handle_nulls_all_null_category_falls_back_to_zero(self):
        df = pd.DataFrame(
            {
                "tool_name": ["A", "B"],
                "category": ["x", "x"],
                "vertical": ["Business", "Business"],
                "free_plan": [True, True],
                "starting_price_usd": [0.0, 0.0],
                "highest_plan_price_usd": [None, None],
                "plan_count": [1, 1],
                "rating": [3.0, 4.0],
                "features_count": [5, 5],
                "website": ["a.com", "b.com"],
            }
        )
        result = handle_nulls(df)
        assert result["highest_plan_price_usd"].isna().sum() == 0
        assert result["highest_plan_price_usd"].iloc[0] == 0.0


class TestCastTypes:
    def test_numeric_columns_are_float(self, base_df):
        df = handle_nulls(base_df)
        result = cast_types(df)
        assert result["starting_price_usd"].dtype == float
        assert result["highest_plan_price_usd"].dtype == float
        assert result["rating"].dtype == float

    def test_plan_count_is_int(self, base_df):
        df = handle_nulls(base_df)
        result = cast_types(df)
        assert result["plan_count"].dtype == int

    def test_features_count_is_int(self, base_df):
        df = handle_nulls(base_df)
        result = cast_types(df)
        assert result["features_count"].dtype == int

    def test_free_plan_is_bool(self, base_df):
        df = handle_nulls(base_df)
        result = cast_types(df)
        assert result["free_plan"].dtype == bool

    def test_categorical_columns(self, base_df):
        df = handle_nulls(base_df)
        result = cast_types(df)
        assert str(result["category"].dtype) == "category"
        assert str(result["vertical"].dtype) == "category"


class TestEngineerFeatures:
    def _prepped(self, base_df):
        df = handle_nulls(base_df)
        df = cast_types(df)
        return df

    def test_price_range_non_negative(self, base_df):
        result = engineer_features(self._prepped(base_df))
        assert (result["price_range_usd"] >= 0).all()

    def test_price_per_feature_non_negative(self, base_df):
        result = engineer_features(self._prepped(base_df))
        assert (result["price_per_feature_usd"] >= 0).all()

    def test_is_freemium_logic(self, base_df):
        result = engineer_features(self._prepped(base_df))
        notion_row = result[result["tool_name"] == "Notion"].iloc[0]
        clickup_row = result[result["tool_name"] == "ClickUp"].iloc[0]
        assert not notion_row["is_freemium"]
        assert clickup_row["is_freemium"]

    def test_rating_tier_values(self, base_df):
        result = engineer_features(self._prepped(base_df))
        valid = {"Low", "Mid", "High"}
        assert set(result["rating_tier"].dropna().astype(str)).issubset(valid)

    def test_log_highest_price_non_negative(self, base_df):
        result = engineer_features(self._prepped(base_df))
        assert (result["log_highest_price"] >= 0).all()

    def test_new_columns_dtypes(self, base_df):
        result = engineer_features(self._prepped(base_df))
        expected = {
            "price_range_usd": float,
            "price_per_feature_usd": float,
            "is_freemium": bool,
            "log_highest_price": float,
        }
        for col, dtype in expected.items():
            assert col in result.columns
            assert result[col].dtype == dtype, f"{col}: expected {dtype}, got {result[col].dtype}"

    def test_categorical_tier_columns_exist(self, base_df):
        result = engineer_features(self._prepped(base_df))
        for col in ["rating_tier", "features_tier"]:
            assert col in result.columns
            assert str(result[col].dtype) == "category"

    def test_all_identical_ratings_does_not_raise(self):
        df = pd.DataFrame({
            "tool_name": ["A", "B", "C"],
            "category": ["x", "x", "x"],
            "vertical": ["Business", "Business", "Business"],
            "free_plan": [True, False, True],
            "starting_price_usd": [0.0, 5.0, 10.0],
            "highest_plan_price_usd": [10.0, 20.0, 30.0],
            "plan_count": [2, 3, 1],
            "rating": [4.5, 4.5, 4.5],
            "features_count": [10, 10, 10],
            "website": ["a.com", "b.com", "c.com"],
        })
        df = handle_nulls(df)
        df = cast_types(df)
        result = engineer_features(df)
        assert result["rating_tier"].notna().all()
        assert result["features_tier"].notna().all()
        assert (result["rating_tier"].astype(str) == "Mid").all()
        assert (result["features_tier"].astype(str) == "Mid").all()


class TestCastTypesWithNulls:
    def test_cast_types_handles_null_plan_count(self, base_df):
        df = handle_nulls(base_df)
        df["plan_count"] = df["plan_count"].where(df["plan_count"] != 3, None)
        result = cast_types(df)
        assert result["plan_count"].dtype == int
        assert result["plan_count"].isna().sum() == 0

    def test_cast_types_handles_null_features_count(self, base_df):
        df = handle_nulls(base_df)
        df["features_count"] = df["features_count"].where(df["features_count"] != 20, None)
        result = cast_types(df)
        assert result["features_count"].dtype == int
        assert result["features_count"].isna().sum() == 0

    def test_cast_types_handles_null_free_plan(self, base_df):
        df = handle_nulls(base_df)
        df["free_plan"] = df["free_plan"].where(~df["free_plan"], None)
        result = cast_types(df)
        assert result["free_plan"].dtype == bool
        assert result["free_plan"].isna().sum() == 0


class TestDeduplicate:
    def test_removes_duplicate_tool_names(self, base_df):
        df = pd.concat([base_df, base_df.iloc[[0]]], ignore_index=True)
        result = deduplicate(df)
        assert len(result) == len(base_df)

    def test_no_duplicates_unchanged(self, base_df):
        df = base_df
        result = deduplicate(df)
        assert len(result) == len(df)

    def test_keeps_first_occurrence(self):
        df = pd.DataFrame({
            "tool_name": ["A", "A", "B"],
            "category": ["x", "y", "z"],
            "vertical": ["Business", "AI", "Business"],
            "free_plan": [True, False, True],
            "starting_price_usd": [0.0, 10.0, 0.0],
            "highest_plan_price_usd": [10.0, 20.0, 15.0],
            "plan_count": [2, 3, 1],
            "rating": [4.0, 3.0, 5.0],
            "features_count": [10, 15, 8],
            "website": ["a.com", "a2.com", "b.com"],
        })
        result = deduplicate(df)
        assert len(result) == 2
        assert result.loc[0, "category"] == "x"


class TestTransformIntegration:
    def test_full_transform_runs(self, base_df):
        df = base_df
        result = transform(df)
        assert len(result) == len(df)

    def test_no_nulls_after_transform(self, base_df):
        df = transform(base_df)
        for col in ["starting_price_usd", "highest_plan_price_usd", "rating"]:
            assert df[col].isna().sum() == 0
