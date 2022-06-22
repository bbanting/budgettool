from __future__ import annotations
import datetime
import logging

from datetime import date
from dataclasses import dataclass
from colorama import Style

import config
import db
import target

from config import DATEW, AMOUNTW, TARGETW


@dataclass(slots=True)
class Entry:
    """Represent one entry in the budget."""
    id: int
    date: date
    amount: int
    targ: str
    note: str
    target: target.Target = None
    
    def __post_init__(self) -> None:
        self.target = target.select_one(self.targ)

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

    def fields_and_values(self) -> tuple[tuple]:
        """Return the fields and values for an SQL insert."""
        date = self.date.isoformat()
        d = {
            "id":       self.id,
            "date":     date,
            "amount":   self.amount,
            "target":   self.target.id,
            "note":     self.note
        }
        if not self.id:
            d.pop("id")

        return (tuple(d.keys()), tuple(d.values()))

    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        return f"{date:{DATEW}}"\
        f"{dollar_str(self.amount):{AMOUNTW}}"\
        f"{self.target.name:{TARGETW}}"\
        f"{self.note}"

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
    # Make a target instance for this month if it doesn't exist
    targ = entry.target
    if not targ.instance_exists(entry.tframe):
        targ.set_instance(entry.tframe, targ.default_amt)

    db.insert_row(db.ENTRIES, *entry.fields_and_values())


def delete(entry:Entry) -> None:
    """Delete an entry from the database."""
    db.delete_row_by_id(db.ENTRIES, entry.id)


def update(entry:Entry) -> None:
    """Update an entry in the database."""
    fields, values = entry.fields_and_values()
    db.update_row(db.ENTRIES, entry.id, fields[1:], values[1:])


def select(tframe:config.TimeFrame, category:str, targets:list) -> list[Entry]:
    """Select entries from the database."""
    entry_tuples = db.select_entries(tframe, category, targets)
    return [Entry.from_tuple(e) for e in entry_tuples]
    