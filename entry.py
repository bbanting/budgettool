from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass

import config
from config import DATEW, AMOUNTW, TAGSW


class EntryError(Exception):
    pass


@dataclass
class Entry:
    """Represent one entry in the budget."""
    def __init__(self, id:int, date:datetime, amount:int, tags:str, note:str):
        self.id: int = id
        self.date: datetime = date
        self.amount: int = amount
        self.tags: str = tags
        self.note: str = note

    @property
    def category(self) -> str:
        if self.amount > 0:
            return "income"
        else:
            return "expense"

    # @classmethod
    # def from_csv(cls, data: list):
    #     """Contruct an entry from a csv line."""
    #     id, date, amount, tags, note = data
    #     id = int(id)
    #     date = datetime.strptime(date, "%Y/%m/%d")
    #     amount = int(amount)
    #     tags = verify_tags(tags.split(" "))

    #     return cls(date, amount, tags, note, id=id)

    # def to_csv(self) -> list:
    #     """Convert entry into list for writing by the csv module."""
    #     date = self.date.strftime("%Y/%m/%d")
    #     return [self.id, date, str(self.amount), " ".join(self.tags), self.note]

    @classmethod
    def from_tuple(cls, data:tuple):
        """Construct an entry from a database row."""
        id, date, amount, tags, note = data
        id = int(id)
        date = datetime.strptime(date, "%Y/%m/%d")
        amount = int(amount)
        tags = verify_tags(tags)

        return cls(id, date, amount, tags, note)

    def to_tuple(self) -> tuple:
        date = self.date.strftime("%Y/%m/%d")
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
        if len(tags) > 12:
            tags = tags[:9] + "..."
        return f"{date:{DATEW}} {self.in_dollars():{AMOUNTW}} {self.tags:{TAGSW}} {self.note}"

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