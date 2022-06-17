from . import db

def select_all() -> dict:
    """Select and return all shortcuts."""
    return db.select_shortcuts()


def select(short:str) -> dict:
    """Return a shortcut from the database."""


def insert(short:str, full:str) -> None:
    """Insert a new shortcut into the db."""
    fields = ("shortform", "full")
    values = (short, full)
    
    db.insert_row(db.SHORTCUTS, fields, values)


def delete(short:str) -> None:
    """Delete a shortcut from the db."""
    fields = ("shortform",)
    values = (short,)
    db.delete_row_by_value(db.SHORTCUTS, fields, values)
