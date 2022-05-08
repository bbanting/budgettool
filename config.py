from __future__ import annotations
import datetime
import enum
import logging
from dataclasses import dataclass



# Constants
FILENAME = "config.json"
TODAY = datetime.date.today()
KEYWORDS = ("income", "expense", "all", "target", "targets", "entry", "entries")

# Widths for display columns
DATEW = 8
AMOUNTW = 12


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
    targets: list


entry_filter_state = EntryFilterState(tframe=TimeFrame(), category="", targets=[])
target_filter_state = TargetFilterState(tframe=TimeFrame(), category="")
