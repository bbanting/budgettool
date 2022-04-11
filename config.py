from __future__ import annotations
import json
import datetime
import enum


# Constants
FILENAME = "config.json"
ENTRY_FOLDER = "records"
TODAY = datetime.date.today()
HEADERS = ("id","date","amount","tags","note")
KEYWORDS = ("income", "expense", "all", "tag", "help", "q", "quit") 

# Widths for display columns
IDW = 8
DATEW = 8
AMOUNTW = 10
TAGSW = 12


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


class Date:
    def __init__(self, year=TODAY.year, month=TODAY.month):
        year: int = year
        month: Month = month


class ConfigError(Exception):
    pass


class UserData:
    def __init__(self, filename) -> None:
        UserData.check_file(filename)
        with open(filename, "r") as fp:
            data = json.load(fp)

        self.filename = filename
        self.tags = data["tags"]
        self.old_tags = data["old_tags"]
        self.bills = data["bills"]

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
                cfg = {"tags": [], "old_tags": [], "bills": {}}
                json.dump(cfg, fp)

    def overwrite(self) -> None:
        """Overwrite file with current state."""
        self.check_file(self.filename)
        with open(self.filename, "w") as fp:
            json.dump(self.to_dict(), fp)

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the config."""
        return {"tags": self.tags,
                "old_tags": self.old_tags,
                "bills": self.bills,
                }

    def add_tag(self, name: str):
        """Takes a str and adds it to config as a tag."""
        self.tags.append(name)
        if name in self.old_tags:
            self.old_tags.remove(name)
        self.overwrite()

    def remove_tag(self, name: str, for_undo=False):
        """Removes a tag from the config. str should already be validated."""
        if name not in self.tags:
            raise ConfigError("Tag not found.")

        self.tags.remove(name)
        # Only add to old_tags if this isn't for an undo command
        if not for_undo: 
            self.old_tags.append(name)
        self.overwrite()


# Other globals
udata = UserData(FILENAME)
last_query = (Date(), None, None)
records = None
