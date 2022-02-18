# Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

import sys
import os
import csv
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List
from collections import UserList
from parser import route_command, command, branch, ParseUserError
from parser.validators import VLit, VBool, Validator


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
    def __init__(self) -> None:
        Config._check_file()
        with open("config.json", "r") as fp:
                cfgdata = json.load(fp)

        self.active_year = cfgdata["active_year"]
        self.tags = cfgdata["tags"]
        self.old_tags = cfgdata["old_tags"]
        self.bills = cfgdata["bills"]

    def _overwrite(self) -> None:
        """Overwrite file with current state."""
        Config._check_file()
        with open("config.json", "w") as fp:
            json.dump(self.to_dict(), fp)
    
    def to_dict(self) -> dict:
        return {"active_year": self.active_year,
                "tags": self.tags,
                "old_tags": self.old_tags,
                "bills": self.bills,
                }

    def add_tag(self, name: str):
        if name not in self.tags:
            self.tags.append(name)
            if name in self.old_tags:
                self.old_tags.remove(name)
            self._overwrite()
        else:
            raise BTError("Tag already exists.")

    def remove_tag(self, name: str):
        if name in self.tags:
            self.tags.remove(name)
            if name not in self.old_tags:
                self.old_tags.append(name)
            self._overwrite()
        else:
            raise BTError("Tag not found.")
        
            
    @staticmethod
    def _check_file():
        """Check if the config exists."""
        try:
            with open("config.json", "r+") as fp:
                pass
        except PermissionError:
            print("You do not have the necessary file permissions.")
            quit()
        except FileNotFoundError:
            with open("config.json", "w") as fp:
                cfg = {"active_year": TODAY.year, "tags": [], "old_tags": [], "bills": {}}
                json.dump(cfg, fp)

if __name__=="__main__":
    config = Config()


def _verify_tags(tags: List):
    """
    Raise error if one of the tags are invalid;
    Otherwise return list back.
    """
    for t in tags:
        if t not in (config.tags + config.old_tags):
            raise BTError("Invalid tag.")
    return tags


