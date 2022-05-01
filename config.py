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
KEYWORDS = ("income", "expense", "all", "target", "help", "q", "quit") 

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


class TimeFrame:
    """Represents a timeframe within which to filter entries."""
    year: int
    month: Month
    def __init__(self, year:int=TODAY.year, month:int=TODAY.month):
        self.year = year
        self.month = Month(month)


class ConfigError(Exception):
    pass


class TargetWrapper:
    """Transient wrapper for targets and target groups."""
    name: str
    targets: list

    @property
    def amount(self) -> int:
        return sum([t["amount"] for t in self.targets])

    def __init__(self, name:str, targets:list) -> None:
        self.name = name
        self.targets = targets
        self.date = target_filter_state.date

    def __str__(self) -> str:
        current = entry.cents_to_dollars(sum([db.sum_target(t["name"], self.date) for t in self.targets]))
        goal = entry.cents_to_dollars(sum([t.amount for t in self.targets]))
        return f"{self.name}: {current:.2f}/{goal:.2f}"


class StateObject:
    """Convenience class for state storage."""
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def set(self, **kwargs) -> None:
        self.__init__(**kwargs)


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
            cfg = {"targets": [], "groups": []}
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
        "groups": groups
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
        groups.remove(t)
        break
    overwrite()

def add_group(name:str, targets:list[str]) -> None:
    """Add a target group to the config file."""
    groups.append({"name": name, "targets": targets})
    overwrite()

def remove_group(name:str) -> None:
    """Remove a target group from the config file."""
    for g in groups:
        if g["name"] != name:
            continue
        groups.remove(g)
        break
    overwrite()


def get_target(name:str) -> TargetWrapper | None:
    """Return a TargetWrapper if name refers to a target or group."""
    for t in targets:
        if t["name"] != name:
            continue
        return TargetWrapper(name, [t])
    
    for g in groups:
        if g["name"] != name:
            continue
        return TargetWrapper(name, g["targets"])


check_file(FILENAME)
with open(FILENAME, "r") as fp:
    data = json.load(fp)
try:
    targets = data["targets"]
    groups = data["groups"]
except KeyError:
    print("Error loading config file.")
    quit()


targets: list[dict]
groups: list[dict]

entry_filter_state = StateObject(date=TimeFrame(), category="", target=None)
target_filter_state = StateObject(date=TimeFrame(), category="")
