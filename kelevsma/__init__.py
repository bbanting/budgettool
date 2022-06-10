"""A package for creating primitive and user-friendly command line programs."""

from .command import Command, CommandError, ForkCommand, SporkCommand, ContextualCommand, CommandController
from .validator import Validator, ValidatorError, VLit, VBool, VAny
from .main import run, quit_program, is_running, add_screen, register_command