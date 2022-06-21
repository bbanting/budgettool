from __future__ import annotations
import datetime
import enum
import logging
from dataclasses import dataclass



# Constants
FILENAME = "config.json"
TODAY = datetime.date.today()
KEYWORDS = ("income", "expense", "all", "target", "targets", "entry", "entries", "default")

# Screen names
ENTRIES = "entries"
TARGETS = "targets"

# Widths for display columns
DATEW = 8
AMOUNTW = 12
NAMEW = 12  # For target names


class Month(enum.IntEnum):
    all = 0
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12
KEYWORDS += tuple(Month.__members__)


@dataclass(slots=True)
class TimeFrame:
    """Represents a timeframe within which to filter entries."""
    year: int
    month: Month
    def __init__(self, year:int=TODAY.year, month:int=TODAY.month):
        self.year = year
        self.month = Month(month)

    def iso_format(self, *, month:bool=True) -> str:
        """Return date in iso format for querying db."""
        if month:
            return f"{self.year}-{self.month.value:02}-%"
        return f"{self.year}-%"


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
