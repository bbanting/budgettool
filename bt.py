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
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List, Union
import parser
from parser.validator import VLit, VBool, Validator, ValidatorError, VComment


ENTRY_FOLDER = "records"

TODAY = datetime.now()

HEADERS = ("id","date","amount","tags","note","hidden")

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
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


def to_bool(string):
    if string == "True":
        return True
    elif string == "False":
        return False
    else:
        raise BTError("Invalid format.")


class BTError(Exception):
    pass


class Config:
    """A class to manage the state of the programs configuration."""
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self._check_file()
        with open(filename, "r") as fp:
                cfgdata = json.load(fp)
        self.shell = False
        self.active_year = cfgdata["active_year"]
        self.tags = cfgdata["tags"]
        self.old_tags = cfgdata["old_tags"]
        self.bills = cfgdata["bills"]

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

    def remove_tag(self, name: str):
        """Removes a tag from the config."""
        if name in self.tags:
            self.tags.remove(name)
            # if name in {t for e in entry_list for t in e.tags}:
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

    def __init__(self, date: datetime, amount: Decimal, tags: List, note:str,
                    hidden:bool=False, id:int=0):
        self.date = date
        self.amount = amount
        self.tags = tags
        self.note = note
        self.hidden = hidden

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
    def dollars(self) -> str:
        if self.amount > 0:
            return f"+${self.amount:.2f}"
        else:
            return f"-${abs(self.amount):.2f}"

    @property
    def parent_record(self) -> YearlyRecord:
        return active_records[self.date.year]

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

    @classmethod
    def from_csv(cls, data: list):
        """Contruct an entry from a csv line."""
        id, date, amount, tags, note, hidden = data
        id = int(id)
        date = datetime.strptime(date, "%Y/%m/%d")
        amount = Decimal(amount)
        tags = cls._verify_tags(tags.split(" "))
        hidden = to_bool(hidden)

        return cls(date, amount, tags, note, hidden=hidden, id=id)

    def to_csv(self) -> List:
        """Convert entry into list for writing by the csv module."""
        date = self.date.strftime("%Y/%m/%d")
        return [self.id, date, f"{self.amount}", " ".join(self.tags), self.note, self.hidden]

    def generate_id(self) -> int:
        """Generate a new unused ID for a new entry."""
        if len(self.parent_record) > 0:
            prev_id = self.parent_record[-1].id
            return prev_id + 1
        else:
            return 1

    def edit(self, attr, value):
        """Set an attribute and overwrite the file."""
        setattr(self, attr, value)
        self.parent_record._overwrite()
    
    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        note = self.note if self.note else "..."
        tags = ", ".join(self.tags)
        if len(tags) > 12:
            tags = tags[:9] + "..."
        return f"{str(self.id).zfill(4):{IDW}}{date:{DATEW}} {self.dollars:{AMOUNTW}} {tags:{TAGSW}} {note}"


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
            except (ValueError, InvalidOperation, BTError):
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

    def append(self, item):
        super().append(item)
        self._overwrite()

    def remove(self, item):
        super().remove(item)
        self._overwrite()


class VMonth(Validator):
    """Verify that input refers to a month; if so, return it as int."""
    def validate(self, value) -> Union[int, str, ValidatorError]:
        # if value.isdigit() and int(value) in range(1, 13):
        #     return int(value)
        
        name = value.lower()
        for month in MONTHS:
            if month.startswith(name): 
                return MONTHS[month]
        
        if not self.strict and name in ("all", "year"):
            return "year"
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
        if not amount.startswith("-") and not amount.startswith("+"):
            print("The amount must start with + or -")
            continue
        try:
            amount = Decimal(amount)
        except InvalidOperation:
            print("Invalid input.")
        else:
            if amount == 0:
                print("Amount cannot be zero.")
                continue
            else:
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
        return note


def check_tag(tag, tag_list) -> bool:
    if tag in tag_list:
        return True
    else:
        return False


def _filter_entries(month=None, typ=None, tags=()) -> List[Entry]:
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
        if e.hidden:
            continue
        if month != "year" and e.date.month != month:
            continue
        if typ and typ != e.type:
            continue
        if tags and not any([True if t in e.tags else False for t in tags]):
        # if tags and not any([check_tag(t, e.tags) for t in tags]):
            continue
        filtered_entries.append(e)

    if not filtered_entries:
        raise BTError("No entries found.")
    return sorted(filtered_entries, key=lambda x: x.date)


@parser.command("list")
def list_entries(typ=VType(), month=VMonth(), tags=VTag()):
    """Print the entries. Filtered by the user by type, month, and tags."""
    try:
        entries = _filter_entries(month, typ, tags)
    except BTError as e:
        print(e)
    else:
        print(f"{'':{IDW}}{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'TAGS':{TAGSW}} {'NOTE'}")
        total = sum([e.amount for e in entries])
        for entry in entries:
            print(entry)
        sign = "-" if total < 0 else ""
        print(f"\nTOTAL: {sign}${abs(total)}")


