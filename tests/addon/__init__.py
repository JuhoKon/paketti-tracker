"""Shared fixtures for addon tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add addon directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "addon"))
