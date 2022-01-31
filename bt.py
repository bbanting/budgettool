# BT: Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

import sys
import os
import csv
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List


TODAY = datetime.now()

HEADERS = ("id","date","amount","category","earner","note","hidden")

COMMANDS = {
    "list": "list_entries",
    "add": "add_entry",
    "bills": "show_bills",
    "edit": "edit_entry",
    "del": "delete_entry",
    "config": "manage_config",
    # "sum": "summarize",
    # "graph": "graph_entries",
    # "help": "help",
    "switch": "switch_year",
    "quit": "quit_program",
    "q": "quit_program",
}

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

KEYWORDS = ("income", "expense") + tuple(MONTHS)


def check_file(year):
    if not os.path.exists(f"{year}.csv"):
        with open(f"{year}.csv", "w", newline="") as fp:
            csv.writer(fp).writerow(HEADERS)


def to_bool(string):
    if string == "True":
        return True
    else:
        return False


class BTError(Exception):
    pass


class Config:
    """A class to manage the state of the programs configuration"""
    def __init__(self) -> None:
        with open("config.json", "r") as fp:
            cfgdata = json.load(fp)

        self.active_year = cfgdata["active_year"]
        self.users = cfgdata["users"]
        self.categories = cfgdata["categories"]
        self.bills = cfgdata["bills"]

    def update(self, attr, value) -> None:
        """Update attribute and overwrite file."""
        setattr(self, attr, value)
        with open("config.json", "w") as fp:
            json.dump(self.to_dict(), fp)
    
    def to_dict(self) -> dict:
        return {"active_year": self.active_year,
                "users": self.users,
                "categories": self.categories,
                "bills": self.bills,
            }

    @staticmethod
    def check():
        """Check if the config exists."""
        pass


class Entry:
    editable_fields = {
        "amount": "get_amount", 
        "category": "get_category",
        }

    def __init__(self, date: str, amount: Decimal, category: str, note:str, earner:str="",
                    hidden:bool=False, id:int=0):
        self.date = date
        self.amount = amount
        self.category = category
        self.earner = earner
        self.note = note
        self.hidden = hidden

        if id:
            self.id = id
        else:
            self.id = self.generate_id()

    @property
    def type(self):
        if self.amount > 0:
            return "income"
        else:
            return "expense"

    @property
    def dollars(self):
        if self.amount > 0:
            return f"+${self.amount}"
        else:
            return f"-${abs(self.amount)}"

    @classmethod
    def from_csv(cls, data: list):
        id, date, amount, category, earner, note, hidden = data
        id= int(id)
        date = datetime.strptime(date, "%Y/%m/%d")
        amount = Decimal(amount)
        hidden = to_bool(hidden)
        return cls(date, amount, category, note, hidden=hidden, earner=earner, id=id)

    def generate_id(self):
        check_file(TODAY.year)
        with open(f"{config.active_year}.csv", "r", newline="") as f:
            lines = list(csv.reader(f))
            if len(lines) > 1:
                line = lines[-1]
                prev_id = int(line[0])
                return prev_id + 1
            else:
                return 1

    def to_csv(self):
        date = self.date.strftime("%Y/%m/%d")
        return [self.id, date, f"{self.amount:.2f}", self.category, self.earner, self.note, self.hidden]
    
    def __str__(self):
        date = self.date.strftime("%b %d")
        earner = self.earner + " - " if self.earner else ""
        return f"{str(self.id).zfill(4):8}{date:8} {self.dollars:10} {self.category:12} {earner}{self.note}"


def match_month(name:str) -> int:
    if name.isdigit() and int(name) in range(1, 13):
        return int(name)
    
    name = name.title()
    for month in MONTHS:
        if month.startswith(name): 
            return MONTHS[month]
    else:
        raise BTError("Invalid month input.")


def get_date(quick_input=None, *args):
    # Short-circuit if called through quick add
    if quick_input:
        return match_month(quick_input)

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
                month, day = match_month(month), int(day)
            except (BTError, ValueError):
                print("Invalid input.")
                continue
            else:
                return datetime(config.active_year, month, day)
        else:
            print("Invalid input.")


def get_amount(*args):
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


def _search_category(query):
    query = query.strip().lower()
    results = []

    for c in config.categories:
        if c.lower().startswith(query):
            results.append(c)
    
    if len(results) != 1:
        return None
    else:
        return results[0]


def get_category(amount, *args):
    while True:
        category = input("Category: ")
        if category.lower() == "back":
            raise BTError("Command terminated.")
        # if amount > 0:
        #     category = _search_category(category, config.income_cats)
        # else:
        #     category = _search_category(category, config.expense_cats)

        category = _search_category(category)
        
        if category:
            return category
        else:
            # categories = config.income_cats if amount > 0 else config.expense_cats
            categories = config.categories
            print("Category not found...")
            print(f"Categories: {', '.join(categories)}")


def get_earner_and_note(amount, *args) -> tuple:
    while True:
        if amount > 0:
            earner = input("Earner: ")
            for name in config.users:
                if name.lower().startswith(earner.lower()):
                    earner = name
                    note = input("Note: ")
                    return (earner, note)
        else:
            note = input("Note: ")
            if note.lower() == "back":
                raise BTError("Command terminated.")
            return (None, note)


def get_earner(amount, *args):
    if amount < 0:
        return None
    while True:
        earner = input("Earner: ")
        for name in config.users:
            if name.lower().startswith(earner.lower()):
                return name


