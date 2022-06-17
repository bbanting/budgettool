"""Top level module for public functions."""

from __future__ import annotations

import logging
import shlex
import threading

from . import command, display, shortcut


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


display.add_screen("help")
command.register(command.NewShortcutCommand)
command.register(command.DeleteShortcutCommand)
command.register(command.HelpCommand)
command.register(command.UndoCommand)
command.register(command.RedoCommand)
command.register(command.QuitCommand)
