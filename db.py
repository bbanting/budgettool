from __future__ import annotations

import sqlite3
import logging

import kelevsma.display as display
import config
import target
import entry


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


def make_select_query_entry(tframe:config.TimeFrame, category:str, targets:list) -> str:
    """Construct a query to select entries in the database."""
    if tframe.month == 0:
        tframe_str = tframe.iso_format(month=False)
    else:
        tframe_str = tframe.iso_format()

    query = f"""
    SELECT e.id, e.date, e.amount, targets.name, e.note 
    FROM entries AS e
    INNER JOIN targets ON e.target = targets.id
    WHERE date LIKE '{tframe_str}'"""

    if category == "expense":
        query += " AND amount < 0"
    elif category == "income":
        query += " AND amount >= 0"

    if targets:
        targets_str = [f"'{t}'" for t in targets]
        query += f" AND target in ({', '.join(targets_str)})"

    return query


def make_insert_query_entry(entry:entry.Entry) -> str:
    """Construct a query to insert an entry into the database."""
    fields = "(date, amount, target, note)"
    if entry.id:
        fields = "(id, date, amount, target, note)"
    
    return f"INSERT INTO entries {fields} VALUES {entry.to_tuple()}"


def make_delete_query_entry(entry_id:int) -> str:
    """Construct a query to delete an entry from the database."""
    return f"DELETE FROM entries where id = {entry_id}"


def make_update_query_entry(new_entry_values:tuple) -> str:
    """Construct a query to overwrite an entry in the database. The
    new entry has the same id and the entry it's replacing.
    """
    new_entry_values = new_entry_values.to_tuple()
    query = """
    UPDATE entries 
    SET date = '{}', amount = {}, target = '{}', note = '{}'
    WHERE id = {id}
    """
    query = query.format(id=new_entry_values[0], *new_entry_values[1:])

    return query


def make_select_query_target(name:str) -> str:
    """Construct a query to select targets."""
    query = "SELECT * FROM targets"
    if name:
        query += f" WHERE name = '{name}'"
    return query


def make_insert_query_target(id:int, name:str, default_amt:int) -> str:
    """Construct a query to insert a target."""
    fields = "(name, default_amt)"
    values = (name, default_amt)
    if id:
        fields = "(id, name, default_amt)"
        values = (id, name, default_amt)
    query = f"""
    INSERT INTO targets {fields}
    VALUES {values}
    """
    return query


def make_delete_query_target(target_id:int) -> str:
    """Construct a query to delete a target."""
    query = f"DELETE FROM targets WHERE id = {target_id}"
    return query


def make_update_query_target(id:int, name:str, default_amt:int) -> str:
    """Construct a query to overwrite a target in the database."""
    new_values = []
    if name:
        new_values.append(f"{name=}")
    if default_amt is not None:
        new_values.append(f"{default_amt=}")

    query = f"""
    UPDATE targets 
    SET {', '.join(new_values)}
    WHERE id = {id}
    """
    return query


def sum_target(target:str, tframe:config.TimeFrame) -> int:
    """Sum entries with a particular target in a time period."""
    tframe_str = tframe.iso_format()
    query = f"""
    SELECT SUM(amount) 
    FROM entries 
    WHERE date LIKE '{tframe_str}' AND target = {target.id}
    """
    sum_amount = run_select_query(query)[0][0]
    return sum_amount if sum_amount else 0


def set_target_instance(target:target.Target, amount:int, tframe:config.TimeFrame) -> None:
    """Set the target amount for the specified month. Start by deleting the 
    old target instance if it exists, and then insert a new one.
    """
    del_query = f"""
    DELETE FROM target_instances
    WHERE target={target.id} AND year={tframe.year} AND month={tframe.month.value}
    """

    insert_query = f"""
    INSERT INTO target_instances (target, amount, year, month)
    VALUES ({target.id}, {amount}, {tframe.year}, {tframe.month.value})
    """

    if not run_query(del_query): # If error in query, don't run next query
        return
    run_query(insert_query)


def get_target_default(name:str) -> int:
    """Get the default goal for a target."""
    query = f"SELECT default_amt FROM targets WHERE name = '{name}'"
    return run_select_query(query)[0][0]


def get_target_instance(target:target.Target, tframe:config.TimeFrame) -> list:
    """Returns the amounts for the target instances."""
    query = f"""
    SELECT amount 
    FROM target_instances
    WHERE target = '{target.id}' AND year = {tframe.year}
    """
    if tframe.month != 0:
        query += f" AND month = {tframe.month.value}"

    return run_select_query(query)


def get_target_goal(target:target.Target, tframe:config.TimeFrame) -> int:
    """Returns the sum of the amounts for a target for either one
    month or an entire year. If target instances don't exist for
    a particular month, the default amount is returned.
    """
    expected_n_values = 12
    if tframe.month != 0:
        expected_n_values = 1

    result = get_target_instance(target, tframe)
    if diff := (expected_n_values - len(result)):
        return sum([x[0] for x in result]) + (target.default_amt * diff)
    return sum([x[0] for x in result])


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

# logging.info(run_select_query("SELECT * FROM target_instances"))
# logging.info(run_select_query("SELECT * FROM targets"))
# logging.info(run_select_query("SELECT * FROM entries"))