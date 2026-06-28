"""
Shared fixtures and configuration for all tests.
"""

import pandas as pd
import pytest
from loguru import logger


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
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
        }
    )


@pytest.fixture
def base_df():
    return pd.DataFrame(
        {
            "tool_name": ["Notion", "ClickUp", "Asana"],
            "category": ["pm", "pm", "pm"],
            "vertical": ["Business", "Business", "Business"],
            "free_plan": [True, True, False],
            "starting_price_usd": [0.0, 5.0, 10.0],
            "highest_plan_price_usd": [18.0, None, 25.0],
            "plan_count": [4, 3, 4],
            "rating": [4.7, None, 4.4],
            "features_count": [32, 20, 31],
            "website": ["a.com", "b.com", "c.com"],
        }
    )


@pytest.fixture(autouse=True)
def suppress_loguru():
    """Suppress loguru output during tests to avoid noise in logs/."""
    logger.remove()
    logger.add(lambda _: None, level="CRITICAL")
