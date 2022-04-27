from __future__ import annotations
from typing import Any, TypeVar
import inspect
import abc
import logging

import kelevsma.display as display
from .validator import Validator, ValidatorError, VLit

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

    def register(self, command:Command, associated_screen:str="") -> None:
        """Attach the controller to the command and append command to commands list"""
        command.controller = self
        for n in command.names:
            if type(n) != str:
                raise ParseError("Invalid command name format.")
            self.command_register.update({n: command})
        if associated_screen:
            command.screen = associated_screen

    def get_command(self, args) -> Command | None:
        """Return the command function."""
        command = self.command_register.get(args.pop(0).lower())
        # Check for and process fork command
        if hasattr(command, "forks"):
            return command.fork(args)
        return command

    def execute(self, command:Command) -> None:
        """Wrapper around execute methods to give the option to include
        parameters."""
        if hasattr(command, "screen"):
            display.switch_screen(command.screen)
        argspec = inspect.getfullargspec(command.execute)
        # If more than just self is specified, include **data in the call
        if len(argspec.args) > 1:
            command.execute(**command.data)
        else:
            command.execute()

    def route_command(self, args:list[str]):
        """Process user input, execute command."""
        # Ensure input isn't empty
        if not args or not args[0]:
            raise CommandError("Try 'help' if you're having trouble.")
        
        # Get the command
        command_cls = self.get_command(args)
        if not command_cls:
            raise CommandError("Command not found.")

        # Execute the command
        try:
            command = command_cls(args)
        except CommandError as e:
            raise CommandError(str(e) + "; Try 'help' if you're having trouble.")
        else:
            self.execute(command)
            if "undo" in command.__class__.__dict__:
                self.undo_stack.append(command)
                self.redo_stack.clear()
    
    def undo(self) -> None:
        if not self.undo_stack:
            display.message("Nothing to undo")
            return
        command = self.undo_stack.pop()
        self.redo_stack.append(command)
        command.undo()

    def redo(self) -> None:
        if not self.redo_stack:
            display.message("Nothing to redo")
            return
        command = self.redo_stack.pop()
        self.undo_stack.append(command)
        command.redo()


class Command(metaclass=abc.ABCMeta):
    """Base class for a command."""
    names: tuple[str] = ()
    params: dict[str, Validator] = {}
    data: dict[str, Any]
    controller: CommandController
    help_text: str = ""
    screen: str
    
    def __init__(self, args:list[str]) -> None:
        """Ensures passed data is valid and store in self.data."""
        self.data = {}
        for key, validator in self.params.items():
            try:
                result = validator(args)
                self.data.update({key: result})
            except ValidatorError as e:
                raise CommandError(f"{e}: {key}")
        if args: # Should be empty if successful
            raise CommandError(f"Invalid input: {', '.join(args)}")

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


class ForkCommand:
    """A class for two-word commands that fork based on the second word."""
    names: tuple[str] = ()
    forks: dict[str, Command] = {}
    default: str | None = None
    controller: CommandController
    help_text: str = ""

    @classmethod
    def fork(cls, args:list[str]) -> Command | None:
        """Return the selected fork."""
        if args and args[0] in cls.forks:
            return cls.forks.get(args.pop(0))
        return cls.forks.get(cls.default)


class ContextualCommand(ForkCommand):
    """A class for commands that fork based on the active screen."""
    @classmethod
    def fork(cls, args:list[str]) -> Command | None:
        """Return the selected fork based on the screen."""
        return cls.forks.get(display.get_screen().name)


class UndoCommand(Command):
    """Undo the last command."""
    names = ("undo",)

    def execute(self) -> None:
        self.controller.undo()


class RedoCommand(Command):
    """Redo the last undo."""
    names = ("redo",)

    def execute(self) -> None:
        self.controller.redo()


class HelpCommand(Command):
    """A command to give information on how to use other commands."""
    names = ("help",)

    def __init__(self, args: list[str]):
        # Overriding __init__ is necessary because the validator for "command"
        # in params depends on the prior instantiation of CommandController
        HelpCommand.params = {"command": VLit(self.controller.command_register)}
        super().__init__(args)
        
    def execute(self, command: str):
        command = self.controller.command_register.get(command)
        if not command:
            print(self.get_general_help())
            return

        if issubclass(command, ForkCommand):
            print(f"'{command.names[0]}' is a compound command:")
            self.fork_execute(command)
            return

        print(self.get_names(command))
        if self.get_format:
            print(self.get_format(command))
        print("\t" + command.__doc__)
        if self.get_help_note(command):
            print("\t" + self.get_help_note(command))

    def fork_execute(self, command: Command) -> None:
        print("\t" + command.__doc__)
        print(f"\t{self.get_help_note(command)}")
        for i, (k, v) in enumerate(command.forks.items()):
            v.names = (f"{command.names[0]} {k}",)
            number = f"{i+1}. "
            print(f"{number:>8}{self.get_names(v)}")
            if self.get_format(v):
                print(f"\t{self.get_format(v)}")
            print("\t" + v.__doc__)
            if self.get_help_note(v):
                print(f"\t{self.get_help_note(v)}")

    def get_general_help(self) -> str:
        message = "Enter \"help <command>\" for specific command details."
        prev = None
        for k, v in self.controller.command_register.items():
            if v == prev:
                continue
            message += f"\n{k:.<15}{v.__doc__}"
            prev = self.controller.command_register[k]
        return message

    def get_names(self, command: Command) -> str:
        name_suffix = "" if len(command.names)<=1 else "S"
        return f"COMMAND NAME{name_suffix}: {', '.join(command.names)}"
    
    def get_format(self, command: Command) -> str:
        if not command.params:
            return ""
        param_format = []
        for k, v in command.params.items():
            req = "*" if v.required else ""
            param_format.append(f"<{req}{k}>")
        return f"FORMAT: \"{command.names[0]} {' '.join(param_format)}\""

    def get_help_note(self, command: Command) -> str:
        if command.help_text:
            return f"{command.help_text}"
        return ""