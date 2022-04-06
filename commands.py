import copy
import logging
from typing import Union
from datetime import datetime

import command
import config
import display

from config import TODAY
import main
import entry
from entry import Entry
from command.validator import VLit, VBool
from validators import VDay, VMonth, VYear, VType, VTag, VNewTag, VID


def get_date() -> Union[datetime, None]:
    """Retrieve the date input from the user."""
    display.refresh()
    date = input("Date: ")

    if date.lower() in ("q", "quit"):
        raise main.BTError("Input aborted by user.")

    date = date.split()

    if not date:
        return TODAY
    elif 2 <= len(date) <= 3:
        month = VMonth(strict=True)(date)
        day = VDay()(date)
        year = VYear(default=config.active_year)(date)
        return datetime(year, month, day)
    else:
        display.message("Invalid input.")


def get_amount() -> Union[int, None]:
    """Retrieve the amount input from the user."""
    display.refresh()
    amount = input("Amount: ").strip()

    if amount.lower() in ("q", "quit"):
        raise main.BTError("Input aborted by user.")

    if not amount.startswith(("-", "+")):
        display.message("The amount must start with + or -")
        return

    return entry.dollars_to_cents(amount)


def _match_tag(query: str) -> Union[str, None]:
    """Check if string matches a tag. If so, return the tag."""
    result = None
    for t in config.udata.tags:
        if t.lower().startswith(query):
            result = t
            break

    return result


def get_tags() -> Union[list, None]:
    """Get tag(s) input from user."""
    display.message(f"({', '.join(config.udata.tags)})")
    display.refresh()
    tags = input("Tags: ").lower().strip()

    if tags in ("q", "quit"):
        raise main.BTError("Input aborted by user.")
    if tags == "help":
        display.message(f"({', '.join(config.udata.tags)})")
        return

    tags = tags.split(" ")
    if not all(tags := [_match_tag(t) for t in tags]):
        display.message("Invalid tags given. Enter 'help' to see tags.")
        return

    return tags
            

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


editable_fields = {
        "amount":   get_amount, 
        "tags":     get_tags,
        "note":     get_note,
        "date":     get_date,
        }


class ListCommand(command.Command):
    """Display a list of entries filtered by type, month, and tags."""
    names = ("list",)
    params = {
        "month": VMonth(default=TODAY.month),
        "category": VType(),
        "tags": VTag(),
        }
    help_text = "If no year or month are specified it will default to the current year and month."
    
    def execute(self, month, category, tags):
        config.last_query = [month, category, tags]
        display.change_page(1)


class AddEntryCommand(command.Command):
    """Add an entry, entering input through a series of prompts."""
    def execute(self):
        try:
            date, amount, tags, note = get_input(get_date, get_amount, get_tags, get_note)
        except main.BTError:
            pass # Exit the command
        else:
            self.entry = Entry(date, amount, tags, note)
            # self.entry = Entry(0, date, amount, tags, note)
            config.records[date.year].append(self.entry)
        
    def undo(self):
        config.records[self.entry.date.year].remove(self.entry)

    def redo(self):
        config.records[self.entry.date.year].append(self.entry)


class AddTagCommand(command.Command):
    """Add a name to the list of tags."""
    params = {
        "name": VNewTag(req=True),
    }

    def execute(self):
        config.udata.add_tag(self.data["name"])

    def undo(self):
        config.udata.remove_tag(self.data["name"], for_undo=True)

    def redo(self):
        config.udata.add_tag(self.data["name"])


class AddCommand(command.ForkCommand):
    """Add an entry or tag."""    
    names = ("add",)
    forks = {
        "entry": AddEntryCommand,
        "tag": AddTagCommand
    }
    default = "entry"
    help_text = "If neither 'entry' or 'tag' are specified, it will default to 'entry.'"


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
            config.records[self.entry.date.year].remove(self.entry)
        display.deselect()

    def undo(self):
        config.records[self.entry.date.year].append(self.entry)

    def redo(self):
        config.records[self.entry.date.year].remove(self.entry)


class RemoveTagCommand(command.Command):
    """Remove a tag by its name."""
    params = {
        "name": VTag(req=True),
    }

    def execute(self):
        config.udata.remove_tag(self.data["name"])

    def undo(self):
        config.udata.add_tag(self.data["name"])

    def redo(self):
        config.udata.remove_tag(self.data["name"])


class RemoveCommand(command.ForkCommand):
    """Delete an entry or tag."""
    names = ("del", "delete", "remove")
    forks = {
        "entry": RemoveEntryCommand,
        "tag": RemoveTagCommand,
    }
    default = "entry"


class EditEntryCommand(command.Command):
    """Edit an entry; requires an ID and a field."""
    names = ("edit",)
    params = {
        "id": VID(req=True),
        "field": VLit(editable_fields, lower=True, req=True),
    }

    def execute(self, id: int, field: str) -> None:
        self.old_entry = display.select(id)
        self.new_entry = copy.copy(self.old_entry)
        new_value = editable_fields[field]()
        setattr(self.new_entry, field, new_value)
        config.records[config.active_year].replace(self.old_entry, self.new_entry)
        display.deselect()

    def undo(self) -> None:
        config.records[config.active_year].replace(self.new_entry, self.old_entry)
    
    def redo(self) -> None:
        config.records[config.active_year].replace(self.old_entry, self.new_entry)


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


class ShowBillsCommand(command.Command):
    """Display the bills; placeholder command."""
    names = ("bills",)

    def execute(self):
        for k, v in config.bills.items():
            print(f"{k}:\t{v}")


# def switch_year(year=VBool(str.isdigit, req=True)):
#     """Switches to different year.""" ### Maybe don't write to config??
#     year = int(year)
#     if os.path.exists(f"{year}.csv"):
#         config.active_year = year
#         print(f"Records for {year} are now active.")
#         return

#     print("Invalid year input.")


# def quick_add_entry(*args):
#     amount, category = args[:2]
#     note = ",".join(args[2:])
#     entry = Entry(TODAY.strftime("%Y/%m/%d"), amount, category, note)