### Small module for parsing arguments

from functools import wraps
from nis import match


command_register = []

class ParseError(Exception):
    pass


def command(*names: tuple[str]):
    """Decorator to mark a function as a command and name it."""
    def decorator(f):
        f.names = names
        f.branches = []
        command_register.append(f)
        print(f"Registering command {f.__qualname__}")
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


def vliteral(match_value, plural=False):
    """
    Factory for validator functions based on string literals. 
    If the input value matches any of the literals, it is returned
    """
    def validator(input_val: str):
        if hasattr(match_value, "__iter__") and type(match_value) != str:
            if input_val.lower() in [v.lower() for v in match_value]:
                return input_val
            else:
                return None
        else: 
            if input_val.lower() == match_value.lower():
                return input_val
            else:
                return None
    validator.plural = plural
    return validator


def vnotliteral(match_value, plural=False):
    def validator(input_val: str):
        if hasattr(match_value, "__iter__") and type(match_value) != str:
            if input_val.lower() in [v.lower() for v in match_value]:
                return None
            else:
                return input_val
        else: 
            if input_val.lower() == match_value.lower():
                return None
            else:
                return input_val
    validator.plural = plural
    return validator


def vbool(f, plural=False): ### Not working entirely as I want it to
    """
    Factory for validator functions based on provided function.
    The function must return a boolean, e.g. str.isalpha, and may be
    either a string method or user-defined function that takes a string.
    If the input value matches any of the literals, it is returned
    """
    def validator(input_val: str):
        if hasattr(str, f.__name__):
            if getattr(input_val, f.__name__)():
                return input_val
            else:
                return None
        else:
            if f(input_val):
                return input_val
            else:
                return None
    validator.plural = plural
    return validator


def run_validator(validator, args, arguments):
    data = []
    for arg in args:
        if (result := validator(arg)) is not None:
            if result not in arguments:
                data.append(result)
                if not validator.plural:
                    break
    if data:
        return data if validator.plural else data[0]
    else:
        return None


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
        if len(branch["validators"]) > len(args[1:]):
            continue
        arguments = []
        for validator in branch["validators"]:
            data = run_validator(validator, args[1:], arguments)
            if data is None:
                # Validator failed, go to next branch
                break 
            else:
                ### Maybe include the name and make a dict
                arguments.append(data)
        else:
            # If all validators were successful, execute the command
            command(arguments, branch=branch["name"])
            break
    else:
        raise ParseError("No branches matched.")