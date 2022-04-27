"""
Budgetool
Created by Ben Banting
A simple tool to keep track of expenses and earnings.
"""

from __future__ import annotations
import shlex
import logging

import kelevsma.command as command
import kelevsma.display as display
import commands
import config
import db

from entry import cents_to_dollars, Target
from kelevsma.command import CommandError
from config import TimeFrame, DATEW, AMOUNTW

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


def push_targets() -> None:
    for t in config.udata.targets:
        t.date = commands.ListTargetsCommand.query_date # Necessary for Target.__str__()
        display.push(t)


def push_entries() -> None:
    """Push the current entries to the display."""
    date, category, target = config.last_query
    entries = db.select_entries(date, category, target)
    total = cents_to_dollars(sum(entries))
    total_str = f"${abs(total):.2f}"
    if total > 0: total_str = "+" + total_str
    if total < 0: total_str = "-" + total_str
    summary = get_filter_summary(len(entries), date, category, target)

    display.push_h(f"{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'NOTE'}")
    for entry in entries: 
        display.push(entry)
    display.push_f("", f"TOTAL: {total_str}", summary)

def get_filter_summary(n:int, date:TimeFrame, category:str, target:Target) -> str:
    date = f"{date.month.name} {date.year}"
    category = f" of type {category}" if category else ""
    target = f" at target: {', '.join(target)}" if target else ""
    return f"{n} entries{category} from {date}{target}."


def register_commands(controller: command.CommandController):
    controller.register(command.UndoCommand)
    controller.register(command.RedoCommand)
    controller.register(command.HelpCommand, "help")
    controller.register(commands.ListCommand, "entries")
    controller.register(commands.QuitCommand)
    controller.register(commands.RemoveCommand)
    controller.register(commands.RemoveEntryCommand, "entries")
    controller.register(commands.RemoveTargetCommand, "targets")
    controller.register(commands.AddCommand)
    controller.register(commands.AddEntryCommand, "entries")
    controller.register(commands.AddTargetCommand, "targets")
    controller.register(commands.AddEntryTodayCommand, "entries")
    controller.register(commands.EditCommand)
    controller.register(commands.EditEntryCommand, "entries")
    controller.register(commands.EditTargetCommand, "targets")
    controller.register(commands.ChangePageCommand)
    controller.register(commands.ListTargetsCommand, "targets")


def main():
    display.add_screen("entries", offset=1, numbered=True, refresh_func=push_entries)
    display.add_screen("targets", offset=1, numbered=True, refresh_func=push_targets)
    display.add_screen("help", offset=1)

    controller = command.CommandController()
    register_commands(controller)

    controller.route_command(["list"])
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
