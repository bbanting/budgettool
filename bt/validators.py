import entry
import target
from config import KEYWORDS, Month
from kelevsma.validator import Validator, Result


class VMonth(Validator):
    """Verify that input refers to a month; if so, return it as int."""
    def __init__(self, allow_any:bool=True, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.allow_any = allow_any

    def validate(self, value) -> Result:
        name = value.lower()
        for month in Month:
            if not self.allow_any and not month.value:
                continue
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
    """Verify that input belongs to the user's targets or groups. Invertable."""
    def validate(self, value) -> Result:
        value = value.lower()
        if value in KEYWORDS:
            return Result.err()
            
        ret_val = [Result.ok(value), Result.err()]
        if value not in target.get_target_names():
            ret_val.reverse()

        return ret_val[self.invert]


class VAmount(Validator):
    """Capture a positive or negative amount in dollars. Return in cents."""
    def __init__(self, allow_zero:bool=False, *args, **kwargs) -> None:
        self.allow_zero = allow_zero
        super().__init__(*args, **kwargs)
        
    def validate(self, value:str) -> Result:
        if not value.startswith(("-", "+")):
            return Result.err()
        if not value[1:].isnumeric():
            return Result.err()
        if not self.allow_zero and int(value) == 0:
            return Result.err()
        
        amount = entry.dollars_to_cents(value)
        if not -100000000 < amount < 100000000:
            return Result.err()
        return Result.ok(amount)


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
