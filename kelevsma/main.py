from __future__ import annotations
import logging
import shlex

import command
import display


is_running: bool
controller = command.CommandController()


def quit_program() -> None:
    """Quit the program"""
    global is_running
    is_running = False
    quit()


def run(init_cmd:list=[]) -> None:
    """Start the program loop. If init_cmd is given, a command will be
    run before the loop begins.
    """
    global is_running
    is_running = True

    if init_cmd:
        controller.route_command(init_cmd)
        display.refresh()

    while True:
        try:
            user_input = shlex.split(input())
            controller.route_command(user_input)
        except (display.DisplayError) as e:
            display.error(e)
        except command.CommandError as e:
            display.message(str(e))
            display.refresh()
        except KeyboardInterrupt:
            print("")
            break
        else:
            display.refresh()    

    is_running = False


def register_command(command:command.Command, associated_screen:str="") -> None:
    """Register a command to the controller."""
    controller.register(command, associated_screen)


def add_screen(name:str, *, min_body_height:int=1, numbered:bool=False, 
            truncate:bool=False, refresh_func=None) -> None:
    """Public func to add a screen to the controller."""
    display.add_screen(name, min_body_height, numbered, truncate, refresh_func)