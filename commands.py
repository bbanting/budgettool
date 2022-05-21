from __future__ import annotations

import copy
import logging
import datetime

import kelevsma
import config
import kelevsma.display as display
import main
import entry
import target
import db

from config import TODAY
from entry import Entry
from kelevsma.command import Example
from kelevsma.validator import VLit, VBool, VAny
from validators import VDay, VMonth, VYear, VType, VTarget, VID, VAmount


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


def get_target() -> dict | None:
    """Get target input from user."""
    target_names = target.get_target_names()
    display.message(f"({', '.join(target_names)})")
    display.refresh()
    t_input = input("Target: ").lower().strip()

    if t_input in ("q", "quit"):
        raise main.BTError("Input aborted by user.")
    if t_input == "help":
        display.message(f"({', '.join(target_names)})")
        return

    if t_input not in target_names:
        display.message("Invalid target given. Enter 'help' to see targets.")
        return

    return t_input
            

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
        "date":     get_date,
        "amount":   get_amount, 
        "target":   get_target,
        "note":     get_note,
        }


def targets_exist() -> bool:
    """Check if user has created any targets."""
    return bool(len(target.select()))


class ListEntriesCommand(kelevsma.Command):
    """Set the entry filter state (tframe, category, and target)."""
    params = {
        "year": VYear(default=TODAY.year),
        "month": VMonth(default=TODAY.month),
        "category": VType(default=""),
        "targets": VTarget(plural=True, default=[]),
    }
    
    def execute(self, year, month, category, targets):
        tframe = config.TimeFrame(year, month)
        config.entry_filter_state.__init__(tframe=tframe, category=category, targets=targets)
        config.target_filter_state.__init__(tframe=tframe)
        display.change_page(1)


class ListTargetsCommand(kelevsma.Command):
    """Set the target filter state."""
    params = {
        "year": VYear(default=TODAY.year),
        "month": VMonth(default=TODAY.month),
    }

    def execute(self, year, month) -> None:
        tframe = config.TimeFrame(year, month)
        config.target_filter_state.__init__(tframe=tframe)
        display.change_page(1)


class ListCommand(kelevsma.ForkCommand):
    """List either the entries or targets."""
    names = ("list", "ls")
    forks = {
        "entries": ListEntriesCommand,
        "entry": ListEntriesCommand,
        "targets": ListTargetsCommand,
        "target": ListTargetsCommand,
    }
    default = "entries"
    examples = (
        Example("list march 2022 other", "List the entries for March of 2022 at target 'other.'"),
        Example("list all income", "List all positive entries from current year."),
        Example("list targets", "List all targets.")
    )


class AddEntryTodayCommand(kelevsma.Command):
    """Add an entry for today with one line."""
    params = {
        "amount": VAmount(),
        "target": VTarget(),
        "note": VAny(plural=True),
    }

    def execute(self, amount, target, note) -> None:
        if not targets_exist():
            display.message("No targets to add entries to. Make a target with 'add target [name] [amount]'.")
            return

        date = datetime.date.today()
        note = " ".join(note)
        self.entry = Entry(0, date, amount, target, note)
        entry.insert(self.entry)

        date = date.strftime("%b %d")
        amount = entry.dollar_str(self.entry.amount)
        display.message(f"Entry added: {date} - {amount} - {note}")

    def undo(self) -> None:
        entry.delete(self.entry)

    def redo(self) -> None:
        entry.insert(self.entry)


class AddEntryCommand(kelevsma.Command):
    """Add an entry, entering input through a series of prompts."""
    def execute(self) -> None:
        if not targets_exist():
            display.message("No targets to add entries to. Make a target with 'add target [name] [amount]'.")
            return

        try:
            date, amount, target, note = get_input(*list(input_functions.values()))
        except main.BTError:
            return # Exit the command
        self.entry = Entry(0, date, amount, target, note)
        entry.insert(self.entry)

        date = date.strftime("%b %d")
        amount = entry.dollar_str(self.entry.amount)
        display.message(f"Entry added: {date}, {amount}, {note}")
        
    def undo(self):
        entry.delete(self.entry)

    def redo(self):
        entry.insert(self.entry)


