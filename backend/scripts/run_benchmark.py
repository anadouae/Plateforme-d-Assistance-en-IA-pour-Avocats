"""Run the 50-question Moroccan legal benchmark."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.benchmark import run_benchmark


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print("Running Sanad benchmark (50 MA legal questions)...")
    summary = run_benchmark(limit=limit)
    print(f"Pass rate: {summary['pass_rate_pct']}% ({summary['passed']}/{summary['total']})")
    print(f"Avg score: {summary['avg_score']}")
    print(f"By domain: {summary['by_domain']}")
    print(f"Results saved to backend/data/benchmark_results.json")


if __name__ == "__main__":
    main()
