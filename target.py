import config
import entry
import db

class Target:
    """Class for printing targets."""
    name: str
    default_amount: int
    tframe: config.TimeFrame

    def __init__(self, name:str, default_amount:int) -> None:
        self.name = name
        self.tframe = config.target_filter_state.tframe
        self.default_amount = default_amount

    def current_total(self) -> int:
        """Return the amount sum for entries with this 
        target in the specified timeframe.
        """
        return db.sum_target(self.name, self.tframe)

    def goal(self) -> int:
        """Return the goal with respect to current timeframe."""
        if self.tframe.month == 0:
            goals = [db.get_monthly_target_amount(self.name, x) for x in range(1, 13)]
            return sum(goals)
        return db.get_monthly_target_amount(self.name, self.tframe.month.value)

    def __str__(self) -> str:
        current = entry.cents_to_dollars(self.current_total())
        goal = entry.cents_to_dollars(self.goal())
        return f"{self.name}: {current:.2f}/{goal:.2f}"


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