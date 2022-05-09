from __future__ import annotations

import sqlite3
import logging

import kelevsma.display as display
import config


def run_query(query:str) -> sqlite3.Cursor | None:
    """Execute an SQL query"""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as e:
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


def make_select_query_entry(date:config.TimeFrame, category:str, targets:list) -> str:
    """Construct a query to select entries in the database."""
    if date.month == 0:
        date = f"{date.year}-%"
    else:
        date = f"{date.year}-{str(date.month.value).zfill(2)}-%"

    query = f"""
    SELECT e.id, e.date, e.amount, targets.name, e.note 
    FROM entries AS e
    INNER JOIN targets ON e.target = targets.id
    WHERE date LIKE '{date}'"""

    if category == "expense":
        query += " AND amount < 0"
    elif category == "income":
        query += " AND amount >= 0"

    if targets:
        targets_str = [f"'{t}'" for t in targets]
        query += f" AND target in ({', '.join(targets_str)})"

    return query


def make_insert_query_entry(entry_values:tuple) -> str:
    """Construct a query to insert an entry into the database."""
    fields = "(date, amount, target, note)"
    if entry_values.id:
        fields = "(id, date, amount, target, note)"
    
    return f"INSERT INTO entries {fields} VALUES {entry_values}"


def make_delete_query_entry(entry_id:int) -> str:
    """Construct a query to delete an entry from the database."""
    return f"DELETE FROM entries where id = {entry_id}"


def make_update_query_entry(new_entry_values:tuple) -> str:
    """Construct a query to overwrite an entry in the database. The
    new entry has the same id and the entry it's replacing.
    """
    new_entry_values = new_entry_values.to_tuple()
    query = \
    """
    UPDATE entries 
    SET date = '{}', amount = {}, target = '{}', note = '{}'
    WHERE id = {id}
    """
    query = query.format(id=new_entry_values[0], *new_entry_values[1:])

    return query


def make_select_query_target() -> str:
    return "SELECT name, default_amt FROM targets"


def sum_target(target:str, date:config.TimeFrame) -> int:
    """Sum entries with a particular target in a time period."""
    date = f"{date.year}-{str(date.month.value).zfill(2)}-%"
    query = f"SELECT SUM(amount) FROM entries WHERE date LIKE '{date}' AND target = '{target}'"
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        sum_amount = cursor.fetchone()
    except sqlite3.Error as e:
        display.error(f"Database error")
    else:
        return sum_amount[0] if sum_amount[0] else 0
    

def target_instances(target_name:str) -> int:
    """Return the number of times a target is used in the database."""
    query = f"SELECT * FROM entries WHERE target = '{target_name}'"
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        entries = cursor.fetchall()
    except sqlite3.Error as e:
        display.error(f"Database error")
    else:
        return len(entries)


def set_monthly_target(target_name:str, amount:int) -> None:
    """Set the target amount for the specified month."""


# def get_target_goal_monthly(target_name:str, tframe:config.TimeFrame) -> int:
#     """Returns a monthly target from the database.
#     If no monthly target exists with the input parameters, a new one is
#     created based on the default for that target and returned.
#     """
#     query = f"""
#     SELECT SUM(amount) 
#     FROM monthlytargets 
#     WHERE name = '{target_name}' AND year = {tframe.year}
#     """
#     if tframe.month != 0:
#         query += f" AND month = {tframe.month.value}"

#     amount = run_select_query(query)[0][0]
#     if not amount:
#         default = config.get_target(target_name).default_amount
#         insert_query = f"""
#         INSERT INTO monthlytargets (name, amount, month) 
#         VALUES ('{target_name}', {default}, {month})
#         """
#         run_query(insert_query)
#         return get_target_goal_monthly(target_name, month)
    
#     return amount


def get_target_default(name:str) -> int:
    """Get the default goal for a target."""
    query = f"SELECT default FROM targets WHERE name = '{name}'"
    return run_select_query(query)[0][0]


def get_target_goal(target_name:str, tframe:config.TimeFrame) -> int:
    """Returns a target instance from the database.
    If no target instance exists with the input parameters, the 
    default for that target is returned.
    """
    expected_n_values = 12
    query = f"""
    SELECT amount 
    FROM target_instances
    WHERE name = '{target_name}' AND year = {tframe.year}
    """
    if tframe.month != 0:
        expected_n_values = 1
        query += f" AND month = {tframe.month.value}"

    result = run_select_query(query)
    if diff := (expected_n_values - len(result)):
        default = get_target_default(target_name)
        return sum([x[0][0] for x in result]) + (default * diff)
    
    return sum([x[0][0] for x in result])


target_table_query = """
CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    default_amt INTEGER NOT NULL
);"""

target_instances_table_query = """
CREATE TABLE IF NOT EXISTS target_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    FOREIGN KEY (target) REFERENCES target (id)
);"""

entries_table_query = """
CREATE TABLE IF NOT EXISTS entries (
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