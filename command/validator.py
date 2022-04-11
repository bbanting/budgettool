import abc
from typing import Any

import command.base


class ValidatorError(Exception):
    pass


class Validator(abc.ABC):
    """
    Base class from which validators are derived.
    A validator is passed a list of arguments and calls validate on each until
    a non-None value is returned. If only None is returned, the validator
    returns it's default, which defaults to None.

    plural: Allows more than one value to be returned from validate.
    required: The command will fail if set to True.
    default: Specify a different value to return on failure.
    """
    def __init__(self, plural=False, req=False, default=None, strict=False):
        self.plural = plural
        self.required = req
        self.default = default
        self.strict = strict

    def __call__(self, args:list) -> Any | list[Any]:
        """Calls validate on a list of arguments."""
        data = []
        to_remove = []
        for arg in args:
            result = self.validate(arg)
            if isinstance(result, ValidatorError):
                continue
            data.append(result)
            to_remove.append(arg)
            if not self.plural:
                break

        if not data:
            if self.required:
                raise ValidatorError("Missing required input")
            return self.default
        
        for x in to_remove: args.remove(x)
        if self.plural:
            return data
        return data[0]
    
    @abc.abstractmethod
    def validate(self, value: str) -> Any | ValidatorError:
        """
        This method must return ValidatorError on failure 
        and a validated value on success.
        """
        pass


class VLit(Validator):
    """
    If the input value matches any of the literals, it is returned.
    Otherwise, return ValidatorError.
    """
    def __init__(self, literal, lower=False, invert=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.literal = literal
        self.lower = lower
        self.invert = invert

    def compare(self, lval: str, rval: str):
        if self.strict:
            return lval == rval
        else:
            return lval.lower() == rval.lower()

    def validate(self, value: str) -> Any | ValidatorError:
        found = False
        if hasattr(self.literal, "__iter__") and type(self.literal) != str:
            if not all([True if type(x) is str else False for x in self.literal]):
                raise command.base.ParseError("Literal must be str or an iterable containing only str.")
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
            return value if not self.lower else value.lower()
        else:
            return ValidatorError()


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

    def validate(self, value: str) -> Any | ValidatorError:
        ret_val = None
        # If it's a method
        if hasattr(str, self.func.__name__):
            if getattr(value, self.func.__name__)():
                ret_val = value
        # If it's a function
        else:
            if self.func(value):
                ret_val = value

        if not ret_val:
            return ValidatorError()
        if self.lower:
            ret_val = ret_val.lower()
        return ret_val


class VAny(Validator):
    """Accepts any value."""
    def __init__(self, lower=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lower = lower
    
    def validate(self, value) -> Any | None:
        if self.lower:
            return value.lower()
        return value


class VComment(Validator):
    """
    Looks for a comment in args. Higher indexes and strings with spaces
    are prioritized.
    """
    def __call__(self, args:list) -> Any:
        data = []
        to_remove = []
        filtered_args = [a for a in args if " " in a]
        if filtered_args:
            for arg in filtered_args[::-1]:
                result = self.validate(arg)
                if isinstance(result, ValidatorError):
                    continue
                data.append(result)
                to_remove.append(arg)
                if not self.plural:
                    break
        else:
            for arg in filtered_args[::-1]:
                result = self.validate(arg)
                if isinstance(result, ValidatorError):
                    continue
                data.append(result)
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
    
    def validate(self, value: str) -> str:
        return value
        