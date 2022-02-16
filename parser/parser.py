# Small module for parsing arguments

from functools import wraps
from typing import Union, Any, List
import copy


command_register = []

class ParseError(Exception):
    pass


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


def resolve_key_conflicts(data: List[tuple]) -> dict:
    """
    Check if key conflicts exist. 
    If they do, append a number to the conflicting strings. 
    Convert to dict and return.
    """
    keys = [d[0] for d in data]
    if len(keys) != len(set(keys)):
        for index, key in enumerate(keys):
            n_found = 0
            for i, k in enumerate(keys[index+1:]):
                if key == k:
                    n_found += 1
                    keys[index+1+i] = k+str(n_found+1)
            if n_found:
                keys[index] = key + str(1)
        return dict(zip(keys, [d[1] for d in data]))
    else:
        return dict(data)


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
        command(*args[1:], branch=None)
        return
    
    # Determine branch and return name and args
    for branch in command.branches:
        branch_args = copy.copy(args[1:])
        processed_data = []
        if len(branch["validators"]) > len(branch_args):
            continue
        for validator in branch["validators"]:
            if branch_args:
                data = validator(branch_args)
                if data is None:
                    # Validator failed, go to next branch
                    break 
                else:
                    processed_data.append(data)
        else:
            # All validators were successful, execute the command
            processed_data = resolve_key_conflicts(processed_data)
            processed_data.update({"branch": branch["name"]})
            command(**processed_data)
            break
    else:
        raise ParseError("No branches matched.")