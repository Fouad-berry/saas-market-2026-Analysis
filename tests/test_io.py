"""
Tests for the I/O layer.
"""

import pandas as pd
import pytest

from src.utils.io import read_parquet, write_parquet


class TestWriteParquet:
    def test_writes_and_reads_roundtrip(self, tmp_path):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        path = tmp_path / "test.parquet"
        write_parquet(df, path)
        assert path.exists()
        result = read_parquet(path)
        assert result.equals(df)

    def test_writes_categorical_as_string(self, tmp_path):
        df = pd.DataFrame({"cat": pd.Categorical(["a", "b", "c"])})
        path = tmp_path / "cat.parquet"
        write_parquet(df, path)
        result = read_parquet(path)
        assert result["cat"].tolist() == ["a", "b", "c"]


class TestReadParquet:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_parquet(tmp_path / "nonexistent.parquet")
