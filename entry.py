from __future__ import annotations
import datetime
import logging

from datetime import date
from dataclasses import dataclass
from colorama import Style

import config
from config import DATEW, AMOUNTW


class EntryError(Exception):
    pass


@dataclass
class Entry:
    """Represent one entry in the budget."""
    def __init__(self, id:int, date:date, amount:int, target:Target, note:str):
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
        target = Target.from_str(target)

        return cls(id, date, amount, target, note)

    def to_tuple(self) -> tuple:
        """Return a tuple representation for the database."""
        date = self.date.isoformat()
        values = (date, self.amount, self.target.name, self.note)
        if self.id:
            values = (self.id,) + values
        return values

    def in_dollars(self):
        """Formats the amount for display."""
        amount = cents_to_dollars(self.amount)
        if amount >= 0:
            return f"+${amount:.2f}"
        else:
            return f"-${abs(amount):.2f}"      
    
    def __str__(self) -> str:
        date = self.date.strftime("%b %d")
        return f"{date:{DATEW}} {self.in_dollars():{AMOUNTW}} \
            {Style.DIM}({self.target.name}){Style.NORMAL} {self.note}"

    def __add__(self, other) -> int:
        if type(other) == type(self):
            return self.amount + other.amount
        if type(other) == int:
            return self.amount + other
        return NotImplemented

    def __radd__(self, other) -> int:
        return self.__add__(other)


class Target:
    """Represents a category/goal toward which entries are made."""
    name: str
    amount: int
    
    def __init__(self, name:str, amount:int):
        self.name = name
        self.amount = amount

    @staticmethod
    def from_str(name:str) -> Target:
        """Return the target corresponding to the input string.
        For retrieving targets when creating Entry objects."""
        for t in config.udata.targets:
            if not t.name.contains(name):
                continue
            return t

    @classmethod
    def from_dict(cls, d:dict) -> Target:
        """For instantiating targets from the config file at program start."""
        try:
            name = d["name"]
            amount = d["amount"]
        except KeyError:
            raise EntryError("Corrupted target in config file.")
        else:
            return cls(name, amount)


def cents_to_dollars(cent_amount:int) -> float:
    """Convert a cent amount to dollars."""
    return cent_amount / 100


def dollars_to_cents(dollar_amount:str) -> int:
    """Convert a string dollar ammount to cents for storage."""
    return int(float(dollar_amount) * 100)
