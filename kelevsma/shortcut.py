from . import db, command


def select_all() -> dict:
    """Select and return all shortcuts."""
    tuples = db.select_rows(db.SHORTCUTS)
    if tuples:
        return {f:v for id,f,v in tuples}
    return {}


def select(short:str) -> tuple:
    """Return a shortcut from the database."""
    tuples = db.select_rows(db.SHORTCUTS, shortform=short)
    return tuples[0]


def insert(short:str, full:str) -> None:
    """Insert a new shortcut into the db."""
    fields = ("shortform", "full")
    values = (short, full)
    db.insert_row(db.SHORTCUTS, fields, values)
    command.set_shortcuts(select_all())


def delete(short:str) -> None:
    """Delete a shortcut from the db."""
    fields = ("shortform",)
    values = (short,)
    db.delete_row_by_value(db.SHORTCUTS, fields, values)
    command.set_shortcuts(select_all())
