"""
I/O helpers — read and write Parquet files with consistent settings.
"""

from pathlib import Path

import pandas as pd

from src.utils.logger import logger


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to Parquet via atomic write (tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df_out = df.copy()
    for col in df_out.select_dtypes(include="category").columns:
        df_out[col] = df_out[col].astype(str)
    tmp = path.with_suffix(".tmp.parquet")
    try:
        df_out.to_parquet(tmp, index=False, engine="pyarrow", compression="snappy")
        tmp.rename(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        logger.exception(f"Failed to write Parquet to {path}")
        raise
    size_kb = path.stat().st_size / 1024
    logger.info(f"Written {len(df_out):,} rows → {path.name} ({size_kb:.1f} KB)")


def read_parquet(path: Path) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    try:
        df = pd.read_parquet(path, engine="pyarrow")
    except FileNotFoundError:
        logger.error(f"Parquet file not found: {path}")
        raise
    except Exception:
        logger.exception(f"Failed to read Parquet from {path}")
        raise
    logger.info(f"Read {len(df):,} rows from {path.name}")
    return df
