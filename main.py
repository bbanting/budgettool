# Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

from __future__ import annotations
import os
import csv
import shlex
import collections
import logging

import config
import command
import display
import commands
import db
import entry
from command.base import CommandError
from config import TODAY, ENTRY_FOLDER, HEADERS, DATEW, AMOUNTW, TAGSW, Month, Date
from entry import Entry

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


# class RecordHandler(collections.UserDict):
#     """A class to hold all YearlyRecords."""
#     def __iter__(self):
#         return super().__iter__()
#         # Overwrite this to allow traversing between years
    
#     def __getitem__(self, key: int):
#         try:
#             super().__getitem__(key)
#         except KeyError:
#             self.update({key: Record(key)})
#         return super().__getitem__(key)


# class Record(collections.UserList):
#     """
#     A list to group entry sets together by year and 
#     handle saving them to disk.
#     """
#     def __init__(self, year: int) -> None:
#         """Initialize and check for file errors."""
#         super().__init__()

#         self.year = year
#         self._check_file()

#         with open(f"{ENTRY_FOLDER}/{self.year}.csv", "r", newline="") as fp:
#             lines = list(csv.reader(fp))
#         if lines[0] != list(HEADERS):
#             print(f"Error: Invalid CSV headers.")
#             quit()

#         entries = []
#         for i, ln in enumerate(lines[1:]):
#             try:
#                 entry = Entry.from_csv(ln)
#             except (ValueError, BTError):
#                 print(f"Error parsing line {i+2}. Your CSV file may be corrupted.")
#                 quit()
#             else:
#                 entries.append(entry)
#         self.extend(entries)

#     def _check_file(self) -> None:
#         """Ensure the CSV file can be opened barring a permission error."""
#         os.makedirs(f"{os.getcwd()}/{ENTRY_FOLDER}", exist_ok=True)
#         try:
#             with open(f"{ENTRY_FOLDER}/{self.year}.csv", "r+"):
#                 pass
#         except PermissionError:
#             print("You do not have the necessary file permissions.")
#             quit()
#         except FileNotFoundError:
#             with open(f"{ENTRY_FOLDER}/{self.year}.csv", "w", newline="") as fp:
#                 csv.writer(fp).writerow(HEADERS)

#     def _overwrite(self):
#         """Overwrite the csv file with current entries."""
#         self._check_file()
#         rows = []
#         rows.append(list(HEADERS))
#         for e in self:
#             rows.append(e.to_csv())
#         with open(f"{ENTRY_FOLDER}/{self.year}.csv", "w", newline="") as fp:
#             csv.writer(fp).writerows(rows)

#     def replace(self, old: Entry, new: Entry) -> None:
#         """Replace old Entry with new Entry."""
#         index = self.index(old)
#         self[index] = new
#         self._overwrite()

#     def append(self, item: Entry) -> None:
#         super().append(item)
#         self._overwrite()

#     def remove(self, item: Entry) -> None:
#         super().remove(item)
#         self._overwrite()


def show_entries(month, category, tags):
    """Push the current entries to the display."""
    entries = _filter_entries(month, category, tags)
    total = entry.cents_to_dollars(sum(entries))
    summary = _get_filter_summary(len(entries), month, category, tags)

    display.push_h(f"{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'TAGS':{TAGSW}} {'NOTE'}")
    for entry in entries: display.push(entry)
    display.push_f("", f"TOTAL: {total}", summary)


def _get_filter_summary(n, month, category, tags) -> str:
    month = month.name
    category = f" of type {category}" if category else ""
    tags = f" with tags: {', '.join(tags)}" if tags else ""
    return f"{n} entries{category} from {month} of {config.active_year}{tags}."


def _filter_entries(month=None, category=None, tags=()) -> list[Entry]:
    """Filter and return entries based on input.
    Raise exception if none found.
    """
    if month is None and config.active_year == TODAY.year:
        month = Month(TODAY.month)
    elif month is None and config.active_year != TODAY.year:
        month = Month.December

    filtered_entries = []
    for e in config.records[config.active_year]:
        if month != 0 and e.date.month != month:
            continue
        if category and category != e.category:
            continue
        if tags and not any([True if t in e.tags else False for t in tags]):
            continue
        filtered_entries.append(e)

    return sorted(filtered_entries, key=lambda x: x.date)


def _fetch_entries(date, category, tags) -> list[Entry]:
    """Fetch entries from database based on last query"""
    query = "SELECT * FROM entries"
    if category == "income":
        query += " WHERE amount > 0"
    elif category == "expense":
        query += " WHERE amount < 0"

    query += ";"
    return db.fetch(query)
    

def register_commands(controller: command.CommandController):
    controller.register(command.UndoCommand)
    controller.register(command.RedoCommand)
    controller.register(command.HelpCommand)
    controller.register(commands.ListCommand)
    controller.register(commands.QuitCommand)
    controller.register(commands.RemoveCommand)
    controller.register(commands.RemoveEntryCommand)
    controller.register(commands.RemoveTagCommand)
    controller.register(commands.AddCommand)
    controller.register(commands.AddEntryCommand)
    controller.register(commands.AddTagCommand)
    controller.register(commands.EditEntryCommand)
    controller.register(commands.ShowBillsCommand)
    controller.register(commands.ChangePageCommand)


def main():
    controller = command.CommandController()
    register_commands(controller)
    display.configure(offset=1)

    show_entries(*config.last_query)
    display.refresh()
    while True:
        try:
            user_input = shlex.split(input("> "))
            controller.route_command(user_input)
        except (BTError, display.DisplayError) as e:
            display.error(e)
        except CommandError as e:
            display.message(str(e))
            display.refresh()
        except KeyboardInterrupt:
            print("")
            return
        else:
            show_entries(*config.last_query)
            display.refresh()


if __name__=="__main__":
    config.records = RecordHandler({TODAY.year: Record(TODAY.year)})
    main()
