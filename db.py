import sqlite3
import abc
from datetime import date
from typing import Any


import entry
import display
import config


def make_select_query(date:config.Date, category:str, tags:list) -> str:
    """Construct a query to select entries in the database."""
    if date.month == 0:
        date = f"{date.year}-%"
    else:
        date = f"{date.year}-{str(date.month.value).zfill(2)}-%"

    query = f"SELECT * FROM entries WHERE date LIKE {date}"

    if category == "expense":
        query += " AND amount < 0"
    elif category == "income":
        query += " AND amount >= 0"

    for tag in tags:
        query += f"AND tags LIKE %{tag}%"

    return query


def make_insert_query(entry:entry.Entry) -> str:
    """Construct a query to insert an entry into the database."""
    fields = "(date, amount, tags, note)"
    if entry.id:
        fields = "(id, date, amount, tags, note)"
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
    SET date = {}, amount = {}, tags = {}, note = {}
    WHERE id = {id}
    """
    query = query.format(id=new_entry[0], *new_entry[1:])

    return query


def run_query(conn:sqlite3.Connection, query:str) -> None | sqlite3.Cursor:
    """Execute an SQL query"""
    cursor = conn.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as e:
        # display.error("Database error")
        print(e)
    else:
        conn.commit()
        return cursor


def fetch(query:str) -> list[Any]:
    conn = connection
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        # display.error(f"Database error")
        print(e)


def insert_entry(entry:entry.Entry) -> int:
    """Insert an entry into the database."""
    query = make_insert_query(entry)
    cursor = run_query(connection, query)
    if not cursor: 
        return
    return cursor.lastrowid


table_query = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount INTEGER NOT NULL,
    tags TEXT NOT NULL,
    note TEXT
);"""

connection = sqlite3.connect("records.db")
run_query(connection, table_query)
# run_query(connection, "DROP TABLE entries;")

entry1 = entry.Entry(0, date.today(), 5000, ["other"], "Nothing to note")
# entry2 = entry.Entry(datetime.now(), -7000, ["food"], "Bought food")
insert_entry(entry1)
# insert_entry(entry2)

print(fetch("SELECT * FROM entries"))