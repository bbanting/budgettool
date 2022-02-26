# Small module for parsing arguments

from functools import wraps
from typing import Union, Any, List, Callable
import inspect
from .validator import Validator, ValidatorError


command_register = {}

class ParseError(Exception):
    pass


def command(*names, forks=()):
    """Decorator to mark a function as a command and name it."""
    def decorator(f):
        f.forks = forks
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


"""
Purely semantic difference for code clarity purposes.
A fork_command returns a function and instead of normal parameters
with Validators, it has one paramter, fork. The default for the 
fork parameter is the default fork that will be chosen.
"""
fork_command = command


def get_command(args) -> Union[Callable, None]:
    """Return the command function."""
    command = command_register.get(args.pop(0))
    if command and command.forks:
        if args and args[0].lower() in command.forks:
            c = args.pop(0)
            return command(fork=c)
        return command() # default complement
    return command


def get_command_params(command) -> List[tuple[str, Validator]]:
    """
    Take a command function and output its parameters as a list
    of tuples containing a key and validator.
    """
    argspec = inspect.getfullargspec(command)
    # Turn defaults into an iterable to match args
    if argspec.defaults == None:
        argspec = argspec._replace(defaults=[])
    # Ensure argspec is valid
    if len(argspec.args) != len(argspec.defaults):
        raise ParseError("Every parameter must have a default.")
    # Keep only the params with validators for iterating over
    params = zip(argspec.args, argspec.defaults)
    return [p for p in params if isinstance(p[1], Validator)]


def route_command(args:List[str]):
    """Process user input, execute appropriate function."""
    # Ensure it's a list and first item isn't ''
    args = list(args) 
    if not args[0]:
        return
    
    # Get the function
    command = get_command(args)
    if not command:
        print("Command not found")
        return

    # Execute the command
    params = get_command_params(command)
    validated_data = {}
    for key, validator in params:
        try:
            data = validator(args)
            validated_data.update({key: data})
        except ValidatorError as e:
            print(f"{e}: {key}")
            return
    if args: # Should be empty if successful
        print(f"Unrecognized input: {', '.join(args)}")
        return

    command(**validated_data)
