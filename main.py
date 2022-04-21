# Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

from __future__ import annotations
import shlex
import logging

import command
import display
import commands

from command.base import CommandError

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


def register_commands(controller: command.CommandController):
    controller.register(command.UndoCommand)
    controller.register(command.RedoCommand)
    controller.register(command.HelpCommand)
    controller.register(commands.ListCommand)
    controller.register(commands.QuitCommand)
    controller.register(commands.RemoveCommand)
    controller.register(commands.RemoveEntryCommand)
    controller.register(commands.RemoveTargetCommand)
    controller.register(commands.AddCommand)
    controller.register(commands.AddEntryCommand)
    controller.register(commands.AddTargetCommand)
    controller.register(commands.EditEntryCommand)
    controller.register(commands.ChangePageCommand)
    controller.register(commands.ListTargets)


def main():
    controller = command.CommandController()
    register_commands(controller)

    display.add_screen("entries", offset=1, numbered=True)
    display.add_screen("other", offset=1, numbered=True)

    controller.route_command("list")
    display.refresh()

    while True:
        try:
            user_input = shlex.split(input("> "))
            controller.route_command(user_input)
        except (BTError, display.DisplayError) as e:
            display.error(e)
        except CommandError as e:
            display.message(str(e))
            display.refresh()
        except KeyboardInterrupt:
            print("")
            return
        else:
            display.refresh()


if __name__=="__main__":
    main()
