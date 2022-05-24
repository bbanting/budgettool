from __future__ import annotations
import logging


def get_input() -> str:
    """Get input from the user."""


def quit_program() -> None:
    """Quit the program"""
    global is_running
    is_running = False
    quit()

is_running: bool = True