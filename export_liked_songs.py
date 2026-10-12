"""Source-tree launcher for spotify2csv."""

import sys
from pathlib import Path

# Allow this file to run directly from a clone before the package is installed.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from spotify2csv.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
