from __future__ import annotations
import json
import datetime
import enum
import dataclasses
import collections
import entry
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


@dataclasses.dataclass
class TimeFrame:
    """Represents a timeframe within which to filter entries."""
    year: int
    month: Month
    def __init__(self, year:int, month:int):
        self.year = year
        self.month = Month(month)


Query = collections.namedtuple("Query", ("date", "category", "target"))


class ConfigError(Exception):
    pass


class UserData:
    def __init__(self, filename) -> None:
        UserData.check_file(filename)
        with open(filename, "r") as fp:
            data = json.load(fp)

        self.filename = filename
        try:
            self.targets = [entry.Target.from_dict(d) for d in data["targets"]]
            self.groups = data["groups"]
        except KeyError:
            print("Error loading config file.")
            quit()

    @staticmethod
    def check_file(filename):
        """Ensures the config file exists and the user has file permissions."""
        try:
            with open(filename, "r+") as fp:
                pass
        except PermissionError:
            print("You do not have the necessary file permissions.")
            quit()
        except FileNotFoundError:
            with open(filename, "w") as fp:
                cfg = {"targets": [], "groups": {}}
                json.dump(cfg, fp)

    def overwrite(self) -> None:
        """Overwrite file with current state."""
        self.check_file(self.filename)
        with open(self.filename, "w") as fp:
            json.dump(self.to_dict(), fp)

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the config."""
        return {"targets": [t.__dict__ for t in self.targets],}

    def add_target(self, targ:entry.Target) -> None:
        """Adds a new target to the config file."""
        self.targets.append(targ)
        self.overwrite()

    def remove_target(self, targ:entry.Target) -> None:
        """Removes a target from the config."""
        self.targets.remove(targ)
        self.overwrite()

    def add_group(self, name:str, targets:list[str]) -> None:
        """Add a target group to the config file."""
        self.groups.update({name:targets})
        self.overwrite()

    def remove_group(self, name:str) -> None:
        """Remove a target group from the config file."""
        self.groups.pop(name)
        self.overwrite()


# Other globals
udata = UserData(FILENAME)
last_query = Query(TimeFrame(TODAY.year, TODAY.month), "", [])
