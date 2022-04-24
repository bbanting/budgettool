import config
import entry
from config import KEYWORDS, Month
from kelevsma.validator import Validator, Result


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


class VTarget(Validator):
    """Verify that input belongs to the user's targets. Invertable."""
    def validate(self, value) -> Result:
        value = value.lower()
        if value in KEYWORDS:
            return Result.err()
        if value in [t.name for t in config.udata.targets]:
            ret_val = (Result.ok(value), Result.err())
        else:
            ret_val = (Result.err(), Result.ok(value))

        return ret_val[self.invert]


class VGroup(Validator):
    """Verify that the input string is the name of a target group."""
    def validate(self, value) -> Result:
        value = value.lower()
        if value in KEYWORDS:
            return Result.err()
        if value in config.udata.groups:
            ret_val = (Result.ok(value), Result.err())
        else:
            ret_val = (Result.err(), Result.ok(value))

        return ret_val[self.invert]


class VAmount(Validator):
    """Capture a positive or negative amount."""
    def validate(self, value:str) -> Result:
        if not value.startswith(("-", "+")):
            return Result.err()
        if not value[1:].isnumeric() or int(value) == 0:
            return Result.err()

        return Result.ok(entry.dollars_to_cents(value))


class VType(Validator):
    """Capture the type of entry."""
    def validate(self, value:str) -> Result:
        value = value.lower()
        if value == "income":
            return Result.ok("income")
        elif value in ("expense", "expenses"):
            return Result.ok("expense")
        return Result.err()


class VID(Validator):
    """Capture an ID"""
    def validate(self, value: str) -> Result:
        if value.isdigit():
            return Result.ok(int(value))
        return Result.err()
