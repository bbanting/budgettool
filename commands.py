import copy
import logging
import datetime

import command
import config
import display
import main
import entry
import db

from config import TODAY, DATEW, AMOUNTW, TimeFrame
from entry import Entry, cents_to_dollars
from command.validator import VLit, VBool, VAny
from validators import VDay, VMonth, VYear, VType, VTarget, VID, VAmount, VGroup


def get_date() -> datetime.date | None:
    """Retrieve the date input from the user."""
    display.refresh()
    date = input("Date: ")

    if date.lower() in ("q", "quit"):
        raise main.BTError("Input aborted by user.")

    date = date.split()

    if not date:
        return TODAY
    elif 2 <= len(date) <= 3:
        month = VMonth()(date)
        day = VDay()(date)
        year = VYear(default=config.TODAY.year)(date)
        return datetime.date(year, month, day)
    else:
        display.message("Invalid input.")


def get_amount() -> int | None:
    """Retrieve the amount input from the user."""
    display.refresh()
    amount = input("Amount: ").strip()

    if amount.lower() in ("q", "quit"):
        raise main.BTError("Input aborted by user.")

    if not amount.startswith(("-", "+")):
        display.message("The amount must start with + or -")
        return

    if not amount[1:].isnumeric() or int(amount) == 0:
        display.message("Invalid amount.")
        return

    return entry.dollars_to_cents(amount)


def get_target() -> entry.Target | None:
    """Get target input from user."""
    display.message(f"({', '.join([t.name for t in config.udata.targets])})")
    display.refresh()
    target = input("Target: ").lower().strip()

    if target in ("q", "quit"):
        raise main.BTError("Input aborted by user.")
    if target == "help":
        display.message(f"({', '.join([t.name for t in config.udata.targets])})")
        return

    if target not in [t.name for t in config.udata.targets]:
        display.message("Invalid target given. Enter 'help' to see targets.")
        return

    return entry.Target.from_str(target)
            

def get_note() -> str:
    """Get note input from the user"""
    display.refresh()
    note = input("Note: ")

    if note.lower() in ("q", "quit"):
        raise main.BTError("Input aborted by user.")

    if not note:
        return "..."

    return note


def get_input(*getters) -> tuple:
    """Get input from the user."""
    data = []
    for getter in getters:
        while True:
            ret_val = getter()
            if not ret_val:
                continue
            data.append(ret_val)
            break
    return data


input_functions = {
        "amount":   get_amount, 
        "target":     get_target,
        "note":     get_note,
        "date":     get_date,
        }


def push_entries() -> None:
    """Push the current entries to the display."""
    date, category, target = config.last_query
    entries = db.select_entries(date, category, target)
    total = cents_to_dollars(sum(entries))
    total_str = f"${abs(total):.2f}"
    if total > 0: total_str = "+" + total_str
    if total < 0: total_str = "-" + total_str
    summary = get_filter_summary(len(entries), date, category, target)

    display.push_h(f"{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'NOTE'}")
    for entry in entries: 
        display.push(entry)
    display.push_f("", f"TOTAL: {total_str}", summary)

def get_filter_summary(n:int, date:TimeFrame, category:str, target:entry.Target) -> str:
    date = f"{date.month.name} {date.year}"
    category = f" of type {category}" if category else ""
    target = f" at target: {', '.join(target)}" if target else ""
    return f"{n} entries{category} from {date}{target}."


class ListCommand(command.Command):
    """Display a list of entries filtered by type, month, and target."""
    names = ("list",)
    params = {
        "year": VYear(default=TODAY.year),
        "month": VMonth(default=TODAY.month),
        "category": VType(default=""),
        "target": VTarget(),
        }
    help_text = "If no year or month are specified it will default to the current year and month."
    
    def execute(self, year, month, category, target):
        date = config.TimeFrame(year, month)
        config.last_query = [date, category, target]
        display.change_page(1)

        push_entries()


class AddEntryTodayCommand(command.Command):
    """Add an entry for today with one line."""
    params = {
        "amount": VAmount(),
        "target": VTarget(),
        "note": VAny(plural=True),
    }

    def execute(self, amount, target, note) -> None:
        date = datetime.date.today()
        note = " ".join(note)
        self.entry = Entry(0, date, amount, target, note)
        db.insert_entry(self.entry)

        date = date.strftime("%b %d")
        amount = self.entry.in_dollars()
        display.message(f"Entry added: {date} - {amount} - {note}")

        push_entries()

    def undo(self) -> None:
        db.delete_entry(self.entry)
        push_entries()

    def redo(self) -> None:
        db.insert_entry(self.entry)
        push_entries()


