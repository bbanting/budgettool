"""Top level module for public functions."""

from __future__ import annotations

import logging
import shlex
import threading

from . import command, display
from .command import CommandError


class QuitProgramException(Exception):
    pass   


def run(init_cmd:str="") -> None:
    """Start the program loop. If init_cmd is given, a command will be
    run before the loop begins.
    """
    height_check_thread = threading.Thread(target=display.height_checker, daemon=True)
    height_check_thread.start()

    if init_cmd:
        command.controller.route_command(shlex.split(init_cmd))
        display.refresh()
    
    while True:
        try:
            user_input = shlex.split(input())
            command.controller.route_command(user_input)
        except (display.DisplayError) as e:
            display.error(e)
        except CommandError as e:
            display.message(str(e))
            display.refresh()
        except (QuitProgramException, KeyboardInterrupt):
            break
        else:
            display.refresh()
