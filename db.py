from __future__ import annotations

import sqlite3
import logging
import typing

import kelevsma.display as display
import config
import target


ENTRIES = "entries"
TARGETS = "targets"
TARGET_INSTANCES = "target_instances"


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
        logging.info(e)
        display.error("Database error")
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
        logging.info(e)
        display.error(f"Database error")
    else:
        return items


def delete_row(table_name:str, id:int) -> None:
    """Delete a row from the database by its id."""
    run_query(f"DELETE FROM {table_name} where id = {id}")


def insert_row(table_name:str, fields:tuple, values:tuple) -> None:
    """Inserts a row into the database, given the table, fields, and values."""
    query = f"""
    INSERT INTO {table_name} {format_iter(fields)}
    VALUES {format_iter(values)}
    """
    run_query(query)


def update_row(table_name:str, id:int, fields:tuple, values:tuple) -> None:
    """Updates a row in the database."""
    values = [f"'{v}'" if type(v) is str else v for v in values]
    pairs = [f"{f} = {v}" for f, v in zip(fields, values)]
    query = f"""
    UPDATE {table_name} 
    SET {", ".join(pairs)}
    WHERE id = {id}
    """

    run_query(query)


def select_entries(tframe:config.TimeFrame, category:str, targets:list) -> list:
    """Select and return a list of entries from the database."""
    if tframe.month == 0:
        tframe_str = tframe.iso_format(month=False)
    else:
        tframe_str = tframe.iso_format()

    query = f"""
    SELECT e.id, e.date, e.amount, targets.name, e.note 
    FROM {ENTRIES} AS e
    INNER JOIN targets ON e.target = targets.id
    WHERE date LIKE '{tframe_str}'"""

    if category == "expense":
        query += " AND amount < 0"
    elif category == "income":
        query += " AND amount >= 0"

    if targets:
        query += f" AND targets.name in {format_iter(targets)}"

    return run_select_query(query)


def select_targets(name:str) -> list:
    """Construct a query to select targets."""
    query = f"SELECT * FROM {TARGETS}"
    if name:
        query += f" WHERE name = '{name}'"
    return run_select_query(query)


def sum_target(target:str, tframe:config.TimeFrame) -> int:
    """Sum entries with a particular target in a time period."""
    tframe_str = tframe.iso_format()
    query = f"""
    SELECT SUM(amount) 
    FROM {ENTRIES} 
    WHERE date LIKE '{tframe_str}' AND target = {target.id}
    """
    sum_amount = run_select_query(query)[0][0]
    return sum_amount if sum_amount else 0


def set_target_instance(target_id:int, amount:int, tframe:config.TimeFrame) -> None:
    """Set the target amount for the specified month. Start by deleting the 
    old target instance if it exists, and then insert a new one.
    """
    del_query = f"""
    DELETE FROM {TARGET_INSTANCES}
    WHERE target={target_id} AND year={tframe.year} AND month={tframe.month.value}
    """

    insert_query = f"""
    INSERT INTO {TARGET_INSTANCES} (target, amount, year, month)
    VALUES ({target_id}, {amount}, {tframe.year}, {tframe.month.value})
    """

    if not run_query(del_query): # If error in query, don't run next query
        return
    run_query(insert_query)


def select_target_instance_amount(target_id:int, tframe:config.TimeFrame, use_default:bool=True) -> int:
    """Returns the amount for a target instances or an entire year."""
    query = f"""
    SELECT amount 
    FROM {TARGET_INSTANCES}
    WHERE target = {target_id} AND year = {tframe.year}
    """
    expected_n_values = 12
    if tframe.month != 0:
        query += f" AND month = {tframe.month.value}"
        expected_n_values = 1

    result = [x[0] for x in run_select_query(query)]
    diff = expected_n_values - len(result)
    if diff and use_default:
        return sum(result) + (target.default_amt * diff)
    return sum(result)


target_table_query = f"""
CREATE TABLE IF NOT EXISTS {TARGETS} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    default_amt INTEGER NOT NULL
);"""

target_instances_table_query = f"""
CREATE TABLE IF NOT EXISTS {TARGET_INSTANCES} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    FOREIGN KEY (target) REFERENCES target (id)
);"""

entries_table_query = f"""
CREATE TABLE IF NOT EXISTS {ENTRIES} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount INTEGER NOT NULL,
    target INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY (target) REFERENCES targets (id)
);"""


try:
    connection = sqlite3.connect("records.db")
except sqlite3.Error:
    display.error("Database connection error.")
    quit()

run_query(target_table_query)
run_query(target_instances_table_query)
run_query(entries_table_query)

# logging.info(run_select_query("SELECT * FROM target_instances"))
# logging.info(run_select_query("SELECT * FROM targets"))
# logging.info(run_select_query("SELECT * FROM entries"))