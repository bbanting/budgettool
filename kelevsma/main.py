from __future__ import annotations
import logging


def get_input() -> str:
    """Get input from the user."""


def quit_program() -> None:
    global running
    running = False
    quit()

running: bool = True