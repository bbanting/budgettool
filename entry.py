from __future__ import annotations
import datetime
import logging

from datetime import date
from dataclasses import dataclass
from colorama import Style

import config
import db


class EntryError(Exception):
    pass


@dataclass
class Entry:
    """Represent one entry in the budget."""
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
        values = (date, self.amount, self.target.name, self.note)
        if self.id:
            values = (self.id,) + values
        return values

    def in_dollars(self) -> str:
        """Formats the amount for display."""
        amount = cents_to_dollars(self.amount)
        if amount >= 0:
            return f"+${amount:.2f}"
        else:
            return f"-${abs(amount):.2f}"      
    
    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        return f"{date:{config.DATEW}} {self.in_dollars():{config.AMOUNTW}} {Style.DIM}({self.target.name}){Style.NORMAL} {self.note}"

    def __add__(self, other) -> int:
        if type(other) == type(self):
            return self.amount + other.amount
        if type(other) == int:
            return self.amount + other
        return NotImplemented

    def __radd__(self, other) -> int:
        return self.__add__(other)


def cents_to_dollars(cent_amount:int) -> float:
    """Convert a cent amount to dollars."""
    if not cent_amount:
        return float(0)
    return cent_amount / 100


def dollars_to_cents(dollar_amount:str) -> int:
    """Convert a string dollar ammount to cents for storage."""
    return int(float(dollar_amount) * 100)
