from __future__ import annotations

import logging
import shlex
import threading

import kelevsma.display as display
from kelevsma.command import Command, CommandController, CommandError


# Globals
controller = CommandController()


class QuitProgramException(Exception):
    pass   


def run(init_cmd:str="") -> None:
    """Start the program loop. If init_cmd is given, a command will be
    run before the loop begins.
    """
    height_check_thread = threading.Thread(target=display.height_checker, daemon=True)
    height_check_thread.start()

    if init_cmd:
        controller.route_command(shlex.split(init_cmd))
        display.refresh()
    
    while True:
        try:
            user_input = shlex.split(input())
            controller.route_command(user_input)
        except (display.DisplayError) as e:
            display.error(e)
        except CommandError as e:
            display.message(str(e))
            display.refresh()
        except (QuitProgramException, KeyboardInterrupt):
            break
        else:
            display.refresh()


def register_command(command:Command, associated_screen:str="") -> None:
    """Register a command to the controller."""
    controller.register(command, associated_screen)


def add_screen(name:str, *, min_body_height:int=1, numbered:bool=False, 
            truncate:bool=False, refresh_func=None) -> None:
    """Public func to add a screen to the controller."""
    display.add_screen(name, min_body_height, numbered, truncate, refresh_func)
