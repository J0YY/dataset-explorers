#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from datasets import load_dataset
from huggingface_hub import hf_hub_download


HF_ID = "jihyoung/MiSC"  # or "hf://jihyoung/MiSC"
SPLITS = ["train", "validation", "test"]
FILES = ["train.jsonl", "val.jsonl", "test.jsonl"]
TARGET_DIR = Path(__file__).resolve().parents[1] / "data" / "misc"


def cache_via_datasets() -> None:
    hf_id = HF_ID.replace("hf://", "")
    for split in SPLITS:
        try:
            ds = load_dataset(hf_id, split=split)
            _ = ds.select(range(min(100, len(ds))))
            print(f"Cached split via datasets: {split} (rows={len(ds)})")
        except Exception as e:
            print(f"Skip split {split} via datasets: {e}")


def download_raw_files() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for fname in FILES:
        try:
            path = hf_hub_download(
                repo_id=HF_ID.replace("hf://", ""),
                filename=fname,
                repo_type="dataset",
                local_dir=str(TARGET_DIR),
            )
            print(f"Downloaded: {path}")
        except Exception as e:
            print(f"Skip file {fname}: {e}")


def main() -> None:
    cache_via_datasets()
    download_raw_files()
    print(f"Ready. Local raw files dir: {TARGET_DIR}")


if __name__ == "__main__":
    main()