class AddEntryCommand(command.Command):
    """Add an entry, entering input through a series of prompts."""
    def execute(self) -> None:
        try:
            date, amount, target, note = get_input(get_date, get_amount, get_target, get_note)
        except main.BTError:
            return # Exit the command
        self.entry = Entry(0, date, amount, target, note)
        db.insert_entry(self.entry)

        date = date.strftime("%b %d")
        amount = self.entry.in_dollars()
        display.message(f"Entry added: {date} - {amount} - {note}")

        push_entries()
        
    def undo(self):
        db.delete_entry(self.entry)
        push_entries()

    def redo(self):
        db.insert_entry(self.entry)
        push_entries()


class AddTargetCommand(command.Command):
    """Add a new target."""
    params = {
        "name": VTarget(req=True, invert=True),
        "amount": VAmount(req=True),
    }

    def execute(self, name, amount) -> None:
        self.target = entry.Target(name, amount)
        config.udata.add_target(self.target)

    def undo(self) -> None:
        config.udata.remove_target(self.target)

    def redo(self) -> None:
        config.udata.add_target(self.target)


class AddGroupCommand(command.Command):
    """Remove a target group by it's name."""
    params = {
        "name": VGroup(req=True, invert=True),
        "targets": VTarget(req=True, plural=True),
    }

    def execute(self, name:str, targets:list[str]) -> None:
        self.name = name
        self.targets = targets
        config.udata.add_group(name, targets)
    
    def undo(self) -> None:
        config.udata.remove_group(self.name)

    def redo(self) -> None:
        config.udata.remove_group(self.name, self.targets)


class AddCommand(command.ForkCommand):
    """Add an entry or target."""    
    names = ("add",)
    forks = {
        "entry": AddEntryCommand,
        "today": AddEntryTodayCommand,
        "target": AddTargetCommand,
        "group": AddGroupCommand,
    }
    default = "entry"


class RemoveEntryCommand(command.Command):
    """Remove and Entry by its ID."""
    params = {
        "id": VID(req=True),
    }

    def execute(self, id):
        self.entry = display.select(id)
        ans = None
        while ans not in ("yes", "no", "y", "n"):
            display.refresh()
            ans = input("(Y/n) Are you sure you want to delete this entry? ").lower()
        if ans in ("yes", "y"):
            db.delete_entry(self.entry)
        display.deselect()

        push_entries()

    def undo(self):
        db.insert_entry(self.entry)
        push_entries()

    def redo(self):
        db.delete_entry(self.entry)
        push_entries()


class RemoveTargetCommand(command.Command):
    """Remove a target by its name."""
    params = {
        "target": VTarget(req=True),
    }

    def execute(self, target:str) -> None:
        self.target = entry.Target.from_str(target)
        config.udata.remove_target(self.target)

    def undo(self):
        config.udata.add_target(self.target)

    def redo(self):
        config.udata.remove_target(self.target)


class RemoveGroupCommand(command.Command):
    """Remove a target group by it's name."""
    params = {
        "name": VGroup(req=True),
    }

    def execute(self, name:str) -> None:
        self.name = name 
        self.targets = config.udata.groups.get(name)
        config.udata.remove_group(name)
    
    def undo(self):
        config.udata.add_group(self.name, self.targets)

    def redo(self):
        config.udata.remove_group(self.name)


class RemoveCommand(command.ForkCommand):
    """Delete an entry or target."""
    names = ("del", "delete", "remove")
    forks = {
        "entry": RemoveEntryCommand,
        "target": RemoveTargetCommand,
        "group": RemoveGroupCommand,
    }
    default = "entry"


class ListTargets(command.Command):
    """Display a list of the targets."""
    names = ("targets",)
    params = {
        "year": VYear(default=TODAY.year),
        "month": VMonth(default=TODAY.month),
    }

    def execute(self, year, month) -> None:
        date = config.TimeFrame(year, month)
        for t in config.udata.targets:
            current = cents_to_dollars(db.sum_target(t, date))
            goal = cents_to_dollars(t.amount)
            display.push(f"{t.name}: {current:.2f}/{goal:.2f}")


class EditEntryCommand(command.Command):
    """Edit an entry; requires an ID and a field."""
    names = ("edit",)
    params = {
        "id": VID(req=True),
        "field": VLit(input_functions, lower=True, req=True),
    }

    def execute(self, id: int, field: str) -> None:
        self.old_entry = display.select(id)

        self.new_entry = copy.copy(self.old_entry)
        new_value = input_functions[field]()
        setattr(self.new_entry, field, new_value)

        db.update_entry(self.new_entry)
        display.deselect()

        push_entries()

    def undo(self) -> None:
        db.update_entry(self.old_entry)
        push_entries()
    
    def redo(self) -> None:
        db.update_entry(self.new_entry)
        push_entries()


class ChangePageCommand(command.Command):
    """Change to another page of the current entry list."""
    names = ("page",)
    params = {
        "number": VBool(str.isdigit, req=True)
    }

    def execute(self, number: str) -> None:
        number = int(number)
        display.change_page(number)


class QuitCommand(command.Command):
    """Quits the program."""
    names = ("q", "quit")

    def execute(self):
        quit()
