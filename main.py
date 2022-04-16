# Budget Tool
# Created by Ben Banting
# A simple tool to keep track of expenses and earnings.

from __future__ import annotations
import shlex
import logging

import config
import command
import display
import commands
import db

from entry import cents_to_dollars
from command.base import CommandError
from config import DATEW, AMOUNTW, TAGSW, TimeFrame

logging.basicConfig(level=logging.INFO, filename="general.log", filemode="w", encoding="utf-8")


class BTError(Exception):
    pass


def show_entries(date:TimeFrame, category:str, tags:str) -> None:
    """Push the current entries to the display."""
    entries = db.fetch_entries(date, category, tags)
    total = cents_to_dollars(sum(entries))
    total_str = f"${total:.2f}"
    if total > 0: total_str += "+"
    if total < 0: total_str += "-"
    summary = _get_filter_summary(len(entries), date, category, tags)

    display.push_h(f"{'DATE':{DATEW}} {'AMOUNT':{AMOUNTW}} {'TAGS':{TAGSW}} {'NOTE'}")
    for entry in entries: display.push(entry)
    display.push_f("", f"TOTAL: {total_str}", summary)


def _get_filter_summary(n:int, date:TimeFrame, category:str, tags:str) -> str:
    date = f"{date.month.name} {date.year}"
    category = f" of type {category}" if category else ""
    tags = f" with tags: {', '.join(tags)}" if tags else ""
    return f"{n} entries{category} from {date}{tags}."
    

def register_commands(controller: command.CommandController):
    controller.register(command.UndoCommand)
    controller.register(command.RedoCommand)
    controller.register(command.HelpCommand)
    controller.register(commands.ListCommand)
    controller.register(commands.QuitCommand)
    controller.register(commands.RemoveCommand)
    controller.register(commands.RemoveEntryCommand)
    controller.register(commands.RemoveTagCommand)
    controller.register(commands.AddCommand)
    controller.register(commands.AddEntryCommand)
    controller.register(commands.AddTagCommand)
    controller.register(commands.EditEntryCommand)
    controller.register(commands.ShowBillsCommand)
    controller.register(commands.ChangePageCommand)


def main():
    controller = command.CommandController()
    register_commands(controller)
    display.configure(offset=1)

    show_entries(*config.last_query)
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
            show_entries(*config.last_query)
            display.refresh()


if __name__=="__main__":
    main()
