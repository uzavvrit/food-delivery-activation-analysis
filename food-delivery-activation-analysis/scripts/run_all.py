"""Single command to rebuild all metrics and charts from scratch."""
from pathlib import Path
from scripts.generate_data import generate, N_USERS, SEED
from scripts.run_analysis import analyze


def main() -> None:
    print(f"Generating {N_USERS:,} synthetic users (seed={SEED})...")
    generate(Path("data/raw"))
    metrics = analyze(Path("data/raw"), Path("reports"))
    print(f"Done: first-order conversion = {metrics['conversion']:.2f}%")
    print("Open README.md and reports/analysis_report.md")


if __name__ == "__main__":
    main()
