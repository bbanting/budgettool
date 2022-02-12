### Small module for parsing arguments

from functools import wraps
from typing import Union, Any
import copy


command_register = []

class ParseError(Exception):
    pass


class ValidatorError(Exception):
    pass


class Validator():
    def __init__(self, key=None, plural=False):
        if key:
            if type(key) is not str:
                raise ValidatorError("Invalid key.")
        else:
            key = self.__class__.__qualname__.lower()
        self.key = key
        self.plural = plural

    def __call__(self, args):
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
            return {self.key: data}
        else:
            return None
    
    def validate(self, value) -> Union[Any, None]:
        """This method must be overwritten and must return None on failure."""
        raise ValidatorError("Validator not implemented")


class Vlit(Validator):
    """
    If the input value matches any of the literals, it is returned
    """
    def __init__(self, literal, lower=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.literal = literal
        self.lower = lower
    def validate(self, value: str) -> Union[Any, None]:
        if hasattr(self.literal, "__iter__") and type(self.literal) != str:
            if value.lower() in [v.lower() for v in self.literal]:
                ret_val = value
            else:
                ret_val = None
        else: 
            if value.lower() == self.literal.lower():
                ret_val = value
            else:
                ret_val = None
        if self.lower:
            ret_val = ret_val.lower()
        return ret_val


class Vnlit(Vlit):
    def validate(self, value: str) -> Union[Any, None]:
        if hasattr(self.literal, "__iter__") and type(self.literal) != str:
            if value.lower() in [v.lower() for v in self.literal]:
                ret_val = None
            else:
                ret_val = value
        else: 
            if value.lower() == self.literal.lower():
                ret_val = None
            else:
                ret_val = value
        if self.lower:
            ret_val = ret_val.lower()
        return ret_val


class Vbool(Validator):
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


def command(*names: tuple[str]):
    """Decorator to mark a function as a command and name it."""
    def decorator(f):
        f.names = names
        f.branches = []
        command_register.append(f)
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator


def branch(name, *validators):
    """Decorator that defines a branch."""
    def decorator(f):
        branch = {
            "name": name,
            "validators": validators,
        }
        f.branches.append(branch)
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator


def route_command(args):
    """Process user input, route to appropriate function."""
    if not args[0]:
        return

    # Find the function
    command_name = args[0].lower()
    for f in command_register:
        if command_name in f.names:
            command = f
            break
    else:
        raise ParseError("Command not found.")

    # If command has no branches, run it
    if not command.branches:
        command(args[1:], branch=None)
        return
    
    # Determine branch and return name and args
    for branch in command.branches:
        branch_args = copy.copy(args[1:])
        processed_data = {}
        if len(branch["validators"]) > len(branch_args):
            continue
        for validator in branch["validators"]:
            if branch_args:
                data = validator(branch_args)
                if data is None:
                    # Validator failed, go to next branch
                    break 
                else:
                    ### Maybe include the name and make a dict
                    processed_data.update(data)
        else:
            # If all validators were successful, execute the command
            processed_data.update({"branch": branch["name"]})
            command(**processed_data)
            break
    else:
        raise ParseError("No branches matched.")