from __future__ import annotations
import datetime
import logging

from datetime import date
from dataclasses import dataclass
from colorama import Style

import config
import db
import target

from config import DATEW, AMOUNTW


@dataclass
class Entry:
    """Represent one entry in the budget."""
    __slots__ = ("id", "date", "amount", "target", "note")
    def __init__(self, id:int, date:date, amount:int, target:str, note:str):
        self.id = id
        self.date = date
        self.amount = amount
        self.target = target
        self.note = note

    @property
    def category(self) -> str:
        if self.amount > 0:
            return "income"
        else:
            return "expense"

    @property
    def tframe(self) -> config.TimeFrame:
        """Return the time frame that the entry belongs to."""
        return config.TimeFrame(self.date.year, self.date.month)

    @classmethod
    def from_tuple(cls, data:tuple):
        """Construct an entry from a database row (tuple)."""
        id, date, amount, target, note = data
        id = int(id)
        date = datetime.date.fromisoformat(date)
        amount = int(amount)

        return cls(id, date, amount, target, note)

    def to_tuple(self) -> tuple:
        """Return a tuple representation for the database."""
        date = self.date.isoformat()
        targ_id = target.select_one(self.target).id
        values = (date, self.amount, targ_id, self.note)
        if self.id:
            values = (self.id,) + values
        return values

    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        return f"{date:{DATEW}}" \
        f"{dollar_str(self.amount):{AMOUNTW}}" \
        f"{Style.DIM}({self.target}){Style.NORMAL} {self.note}"

    def __add__(self, other) -> int:
        if type(other) == type(self):
            return self.amount + other.amount
        if type(other) == int:
            return self.amount + other
        return NotImplemented

    def __radd__(self, other) -> int:
        return self.__add__(other)


def dollar_str(amount:int) -> str:
    """Formats a cent amount for display in dollars."""
    amount = cents_to_dollars(amount)
    if amount >= 0:
        return f"+${amount:.2f}"
    else:
        return f"-${abs(amount):.2f}"      


def cents_to_dollars(cent_amount:int) -> float:
    """Convert a cent amount to dollars."""
    if not cent_amount:
        return float(0)
    return cent_amount / 100


def dollars_to_cents(dollar_amount:str) -> int:
    """Convert a string dollar ammount to cents for storage."""
    return int(float(dollar_amount) * 100)


def insert(entry:Entry) -> None:
    """Insert an entry into the database."""
    query = db.make_insert_query_entry(entry)
    targ = target.select_one(entry.target)
    if not targ.instance_exists(entry.tframe):
        db.set_target_instance(targ, targ.default_amt, entry.tframe)
    db.run_query(query)


def delete(entry:Entry) -> None:
    """Delete an entry from the database."""
    db.delete_by_id(db.ENTRIES, entry.id)


def update(entry:Entry) -> None:
    """Update an entry in the database."""
    query = db.make_update_query_entry(entry.to_tuple())
    db.run_query(query)


def select(date:config.TimeFrame, category:str, targets:list) -> list[Entry]:
    """Select entries from the database."""
    query = db.make_select_query_entry(date, category, targets)
    entry_tuples = db.run_select_query(query)
    return [Entry.from_tuple(e) for e in entry_tuples]