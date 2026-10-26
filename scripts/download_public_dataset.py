"""Download the public educational e-commerce A/B dataset to data/raw/.

Run from the project root:
    python scripts/download_public_dataset.py
"""
from pathlib import Path
import pandas as pd
from src.real_dataset_adapter import PUBLIC_AB_DATA_URL


def main():
    destination = Path("data/raw/ab_data.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading educational dataset from: {PUBLIC_AB_DATA_URL}")
    frame = pd.read_csv(PUBLIC_AB_DATA_URL)
    frame.to_csv(destination, index=False)
    print(f"Saved {len(frame):,} rows to {destination}")
    print("This is a public educational dataset, not verified production data.")


if __name__ == "__main__":
    main()
