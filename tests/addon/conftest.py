"""Conftest for addon tests — ensures addon is importable."""

from __future__ import annotations

import sys
from pathlib import Path

# Add addon directory to Python path
addon_path = str(Path(__file__).parent.parent.parent / "addon")
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)
