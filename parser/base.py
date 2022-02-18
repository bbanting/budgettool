# Small module for parsing arguments

from functools import wraps
from typing import Union, Any, List
import inspect
from .validators import Validator


command_register = {}

class ParseError(Exception):
    pass


def command(*names):
    """Decorator to mark a function as a command and name it."""
    def decorator(f):
        for n in names:
            if type(n) == str:
                command_register.update({n: f})
            else:
                raise ParseError("Invalid command name format.")
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator


def branch(name, *validators):
    """Decorator that defines a branch."""
    def decorator(f):
        if type(name) is not str:
            raise ParseError("Branch name must be of type str.")
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

    # Get the function
    command = command_register.get(args[0])
    if not command:
        raise ParseError("Command not found.")
    args.remove(args[0])

    argspec = inspect.getfullargspec(command)
    # The code below expect defaults to be an iterable not None
    if argspec.defaults == None:
        argspec = argspec._replace(defaults=[])

    keys = [k for k in argspec.args if k.lower() not in ("errors", "extra")]
    validators = [v for v in argspec.defaults if isinstance(v, Validator)]

    validated_data = {}
    errors = []
    for key, validator in zip(keys, validators):
        if args:
            data = validator(args)
            if data is None and validator.required:
                raise ParseError("Command is missing required input.")
            elif data is None and not validator.required:
                validated_data.update({key: None})
                errors.append(key)
                continue
            else:
                validated_data.update({key: data})
        else:
            if validator.required:
                raise ParseError("Command is missing required input.")
            validated_data.update({key: None})
            errors.append(key)

    # Execute the command
    if "errors" in argspec.args:
        validated_data.update({"errors": errors})
    if "extra" in argspec.args:
        validated_data.update({"extra": args})
    command(**validated_data)