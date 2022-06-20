import logging

import config
import entry
import kelevsma.db as kdb
import db

from config import NAMEW

class Target:
    """Class for manipulating and printing rows from the targets table."""
    __slots__ = ("id", "name", "default_amt")
    id: int
    name: str
    default_amt: int

    def __init__(self, id:int, name:str, default_amt:int) -> None:
        self.id = id
        self.name = name
        self.default_amt = default_amt

    def current_total(self) -> int:
        """Return the amount sum for entries with this 
        target in the current timeframe.
        """
        tframe = config.target_filter_state.tframe
        return db.sum_target(self.id, tframe)

    def goal(self, tframe=None) -> int:
        """Return the goal with respect to current timeframe."""
        if not tframe:
            tframe = config.target_filter_state.tframe
        if tframe.month:
            instances = kdb.select_rows(db.TARGET_INSTANCES,
                target=self.id, year=tframe.year, month=tframe.month.value)
        else:
            instances = kdb.select_rows(db.TARGET_INSTANCES, target=self.id, year=tframe.year)
            
        instances_sum = sum([x[2] for x in instances])
        diff = 12 - len(instances)

        if not diff:
            return instances_sum
        return instances_sum + (diff * self.default_amt)

    def instance_exists(self, tframe:config.TimeFrame) -> bool:
        """Return true if an instance exists in the db with this 
        target and time frame.
        """
        return bool(kdb.select_rows(db.TARGET_INSTANCES, 
                target=self.id, year=tframe.year, month=tframe.month.value))

    def set_instance(self, tframe:config.TimeFrame, amount:int) -> None:
        """Set the target amount for the specified month. Start by deleting the 
        old target instance if it exists, and then insert a new one.
        """
        del_fields = ("target", "year", "month")
        del_values = (self.id, tframe.year, tframe.month.value)

        ins_fields = ("target", "amount", "year", "month")
        ins_values = (self.id, amount, tframe.year, tframe.month.value)
        
        if kdb.delete_row_by_value(db.TARGET_INSTANCES, del_fields, del_values):
            # If first query works, run the next one
            db.insert_row(db.TARGET_INSTANCES, ins_fields, ins_values)

    def fields_and_values(self) -> tuple[tuple]:
        """Return the fields and values for an SQL insert."""
        d = {
            "id":           self.id,
            "name":         self.name,
            "default_amt":  self.default_amt,
        }
        if not self.id:
            d.pop("id")

        return (tuple(d.keys()), tuple(d.values()))

    def times_used(self) -> int:
        """Return the number of times target is used in the database."""
        query = f"SELECT * FROM entries WHERE target = {self.id}"
        return len(db.run_select_query(query))
        
    def update_instance(self, amount:int, tframe:config.TimeFrame) -> None:
        """Update the amount for a target instance."""
        db.set_target_instance(self.id, amount, tframe)

    def __str__(self) -> str:
        name = self.name[:NAMEW]
        current = entry.cents_to_dollars(self.current_total())
        goal = entry.cents_to_dollars(self.goal())
        string =  f"{name:{NAMEW}}{current:.2f} / {goal:.2f}"
        default = entry.cents_to_dollars(self.default_amt)
        if goal != default and config.target_filter_state.tframe.month.value:
            string += f" (default: {default})"
        return string


def insert(target:Target) -> None:
    """Adds a new target to the database."""
    db.insert_row(db.TARGETS, *target.fields_and_values())


def delete(target:Target) -> None:
    """Removes a target from the database."""
    db.delete_row_by_id(db.TARGETS, target.id)


def update(target:Target) -> None:
    """Update a target."""
    fields, values = target.fields_and_values()
    db.update_row(db.TARGETS, target.id, fields[1:], values[1:])


def select() -> list[Target]:
    """Return one target or the whole list of targets as Target objects."""
    target_tuples = kdb.select_rows(db.TARGETS)
    return [Target(*t) for t in target_tuples]


def select_one(name:str) -> Target:
    """Return a single target from the database."""
    target_tuples = kdb.select_rows(db.TARGETS, name=name)
    return Target(*target_tuples[0])


def get_target_names() -> list[str]:
    """Return a list of the target names."""
    return [t.name for t in select()]
