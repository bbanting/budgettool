"""Utility functions and classes"""

import enum
import datetime
from dataclasses import dataclass


class Month(enum.IntEnum):
    all = 0
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


this_year = datetime.date.today().year
this_month = datetime.date.today().month

@dataclass(slots=True)
class TimeFrame:
    """Represents a timeframe within which to filter entries."""
    year: int
    month: Month
    def __init__(self, year:int=this_year, month:int=this_month):
        self.year = year
        self.month = Month(month)

    def iso_format(self, *, month:bool=True) -> str:
        """Return date in iso format for querying db."""
        if self.month.value:
            return f"{self.year}-{self.month.value:02}-%"
        return f"{self.year}-%"


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
    