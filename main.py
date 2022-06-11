"""
Budgetool
Created by Ben Banting
A simple tool to keep track of expenses and earnings.
"""

from __future__ import annotations
import logging
import kelevsma

import kelevsma.command as command
import kelevsma.display as display
import commands
import config
import target
import entry

from config import TimeFrame, DATEW, AMOUNTW, NAMEW


logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


def push_targets() -> None:
    year = config.target_filter_state.tframe.year
    month = config.target_filter_state.tframe.month.name
    display.push_h(f"   {'NAME':{NAMEW}}{'PROGRESS'}")
    display.push(*target.select())
    display.push_f(f"Showing targets for {month} of {year}.")


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


def get_target_progress(target_names:list[str]) -> str:
    """Return summary of targets in current filter."""
    if not target_names:
        target_names = target.select()
    else:
        target_names = [target.select_one(t) for t in target_names]
    current = sum([t.current_total() for t in target_names])
    goal = sum([t.goal() for t in target_names])
    return f"Progress: {entry.dollar_str(current)} / {entry.dollar_str(goal)} ({len(target_names)})"


def register_commands():
    kelevsma.register_command(command.UndoCommand)
    kelevsma.register_command(command.RedoCommand)
    kelevsma.register_command(command.HelpCommand, "help")
    kelevsma.register_command(command.QuitCommand)
    kelevsma.register_command(commands.ListCommand)
    kelevsma.register_command(commands.ListEntriesCommand, "entries")
    kelevsma.register_command(commands.ListTargetsCommand, "targets")
    kelevsma.register_command(commands.RemoveCommand)
    kelevsma.register_command(commands.RemoveEntryCommand, "entries")
    kelevsma.register_command(commands.RemoveTargetCommand, "targets")
    kelevsma.register_command(commands.AddCommand)
    kelevsma.register_command(commands.AddEntryCommand, "entries")
    kelevsma.register_command(commands.AddTargetCommand, "targets")
    kelevsma.register_command(commands.AddEntryTodayCommand, "entries")
    kelevsma.register_command(commands.EditEntryCommand, "entries")
    kelevsma.register_command(commands.RenameTargetCommand, "targets")
    kelevsma.register_command(commands.ChangePageCommand)
    kelevsma.register_command(commands.SetTargetCommand, "targets")
    kelevsma.register_command(commands.SetTargetForMonthCommand, "targets")
    kelevsma.register_command(commands.SetTargetDefaultCommand, "targets")


def main():
    """Main function."""
    kelevsma.add_screen("entries", min_body_height=3, numbered=True, refresh_func=push_entries)
    kelevsma.add_screen("targets", numbered=True, refresh_func=push_targets)
    kelevsma.add_screen("help")

    register_commands()

    kelevsma.run("list")


if __name__=="__main__":
    main()
