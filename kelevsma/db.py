from __future__ import annotations

import sqlite3
import typing
import kelevsma


SHORTCUTS = "shortcuts"


def format_iter(iter:typing.Iterable) -> str:
    """Format an iterable to be used in an SQL query."""
    iter = [f"'{x}'" if  type(x) is str else x for x in iter]
    return f"({', '.join(iter)})"


def run_query(query:str) -> sqlite3.Cursor | None:
    """Execute an SQL query"""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as e:
        kelevsma.error("Database error")
    else:
        connection.commit()
        return cursor


def run_select_query(query:str) -> list[tuple|None]:
    """Run an SQL SELECT Query."""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        items = cursor.fetchall()
    except sqlite3.Error as e:
        kelevsma.error(f"Database error")
    else:
        return items


def delete_row_by_id(table_name:str, id:int) -> sqlite3.Cursor | None:
    """Delete a row from the database by its id."""
    return run_query(f"DELETE FROM {table_name} WHERE id = {id}")


def delete_row_by_value(table_name:str, fields:tuple, values:tuple) -> sqlite3.Cursor | None:
    """Delete a row from the database by specified values."""
    values = [f"'{v}'" if type(v) is str else v for v in values]
    pairs = [f"{f} = {v}" for f, v in zip(fields, values)]
    query = f"""
    DELETE FROM {table_name}
    WHERE {' AND '.join(pairs)}
    """

    return run_query(query)


def insert_row(table_name:str, fields:tuple, values:tuple) -> sqlite3.Cursor | None:
    """Inserts a row into the database, given the table, fields, and values."""
    query = f"""
    INSERT INTO {table_name} {format_iter(fields)}
    VALUES {format_iter(values)}
    """

    return run_query(query)


def update_row(table_name:str, id:int, fields:tuple, values:tuple) -> sqlite3.Cursor | None:
    """Updates a row in the database."""
    values = [f"'{v}'" if type(v) is str else v for v in values]
    pairs = [f"{f} = {v}" for f, v in zip(fields, values)]
    query = f"""
    UPDATE {table_name} 
    SET {", ".join(pairs)}
    WHERE id = {id}
    """

    return run_query(query)


def select_shortcuts() -> dict:
    """Select and return shortcuts as dict."""
    query = f"""
    SELECT shortform, full
    FROM {SHORTCUTS}
    """
    tuples = run_select_query(query)
    return {k:v for k, v in tuples}


shortcuts_table_query = f"""
CREATE TABLE IF NOT EXISTS {SHORTCUTS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shortform TEXT NOT NULL,
    full TEXT NOT NULL
);"""


try:
    connection = sqlite3.connect("records.db")
except sqlite3.Error:
    kelevsma.error("Database connection error.")
    quit()

run_query(shortcuts_table_query)
