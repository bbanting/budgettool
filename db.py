import sqlite3
from datetime import datetime
from typing import Any, Union, List


import entry
import display


def run_query(conn:sqlite3.Connection, query:str) -> Union[None, sqlite3.Cursor]:
    """Execute an SQL query. Uses execute or executemany depending on 'value.'"""
    cursor = conn.cursor()  
    try:
        cursor.execute(query)
    except sqlite3.Error as e:
        # display.error("Database error")
        print(e)
    else:
        conn.commit()
        return cursor


def fetch(con:sqlite3.Connection, query:str) -> List[Any]:
    cursor = con.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        # display.error(f"Database error")
        print(e)


def insert_entry(entry:entry.Entry) -> int:
    """Insert an entry into the database."""
    q = f"INSERT INTO entries (date, amount, tags, note) VALUES {entry.to_tuple()}"
    cursor = run_query(connection, q)
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

entry1 = entry.Entry(datetime.now(), 5000, "other", "Nothing to note")
entry2 = entry.Entry(datetime.now(), -7000, "food", "Bought food")
insert_entry(entry1.to_tuple)
insert_entry(entry2.to_tuple)

print(fetch(connection, "SELECT * FROM entries"))