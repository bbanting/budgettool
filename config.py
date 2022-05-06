from __future__ import annotations
import json
import datetime
import enum
import dataclasses
import entry
import db
import logging


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


@dataclasses.dataclass
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
    """Wrapper class for printing targets."""
    name: str
    amount: int
    tframe: TimeFrame

    def __init__(self, name:str, amount:int) -> None:
        self.name = name
        self.amount = amount
        self.tframe = target_filter_state.tframe
    
    def current_total(self) -> int:
        """Return the amount sum for entries with this 
        target in the specified timeframe.
        """
        return db.sum_target(self.name, self.tframe)

    def goal(self) -> int:
        """Return the goal with respect to current timeframe."""
        if self.tframe.month == 0:
            return self.amount * 12
        return self.amount

    def __str__(self) -> str:
        current = entry.cents_to_dollars(self.current_total())
        goal = entry.cents_to_dollars(self.goal())
        return f"{self.name}: {current:.2f}/{goal:.2f}"


class StateObject:
    """Convenience class for state storage."""
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def set(self, **kwargs) -> None:
        self.__init__(**kwargs)

    def __repr__(self) -> str:
        return f"StateObject({self.__dict__})"


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
    targets.append({"name": name, "amount": amount})
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

entry_filter_state = StateObject(tframe=TimeFrame(), category="", targets=[])
target_filter_state = StateObject(tframe=TimeFrame(), category="")
