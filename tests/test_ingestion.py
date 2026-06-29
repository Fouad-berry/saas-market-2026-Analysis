"""
Tests for the ingestion layer.
"""

import pandas as pd
import pytest

from src.ingestion.loader import load_and_validate, load_raw, validate_schema
from src.utils.config import EXPECTED_COLUMNS as EXPECTED_COLS


def make_df(**overrides):
    """Build a minimal valid DataFrame for testing."""
    base = {
        "tool_name": ["Notion", "Asana"],
        "category": ["project-management", "project-management"],
        "vertical": ["Business", "Business"],
        "free_plan": [True, True],
        "starting_price_usd": [0.0, 0.0],
        "highest_plan_price_usd": [18.0, 24.99],
        "plan_count": [4, 4],
        "rating": [4.7, 4.4],
        "features_count": [32, 31],
        "website": ["https://notion.com", "https://asana.com"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


class TestValidateSchema:
    def test_valid_df_passes(self):
        validate_schema(make_df())

    def test_missing_column_raises(self):
        df = make_df().drop(columns=["rating"])
        with pytest.raises(ValueError, match="Missing columns"):
            validate_schema(df)

    def test_extra_columns_allowed(self):
        df = make_df()
        df["extra_col"] = "foo"
        validate_schema(df)


class TestLoadRaw:
    def test_loads_csv_with_expected_columns(self, tmp_path):
        csv = tmp_path / "test.csv"
        csv.write_text(
            "tool_name,category,vertical,free_plan,starting_price_usd,"
            "highest_plan_price_usd,plan_count,rating,features_count,website\n"
            "ToolA,pm,Business,true,0.0,10.0,3,4.5,10,https://toola.com\n"
            "ToolB,pm,Business,false,5.0,20.0,2,4.0,8,https://toolb.com\n"
        )
        df = load_raw(csv)
        assert list(df.columns) == EXPECTED_COLS
        assert len(df) == 2

    def test_loads_empty_csv_returns_empty_df(self, tmp_path):
        csv = tmp_path / "empty.csv"
        csv.write_text(
            "tool_name,category,vertical,free_plan,starting_price_usd,"
            "highest_plan_price_usd,plan_count,rating,features_count,website\n"
        )
        df = load_raw(csv)
        assert len(df) == 0
        assert list(df.columns) == EXPECTED_COLS

    def test_load_raw_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_raw(tmp_path / "nonexistent.csv")


class TestLoadAndValidate:
    def test_load_and_validate_returns_dataframe(self, tmp_path):
        csv = tmp_path / "valid.csv"
        csv.write_text(
            "tool_name,category,vertical,free_plan,starting_price_usd,"
            "highest_plan_price_usd,plan_count,rating,features_count,website\n"
            "ToolA,pm,Business,true,0.0,10.0,3,4.5,10,https://toola.com\n"
        )
        df = load_and_validate(csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert list(df.columns) == EXPECTED_COLS

    def test_load_and_validate_missing_column_raises(self, tmp_path):
        csv = tmp_path / "bad.csv"
        csv.write_text("tool_name,category\nToolA,pm\n")
        with pytest.raises(ValueError, match="Missing columns"):
            load_and_validate(csv)
