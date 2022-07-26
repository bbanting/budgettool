"""A one-use script to convert from the previous entry format."""

import csv
import datetime

import entry, target, util


def main(filename:str):
    with open(filename, "r") as f:
        lines = f.readlines()
        reader = csv.DictReader(lines)
        for l in reader:
            date = datetime.date.fromisoformat(l["date"].replace("/", "-"))
            amount = util.dollars_to_cents(l["amount"])
            targ = get_target(l["category"])
            note = l["note"]
            e = entry.Entry(0, date, amount, targ, note)
            entry.insert(e)


def get_target(category:str) -> str:
    """Takes the name of a category and creates a target with the same
    name if it does not exist."""
    if not target.select_one(category):
        targ = target.Target(0, category, 1000)
        target.insert(targ)
    return category


if __name__ == "__main__":
    main()
        