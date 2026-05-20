"""
I/O helpers — read and write Parquet files with consistent settings.
"""

from pathlib import Path

import pandas as pd

from src.utils.logger import logger


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to Parquet, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Convert categoricals back to string for broad Parquet compatibility
    df_out = df.copy()
    for col in df_out.select_dtypes(include="category").columns:
        df_out[col] = df_out[col].astype(str)
    df_out.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    size_kb = path.stat().st_size / 1024
    logger.info(f"Written {len(df_out):,} rows → {path.name} ({size_kb:.1f} KB)")


def read_parquet(path: Path) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    df = pd.read_parquet(path, engine="pyarrow")
    logger.info(f"Read {len(df):,} rows from {path.name}")
    return df
