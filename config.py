from __future__ import annotations
import json
import datetime
from tokenize import Token


# Constants
FILENAME = "config.json"
ENTRY_FOLDER = "records"
TODAY = datetime.datetime.now()
HEADERS = ("id","date","amount","tags","note")
MONTHS = {
    "all": 0, "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
KEYWORDS = ("income", "expense", "all", "tag") + tuple(MONTHS)


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


# Other variables
udata = UserData(FILENAME)
active_year = TODAY.year
last_query = [TODAY.month, None, None]
records = None
