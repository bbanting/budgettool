# Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

from __future__ import annotations
import sys
import os
import csv
import json
import shlex
import collections
import logging
import parser
import copy
from datetime import datetime
from typing import List, Union
from parser.validator import VLit, VBool, Validator, ValidatorError, VComment

logging.basicConfig(level=logging.INFO)

ENTRY_FOLDER = "records"

TODAY = datetime.now()

HEADERS = ("id","date","amount","tags","note")

MONTHS = {
    "all": 0, "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

# Words that cannot be used in tags
KEYWORDS = ("income", "expense", "year", "all", "tag") + tuple(MONTHS)

# Widths for display columns
IDW = 8
DATEW = 8
AMOUNTW = 10
TAGSW = 12
NOTEW = None


class BTError(Exception):
    pass


class Config:
    """A class to manage the state of the programs configuration."""
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self._check_file()
        with open(filename, "r") as fp:
                cfgdata = json.load(fp)
        self.active_year = cfgdata["active_year"]
        self.tags = cfgdata["tags"]
        self.old_tags = cfgdata["old_tags"]
        self.bills = cfgdata["bills"]
        
        self.last_query = [TODAY.month, None, None]

    def _overwrite(self) -> None:
        """Overwrite file with current state."""
        self._check_file()
        with open(self.filename, "w") as fp:
            json.dump(self.to_dict(), fp)
    
    def to_dict(self) -> dict:
        """Returns a dictionary representation of the config."""
        return {"active_year": self.active_year,
                "tags": self.tags,
                "old_tags": self.old_tags,
                "bills": self.bills,
                }

    def add_tag(self, name: str):
        """Takes a str and adds it to config as a tag."""
        self.tags.append(name)
        if name in self.old_tags:
            self.old_tags.remove(name)
        self._overwrite()

    def remove_tag(self, name: str, for_undo=False):
        """Removes a tag from the config."""
        if name in self.tags:
            self.tags.remove(name)
            # if name in {t for e in entry_list for t in e.tags}:
            # Only add to old_tags if this isn't for an undo command
            if not for_undo: 
                self.old_tags.append(name)
            self._overwrite()
        else:
            raise BTError("Tag not found.")

    def _check_file(self):
        """Ensures the config exists and the user has file permissions."""
        try:
            with open(self.filename, "r+") as fp:
                pass
        except PermissionError:
            print("You do not have the necessary file permissions.")
            quit()
        except FileNotFoundError:
            with open(self.filename, "w") as fp:
                cfg = {"active_year": TODAY.year, "tags": [], "old_tags": [], "bills": {}}
                json.dump(cfg, fp)


class Entry:
    editable_fields = {
        "amount":   "get_amount", 
        "tags":     "get_tags",
        "note":     "get_note",
        "date":     "get_date",
        }

    def __init__(self, date: datetime, amount: int, tags: List, note:str, id:int=0):
        self.date = date
        self.amount = amount
        self.tags = tags
        self.note = note

        if id:
            self.id = id
        else:
            self.id = self.generate_id()

    @property
    def type(self) -> str:
        if self.amount > 0:
            return "income"
        else:
            return "expense"

    @property
    def parent_record(self) -> YearlyRecord:
        return active_records[self.date.year]

    @classmethod
    def from_csv(cls, data: list):
        """Contruct an entry from a csv line."""
        id, date, amount, tags, note = data
        id = int(id)
        date = datetime.strptime(date, "%Y/%m/%d")
        amount = int(amount)
        tags = cls._verify_tags(tags.split(" "))

        return cls(date, amount, tags, note, id=id)

    @staticmethod
    def cents_to_dollars(cent_amount) -> str:
        """Convert a cent amount to dollars for display."""
        if cent_amount > 0:
            return f"+${cent_amount/100:.2f}"
        else:
            return f"-${abs(cent_amount/100):.2f}"

    @staticmethod
    def dollars_to_cents(dollar_amount: str) -> int:
        """Convert a string dollar ammount to cents for storage."""
        return int(float(dollar_amount) * 100)

    @staticmethod
    def _verify_tags(tags: List):
        """
        Raise error if one of the tags are invalid;
        Otherwise return list back.
        """
        for t in tags:
            if t not in (config.tags + config.old_tags):
                raise BTError("Invalid tag.")
        return tags

    def in_dollars(self):
        return Entry.cents_to_dollars(self.amount)

    def to_csv(self) -> List:
        """Convert entry into list for writing by the csv module."""
        date = self.date.strftime("%Y/%m/%d")
        return [self.id, date, f"{self.amount}", " ".join(self.tags), self.note]

    def generate_id(self) -> int:
        """Generate a new unused ID for a new entry."""
        if len(self.parent_record) > 0:
            prev_id = self.parent_record[-1].id
            return prev_id + 1
        else:
            return 1
    
    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        tags = ", ".join(self.tags)
        if len(tags) > 12:
            tags = tags[:9] + "..."
        return f"{str(self.id).zfill(4):{IDW}}{date:{DATEW}} {self.in_dollars():{AMOUNTW}} {tags:{TAGSW}} {self.note}"


class MasterRecord(collections.UserDict):
    """A class to hold all YearlyRecords."""
    def add_yearly_record(self, year: int) -> YearlyRecord:
        self[year] = YearlyRecord(year)

    def __iter__(self):
        return super().__iter__()
        # Overwrite this to allow traversing between years
    
    def __getitem__(self, key: int):
        try:
            super().__getitem__(key)
        except KeyError:
            self.update({key: YearlyRecord(key)})
        return super().__getitem__(key)


class YearlyRecord(collections.UserList):
    """
    A list to group entry sets together by year and 
    handle saving them to disk.
    """
    def __init__(self, year: int) -> None:
        """Initialize and check for file errors."""
        super().__init__()

        self.year = year
        self._check_file()

        with open(f"{ENTRY_FOLDER}/{self.year}.csv", "r", newline="") as fp:
            lines = list(csv.reader(fp))
        if lines[0] != list(HEADERS):
            print(f"Error: Invalid CSV headers.")
            quit()

        entries = []
        for i, ln in enumerate(lines[1:]):
            try:
                entry = Entry.from_csv(ln)
            except (ValueError, BTError):
                print(f"Error parsing line {i+2}. Your CSV file may be corrupted.")
                quit()
            else:
                entries.append(entry)
        self.extend(entries)

    def _check_file(self) -> None:
        """Ensure the CSV file can be opened barring a permission error."""
        os.makedirs(f"{os.getcwd()}/{ENTRY_FOLDER}", exist_ok=True)
        try:
            with open(f"{ENTRY_FOLDER}/{self.year}.csv", "r+"):
                pass
        except PermissionError:
            print("You do not have the necessary file permissions.")
            quit()
        except FileNotFoundError:
            with open(f"{ENTRY_FOLDER}/{self.year}.csv", "w", newline="") as fp:
                csv.writer(fp).writerow(HEADERS)

    def _overwrite(self):
        """Overwrite the csv file with current entries."""
        self._check_file()
        rows = []
        rows.append(list(HEADERS))
        for e in self:
            rows.append(e.to_csv())
        with open(f"{ENTRY_FOLDER}/{self.year}.csv", "w", newline="") as fp:
            csv.writer(fp).writerows(rows)

    def replace(self, old: Entry, new: Entry) -> None:
        """Replace old Entry with new Entry."""
        index = self.index(old)
        self[index] = new
        self._overwrite()

    def append(self, item: Entry) -> None:
        super().append(item)
        self._overwrite()

    def remove(self, item: Entry) -> None:
        super().remove(item)
        self._overwrite()


class VMonth(Validator):
    """Verify that input refers to a month; if so, return it as int."""
    def validate(self, value) -> Union[int, ValidatorError]:
        name = value.lower()
        for month in MONTHS:
            if month.startswith(name): 
                return MONTHS[month]
        
        # if not self.strict and name in ("all", "year"):
        #     return "year"
        return ValidatorError("Month not found")


class VDay(Validator):
    """Verify and capture day of a month."""
    def validate(self, value) -> Union[int, ValidatorError]:
        if value.isdigit() and int(value) in range(1, 32):
            return int(value)
        return ValidatorError("Invalid day number")


class VYear(Validator):
    """Verify and capture year number."""
    def validate(self, value) -> Union[int, ValidatorError]:
        if value.isdigit() and len(value) == 4:
            return int(value)
        return ValidatorError("Invalid year number")


class VTag(Validator):
    """Verify that input belongs to the user's tags; if so, return it."""
    def __init__(self, *args, **kwargs):
        super().__init__(plural=True, *args, **kwargs)

    def validate(self, value) -> Union[str, ValidatorError]:
        if value.lower() in config.tags:
            return value.lower()
        else:
            return ValidatorError("Tag not found.")


class VNewTag(Validator):
    """Verify that str is a valid name for a new tag."""
    def validate(self, value: str) -> Union[str, ValidatorError]:
        value = value.lower()
        if value in KEYWORDS:
            return ValidatorError("Tag name may not be a keyword.")
        if ("+" in value) or ("!" in value):
            return ValidatorError("Tag name may not contain '+' or '!'.")
        if value in config.tags:
            return ValidatorError("Tag already exists.")
        return value


class VType(Validator):
    """Capture the type of entry."""
    def validate(self, value: str) -> Union[str, ValidatorError]:
        value = value.lower()
        if value == "income":
            return value
        elif value in ("expense", "expenses"):
            return "expense"
        return ValidatorError("Invalid type.")


class VID(Validator):
    """Capture an ID"""
    def validate(self, value: str) -> Union[int, ValidatorError]:
        if value.isdigit() and len(value) <= 4:
            return int(value)
        return ValidatorError("Invalid ID")


def get_date():
    """Retrieve the date input from the user."""
    while True:
        user_input = input("Date: ").split()
        if not user_input and TODAY.year != config.active_year:
            print("Can't infer date when current year not active.")
        elif not user_input:
            return TODAY
        elif len(user_input) >= 2 <= 3:
            month = VMonth(strict=True)(user_input)
            day = VDay()(user_input)
            year = VYear(default=config.active_year)(user_input)
            return datetime(year, month, day)
        else:
            print("Invalid input.")


def get_amount():
    """Retrieve the amount input from the user."""
    while True:
        amount = input("Amount: ").strip()
        if amount.lower() == "back":
            raise BTError("Command terminated.")
        if not amount.startswith(("-", "+")):
            print("The amount must start with + or -")
            continue
        amount = Entry.dollars_to_cents(amount)
        return amount


def _match_tag(query: str) -> str:
    """Check if string matches a tag. If so, return the tag."""
    query = query.strip().lower()
    results = []

    for t in config.tags:
        if t.lower().startswith(query):
            results.append(t)
    
    if len(results) != 1:
        return None
    else:
        return results[0]


def get_tags() -> List:
    """Get tag(s) input from user."""
    while True:
        tags = input("Tags: ")
        if tags.lower().strip() == "back":
            raise BTError("Command terminated.")
        if tags == "":
            print(f"Tags: {', '.join(config.tags)}")
            continue
        else:
            tags = tags.split(" ")

        if not all(tags := [_match_tag(t) for t in tags]):
            print("Invalid tags given.")
            continue
        return tags
            

def get_note() -> str:
    """Get note input from the user"""
    while True:
        note = input("Note: ")
        if note.lower() == "back":
            raise BTError("Command terminated.")
        if not note:
            return "..."
        return note


def find_entry(year: YearlyRecord, id: int) -> Union[Entry, None]:
    """Find an entry by ID and return it."""
    for entry in reversed(year):
        if entry.id != id:
            continue
        return entry


class ListCommand(parser.Command):
    """Display a list of entries filtered by type, month, and tags."""
    names = ("list",)
    params = {
        "month": VMonth(default=TODAY.month),
        "typ": VType(),
        "tags": VTag(),
        }
    help_text = "If no year or month are specified it will default to the current year and month."
    
    def execute(self, month, typ, tags):
        entries = self.filter_entries(month, typ, tags)
        
        print(f"{'':{IDW}}{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'TAGS':{TAGSW}} {'NOTE'}")
        total = Entry.cents_to_dollars(sum([e.amount for e in entries]))
        for entry in entries:
            print(entry)
        print("-" * (os.get_terminal_size()[0] - 1))
        print(f"TOTAL: {total}")
        print(self.get_filter_summary(len(entries), month, typ, tags))

    def get_filter_summary(self, n, month, typ, tags) -> str:
        month = list(MONTHS)[month].title()
        typ = f" of type {typ}" if typ else ""
        tags = " with tags: " + ', '.join(tags) if tags else ""
        return f"{n} entries{typ} from {month} of {config.active_year}{tags}."
    
    def filter_entries(self, month=None, typ=None, tags=()) -> list[Entry]:
        """
        Filter and return entries based on input.
        Raise exception if none found
        """
        if month is None and config.active_year == TODAY.year:
            month = TODAY.month
        elif month is None and config.active_year != TODAY.year:
            month = 12

        if len(active_records[config.active_year]) == 0:
            raise BTError("Record is empty.")

        filtered_entries = []
        for e in active_records[config.active_year]:
            if month != 0 and e.date.month != month:
                continue
            if typ and typ != e.type:
                continue
            if tags and not any([True if t in e.tags else False for t in tags]):
                continue
            filtered_entries.append(e)

        if not filtered_entries:
            raise BTError("No entries found.")
        return sorted(filtered_entries, key=lambda x: x.date)


class GetCommand(ListCommand):
    names = ("get",)
    def execute(self, month, typ, tags):
        config.last_query = [month, typ, tags]
    

class SummarizeCommand(ListCommand):
    """Display a summary of entries filtered by type, month, and tags."""
    names = ("sum", "summarize")

    def execute(self, month, typ, tags):
        try:
            entries = self.filter_entries(month, typ, tags)
        except BTError as e:
            print(e)
        else:
            total = Entry.cents_to_dollars(sum([e.amount for e in entries]))
            x = "Entry" if len(entries) < 2 else "Entries"
            print(f"{len(entries)} {x}")
            print(f"TOTAL: {total}")
            print(self.get_filter_summary(len(entries), month, typ, tags))


# def quick_add_entry(*args):
#     amount, category = args[:2]
#     note = ",".join(args[2:])
#     entry = Entry(TODAY.strftime("%Y/%m/%d"), amount, category, note)


class AddEntryCommand(parser.Command):
    """Add an entry, entering input through a series of prompts."""
    def execute(self):
        try:
            date = get_date()
            amount = get_amount()
            tags = get_tags()
            note = get_note()
        except BTError:
            pass # Exit the command
        else:
            self.entry = Entry(date, amount, tags, note)
            active_records[date.year].append(self.entry)
        
    def undo(self):
        active_records[self.entry.date.year].remove(self.entry)

    def redo(self):
        active_records[self.entry.date.year].append(self.entry)


class AddTagCommand(parser.Command):
    """Add a name to the list of tags."""
    params = {
        "name": VNewTag(req=True),
    }

    def execute(self):
        config.add_tag(self.data["name"])

    def undo(self):
        config.remove_tag(self.data["name"], for_undo=True)

    def redo(self):
        config.add_tag(self.data["name"])


class AddCommand(parser.ForkCommand):
    """Add an entry or tag."""    
    names = ("add",)
    forks = {
        "entry": AddEntryCommand,
        "tag": AddTagCommand
    }
    default = "entry"
    help_text = "If neither 'entry' or 'tag' are specified, it will default to 'entry.'"


class RemoveEntryCommand(parser.Command):
    """Remove and Entry by its ID."""
    params = {
        "id": VID(req=True),
    }

    def execute(self, id):
        self.entry = find_entry(active_records[config.active_year], id)
        if not self.entry:
            print("Entry not found.")
            return
        ans = None
        date = self.entry.date.strftime("%b %d")
        prompt = f"(Y/n) Are you sure you want to delete entry {self.entry.id}? ({date}: {self.entry.in_dollars()})\n"
        while ans not in ("yes", "no", "y", "n"):
            ans = input(prompt).lower()
        if ans in ("yes", "y"):
            active_records[self.entry.date.year].remove(self.entry)

    def undo(self):
        active_records[self.entry.date.year].append(self.entry)

    def redo(self):
        active_records[self.entry.date.year].remove(self.entry)


class RemoveTagCommand(parser.Command):
    """Remove a tag by its name."""
    params = {
        "name": VTag(req=True),
    }

    def execute(self):
        config.remove_tag(self.data["name"])

    def undo(self):
        config.add_tag(self.data["name"])

    def redo(self):
        config.remove_tag(self.data["name"])


class RemoveCommand(parser.ForkCommand):
    """Delete an entry or tag."""
    names = ("del", "delete", "remove")
    forks = {
        "entry": RemoveEntryCommand,
        "tag": RemoveTagCommand,
    }
    default = "entry"


class EditEntryCommand(parser.Command):
    """Edit an entry; requires an ID and a field."""
    names = ("edit",)
    params = {
        "id": VID(req=True),
        "field": VLit(Entry.editable_fields, lower=True, req=True),
    }

    def execute(self, id: int, field: str) -> None:
        self.old_entry = find_entry(active_records[config.active_year], id)
        if not self.old_entry:
            print("Entry not found.")
            return
        self.new_entry = copy.copy(self.old_entry)
        new_value = globals()[self.new_entry.editable_fields[field]]()
        setattr(self.new_entry, field, new_value)
        active_records[config.active_year].replace(self.old_entry, self.new_entry)

    def undo(self) -> None:
        active_records[config.active_year].replace(self.new_entry, self.old_entry)
    
    def redo(self) -> None:
        active_records[config.active_year].replace(self.old_entry, self.new_entry)


class ShowBillsCommand(parser.Command):
    """Display the bills; placeholder command."""
    names = ("bills",)

    def execute(self):
        for k, v in config.bills.items():
            print(f"{k}:\t{v}")


def manage_goals():
    pass


# def switch_year(year=VBool(str.isdigit, req=True)):
#     """Switches to different year.""" ### Maybe don't write to config??
#     year = int(year)
#     if os.path.exists(f"{year}.csv"):
#         config.active_year = year
#         print(f"Records for {year} are now active.")
#         return

#     print("Invalid year input.")


class QuitCommand(parser.Command):
    """Quits the program."""
    names = ("q", "quit")

    def execute(self):
        quit()


def btinput(context) -> str:
    """Wrapper for builtin input function"""
    pass


def filter_entries(month=None, typ=None, tags=()) -> list[Entry]:
    """
    Filter and return entries based on input.
    Raise exception if none found
    """
    if month is None and config.active_year == TODAY.year:
        month = TODAY.month
    elif month is None and config.active_year != TODAY.year:
        month = 12

    if len(active_records[config.active_year]) == 0:
        raise BTError("Record is empty.")

    filtered_entries = []
    for e in active_records[config.active_year]:
        if month != 0 and e.date.month != month:
            continue
        if typ and typ != e.type:
            continue
        if tags and not any([True if t in e.tags else False for t in tags]):
            continue
        filtered_entries.append(e)

    if not filtered_entries:
        raise BTError("No entries found.")
    return sorted(filtered_entries, key=lambda x: x.date)


def display_entry_summary(n, month, typ, tags):
    month = list(MONTHS)[month].title()
    typ = f" of type {typ}" if typ else ""
    tags = " with tags: " + ', '.join(tags) if tags else ""
    print(f"Showing {n} entries{typ} from {month} of {config.active_year}{tags}.")


def refresh_display():
    print("\n" * os.get_terminal_size()[1])
    error = None
    entries = None
    try:
        entries = filter_entries(*config.last_query)
    except BTError as e:
        error = e
    else:
        for entry in entries:
            print(entry)

    print("-" * (os.get_terminal_size()[0] - 1))
    if entries:
        display_entry_summary(len(entries), *config.last_query)
    if error:
        print(error)


def main():
    controller = parser.CommandController()
    controller.register(parser.UndoCommand)
    controller.register(parser.RedoCommand)
    controller.register(parser.HelpCommand)
    controller.register(ListCommand)
    controller.register(SummarizeCommand)
    controller.register(QuitCommand)
    controller.register(RemoveCommand)
    controller.register(RemoveEntryCommand)
    controller.register(RemoveTagCommand)
    controller.register(AddCommand)
    controller.register(AddEntryCommand)
    controller.register(AddTagCommand)
    controller.register(EditEntryCommand)
    controller.register(ShowBillsCommand)
    controller.register(GetCommand)

    controller.route_command(["get"])
    while True:
        refresh_display()
        user_input = shlex.split(input("> "))
        try:
            controller.route_command(user_input, default=GetCommand)
        except BTError as e:
            print(e)
        except KeyboardInterrupt:
            print("")


if __name__=="__main__":
    config = Config("config.json")
    active_records = MasterRecord({TODAY.year: YearlyRecord(TODAY.year)})
    main()
