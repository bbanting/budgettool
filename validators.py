import enum

import config
from config import KEYWORDS, Month
from command.validator import Validator, Result


class VMonth(Validator):
    """Verify that input refers to a month; if so, return it as int."""
    def validate(self, value) -> Result:
        name = value.lower()
        for month in Month:
            if not month.name.lower().startswith(name): 
                continue
            return Result.ok(month)
        
        return Result.err()


class VDay(Validator):
    """Verify and capture day of a month."""
    def validate(self, value) -> Result:
        if value.isdigit() and int(value) in range(1, 32):
            return Result.ok(int(value))
        return Result.err()


class VYear(Validator):
    """Verify and return year number."""
    def validate(self, value) -> Result:
        if value.isdigit() and len(value) == 4:
            return Result.ok(int(value))
        return Result.err()


class VTags(Validator):
    """Verify that input belongs to the user's tags; if so, return it."""
    def __init__(self, *args, **kwargs):
        super().__init__(plural=True, *args, **kwargs)

    def validate(self, value) -> Result:
        value = value.lower()
        if value in config.udata.tags:
            return Result.ok(value)
        else:
            return Result.err()


class VNewTag(Validator):
    """Verify that str is a valid name for a new tag."""
    def validate(self, value: str) -> Result:
        value = value.lower()
        if value in KEYWORDS:
            # Tag name may not be a keyword.
            return Result.err()
        if ("+" in value) or ("!" in value):
            # Tag name may not contain '+' or '!'.
            return Result.err()
        if value in config.udata.tags:
            # Tag already exists.
            return Result.err()
        return Result.ok(value)


class VType(Validator):
    """Capture the type of entry."""
    def validate(self, value: str) -> Result:
        value = value.lower()
        if value == "income":
            return Result.ok("income")
        elif value in ("expense", "expenses"):
            return Result.ok("expense")
        return Result.err()


# class VID(Validator):
#     """Capture an ID"""
#     def validate(self, value: str) -> Result:
#         if value.isdigit() and len(value) <= 4:
#             return Result.ok(int(value))
#         return Result.err()