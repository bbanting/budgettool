from __future__ import annotations
import datetime
import logging
from dataclasses import dataclass

from util import TimeFrame, Month



# Constants
FILENAME = "config.json"
TODAY = datetime.date.today()
KEYWORDS = ("income", "expense", "all", "target", "targets", "entry", "entries", "default")
KEYWORDS += tuple(Month.__members__)

# Screen names
ENTRIES = "entries"
TARGETS = "targets"
GRAPH = "graph"

# Widths for display columns
DATEW = 8
AMOUNTW = 12
TARGETW = 12
NAMEW = 12  # For target names


@dataclass(slots=True)
class TargetFilterState:
    """Convenience class for storing target filter state."""
    tframe: TimeFrame
    category: str = ""


@dataclass(slots=True)
class EntryFilterState:
    """Convenience class for storing target filter state."""
    tframe: TimeFrame
    category: str
    targets: list[str]


entry_filter_state = EntryFilterState(tframe=TimeFrame(), category="", targets=[])
target_filter_state = TargetFilterState(tframe=TimeFrame(), category="")
