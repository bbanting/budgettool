# Small module for parsing arguments

from __future__ import annotations
from functools import wraps
from typing import Union, Any, List, Callable
import inspect
from .validator import Validator, ValidatorError
import abc


command_register = {}

class ParseError(Exception):
    pass

class CommandError(Exception):
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



class CommandController:
    def __init__(self) -> None:
        self.commands = {}
        self.undo_stack = []
        self.redo_stack = []

    def undo(self):
        pass

    def redo(self):
        pass

    def register(self, command: Command, names: str=None) -> None:
        if not names:
            names = command.names
        for n in names:
            if type(n) != str:
                raise ParseError("Invalid command name format.")
            self.commands.update({n: command})

    def get_command(self, args) -> Union[Callable, None]:
        """Return the command function."""
        command = self.commands.get(args.pop(0))
        if command and command.forks:
            if args and args[0].lower() in command.forks:
                c = args.pop(0)
                return command(fork=c)
            return command() # default complement
        return command

    def route_command(self, args:List[str]):
        """Process user input, execute appropriate function."""
        # Ensure it's a list and first item isn't ''
        args = list(args) 
        if not args[0]:
            return
        
        # Get the function
        command_cls = self.get_command(args)
        if not command_cls:
            print("Command not found")
            return

        # Execute the command
        try:
            command = command_cls()
        except CommandError as e:
            print(e)
        else:
            command.execute()
            if command.undo:
                self.undo_stack.append(command)


class Command(metaclass=abc.ABCMeta):
    """Base class for a command. Kwargs replaced by dict class attr."""
    names: List[str] = []
    params: dict[str, Validator] = {}
    
    def __init__(self, args: List[str]) -> None:
        """Ensures passed data is valid."""
        self.data = {}
        for key, validator in self.params:
            try:
                result = validator(args)
                self.data.update({key: result})
            except ValidatorError as e:
                raise CommandError(f"{e}: {key}")
        if args: # Should be empty if successful
            raise CommandError(f"Unrecognized input: {', '.join(args)}")

    # def _get_params(self) -> List[tuple[str, Validator]]:
    #     """
    #     Take a command function and output its parameters as a list
    #     of tuples containing a key and validator.
    #     """
    #     params = []
    #     for x in self.__dict__:
    #         if not isinstance(self.__dict__[x], Validator):
    #             continue
    #         params.append((x, self.__dict__[x]))

    @abc.abstractmethod
    def execute(self):
        """
        User defines what the command does with the validated data 
        in self.data.
        """
        pass

    def undo(self):
        raise NotImplementedError("Undo has not been implemented.")
    
    def redo(self):
        raise NotImplementedError("Redo has not been implemented.")
    

"""
Purely semantic difference for code clarity purposes.
A fork_command returns a function and instead of normal parameters
with Validators, it has one paramter, fork. The default for the 
fork parameter is the default fork that will be chosen.
"""
fork_command = command
