import enum
from typing import Union

import config
from config import KEYWORDS, Month
from command.validator import Validator, ValidatorError


class VMonth(Validator):
    """Verify that input refers to a month; if so, return it as int."""
    def validate(self, value) -> Union[enum.IntEnum, ValidatorError]:
        name = value.lower()
        for month in Month:
            if not month.name.lower().startswith(name): 
                continue
            return month
        
        # if not self.strict and name in ("all", "year"):
        #     return "year"
        return ValidatorError("Month not found")


class VDay(Validator):
    """Verify and capture day of a month."""
    def validate(self, value) -> Union[int, ValidatorError]:
        if value.isdigit() and int(value) in range(1, 32):
            return int(value)
        return ValidatorError("Invalid day number")


class VYear(Validator):
    """Verify and capture year number."""
    def validate(self, value) -> Union[int, ValidatorError]:
        if value.isdigit() and len(value) == 4:
            return int(value)
        return ValidatorError("Invalid year number")


class VTag(Validator):
    """Verify that input belongs to the user's tags; if so, return it."""
    def __init__(self, *args, **kwargs):
        super().__init__(plural=True, *args, **kwargs)

    def validate(self, value) -> Union[str, ValidatorError]:
        if value.lower() in config.udata.tags:
            return value.lower()
        else:
            return ValidatorError("Tag not found.")


class VNewTag(Validator):
    """Verify that str is a valid name for a new tag."""
    def validate(self, value: str) -> Union[str, ValidatorError]:
        value = value.lower()
        if value in KEYWORDS:
            return ValidatorError("Tag name may not be a keyword.")
        if ("+" in value) or ("!" in value):
            return ValidatorError("Tag name may not contain '+' or '!'.")
        if value in config.udata.tags:
            return ValidatorError("Tag already exists.")
        return value


class VType(Validator):
    """Capture the type of entry."""
    def validate(self, value: str) -> Union[str, ValidatorError]:
        value = value.lower()
        if value == "income":
            return value
        elif value in ("expense", "expenses"):
            return "expense"
        return ValidatorError("Invalid type.")


class VID(Validator):
    """Capture an ID"""
    def validate(self, value: str) -> Union[int, ValidatorError]:
        if value.isdigit() and len(value) <= 4:
            return int(value)
        return ValidatorError("Invalid ID")