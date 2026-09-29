"""Put scripts/ and evals/ on sys.path so tests can import the tools."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sub in ("scripts", "evals"):
    path = str(ROOT / sub)
    if path not in sys.path:
        sys.path.insert(0, path)
