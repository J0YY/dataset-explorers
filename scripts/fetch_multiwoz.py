#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


REPO_URL = "https://github.com/budzianowski/multiwoz"
TARGET_DIR = Path(__file__).resolve().parents[1] / "multiwoz"
NEEDED = TARGET_DIR / "data" / "MultiWOZ_2.2" / "train" / "dialogues_001.json"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    if NEEDED.exists():
        print("MultiWOZ 2.2 already present:", NEEDED)
        return 0

    if TARGET_DIR.exists():
        print("Found", TARGET_DIR, "but required files are missing. Pulling latest...")
        rc = run(["git", "-C", str(TARGET_DIR), "pull", "--ff-only"])
        if rc != 0:
            print("git pull failed; please check your network and try again.")
            return rc
    else:
        print("Cloning MultiWOZ repo into:", TARGET_DIR)
        rc = run(["git", "clone", REPO_URL, str(TARGET_DIR)])
        if rc != 0:
            print("git clone failed; please check your network and try again.")
            return rc

    if NEEDED.exists():
        print("Success: MultiWOZ 2.2 files are available.")
        return 0

    print("Repo cloned but MultiWOZ_2.2 files not found at:", NEEDED.parent)
    print("Please verify the repository layout or fetch the dataset manually.")
    return 1


if __name__ == "__main__":
    sys.exit(main())


