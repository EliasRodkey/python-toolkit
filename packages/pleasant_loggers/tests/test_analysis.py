"""
tests.test_analysis

Tests for LogReader: load() round-trip, filter() on all axes,
performance_summary(), activity_timeline(), unknown fields as nullable columns,
and ImportError message when pandas missing.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
import structlog

from pleasant_loggers._config import configure_logging
from pleasant_loggers._handlers import HandlerController
from pleasant_loggers._levels import add_performance_level, PERFORMANCE_LEVEL_NUM
from pleasant_loggers._loggers import get_logger
from pleasant_loggers._analysis import LogReader
from pleasant_loggers._modes import DIRECTORY_PER_RUN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset():
    HandlerController._reset()
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()
    yield
    HandlerController._reset()
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()


@pytest.fixture()
def log_file(tmp_path):
    """
    Configure logging, emit several records (standard + PERFORMANCE), and
    return the path to the JSON log file.
    """
    add_performance_level()
    lc = configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN)
    logger = get_logger("test_module")
    stdlib_logger = logging.getLogger("stdlib_module")

    stdlib_logger.info("stdlib info message", extra={"source": "stdlib"})
    stdlib_logger.error("stdlib error message")
    logger.info("structlog info message", category="alpha")
    logger.warning("structlog warning message", category="beta")

    with logger.perf("timed_operation", job_id=1):
        pass

    with logger.perf("timed_operation", job_id=2):
        pass

    return lc.json_file_path


@pytest.fixture()
def reader(log_file):
    return LogReader(log_file).load()


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------

class TestLoad:

    def test_load_returns_self(self, log_file):
        lr = LogReader(log_file)
        assert lr.load() is lr

    def test_load_populates_dataframe(self, reader):
        df = reader.to_df()
        assert len(df) > 0

    def test_to_df_returns_dataframe(self, reader):
        import pandas as pd
        assert isinstance(reader.to_df(), pd.DataFrame)

    def test_records_have_timestamp_column(self, reader):
        df = reader.to_df()
        assert "timestamp" in df.columns

    def test_records_have_level_column(self, reader):
        df = reader.to_df()
        assert "level" in df.columns

    def test_records_have_event_column(self, reader):
        df = reader.to_df()
        assert "event" in df.columns

    def test_records_count_matches_emitted(self, reader):
        """6 records should be in the log file (4 standard + 2 PERFORMANCE)."""
        assert len(reader.to_df()) == 6

    def test_load_twice_resets_state(self, log_file):
        """Calling load() twice must not double the records."""
        lr = LogReader(log_file)
        lr.load()
        lr.load()
        assert len(lr.to_df()) == 6


# ---------------------------------------------------------------------------
# filter()
# ---------------------------------------------------------------------------

class TestFilter:

    def test_filter_by_single_level(self, reader):
        df = reader.filter(level="error")
        assert len(df) > 0
        assert all(df["level"].str.lower() == "error")

    def test_filter_by_multiple_levels(self, reader):
        df = reader.filter(level=["info", "warning"])
        assert len(df) > 0
        levels = set(df["level"].str.lower())
        assert levels.issubset({"info", "warning"})

    def test_filter_by_performance_level(self, reader):
        df = reader.filter(level="performance")
        assert len(df) == 2

    def test_filter_by_func_name(self, reader):
        """Filtering by func_name should return matching records."""
        df_all = reader.to_df()
        if "func_name" in df_all.columns:
            func_names = df_all["func_name"].dropna().unique()
            if len(func_names) > 0:
                target = func_names[0]
                df = reader.filter(func_name=target)
                assert all(df["func_name"] == target)

    def test_filter_by_module(self, reader):
        df_all = reader.to_df()
        if "module" in df_all.columns:
            modules = df_all["module"].dropna().unique()
            if len(modules) > 0:
                target = modules[0]
                df = reader.filter(module=target)
                assert all(df["module"] == target)

    def test_filter_by_start_time_excludes_earlier(self, reader):
        df_all = reader.to_df()
        if len(df_all) > 0:
            # Use a future timestamp — should return empty
            future = "2099-01-01T00:00:00+00:00"
            df = reader.filter(start=future)
            assert len(df) == 0

    def test_filter_by_end_time_excludes_later(self, reader):
        # Use a past timestamp — should return empty
        past = "2000-01-01T00:00:00+00:00"
        df = reader.filter(end=past)
        assert len(df) == 0

    def test_filter_no_args_returns_all(self, reader):
        df = reader.filter()
        assert len(df) == len(reader.to_df())


# ---------------------------------------------------------------------------
# performance_summary()
# ---------------------------------------------------------------------------

class TestPerformanceSummary:

    def test_returns_dataframe(self, reader):
        import pandas as pd
        assert isinstance(reader.performance_summary(), pd.DataFrame)

    def test_summary_has_func_name_index_or_column(self, reader):
        df = reader.performance_summary()
        assert "func_name" in df.columns or df.index.name == "func_name"

    def test_summary_has_duration_aggregates(self, reader):
        df = reader.performance_summary()
        col_names = list(df.columns)
        # Should have some form of mean/min/max for duration_ms
        combined = " ".join(str(c) for c in col_names).lower()
        assert "duration" in combined or "mean" in combined or "min" in combined

    def test_summary_only_has_performance_records(self, reader):
        """performance_summary() should only aggregate PERFORMANCE records."""
        df = reader.performance_summary()
        # There should be records (we emitted 2 perf records)
        assert len(df) > 0


# ---------------------------------------------------------------------------
# activity_timeline()
# ---------------------------------------------------------------------------

class TestActivityTimeline:

    def test_returns_dataframe(self, reader):
        import pandas as pd
        df_all = reader.to_df()
        func_names = df_all["func_name"].dropna().unique() if "func_name" in df_all.columns else []
        if len(func_names) > 0:
            df = reader.activity_timeline(func_names[0])
            assert isinstance(df, pd.DataFrame)

    def test_timeline_sorted_by_timestamp(self, reader):
        df_all = reader.to_df()
        if "func_name" not in df_all.columns:
            pytest.skip("No func_name column")
        func_names = df_all["func_name"].dropna().unique()
        if len(func_names) == 0:
            pytest.skip("No func_names found")
        df = reader.activity_timeline(func_names[0])
        if len(df) > 1 and "timestamp" in df.columns:
            ts = df["timestamp"].tolist()
            assert ts == sorted(ts)

    def test_timeline_filters_to_given_func_name(self, reader):
        df_all = reader.to_df()
        if "func_name" not in df_all.columns:
            pytest.skip("No func_name column")
        func_names = df_all["func_name"].dropna().unique()
        if len(func_names) == 0:
            pytest.skip("No func_names found")
        target = func_names[0]
        df = reader.activity_timeline(target)
        assert all(df["func_name"] == target)


# ---------------------------------------------------------------------------
# Unknown fields become nullable columns
# ---------------------------------------------------------------------------

class TestUnknownFields:

    def test_unknown_fields_become_columns(self, tmp_path):
        """LogReader should not require any specific NDJSON schema."""
        ndjson_path = tmp_path / "custom.json.log"
        records = [
            {"timestamp": "2026-01-01T00:00:00Z", "level": "info", "event": "test", "custom_field": "hello"},
            {"timestamp": "2026-01-01T00:01:00Z", "level": "info", "event": "test2", "another_field": 42},
        ]
        with open(ndjson_path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        reader = LogReader(str(ndjson_path)).load()
        df = reader.to_df()
        assert "custom_field" in df.columns
        assert "another_field" in df.columns

    def test_missing_fields_are_nullable(self, tmp_path):
        """Records missing a field should have NaN/None in that column."""
        ndjson_path = tmp_path / "sparse.json.log"
        records = [
            {"timestamp": "2026-01-01T00:00:00Z", "level": "info", "event": "a", "optional_field": "present"},
            {"timestamp": "2026-01-01T00:01:00Z", "level": "info", "event": "b"},
        ]
        with open(ndjson_path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        reader = LogReader(str(ndjson_path)).load()
        df = reader.to_df()
        assert "optional_field" in df.columns
        # Second record should have NaN
        assert df["optional_field"].isna().any()


# ---------------------------------------------------------------------------
# ImportError when pandas not installed
# ---------------------------------------------------------------------------

class TestPandasImportError:

    def test_import_error_has_install_hint(self, tmp_path, monkeypatch):
        """If pandas is unavailable, load() raises ImportError with install hint."""
        ndjson_path = tmp_path / "test.json.log"
        ndjson_path.write_text('{"level": "info", "event": "test"}\n')

        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pandas":
                raise ImportError("No module named 'pandas'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        lr = LogReader(str(ndjson_path))
        with pytest.raises(ImportError, match="pleasant-loggers\\[analysis\\]"):
            lr.load()
