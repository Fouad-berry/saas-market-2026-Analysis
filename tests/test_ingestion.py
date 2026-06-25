"""
Tests for the ingestion layer.
"""

import pandas as pd
import pytest

from src.ingestion.loader import validate_schema

VALID_COLS = [
    "tool_name",
    "category",
    "vertical",
    "free_plan",
    "starting_price_usd",
    "highest_plan_price_usd",
    "plan_count",
    "rating",
    "features_count",
    "website",
]


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
        validate_schema(make_df())  # should not raise

    def test_missing_column_raises(self):
        df = make_df().drop(columns=["rating"])
        with pytest.raises(ValueError, match="Missing columns"):
            validate_schema(df)

    def test_extra_columns_allowed(self):
        df = make_df()
        df["extra_col"] = "foo"
        validate_schema(df)  # extra columns are fine
