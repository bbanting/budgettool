from typing import Union, Any
import abc

import parser.base


class ValidatorError(Exception):
    pass


class Validator(metaclass=abc.ABCMeta):
    """
    Base class from which validators are derived.
    A validator is passed a list of arguments and calls validate on each until
    a non-None value is returned. If only None is returned, the validator
    returns it's default, which defaults to None.

    plural: Allows more than one value to be returned from validate.
    required: The command will fail if set to True.
    default: Specify a different value to return on failure.
    """
    def __init__(self, plural=False, required=False, default=None):
        self.plural = plural
        self.required = required
        self.default = default

    def __call__(self, args:list) -> Any:
        data = []
        to_remove = []
        for arg in args:
            if (result := self.validate(arg)) is not None:
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
                raise parser.base.ParseUserError("Command is missing required input.")
            return self.default
    
    @abc.abstractmethod
    def validate(self, value: str) -> Union[Any, None]:
        """
        This method must return None on failure 
        and a validated value on success.
        """
        pass


class VLit(Validator):
    """
    If the input value matches any of the literals, it is returned.
    Otherwise, return None.
    """
    def __init__(self, literal, lower=False, strict=False, invert=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.literal = literal
        self.lower = lower
        self.strict = strict
        self.invert = invert

    def compare(self, lval: str, rval: str):
        if self.strict:
            return lval == rval
        else:
            return lval.lower() == rval.lower()

    def validate(self, value: str) -> Union[Any, None]:
        found = False
        if hasattr(self.literal, "__iter__") and type(self.literal) != str:
            if all([True if type(x) is str else False for x in self.literal]):
                for l in self.literal:
                    if self.compare(value, l):
                        found = True
                        break
            else:
                raise ValidatorError("Literal must be str or an iterable containing only str.")
        else: 
            if self.compare(value, self.literal):
                found = True

        if not found if self.invert else found:
            return value if not self.lower else value.lower()
        else:
            return None


class VBool(Validator):
    """
    Func must return a boolean, e.g. str.isalpha, and may be
    either a string method or user-defined function that takes a string.
    If func returns true when passed value, value is returned, otherwise None.
    """    
    def __init__(self, func, lower=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func
        self.lower = lower

    def validate(self, value: str):
        if hasattr(str, self.func.__name__):
            if getattr(value, self.func.__name__)():
                ret_val = value
            else:
                ret_val = None
        else:
            if self.func(value):
                ret_val = value
            else:
                ret_val = None
        if self.lower:
            ret_val = ret_val.lower()
        return ret_val


class VAny(Validator):
    """Accepts any value."""
    def __init__(self, lower=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lower = lower
    
    def validate(self, value) -> Union[Any, None]:
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
        if filtered_args := [a for a in args if " " in a]:
            for arg in filtered_args[::-1]:
                if (result := self.validate(arg)) is not None:
                    data.append(result)
                    to_remove.append(arg)
                    if not self.plural:
                        break
        else:
            for arg in args[::-1]:
                if (result := self.validate(arg)) is not None:
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
                raise parser.base.ParseUserError("Command is missing required input.")
            return self.default
    
    def validate(self, value: str) -> str:
        return value