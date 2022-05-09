import config
import entry
import db

class Target:
    """Class for printing targets."""
    name: str

    def __init__(self, name:str) -> None:
        self.name = name

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


def insert(name:str, amount:int) -> None:
    """Adds a new target to the database."""
    targets.append({"name": name, "default_amount": amount})


def delete(name:str) -> None:
    """Removes a target from the database."""
    for t in targets:
        if t["name"] != name:
            continue
        targets.remove(t)
        break


def update(name:str) -> Target | None:
    """Update a target."""
    for t in targets:
        if t["name"] != name:
            continue
        return Target(**t)


def select() -> list[Target]:
    """Return the list of targets."""
    query = db.make_select_query_target()
    target_tuples = db.run_select_query(query)
    return [Target(*t) for t in target_tuples]