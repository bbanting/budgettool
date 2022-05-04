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
import entry

from entry import cents_to_dollars
from kelevsma.command import CommandError
from config import TimeFrame, DATEW, AMOUNTW

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


def push_targets() -> None:
    for t in config.targets:
        display.push(config.get_target(t))


def push_entries() -> None:
    """Push the current entries to the display."""
    s = config.entry_filter_state
    entries = db.select_entries(s.date, s.category, s.targets)
    total = cents_to_dollars(sum(entries))
    total_str = f"${abs(total):.2f}"
    if total > 0: total_str = "+" + total_str
    if total < 0: total_str = "-" + total_str
    summary = get_filter_summary(len(entries), s.date, s.category, s.targets)

    display.push_h(f"{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'NOTE'}")
    for entry in entries: 
        display.push(entry)
    display.push_f("")
    display.push_f(get_target_summary(s.targets)) if s.targets else ...
    display.push_f(f"TOTAL: {total_str}")
    display.push_f(summary)

def get_filter_summary(n:int, date:TimeFrame, category:str, targets:list) -> str:
    """Return a summary of the entry filter results."""
    date = f"{date.month.name} of {date.year}"
    category = f" of type {category}" if category else ""
    target_str = "targets" if len(targets) > 1 else "target"
    targets = f" for {target_str} '{', '.join(targets)}'" if targets else ""
    entry_str = "entries" if n > 1 else "entry"
    return f"{n} {entry_str}{category} from {date}{targets}."

def get_target_summary(targets:list[str]) -> str:
    """Return summary of targets in current filter."""
    targets = [config.get_target(t) for t in targets]
    current = sum([t.current_total() for t in targets])
    goal = sum([t.goal() for t in targets])
    return f"Goal progress: {entry.dollar_str(current)}/{entry.dollar_str(goal)}"


def register_commands(controller: command.CommandController):
    controller.register(command.UndoCommand)
    controller.register(command.RedoCommand)
    controller.register(command.HelpCommand, "help")
    controller.register(commands.QuitCommand)
    controller.register(commands.ListCommand)
    controller.register(commands.ListEntriesCommand, "entries")
    controller.register(commands.ListTargetsCommand, "targets")
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
