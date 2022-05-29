import config
import entry
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
        target in the specified timeframe.
        """
        tframe = config.target_filter_state.tframe
        return db.sum_target(self, tframe)

    def goal(self, tframe=None) -> int:
        """Return the goal with respect to current timeframe."""
        if not tframe:
            tframe = config.target_filter_state.tframe
        return db.get_target_amount(self, tframe)

    def instance_exists(self, tframe:config.TimeFrame) -> bool:
        """Return true if an instance exists in the db with this 
        target and time frame.
        """
        return any(db.get_target_instance_amount(self, tframe, use_default=False))

    def __str__(self) -> str:
        name = self.name[:NAMEW]
        current = entry.cents_to_dollars(self.current_total())
        goal = entry.cents_to_dollars(self.goal())
        string =  f"{name:{NAMEW}}{current:.2f} / {goal:.2f}"
        default = entry.cents_to_dollars(self.default_amt)
        if goal != default:
            string += f" (default: {default})"
        return string


def insert(target:Target) -> None:
    """Adds a new target to the database."""
    query = db.make_insert_query_target(target.id, target.name, target.default_amt)
    db.run_query(query)


def delete(target:Target) -> None:
    """Removes a target from the database."""
    db.delete_by_id(db.TARGETS, target.id)


def update(target:Target, *, name:str=None, default_amt:int=None) -> None:
    """Update a target."""
    query = db.make_update_query_target(target.id, name, default_amt)
    db.run_query(query)


def update_instance(target:Target, amount:int, tframe:config.TimeFrame) -> None:
    """Update the amount for a target instance."""
    db.set_target_instance(target, amount, tframe)


def select(name:str="") -> list[Target]:
    """Return the whole list of targets as Target objects."""
    query = db.make_select_query_target(name)
    target_tuples = db.run_select_query(query)
    return [Target(*t) for t in target_tuples]


def select_one(name:str) -> Target:
    """Return a single target from the database."""
    return select(name)[0]


def get_target_names() -> list[str]:
    """Return a list of the target names."""
    return [t.name for t in select()]


def times_used(target:Target) -> int:
    """Return the number of times a target is used in the database."""
    query = f"SELECT * FROM entries WHERE target = {target.id}"
    return len(db.run_select_query(query))
