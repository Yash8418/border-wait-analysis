"""Run every analysis query and save the results to data/results/.

Usage:
    python -m border_wait.analyze
"""

from __future__ import annotations

from pathlib import Path

from border_wait.db import connect
from border_wait.queries import QUERIES, run

RESULTS_DIR = Path(__file__).resolve().parents[2] / "data" / "results"


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    con = connect()
    for name in QUERIES:
        result = run(con, name)
        result.to_csv(RESULTS_DIR / f"{name}.csv", index=False)
        print(f"{name}: {len(result)} rows")


if __name__ == "__main__":
    main()
