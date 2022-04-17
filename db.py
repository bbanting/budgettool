import sqlite3
import logging
import datetime

import entry
import display
import config


def make_select_query(date:config.TimeFrame, category:str, tags:list) -> str:
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

    for tag in tags:
        query += f" AND tags LIKE '%{tag}%'"

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


def select_entries(date:config.TimeFrame, category:str, tags:list) -> list[entry.Entry]:
    cursor = connection.cursor()
    query = make_select_query(date, category, tags)
    try:
        cursor.execute(query)
        entries = cursor.fetchall()
        logging.info(entries)
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


table_query = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount INTEGER NOT NULL,
    tags TEXT NOT NULL,
    note TEXT
);"""

connection = sqlite3.connect("records.db")
# run_query("DROP TABLE entries;")
run_query(table_query)

# entry1 = entry.Entry(0, datetime.date.today(), 5000, ["other"], "Nothing to note")
# insert_entry(entry1)

# for e in select_entries(config.TimeFrame(2022, 4), "income", ["other"]): 
#     print(e.id, e)