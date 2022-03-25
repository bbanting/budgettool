# Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

from __future__ import annotations
import os
import csv
import shlex
import collections
import logging
from datetime import datetime
from typing import List
from command.base import CommandError

import config
import command
import display
import commands
from config import TODAY, MONTHS, ENTRY_FOLDER, HEADERS, DATEW, AMOUNTW, TAGSW

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


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
    def catgeory(self) -> str:
        if self.amount > 0:
            return "income"
        else:
            return "expense"

    @property
    def parent_record(self) -> Record:
        return config.records[self.date.year]

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
            if t not in (config.udata.tags + config.udata.old_tags):
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
        return f"{date:{DATEW}} {self.in_dollars():{AMOUNTW}} {tags:{TAGSW}} {self.note}"


class RecordHandler(collections.UserDict):
    """A class to hold all YearlyRecords."""
    def __iter__(self):
        return super().__iter__()
        # Overwrite this to allow traversing between years
    
    def __getitem__(self, key: int):
        try:
            super().__getitem__(key)
        except KeyError:
            self.update({key: Record(key)})
        return super().__getitem__(key)


class Record(collections.UserList):
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


def show_entries(month, category, tags):
    try:
        entries = _filter_entries(month, category, tags)
    except BTError as e:
        display.error(str(e))
        return
    total = Entry.cents_to_dollars(sum([e.amount for e in entries]))
    summary = _get_filter_summary(len(entries), month, category, tags)

    display.push_h(f"{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'TAGS':{TAGSW}} {'NOTE'}")
    for entry in entries: display.push(entry)
    display.push_f("", f"TOTAL: {total}", summary)


def _get_filter_summary(n, month, category, tags) -> str:
    month = list(MONTHS)[month].title()
    category = f" of type {category}" if category else ""
    tags = " with tags: " + ', '.join(tags) if tags else ""
    return f"{n} entries{category} from {month} of {config.active_year}{tags}."


def _filter_entries(month=None, category=None, tags=()) -> list[Entry]:
    """Filter and return entries based on input.
    Raise exception if none found
    """
    if month is None and config.active_year == TODAY.year:
        month = TODAY.month
    elif month is None and config.active_year != TODAY.year:
        month = 12

    if len(config.records[config.active_year]) == 0:
        raise BTError("Record is empty.")

    filtered_entries = []
    for e in config.records[config.active_year]:
        if month != 0 and e.date.month != month:
            continue
        if category and category != e.category:
            continue
        if tags and not any([True if t in e.tags else False for t in tags]):
            continue
        filtered_entries.append(e)

    if not filtered_entries:
        raise BTError("No entries found.")
    return sorted(filtered_entries, key=lambda x: x.date)


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
        except KeyboardInterrupt:
            print("")
            return

        try:
            controller.route_command(user_input)
        except (BTError, CommandError) as e:
            display.error(e)
        else:
            show_entries(*config.last_query)
            display.refresh()


if __name__=="__main__":
    config.records = RecordHandler({TODAY.year: Record(TODAY.year)})
    main()
