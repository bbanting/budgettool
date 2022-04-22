import config
import entry
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


class VTarget(Validator):
    """Verify that input belongs to the user's targets; if so, return it."""
    def validate(self, value) -> Result:
        value = value.lower()
        if value in [t.name for t in config.udata.targets]:
            return Result.ok(entry.Target.from_str(value))
        else:
            return Result.err()


class VNewTarget(Validator):
    """Verify that str is a valid name for a new target."""
    def validate(self, value: str) -> Result:
        value = value.lower()
        if value in KEYWORDS:
            # Target name may not be a keyword.
            return Result.err()
        if value in [t.name for t in config.udata.targets]:
            # Target already exists.
            return Result.err()
        return Result.ok(value)


class VGroup(Validator):
    """Verify that the input string is the name of a target group."""
    def validate(self, value) -> Result:
        value = value.lower()
        if value not in config.udata.groups:
            return Result.err()
        return Result.ok(value)


class VNewGroup(Validator):
    """Verify that the input string is not the name of a target group."""
    def validate(self, value) -> Result:
        value = value.lower()
        if value in config.udata.groups:
            return Result.err()
        return Result.ok(value)


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
