# BT: Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

from cmath import exp
import sys
import os

import csv
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
from tabnanny import check
from typing import List


TODAY = datetime.now()

HEADERS = ("id","date","amount","category","earner","note","hidden")

COMMANDS = {
    "list": "list_entries",
    "add": "add_entry",
    "bills": "show_bills",
    "edit": "edit_entry",
    "del": "delete_entry",
    # "sum": "summarize",
    "switch": "switch_year",
    "quit": "quit_program",
    "q": "quit_program",
    # "help": "help",
}

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


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
    """Just a wrapper to avoid using dictionary keys"""
    def __init__(self):
        with open("config.json", "r") as fp:
            cfgdata = json.load(fp)

        self.active_year = cfgdata["active_year"]
        self.users = cfgdata["users"]
        self.income_cats = cfgdata["categories"]["income"]
        self.expense_cats = cfgdata["categories"]["expense"]
        self.bills = cfgdata["bills"]

    def overwrite(self):
        pass
    
    @property
    def categories(self):
        return self.income_cats + self.expense_cats

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


def _search_category(query, categories):
    query = query.strip().lower()
    results = []

    for c in categories:
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
        if amount > 0:
            category = _search_category(category, config.income_cats)
        else:
            category = _search_category(category, config.expense_cats)
        
        if category:
            return category
        else:
            categories = config.income_cats if amount > 0 else config.expense_cats
            print("Category not found...")
            print(f"Categories: {', '.join(categories)}")


def get_earner_and_note(amount, *args):
    while True:
        if amount > 0:
            earner = input("Earner: ")
            for name in ("ben", "rylee"):
                if name.startswith(earner.lower()):
                    earner = name.title()
                    note = input("Note: ")
                    return (earner, note)
        else:
            note = input("Note: ")
            if note.lower() == "back":
                raise BTError("Command terminated.")
            return (None, note)


def _get_entries(month=None, type=None, earner=None) -> List[Entry]:
    if month == None and config.active_year == TODAY.year:
        month = TODAY.month
    elif month == None and config.active_year != TODAY.year:
        month = 12
    if type in ["expense",] + config.expense_cats:
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
        if type and type != e.type and type != e.category:
            continue
        if earner and e.earner != earner:
            continue
        filtered_entries.append(e)

    if not filtered_entries:
        raise BTError("Record is empty.")
    return filtered_entries


def list_entries(*args):
    """Process args and print appropriate entries to the terminal."""
    month, type, earner = None, None, None
    # Check if a month is the the first argument
    if len(args) > 0:
        try:
            month = match_month(args[0])
        except BTError:
            if args[0].lower() == "year":
                month = "year"

    # Process the args for when a month is provided
    if month:
        if len(args) > 1:
            if args[1].lower() in ("income",):
                type = "income"
            elif args[1].lower() in ("expense", "expenses"):
                type = "expense"
            elif cat := _search_category(args[1].lower(), config.categories):
                type = cat
            else:
                print("Invalid entry type.")
                return None
        if len(args) > 2:
            if args[2].lower() in ("ben", "rylee"):
                earner = args[2].title()
            else:
                print("Invalid name.")
                return None
    
    # Process the args for when a month is not provided
    elif not month and len(args) > 0:
        if args[0].lower() in ("income",):
            type = "income"
        elif args[0].lower() in ("expense", "expenses"):
            type = "expense"
        elif cat := _search_category(args[0].lower(), config.categories):
                type = cat
        else:
            print("Invalid type or month.")
            return None
        if len(args) > 1:
            if args[1].lower() in ("ben", "rylee"):
                earner = args[1].title()
            else:
                print("Invalid name.")
                return None

    # Get the entries and print
    try:
        entries = _get_entries(month, type, earner)
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
        earner, note = get_earner_and_note(amount)
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


def get_config() -> dict:
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