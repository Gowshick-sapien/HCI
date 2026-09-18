#!/usr/bin/env python3
"""Launch a user-scoped desktop gaze calibration session.

Usage:
    python scripts/create_user_profile.py --user <username>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permit direct invocation from the repository's scripts directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or recalibrate a personalized gaze profile."
    )
    parser.add_argument("--user", required=True, help="Profile identifier to create or update")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Delay heavy GUI and computer-vision imports until after argument parsing.
    from src.calibration.calibration_wizard import main as calibration_main

    # The GUI module intentionally accepts a positional user id for direct use;
    # normalize the CLI contract here without duplicating its lifecycle code.
    sys.argv = ["calibration_wizard.py", args.user]
    calibration_main()


if __name__ == "__main__":
    main()
