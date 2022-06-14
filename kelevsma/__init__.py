"""A package for creating primitive and somewhat user-friendly command line programs."""

from .command import Command, CommandError, ForkCommand, SporkCommand, ContextualCommand, CommandController, register
from .validator import Validator, ValidatorError, VLit, VBool, VAny
from .display import add_screen, change_page, refresh, message, error, push, push_f, push_h
from .base import run
    