class AddTargetCommand(kelevsma.Command):
    """Add a new target."""
    params = {
        "name": VTarget(req=True, invert=True),
        "amount": VAmount(req=True),
    }

    def execute(self, name, amount) -> None:
        self.target = target.Target(0, name, amount)
        target.insert(self.target)

    def undo(self) -> None:
        target.delete(self.target.name)

    def redo(self) -> None:
        target.insert(self.target)


class AddCommand(kelevsma.ForkCommand):
    """Add an entry or target."""    
    names = ("add",)
    forks = {
        "entry": AddEntryCommand,
        "today": AddEntryTodayCommand,
        "target": AddTargetCommand,
    }
    default = "entry"


class RemoveEntryCommand(kelevsma.Command):
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
            entry.delete(self.entry)
        display.deselect()

    def undo(self):
        entry.insert(self.entry)

    def redo(self):
        entry.delete(self.entry)


class RemoveTargetCommand(kelevsma.Command):
    """Remove a target by its name."""
    params = {
        "name": VTarget(req=True),
    }

    def execute(self, name:str) -> None:
        self.target = target.select_one(name)
        uses = target.times_used(self.target)
        if uses:
            display.message(f"Cannot delete {name}; in use by {uses} entr{'y' if uses<2 else 'ies'}.")
            return

        target.delete(self.target)

    def undo(self):
        target.insert(self.target)

    def redo(self):
        target.delete(self.target)


class RemoveCommand(kelevsma.ForkCommand):
    """Delete an entry or target."""
    names = ("del", "delete", "remove")
    forks = {
        "entry": RemoveEntryCommand,
        "target": RemoveTargetCommand,
    }
    default = "entry"
    

class EditEntryCommand(kelevsma.Command):
    """Edit an entry; requires a line # and a field."""
    names = ("edit",)
    params = {
        "id": VID(req=True),
        "field": VLit(input_functions, lower=True, req=True),
    }

    def execute(self, id:int, field:str) -> None:
        self.old_entry = display.select(id)

        self.new_entry = copy.copy(self.old_entry)
        new_value = input_functions[field]()
        setattr(self.new_entry, field, new_value)

        db.update_entry(self.new_entry)
        display.deselect()
    
    def undo(self) -> None:
        db.update_entry(self.old_entry)
    
    def redo(self) -> None:
        db.update_entry(self.new_entry)


class SetTargetCommand(kelevsma.Command):
    """Set the amount for a target; either the default or for a
    specified month.
    """
    names = ("set",)
    params = {
        "name": VTarget(req=True),
        "amount": VAmount(req=True, allow_zero=True),
        "year": VYear(default=TODAY.year),
        "month": VMonth(default=TODAY.month),
        "default": VLit("default", lower=True)
    }

    def execute(self, name, amount, year, month, default) -> None:
        pass

    def default_branch(self, amount) -> None:
        pass

    def tframe_branch(self, amount, year, month) -> None:
        pass


class RenameTargetCommand(kelevsma.Command):
    """Rename a target."""
    names = ("rename",)
    params = {
        "current_name": VTarget(req=True),
        "new_name": VTarget(req=True, invert=True),
    }

    def execute(self, current_name, new_name) -> None:
        self.old_target = target.select_one(current_name)
        self.new_target = copy.copy(self.old_target)
        self.new_target.name = new_name
        target.update(self.old_target, self.new_target.name)

    def undo(self) -> None:
        target.update(self.new_target, self.old_target.name)

    def redo(self) -> None:
        target.update(self.old_target, self.new_target.name)


class ChangePageCommand(kelevsma.Command):
    """Change to another page of the current screen."""
    names = ("page",)
    params = {
        "number": VBool(str.isdigit, req=True)
    }

    def execute(self, number:str) -> None:
        number = int(number)
        display.change_page(number)


class QuitCommand(kelevsma.Command):
    """Quits the program."""
    names = ("q", "quit")

    def execute(self) -> None:
        kelevsma.main.quit_program()
