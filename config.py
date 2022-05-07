from __future__ import annotations
import json
import datetime
import enum
import logging
from dataclasses import dataclass

import entry
import db


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


class ConfigError(Exception):
    pass


class Target:
    """Class for printing targets."""
    name: str
    default_amount: int
    tframe: TimeFrame

    def __init__(self, name:str, default_amount:int) -> None:
        self.name = name
        self.tframe = target_filter_state.tframe
        self.default_amount = default_amount

    def current_total(self) -> int:
        """Return the amount sum for entries with this 
        target in the specified timeframe.
        """
        return db.sum_target(self.name, self.tframe)

    def goal(self) -> int:
        """Return the goal with respect to current timeframe."""
        if self.tframe.month == 0:
            goals = [db.get_monthly_target_amount(self.name, x) for x in range(1, 13)]
            return sum(goals)
        return db.get_monthly_target_amount(self.name, self.tframe.month.value)

    def __str__(self) -> str:
        current = entry.cents_to_dollars(self.current_total())
        goal = entry.cents_to_dollars(self.goal())
        return f"{self.name}: {current:.2f}/{goal:.2f}"


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


def check_file(filename) -> None:
    """Ensures the config file exists and the user has file permissions."""
    try:
        with open(filename, "r+") as fp:
            pass
    except PermissionError:
        print("You do not have the necessary file permissions.")
        quit()
    except FileNotFoundError:
        with open(filename, "w") as fp:
            cfg = {"targets": []}
            json.dump(cfg, fp)


def overwrite() -> None:
    """Overwrite file with current state."""
    check_file(FILENAME)
    with open(FILENAME, "w") as fp:
        json.dump(to_dict(), fp)


def to_dict() -> dict:
    """Returns a dictionary representation of the config."""
    return {
        "targets": targets, 
        }


def add_target(name:str, amount:int) -> None:
    """Adds a new target to the config file."""
    targets.append({"name": name, "default_amount": amount})
    overwrite()


def remove_target(name:str) -> None:
    """Removes a target from the config."""
    for t in targets:
        if t["name"] != name:
            continue
        targets.remove(t)
        break
    overwrite()


def get_target(name:str) -> Target | None:
    """Return a Target if name refers to a target."""
    for t in targets:
        if t["name"] != name:
            continue
        return Target(**t)


check_file(FILENAME)
with open(FILENAME, "r") as fp:
    data = json.load(fp)
try:
    targets = data["targets"]
except KeyError:
    print("Error loading config file.")
    quit()


targets: list[dict]

entry_filter_state = EntryFilterState(tframe=TimeFrame(), category="", targets=[])
target_filter_state = TargetFilterState(tframe=TimeFrame(), category="")
