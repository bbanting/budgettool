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
import target
import entry

from kelevsma.command import CommandError
from config import TimeFrame, DATEW, AMOUNTW, NAMEW

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


def push_targets() -> None:
    display.push_h(f"{'NAME':{NAMEW}}{'PROGRESS'}")
    display.push(*target.select())


def push_entries() -> None:
    """Push the current entries to the display."""
    global entry # I don't understand why this is necessary
    s = config.entry_filter_state
    entries = entry.select(s.tframe, s.category, s.targets)
    entry_summary = get_entry_summary(len(entries), s.tframe, s.category, s.targets)
    target_progress = get_target_progress(s.targets)

    display.push_h(f"   {'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'NOTE'}")
    display.push(*entries)
    display.push_f("", target_progress, entry_summary)


def get_entry_summary(n:int, date:TimeFrame, category:str, targets:list) -> str:
    """Return a summary of the entry filter results."""
    date = f"{date.month.name} of {date.year}"
    category = f" of type {category}" if category else ""
    target_str = "targets" if len(targets) > 1 else "target"
    targets = f" for {target_str} '{', '.join(targets)}'" if targets else ""
    entry_str = "entry" if n == 1 else "entries"
    return f"{n} {entry_str}{category} from {date}{targets}."


def get_target_progress(targets:list[str]) -> str:
    """Return summary of targets in current filter."""
    if not targets:
        targets = target.select()
    current = sum([t.current_total() for t in targets])
    goal = sum([t.goal() for t in targets])
    return f"Progress: {entry.dollar_str(current)} / {entry.dollar_str(goal)} ({len(targets)})"


def register_commands(con: command.CommandController):
    con.register(command.UndoCommand)
    con.register(command.RedoCommand)
    con.register(command.HelpCommand, "help")
    con.register(command.QuitCommand)
    con.register(commands.ListCommand)
    con.register(commands.ListEntriesCommand, "entries")
    con.register(commands.ListTargetsCommand, "targets")
    con.register(commands.RemoveCommand)
    con.register(commands.RemoveEntryCommand, "entries")
    con.register(commands.RemoveTargetCommand, "targets")
    con.register(commands.AddCommand)
    con.register(commands.AddEntryCommand, "entries")
    con.register(commands.AddTargetCommand, "targets")
    con.register(commands.AddEntryTodayCommand, "entries")
    con.register(commands.EditEntryCommand, "entries")
    con.register(commands.RenameTargetCommand, "targets")
    con.register(commands.ChangePageCommand)
    con.register(commands.SetTargetCommand, "targets")
    con.register(commands.SetTargetForMonthCommand, "targets")
    con.register(commands.SetTargetDefaultCommand, "targets")


def main():
    """Main function."""
    # Create the screens
    display.add_screen("entries", min_body_height=3, numbered=True, refresh_func=push_entries)
    display.add_screen("targets", numbered=True, refresh_func=push_targets)
    display.add_screen("help")

    # Create the command controller and register commands
    controller = command.CommandController()
    register_commands(controller)

    # Start by running the list command
    controller.route_command(["list"])
    display.refresh()

    # Receive input and process commands
    while True:
        try:
            user_input = shlex.split(input())
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
