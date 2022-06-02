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
        return db.select_target_instance_amount(self, tframe)

    def instance_exists(self, tframe:config.TimeFrame) -> bool:
        """Return true if an instance exists in the db with this 
        target and time frame.
        """
        return any(db.select_target_instance_amount(self, tframe, use_default=False))

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
        if goal != default:
            string += f" (default: {default})"
        return string


def insert(target:Target) -> None:
    """Adds a new target to the database."""
    db.insert_row(db.TARGETS, *target.fields_and_values())


def delete(target:Target) -> None:
    """Removes a target from the database."""
    db.delete_row(db.TARGETS, target.id)


def update(target:Target) -> None:
    """Update a target."""
    fields, values = target.fields_and_values()
    db.update_row(db.TARGETS, target.id, fields[1:], values[1:])


def select(name:str="") -> list[Target]:
    """Return one target or the whole list of targets as Target objects."""
    target_tuples = db.select_targets(name)
    return [Target(*t) for t in target_tuples]


def select_one(name:str) -> Target:
    """Return a single target from the database."""
    return select(name)[0]


def get_target_names() -> list[str]:
    """Return a list of the target names."""
    return [t.name for t in select()]
