from __future__ import annotations
from datetime import datetime
from typing import List

import config
import main
from config import DATEW, AMOUNTW, TAGSW


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
    def parent_record(self) -> main.Record:
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
        if cent_amount >= 0:
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
                raise main.BTError("Invalid tag.")
        return tags

    def in_dollars(self):
        return Entry.cents_to_dollars(self.amount)

    def to_csv(self) -> List:
        """Convert entry into list for writing by the csv module."""
        date = self.date.strftime("%Y/%m/%d")
        return [self.id, date, str(self.amount), " ".join(self.tags), self.note]

    def to_tuple(self) -> tuple:
        date = self.date.strftime("%Y/%m/%d")
        return (date, str(self.amount), " ".join(self.tags), self.note)

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
