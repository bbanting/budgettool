# Small module for parsing arguments

from functools import wraps
from typing import Union, Any, List
import inspect
from .validators import Validator


command_register = {}

class ParseError(Exception):
    pass


class ParseUserError(Exception):
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
    # ensure it's a list and first item isn't ''
    args = list(args) 
    if not args[0]:
        return

    # Get the function
    command = command_register.get(args[0])
    if not command:
        raise ParseUserError("Command not found.")
    args.remove(args[0])

    argspec = inspect.getfullargspec(command)
    # Turn defaults into an iterable to match args
    if argspec.defaults == None:
        argspec = argspec._replace(defaults=[])
    # Ensure argspec is valid
    if len(argspec.args) != len(argspec.defaults):
        raise ParseError("Every parameter must have a default.")
    # Keep only the params with validators for iterating over
    params = zip(argspec.args, argspec.defaults)
    params = [p for p in params if isinstance(p[1], Validator)]

    validated_data = {}
    errors = []
    for key, validator in params:
        if args:
            data = validator(args)
            if data is None:
                validated_data.update({key: None})
                errors.append(key)
                continue
            else:
                validated_data.update({key: data})
        else:
            if validator.required:
                raise ParseUserError("Command is missing required input.")
            validated_data.update({key: None})
            errors.append(key)

    # Execute the command
    if "errors" in argspec.args:
        validated_data.update({"errors": errors})
    if "extra" in argspec.args:
        validated_data.update({"extra": args})
    command(**validated_data)