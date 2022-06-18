"""Top level module for public functions."""

from __future__ import annotations

import logging
import shlex
import threading

from . import command, display, shortcut


def push_shortcuts() -> None:
    """Push the shortcut list to the screen."""
    display.push_h(f"{'SHORTCUT':11}  COMMAND")
    display.push(*[f"/{k:10}  {v}" for k, v in command.controller.shortcut_map.items()])

def prof_run(*commands:str, times:int=1) -> None:
    """Run the program for profiling purposes. Does not block for input."""
    command.set_shortcuts(shortcut.select_all())
    for _ in range(times):
        for c in commands:
            command.controller.route_command(shlex.split(c))
            display.refresh()

def run(init_cmd:str="") -> None:
    """Start the program loop. If init_cmd is given, a command will be
    run before the loop begins.
    """
    height_check_thread = threading.Thread(target=display.height_checker, daemon=True)
    height_check_thread.start()

    command.set_shortcuts(shortcut.select_all())

    if init_cmd:
        command.controller.route_command(shlex.split(init_cmd))
        display.refresh()
    
    while True:
        try:
            user_input = shlex.split(input())
            command.controller.route_command(user_input)
        except (display.DisplayError) as e:
            display.error(e)
        except command.CommandError as e:
            display.message(str(e))
            display.refresh()
        except (command.QuitProgramException, KeyboardInterrupt):
            break
        else:
            display.refresh()


display.add_screen("shortcuts", refresh_func=push_shortcuts)
display.add_screen("help")

command.register(command.NewShortcutCommand)
command.register(command.DeleteShortcutCommand)
command.register(command.ViewShortcutsCommand)
command.register(command.HelpCommand)
command.register(command.UndoCommand)
command.register(command.RedoCommand)
command.register(command.QuitCommand)