def get_note(*args):
    while True:
        note = input("Note: ")
        if note.lower() == "back":
            raise BTError("Command terminated.")
        return note


def _get_entries(month=None, typ=None, cats=[], earner=None) -> List[Entry]:
    if month is None and config.active_year == TODAY.year:
        month = TODAY.month
    elif month is None and config.active_year != TODAY.year:
        month = 12
    if typ == "expense":
        earner = None

    check_file(config.active_year)
    with open(f"{config.active_year}.csv", "r", newline="") as f:
        lines = list(csv.reader(f))
        if len(lines) < 2:
            raise BTError("Record is empty.")
    entries = [Entry.from_csv(line) for line in lines[1:]]
    filtered_entries = []

    for e in entries:
        if e.hidden:
            continue
        if month != "year" and e.date.month != month:
            continue
        if typ == "expense" and e.amount > 0:
            continue
        if typ == "income" and e.amount < 0:
            continue
        if cats and e.category not in cats:
            continue
        if earner and e.earner.lower() != earner:
            continue
        filtered_entries.append(e)

    if not filtered_entries:
        raise BTError("No entries found.")
    return filtered_entries


def list_entries(*args):
    month, typ, cats, earner = None, None, [], None
    for arg in args:
        arg = arg.lower()
        if not month:
            try:
                month = match_month(arg)
            except BTError:
                if arg == "year":
                    month = "year"
                    continue
            else:
                continue
        if not typ:
            if arg in ("expense", "income"):
                typ = arg
                continue
        if c := _search_category(arg):
            cats.append(c)
            continue
        if not earner:
            if arg in [u.lower() for u in config.users]:
                earner = arg
                continue

    try:
        entries = _get_entries(month, typ, cats, earner)
    except BTError as e:
        print(e)
    else:
        print(f"{'':8}{'DATE':8} {'AMOUNT':10} {'CATEGORY':12} {'NOTE'}")
        total = sum([e.amount for e in entries])
        for entry in entries:
            print(entry)
        sign = "-" if total < 0 else ""
        print(f"\nRunning total: {sign}${abs(total)}")
        

# def quick_add_entry(*args):
#     amount, category = args[:2]
#     note = ",".join(args[2:])
#     entry = Entry(TODAY.strftime("%Y/%m/%d"), amount, category, note)


def add_entry(*args):
    """Create an entry from user input and append to csv file."""
    try:
        date = get_date()
        amount = get_amount()
        category = get_category(amount)
        earner = get_earner(amount)
        note = get_note()
    except BTError:
        pass # Exit the command
    else:
        entry = Entry(date, amount, category, note, earner=earner)
        check_file(config.active_year)
        with open(f"{config.active_year}.csv", "a", newline="") as f:
            csv.writer(f).writerow(entry.to_csv())


def _overwrite_entries(entries: List[Entry]):
    rows = []
    rows.append(list(HEADERS))
    for e in entries:
        rows.append(e.to_csv())
    check_file(config.active_year)
    with open(f"{config.active_year}.csv", "w", newline="") as f:
        csv.writer(f).writerows(rows)


def delete_entry(*args):
    """Takes an ID and deletes the corresponding entry"""
    try:
        id = int(args[0])
    except (ValueError, IndexError):
        print("Invalid ID")
    else:
        entries = _get_entries(month="year")
        for e in entries:
            if e.id == id:
                ans = None
                date = e.date.strftime("%b %d")
                while ans not in ("yes", "no", "y", "n"):
                    ans = input(f"Are you sure you want to delete entry {e.id}? ({date}: {e.dollars}, {e.note})\n")
                if ans in ("yes", "y"):
                    e.hidden = True
                    _overwrite_entries(entries)
                break
        else:
            print("Entry not found.")


def edit_entry(*args):
    """Takes an ID and data type and allows user to change value"""
    # Check the input
    if len(args) < 2:
        print("Invalid input.")
        return

    try:
        id = int(args[0])
    except ValueError:
        print("Invalid ID.")
        return

    attr = args[1]
    if attr.lower() not in Entry.editable:
        print("Invalid attribute.")
        return

    # Make the change
    entries = _get_entries(month="year")
    for e in entries:
        if e.id == id:
            setattr(e, attr, globals()[Entry.editable[attr]](e.amount))
            _overwrite_entries(entries)
            break
    else:
        print("Entry not found.")


def show_bills(*args):
    for k, v in config.bills.items():
        print(f"{k}:\t{v}")


def manage_config(*args):
    pass


def switch_year(*args):
    """Switches to different year."""
    if len(args) > 0 and args[0].isdigit():
        year = int(args[0])
        if os.path.exists(f"{year}.csv"):
            config.active_year = year
            print(f"Records for {year} are now active.")
            return None

    print("Invalid year input.")
        

def quit_program(*args):
    quit()


def btinput() -> str:
    """Wrapper for builtin input function"""
    pass


def process_command(sysargs):
    command = sysargs[0].lower()
    if command not in COMMANDS:
        raise BTError("Command not found.")
    else:
        func = globals()[COMMANDS[command]]
        func(*sysargs[1:])


def shell():
    print("Budget Tool")
    print(f"Records for {config.active_year} are active.")
    while True:
        user_input = list(input("> ").strip().split(" "))
        try:
            process_command(user_input)
        except BTError as e:
            print(e)


def main(sysargs: List[str]):
    global config
    config = Config()
    check_file(TODAY.year)

    if not sysargs:
        shell()
    else:
        process_command(sysargs)


if __name__=="__main__":
    main(sys.argv[1:])