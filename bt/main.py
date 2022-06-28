"""
Budgetool
Created by Ben Banting
A simple tool to keep track of expenses and earnings.
"""

from __future__ import annotations

import os
import sys

# Because kelevsma is pretending to be an external package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import kelevsma

import commands
import config
import target
import entry

from config import TimeFrame, DATEW, AMOUNTW, TARGETW, NAMEW, ENTRIES, TARGETS, GRAPH


logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


def push_targets() -> None:
    """Push the current targets to the current screen"""
    year = config.target_filter_state.tframe.year
    month = config.target_filter_state.tframe.month.name
    kelevsma.push_h(f"   {'NAME':{NAMEW}}{'PROGRESS'}")
    kelevsma.push(*target.select())
    kelevsma.push_f(f"Showing targets for {month} of {year}.")


def push_entries() -> None:
    """Push the current entries to the current screen."""
    global entry # I don't understand why this is necessary
    s = config.entry_filter_state
    entries = entry.select(s.tframe, s.category, s.targets)
    entry_summary = get_entry_summary(len(entries), s.tframe, s.category, s.targets)
    target_progress = get_target_progress(s.targets)

    kelevsma.push_h(f"   {'DATE':{DATEW}}{' AMOUNT':{AMOUNTW}}{'TARGET':{TARGETW}}{'NOTE'}")
    kelevsma.push(*entries)
    kelevsma.push_f("", target_progress, entry_summary)


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


def push_target_graph() -> None:
    """Push the graph for the current targets to the current screen."""
    width = int(kelevsma.display.t_width() * .75)
    targs = target.select()
    standard = max(targs, key=lambda x: x.current_total)
    for t in targs:
        count = int(t.current_total / standard) * width
        kelevsma.push(f"{'0' * count} {t.name}")


def main():
    """Main function."""
    kelevsma.add_screen(ENTRIES, min_body_height=4, numbered=True, refresh_func=push_entries)
    kelevsma.add_screen(TARGETS, numbered=True, refresh_func=push_targets)
    kelevsma.add_screen(GRAPH, min_width=100, refresh_func=None)

    kelevsma.register(commands.ListCommand)
    kelevsma.register(commands.GraphTargetsCommand)
    kelevsma.register(commands.RemoveCommand)
    kelevsma.register(commands.AddCommand)
    kelevsma.register(commands.AddEntryTodayCommand)
    kelevsma.register(commands.EditEntryCommand)
    kelevsma.register(commands.RenameTargetCommand)
    kelevsma.register(commands.ChangePageCommand)
    kelevsma.register(commands.SetTargetCommand)

    kelevsma.run("list")


if __name__=="__main__":
    main()
