import abc
from typing import Any

from . import command

class ValidatorError(Exception):
    pass


class Result:
    def __init__(self, ok, value=None):
        self._ok: bool = ok
        self._value: Any = value

    @property
    def is_ok(self) -> bool:
        return self._ok

    @property
    def value(self) -> Any:
        return self._value

    @classmethod
    def ok(cls, value):
        return cls(ok=True, value=value)

    @classmethod
    def err(cls):
        return cls(ok=False)
    
    def __str__(self) -> str:
        if self.is_ok:
            return f"Result.ok({self._value})"
        return "Result.err"


class Validator(abc.ABC):
    """Base class from which validators are derived.
    A validator is passed a list of arguments and calls validate on each until
    a non-None value is returned. If only None is returned, the validator
    returns it's default, which defaults to None.

    plural: Allows more than one value to be returned from validate.
    req: The command will fail if set to True.
    default: Specify a different value to return on failure.
    """
    def __init__(self, plural=False, req=False, invert=False, default=None):
        self.plural = plural
        self.required = req
        self.invert = invert
        self.default = default

    def __call__(self, args:list, rmargs:bool=True) -> Any | list[Any]:
        """Calls validate on a list of arguments."""
        data = []
        to_remove = []
        for arg in args:
            result = self.validate(arg)
            if not result.is_ok:
                continue
            data.append(result.value)
            to_remove.append(arg)
            if not self.plural:
                break

        if not data:
            if self.required:
                raise ValidatorError("Missing required input")
            return self.default
        
        if rmargs:
            for x in to_remove:
                args.remove(x) 
        if self.plural:
            return data
        return data[0]
    
    @abc.abstractmethod
    def validate(self, value: str) -> Result:
        """
        This method must return either a Result.ok() on success or
        a Result.err() on failure.
        """
        pass


class VLit(Validator):
    """
    If the input value matches any of the literals, it is returned.
    Otherwise, return ValidatorError.
    """
    def __init__(self, literal, strict=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.literal = literal
        self.strict = strict

    def compare(self, lval: str, rval: str):
        if self.strict:
            return lval == rval
        else:
            return lval.lower() == rval.lower()

    def validate(self, value: str) -> Result:
        found = False
        if hasattr(self.literal, "__iter__") and type(self.literal) != str:
            if not all([True if type(x) is str else False for x in self.literal]):
                raise command.CommandConfigError("Literal must be str or an iterable containing only str.")
            for l in self.literal:
                if self.compare(value, l):
                    found = True
                    break
        else: 
            if self.compare(value, self.literal):
                found = True

        if self.invert:
            found = not found
        if found:
            return Result.ok(value)
        else:
            return Result.err()


class VBool(Validator):
    """
    Func must return a boolean, e.g. str.isalpha, and may be
    either a string method or user-defined function that takes a string.
    If func returns true when passed value, value is returned, otherwise 
    ValidatorError.
    """    
    def __init__(self, func, lower=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func
        self.lower = lower

    def validate(self, value: str) -> Result:
        ret_val = None
        # If it's a string method
        if hasattr(str, self.func.__name__):
            if getattr(value, self.func.__name__)():
                ret_val = value
        # If it's a function
        else:
            if self.func(value):
                ret_val = value

        if not ret_val:
            return Result.err()
        if self.lower:
            ret_val = ret_val.lower()
        return Result.ok(ret_val)


class VAny(Validator):
    """Accepts any value."""
    def validate(self, value) -> Result:
        return Result.ok(value)


class VComment(Validator):
    """
    Looks for a comment in args. Larger indexes and strings with spaces
    are prioritized.
    """
    def __call__(self, args:list) -> Any:
        data = []
        to_remove = []
        filtered_args = [a for a in args if " " in a]
        if filtered_args:
            for arg in filtered_args[::-1]:
                result = self.validate(arg)
                if not result.is_ok:
                    continue
                data.append(result.value)
                to_remove.append(arg)
                if not self.plural:
                    break
        else:
            for arg in args[::-1]:
                result = self.validate(arg)
                if not result.is_ok:
                    continue
                data.append(result.value)
                to_remove.append(arg)
                if not self.plural:
                    break
            
        if data:
            [args.remove(x) for x in to_remove]
            data = data if self.plural else data[0]
            return data
        else:
            if self.required:
                raise ValidatorError("Missing required input")
            return self.default
    
    def validate(self, value: str) -> Result:
        return Result.ok(value)


class VShortcut(Validator):
    """Checks if a word is a valid shortcut."""
    def validate(self, value:str) -> Result:
        if " " in value:
            return Result.err()
        return Result.ok(value)
