import config
import entry
import db


class Target:
    """Class for manipulating and printing targets."""
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
        return db.sum_target(self.name, self.tframe)

    def goal(self) -> int:
        """Return the goal with respect to current timeframe."""
        tframe = config.target_filter_state.tframe
        return db.get_target_goal(self.name, tframe)

    def __str__(self) -> str:
        current = entry.cents_to_dollars(self.current_total())
        goal = entry.cents_to_dollars(self.goal())
        return f"{self.name}: {current:.2f}/{goal:.2f}"


def get_target_names() -> list[str]:
    """Return a list of the target names."""
    query = db.make_select_query_target()
    target_tuples = db.run_select_query(query)
    return [t[0] for t in target_tuples]


def insert(target:Target) -> None:
    """Adds a new target to the database."""
    query = db.make_insert_query_target(**target.__dict__)
    db.run_query(query)


def delete(name:str) -> None:
    """Removes a target from the database."""
    query = db.make_delete_query_target(name)
    db.run_query(query)


def update(name:str, amount:int) -> None:
    """Update a target."""
    query = db.make_update_query_target(name, amount)
    db.run_query(query)


def select(name:str="") -> list[Target]:
    """Return the whole list of targets as Target objects."""
    query = db.make_select_query_target(name)
    target_tuples = db.run_select_query(query)
    return [Target(*t) for t in target_tuples]


def select_one(name:str) -> Target:
    """Return a single target from the database."""
    return select(name)[0]
