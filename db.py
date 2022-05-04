from __future__ import annotations

import sqlite3
import logging

import entry
import kelevsma.display as display
import config


def make_select_query(date:config.TimeFrame, category:str, targets:list) -> str:
    """Construct a query to select entries in the database."""
    if date.month == 0:
        date = f"{date.year}-%"
    else:
        date = f"{date.year}-{str(date.month.value).zfill(2)}-%"

    query = f"SELECT * FROM entries WHERE date LIKE '{date}'"

    if category == "expense":
        query += " AND amount < 0"
    elif category == "income":
        query += " AND amount >= 0"

    if targets:
        targets_str = [f"'{t}'" for t in targets]
        query += f" AND target in ({', '.join(targets_str)})"

    return query


def make_insert_query(entry:entry.Entry) -> str:
    """Construct a query to insert an entry into the database."""
    fields = "(date, amount, target, note)"
    if entry.id:
        fields = "(id, date, amount, target, note)"
    values = entry.to_tuple()
    
    return f"INSERT INTO entries {fields} VALUES {values}"


def make_delete_query(entry:entry.Entry) -> str:
    """Construct a query to delete an entry from the database."""
    return f"DELETE FROM entries where id = {entry.id}"


def make_update_query(new_entry:entry.Entry) -> str:
    """Construct a query to overwrite an entry in the database. The
    new entry has the same id and the entry it's replacing.
    """
    new_entry = new_entry.to_tuple()
    query = \
    """
    UPDATE entries 
    SET date = '{}', amount = {}, target = '{}', note = '{}'
    WHERE id = {id}
    """
    query = query.format(id=new_entry[0], *new_entry[1:])

    return query


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


def select_entries(date:config.TimeFrame, category:str, targets:list) -> list[entry.Entry]:
    cursor = connection.cursor()
    query = make_select_query(date, category, targets)
    try:
        cursor.execute(query)
        entries = cursor.fetchall()
    except sqlite3.Error as e:
        display.error(f"Database error")
    else:
        return [entry.Entry.from_tuple(e) for e in entries]


def insert_entry(entry:entry.Entry) -> None:
    """Insert an entry into the database."""
    query = make_insert_query(entry)
    run_query(query)


def delete_entry(entry:entry.Entry) -> None:
    """Delete an entry from the database."""
    query = make_delete_query(entry)
    run_query(query)


def update_entry(entry:entry.Entry) -> None:
    """Update an entry in the database."""
    query = make_update_query(entry)
    run_query(query)


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
        return sum_amount[0]
    
    return 0


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


table_query = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount INTEGER NOT NULL,
    target TEXT NOT NULL,
    note TEXT
);"""


try:
    connection = sqlite3.connect("records.db")
except sqlite3.Error:
    display.error("Database connection error.")
    quit()

# run_query("DROP TABLE entries;")
run_query(table_query)