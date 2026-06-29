"""
Tests for the pipeline orchestrator.
"""

from pathlib import Path

from src.pipeline import parse_args


class TestParseArgs:
    def test_defaults(self):
        args = parse_args([])
        assert args.input is None
        assert args.output_dir is None
        assert args.skip_validation is False
        assert args.verbose is False

    def test_input(self):
        args = parse_args(["--input", "data/test.csv"])
        assert args.input == Path("data/test.csv")

    def test_input_short(self):
        args = parse_args(["-i", "data/test.csv"])
        assert args.input == Path("data/test.csv")

    def test_output_dir(self):
        args = parse_args(["--output-dir", "data/out"])
        assert args.output_dir == Path("data/out")

    def test_output_dir_short(self):
        args = parse_args(["-o", "data/out"])
        assert args.output_dir == Path("data/out")

    def test_skip_validation(self):
        args = parse_args(["--skip-validation"])
        assert args.skip_validation is True

    def test_skip_validation_short(self):
        args = parse_args(["-s"])
        assert args.skip_validation is True

    def test_verbose(self):
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_verbose_short(self):
        args = parse_args(["-v"])
        assert args.verbose is True

    def test_all_flags(self):
        args = parse_args(["-i", "in.csv", "-o", "out", "-s", "-v"])
        assert args.input == Path("in.csv")
        assert args.output_dir == Path("out")
        assert args.skip_validation is True
        assert args.verbose is True
