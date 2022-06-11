"""A package for creating primitive and somewhat user-friendly command line programs."""

from .command import Command, CommandError, ForkCommand, SporkCommand, ContextualCommand, CommandController
from .validator import Validator, ValidatorError, VLit, VBool, VAny
from .base import run, add_screen, register_command, QuitProgramException