class Entry:
    editable_fields = {
        "amount":   "get_amount", 
        "tags":     "get_tags",
        "note":     "get_note",
        "date":     "get_date",
        }

    def __init__(self, date: str, amount: Decimal, tags: List, note:str,
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

    @classmethod
    def from_csv(cls, data: list):
        """Contruct an entry from a csv line."""
        id, date, amount, tags, note, hidden = data
        id = int(id)
        date = datetime.strptime(date, "%Y/%m/%d")
        amount = Decimal(amount)
        tags = _verify_tags(tags.split(" "))
        hidden = to_bool(hidden)

        return cls(date, amount, tags, note, hidden=hidden, id=id)

    def to_csv(self) -> List:
        """Convert entry into list for writing by the csv module."""
        date = self.date.strftime("%Y/%m/%d")
        return [self.id, date, f"{self.amount}", " ".join(self.tags), self.note, self.hidden]

    def generate_id(self) -> int:
        """Generate a new unused ID for a new entry."""
        if len(entry_list) > 1:
            prev_id = entry_list[-1].id
            return prev_id + 1
        else:
            return 1

    def edit(self, attr, value):
        """Set an attribute and overwrite the file."""
        setattr(self, attr, value)
        entry_list._overwrite()
    
    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        note = self.note if self.note else "..."
        tags = ", ".join(self.tags)
        if len(tags) > 12:
            tags = tags[:9] + "..."
        return f"{str(self.id).zfill(4):{IDW}}{date:{DATEW}} {self.dollars:{AMOUNTW}} {tags:{TAGSW}} {note}"


class EntryList(UserList):
    def __init__(self):
        """Initialize and check for errors."""
        super().__init__()
        self._check_file()

        with open(f"{config.active_year}.csv", "r", newline="") as fp:
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
        try:
            with open(f"{config.active_year}.csv", "r+"):
                pass
        except PermissionError:
            print("You do not have the necessary file permissions.")
            quit()
        except FileNotFoundError:
            with open(f"{config.active_year}.csv", "w", newline="") as fp:
                csv.writer(fp).writerow(HEADERS)

    def _overwrite(self):
        """Overwrite the csv file with current entries."""
        self._check_file()
        rows = []
        rows.append(list(HEADERS))
        for e in self:
            rows.append(e.to_csv())
        with open(f"{config.active_year}.csv", "w", newline="") as fp:
            csv.writer(fp).writerows(rows)

    def append(self, item):
        super().append(item)
        self._overwrite()

    def remove(self, item):
        super().remove(item)
        self._overwrite()

if __name__=="__main__":
    entry_list = EntryList()


class VMonth(Validator):
    def validate(self, value):
        """Return month number based on input."""
        if value.isdigit() and int(value) in range(1, 13):
            return int(value)
        
        name = value.lower()
        for month in MONTHS:
            if month.startswith(name): 
                return MONTHS[month]
        
        if name in ("all", "year"):
            return "year"

        return None


def _match_month(name:str) -> int:
    """Return month number based on input."""
    if name.isdigit() and int(name) in range(1, 13):
        return int(name)
    
    name = name.lower()
    for month in MONTHS:
        if month.startswith(name): 
            return MONTHS[month]
    else:
        raise BTError("Invalid month input.")


def get_date(quick_input=None, *args):
    """Retrieve the date input from the user."""
    # Short-circuit if called through quick add
    if quick_input:
        return _match_month(quick_input)

    while True:
        user_input = input("Date: ")
        if user_input.lower() == "back":
            raise BTError("Command terminated.")
        if not user_input and TODAY.year != config.active_year:
            print("Can't infer date when not in current year.")
            continue
        if not user_input:
            return TODAY
        elif len(user_input.split()) == 2:
            month, day = user_input.split(" ")
            try:
                month, day = _match_month(month), int(day)
            except (BTError, ValueError):
                print("Invalid input.")
                continue
            else:
                return datetime(config.active_year, month, day)
        else:
            print("Invalid input.")


def get_amount(*args):
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


def get_tags(*args) -> List:
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
            

def get_note(*args) -> str:
    """Get note input from the user"""
    while True:
        note = input("Note: ")
        if note.lower() == "back":
            raise BTError("Command terminated.")
        return note


def _filter_entries(month=None, typ=None, tags=()) -> List[Entry]:
    """
    Filter and return entries based on input.
    Raise exception if none found
    """
    if month is None and config.active_year == TODAY.year:
        month = TODAY.month
    elif month is None and config.active_year != TODAY.year:
        month = 12

    if len(entry_list) == 0:
        raise BTError("Record is empty.")

    filtered_entries = []
    for e in entry_list:
        if e.hidden:
            continue
        if month != "year" and e.date.month != month:
            continue
        if typ and typ != e.type:
            continue
        if tags and not any([True if t in e.tags else False for t in tags]):
            continue
        filtered_entries.append(e)

    if not filtered_entries:
        raise BTError("No entries found.")
    return sorted(filtered_entries, key=lambda x: x.date)


@command("list")
def list_entries(
    typ=VLit(("income", "expense"), lower=True), 
    month=VMonth(), 
    tags=VLit(config.tags, lower=True, plural=True),
    errors=None,
    extra=None,):
    """Print the specified entries."""
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
        

@command("sum", "summarize")
def summarize(
    typ=VLit(("income", "expense"), lower=True), 
    month=VMonth(), 
    tags=VLit(config.tags, lower=True, plural=True),
    errors=None,
    extra=None):
    """Print a summary of the specifies entries."""
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


def add_entry(args):
    """Create an entry from user input and append to csv file."""
    try:
        date = get_date()
        amount = get_amount()
        tags = get_tags()
        note = get_note()
    except BTError:
        pass # Exit the command
    else:
        entry = Entry(date, amount, tags, note)
        entry_list.append(entry)


def del_entry(args):
    """Remove an entry by it's ID."""
    id = int(args[0])
    for e in entry_list:
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


def add_tag(args):
    """Add a tag to the config file."""
    tag_name = args[1]
    try:
        config.add_tag(tag_name)
    except BTError as e:
        print(e)


def del_tag(args):
    """Remove a tag from the config file."""
    tag_name = args[1]
    try:
        config.remove_tag(tag_name)
    except BTError as e:
        print(e)


#@branch("entry")
#@branch("entry", VLit("entry"))
#@branch("tag", VLit("tag"), VLit(config.tags, invert=True))
@command("add")
def add_command(*args, **kwargs):
    if kwargs["branch"] == "entry":
        add_entry(args)
    elif kwargs["branch"] == "tag":
        add_tag(args)


#@branch("entry", VBool(str.isdigit))
#@branch("tag", VLit("tag"), VLit(config.tags))
@command("del", "delete", "remove")
def delete_command(*args, **kwargs):
    if branch == "tag":
        del_tag(args)
    elif branch == "entry":
        del_entry(args)


#@branch("main", VBool(str.isdigit), VLit(Entry.editable_fields))
@command("edit")
def edit_entry(*args, **kwargs):
    """Takes an ID and data type and allows user to change value"""
    id = int(kwargs["vbool"])
    attr = kwargs["vlit"]

    # Make the change
    for e in entry_list:
        if e.id == id:
            new_value = globals()[Entry.editable_fields[attr]]()
            e.edit(attr, new_value)
            break
    else:
        print("Entry not found.")


@command("bills")
def show_bills(*args, **kwargs):
    """Print the bills; placeholder function."""
    for k, v in config.bills.items():
        print(f"{k}:\t{v}")


def manage_goals(*args, **kwargs):
    pass


def switch_year(*args, **kwargs):
    """Switches to different year.""" ### Maybe don't write to config??
    if len(args) > 0 and args[0].isdigit():
        year = int(args[0])
        if os.path.exists(f"{year}.csv"):
            config.active_year = year
            print(f"Records for {year} are now active.")
            return

    print("Invalid year input.")
        

@command("q", "quit")
def quit_program():
    quit()


def btinput(context) -> str:
    """Wrapper for builtin input function"""
    pass


def shell():
    print("Budget Tool")
    print(f"Records for {config.active_year} are active.")
    while True:
        user_input = list(input("> ").strip().split(" "))
        try:
            route_command(user_input)
        except (ParseUserError, BTError) as e:
            print(e)


def main(sysargs: List[str]):
    try:
        if not sysargs:
            shell()
        else:
            route_command(sysargs)
    except KeyboardInterrupt:
        print("")


if __name__=="__main__":
    main(sys.argv[1:])