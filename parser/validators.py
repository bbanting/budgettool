from typing import Union, Any


class ValidatorError(Exception):
    pass


class Validator():
    """Base class from which validators are derived."""
    def __init__(self, key=None, plural=False, required=False):
        if key:
            if (type(key) is not str) or (key.lower() == "branch"):
                raise ValidatorError("Invalid key.")
        else:
            key = self.__class__.__qualname__.lower()
        self.key = key
        self.plural = plural
        self.required = required

    def __call__(self, args) -> tuple:
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
            return (self.key, data)
        else:
            return None
    
    def validate(self, value) -> Union[Any, None]:
        """This method must be overwritten and must return None on failure."""
        raise ValidatorError("Validator not implemented")


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
    Factory for validator functions based on provided function.
    The function must return a boolean, e.g. str.isalpha, and may be
    either a string method or user-defined function that takes a string.
    If the input value matches any of the literals, it is returned
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