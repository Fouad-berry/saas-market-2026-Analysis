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


class TestDeduplicate:
    def test_removes_exact_duplicates(self, base_df):
        df = pd.concat([base_df, base_df.iloc[[0]]], ignore_index=True)
        result = deduplicate(df)
        assert len(result) == len(base_df)

    def test_no_duplicates_unchanged(self, base_df):
        df = base_df
        result = deduplicate(df)
        assert len(result) == len(df)


class TestTransformIntegration:
    def test_full_transform_runs(self, base_df):
        df = base_df
        result = transform(df)
        assert len(result) == len(df)

    def test_no_nulls_after_transform(self, base_df):
        df = transform(base_df)
        for col in ["starting_price_usd", "highest_plan_price_usd", "rating"]:
            assert df[col].isna().sum() == 0
