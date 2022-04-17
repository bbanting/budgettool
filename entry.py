from __future__ import annotations
import datetime
import logging

from datetime import date
from dataclasses import dataclass

import config
from config import DATEW, AMOUNTW, TAGSW


class EntryError(Exception):
    pass


@dataclass
class Entry:
    """Represent one entry in the budget."""
    def __init__(self, id:int, date:date, amount:int, tags:str, note:str):
        self.id: int = id
        self.date: date = date
        self.amount: int = amount
        self.tags: str = tags
        self.note: str = note

    @property
    def category(self) -> str:
        if self.amount > 0:
            return "income"
        else:
            return "expense"

    @classmethod
    def from_tuple(cls, data:tuple):
        """Construct an entry from a database row."""
        id, date, amount, tags, note = data
        id = int(id)
        date = datetime.date(int(date[0:4]), int(date[5:7]), int(date[8:10]))
        logging.info(date)
        amount = int(amount)
        tags = verify_tags(tags)

        return cls(id, date, amount, tags, note)

    def to_tuple(self) -> tuple:
        date = self.date.isoformat()
        values = (date, str(self.amount), self.tags, self.note)
        if self.id:
            values = (self.id, date, self.amount, self.tags, self.note)
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
        tags = self.tags
        if len(tags) > 12:
            tags = tags[:9] + "..."
        return f"{date:{DATEW}} {self.in_dollars():{AMOUNTW}} {tags:{TAGSW}} {self.note}"

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
    return cent_amount / 100


def dollars_to_cents(dollar_amount:str) -> int:
    """Convert a string dollar ammount to cents for storage."""
    return int(float(dollar_amount) * 100)


def verify_tags(tags:list):
    """Raise error if one of the tags are invalid;
    Otherwise return list back.
    """
    for t in tags.split(" "):
        if t not in (config.udata.tags + config.udata.old_tags):
            raise EntryError("Invalid tag.")
    return tags