class ListCommand(parser.Command):
    names = ("list",)
    params = {
        "typ": VType(),
        "month": VMonth(),
        "tags": VTag(),
        }
    
    def execute(self):
        entries = _filter_entries(self.data["month"], self.data["typ"], self.data["tags"])

        print(f"{'':{IDW}}{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'TAGS':{TAGSW}} {'NOTE'}")
        total = sum([e.amount for e in entries])
        for entry in entries:
            print(entry)
        sign = "-" if total < 0 else ""
        print(f"\nTOTAL: {sign}${abs(total)}")


@parser.command("sum", "summarize")
def summarize(typ=VType(), month=VMonth(), tags=VTag()):
    """Print a summary of the entries. Filtered by the user by type, month, and tags."""
    try:
        entries = _filter_entries(month, typ, tags)
    except BTError as e:
        print(e)
    else:
        total = sum([e.amount for e in entries])
        sign = "-" if total < 0 else ""
        x = "Entry" if len(entries) < 2 else "Entries"
        print(f"{len(entries)} {x}")
        print(f"TOTAL: {sign}${abs(total)}")


# def quick_add_entry(*args):
#     amount, category = args[:2]
#     note = ",".join(args[2:])
#     entry = Entry(TODAY.strftime("%Y/%m/%d"), amount, category, note)


def add_entry():
    """Create an entry from a series of user input and append to csv file."""
    try:
        date = get_date()
        amount = get_amount()
        tags = get_tags()
        note = get_note()
    except BTError:
        pass # Exit the command
    else:
        entry = Entry(date, amount, tags, note)
        active_records[date.year].append(entry)


def del_entry(id=VID(req=True)):
    """Remove an entry by it's ID."""
    for e in active_records[config.active_year][::-1]:
        if e.id == id:
            ans = None
            date = e.date.strftime("%b %d")
            while ans not in ("yes", "no", "y", "n"):
                ans = input(f"(Y/n) Are you sure you want to delete entry {e.id}? ({date}: {e.dollars})\n").lower()
            if ans in ("yes", "y"):
                e.edit("hidden", True)
            break
    else:
        print("Entry not found.")


def add_tag(name=VNewTag(req=True)):
    """Add a tag to the config file."""
    config.add_tag(name)


def del_tag(name=VTag(req=True)):
    """Remove a tag from the config file."""
    config.remove_tag(name)


class AddCommand(parser.Command):
    names = ("add",)
    params = {
        "name": VNewTag(req=True),
    }

    def execute(self):
        config.add_tag(self.data["name"])

    def undo(self):
        config.remove_tag(self.data["name"])

    def redo(self):
        config.add_tag(self.data["name"])


@parser.fork_command("add", forks=("entry", "tag"))
def add_command(fork="entry"):
    """Generic add command that routes to either add_tag or add_entry."""
    if fork == "entry":
        return add_entry
    elif fork == "tag":
        return add_tag


@parser.fork_command("del", "delete", "remove", forks=("entry", "tag"))
def delete_command(fork="entry"):
    """Generic delete command that routes to either del_tag or del_entry."""
    if fork == "entry":
        return del_entry
    elif fork == "tag":
        return del_tag


@parser.command("edit")
def edit_entry(
    id=VBool(str.isdigit, req=True), 
    field=VLit(Entry.editable_fields, lower=True, req=True)):
    """Takes an ID and data type and allows user to change value"""
    id = int(id)
    for e in active_records[config.active_year]:
        if e.id == id:
            new_value = globals()[Entry.editable_fields[field]]()
            e.edit(field, new_value)
            break
    else:
        print("Entry not found.")


@parser.command("bills")
def show_bills():
    """Print the bills; placeholder function."""
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
        

@parser.command("q", "quit")
def quit_program():
    quit()


class QuitCommand(parser.Command):
    names = ("q", "quit")

    def execute(self):
        quit()


def btinput(context) -> str:
    """Wrapper for builtin input function"""
    pass


def shell(controller):
    config.shell = True
    print("Budget Tool")
    print(f"Records for {config.active_year} are active.")
    while True:
        user_input = shlex.split(input("> "))
        try:
            controller.route_command(user_input)
        except BTError as e:
            print(e)


def main(sysargs: List[str]):
    controller = parser.CommandController()
    controller.register(ListCommand)
    controller.register(parser.UndoCommand)
    controller.register(parser.RedoCommand)
    controller.register(QuitCommand)
    controller.register(AddCommand)
    try:
        if not sysargs:
            shell(controller)
        else:
            controller.route_command(sysargs)
            # Catch BTError?
    except KeyboardInterrupt:
        print("")


if __name__=="__main__":
    config = Config("config.json")
    active_records = MasterRecord({TODAY.year: YearlyRecord(TODAY.year)})
    main(sys.argv[1:])
