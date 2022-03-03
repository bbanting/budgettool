# Small module for parsing arguments

from __future__ import annotations
from typing import Union, Any, List
import inspect
from .validator import Validator, ValidatorError
import abc
import logging

logging.basicConfig(level=logging.INFO)


class ParseError(Exception):
    pass

class CommandError(Exception):
    pass


class CommandController:
    def __init__(self) -> None:
        self.command_register = {}
        self.undo_stack = []
        self.redo_stack = []

    def register(self, command: Command) -> None:
        """Attach the controller to the command and append command to commands list"""
        command.controller = self
        for n in command.names:
            if type(n) != str:
                raise ParseError("Invalid command name format.")
            self.command_register.update({n: command})

    def get_command(self, args) -> Union[Command, None]:
        """Return the command function."""
        command = self.command_register.get(args.pop(0))
        # Check for and process fork command
        if isinstance(command, ForkCommand):
            if args and args[0] in command.forks:
                return command.fork(args.pop(0))
            return command.fork(command.default)
        return command

    def execute(self, command: Command) -> None:
        """Wrapper around execute methods to give the option to include
        parameters."""
        argspec = inspect.getfullargspec(command.execute)
        # If more than just self is specified, include **data in the call
        if len(argspec.args) > 1:
            command.execute(**command.data)
        else:
            command.execute()

    def route_command(self, args:List[str]):
        """Process user input, execute appropriate function."""
        # Ensure it's a list and first item isn't ''
        args = list(args) 
        if not args or not args[0]:
            return
        
        # Get the function
        command_cls = self.get_command(args)
        if not command_cls:
            print("Command not found")
            return

        # Execute the command
        try:
            command = command_cls(args)
        except CommandError as e:
            print(e)
        else:
            self.execute(command)
            if "undo" in type(command).__dict__:
                self.undo_stack.append(command)
                self.redo_stack.clear()
    
    def undo(self) -> None:
        if not self.undo_stack:
            return
        command = self.undo_stack.pop()
        self.redo_stack.append(command)
        command.undo()

    def redo(self) -> None:
        if not self.redo_stack:
            return
        command = self.redo_stack.pop()
        self.undo_stack.append(command)
        command.redo()


class Command(metaclass=abc.ABCMeta):
    """Base class for a command."""
    names: tuple[str] = ()
    params: dict[str, Validator] = {}
    data: dict[str, Any] = {}
    controller: CommandController
    
    def __init__(self, args: List[str]) -> None:
        """Ensures passed data is valid."""
        for key, validator in self.params.items():
            try:
                result = validator(args)
                self.data.update({key: result})
            except ValidatorError as e:
                raise CommandError(f"{e}: {key}")
        if args: # Should be empty if successful
            raise CommandError(f"Unrecognized input: {', '.join(args)}")

    @abc.abstractmethod
    def execute(self) -> None:
        """
        User defines what the command does with the validated data 
        in self.data.
        """
        pass

    def undo(self) -> None:
        raise NotImplementedError("Undo has not been implemented.")
    
    def redo(self) -> None:
        raise NotImplementedError("Redo has not been implemented.")


class ForkCommand():
    """A class for two-word commands that fork based on the second word."""
    names: tuple[str] = ()
    forks: dict[str, Command] = {}
    default: Union[str, None] = None

    def fork(self, chosen_fork) -> Command:
        if not chosen_fork:
            return None
        return self.forks[chosen_fork]


class UndoCommand(Command):
    """Undo the last command."""
    names = ("undo",)

    def execute(self) -> None:
        if not self.controller.undo_stack:
            print("Nothing to undo.")
        self.controller.undo()


class RedoCommand(Command):
    """Redo the last command."""
    names = ("redo",)

    def execute(self) -> None:
        if not self.controller.redo_stack:
            print("Nothing to redo.")
        self.controller.redo()
