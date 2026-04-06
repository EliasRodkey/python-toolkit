"""
pleasant_loggers._analysis

LogReader: parses NDJSON log files into pandas DataFrames with filter(),
performance_summary(), and activity_timeline() methods.

Also provides the CLI entry point registered as `pleasant-logs`.

Usage:
    from pleasant_loggers import LogReader

    reader = LogReader(handler_controller.json_file_path).load()
    df = reader.filter(level="error")
    print(reader.performance_summary())

CLI:
    pleasant-logs data/logs/run.json.log --level ERROR --summary
"""
import argparse
import json
from pathlib import Path
from typing import Optional, Union


class LogReader:
    """
    Reads and analyses a flat NDJSON log file.

    Accepts any flat NDJSON file — unknown fields land as nullable columns.
    pandas is a lazy import: only loaded when load() is called.

    Chain pattern:
        reader = LogReader(path).load()
        df = reader.filter(level="error", start="2026-01-01")
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._df = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> "LogReader":
        """
        Parse the NDJSON log file into an internal DataFrame.

        Returns self for method chaining.

        Raises:
            ImportError: If pandas is not installed, with an actionable
                         install message.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "LogReader requires pandas. "
                "Install it with: pip install pleasant-loggers[analysis]"
            )

        records = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        self._df = pd.DataFrame(records)
        return self

    def to_df(self) -> "pd.DataFrame":
        """Return the full log DataFrame."""
        if self._df is None:
            raise RuntimeError("Call load() before accessing the DataFrame.")
        return self._df

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter(
        self,
        level: Optional[Union[str, list[str]]] = None,
        func_name: Optional[Union[str, list[str]]] = None,
        module: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> "pd.DataFrame":
        """
        Return a filtered DataFrame.

        Args:
            level: One or more log level strings (case-insensitive).
            func_name: One or more function names to filter on.
            module: Module name to filter on.
            start: ISO datetime string — include records at or after this time.
            end: ISO datetime string — include records at or before this time.
        """
        import pandas as pd

        df = self.to_df().copy()

        if level is not None:
            if isinstance(level, str):
                level = [level]
            levels_lower = [l.lower() for l in level]
            if "level" in df.columns:
                df = df[df["level"].str.lower().isin(levels_lower)]

        if func_name is not None:
            if isinstance(func_name, str):
                func_name = [func_name]
            if "func_name" in df.columns:
                df = df[df["func_name"].isin(func_name)]

        if module is not None and "module" in df.columns:
            df = df[df["module"] == module]

        if (start is not None or end is not None) and "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            if start is not None:
                start_dt = pd.to_datetime(start, utc=True)
                df = df[ts >= start_dt]
            if end is not None:
                end_dt = pd.to_datetime(end, utc=True)
                df = df[ts <= end_dt]

        return df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

    def performance_summary(self) -> "pd.DataFrame":
        """
        Return a summary DataFrame for PERFORMANCE records, grouped by
        func_name, with mean/min/max of duration_ms.
        """
        import pandas as pd

        perf_df = self.filter(level="performance")

        if perf_df.empty or "duration_ms" not in perf_df.columns:
            return pd.DataFrame(
                columns=["func_name", "mean_duration_ms", "min_duration_ms", "max_duration_ms"]
            )

        group_col = "func_name" if "func_name" in perf_df.columns else "event"
        summary = (
            perf_df.groupby(group_col)["duration_ms"]
            .agg(mean_duration_ms="mean", min_duration_ms="min", max_duration_ms="max")
            .reset_index()
        )
        return summary

    def activity_timeline(self, func_name: str) -> "pd.DataFrame":
        """
        Return all records for a given function, sorted by timestamp.

        Args:
            func_name: The function name to retrieve.
        """
        import pandas as pd

        if "func_name" not in self.to_df().columns:
            return pd.DataFrame()

        df = self.filter(func_name=func_name)

        if "timestamp" in df.columns:
            df = df.copy()
            df["_ts_sort"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            df = df.sort_values("_ts_sort").drop(columns=["_ts_sort"])

        return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def cli_main() -> None:
    """
    CLI for filtering and summarising log files.

    Usage:
        pleasant-logs <log_file> [options]

    Options:
        --level LEVEL [LEVEL ...]    Filter by one or more log levels
        --func FUNC_NAME             Filter by function name
        --start ISO_DATE             Start datetime filter (ISO format)
        --end ISO_DATE               End datetime filter (ISO format)
        --summary                    Print performance_summary() table
        --output FILE                Write filtered DataFrame to CSV
    """
    parser = argparse.ArgumentParser(
        prog="pleasant-logs",
        description="Filter and analyse pleasant_loggers NDJSON log files.",
    )
    parser.add_argument("log_file", help="Path to the NDJSON log file.")
    parser.add_argument("--level", nargs="+", help="Filter by log level(s).")
    parser.add_argument("--func", help="Filter by function name.")
    parser.add_argument("--start", help="Start datetime (ISO format).")
    parser.add_argument("--end", help="End datetime (ISO format).")
    parser.add_argument("--summary", action="store_true", help="Print performance summary.")
    parser.add_argument("--output", help="Write filtered output to a CSV file.")

    args = parser.parse_args()

    reader = LogReader(args.log_file).load()

    if args.summary:
        print(reader.performance_summary().to_string(index=False))
        return

    df = reader.filter(
        level=args.level,
        func_name=args.func,
        start=args.start,
        end=args.end,
    )

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} records to {args.output}")
    else:
        print(df.to_string(index=False))


if __name__ == "__main__":
    cli_main()
