from __future__ import annotations

import config
import kelevsma.db as kdb


ENTRIES = "entries"
TARGETS = "targets"
TARGET_INSTANCES = "target_instances"


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
        query += f" AND targets.name in {kdb.format_iter(targets)}"

    return kdb.run_select_query(query)


def select_targets(name:str) -> list:
    """Construct a query to select targets."""
    query = f"SELECT * FROM {TARGETS}"
    if name:
        query += f" WHERE name = '{name}'"
        
    return kdb.run_select_query(query)


def sum_target(target_id:int, tframe:config.TimeFrame) -> int:
    """Sum entries with a specified target in a time period."""
    tframe_str = tframe.iso_format()
    query = f"""
    SELECT SUM(amount) 
    FROM {ENTRIES} 
    WHERE date LIKE '{tframe_str}' AND target = {target_id}
    """
    sum_amount = kdb.run_select_query(query)[0][0]
    return sum_amount if sum_amount else 0


def select_target_instance(target_id:int, tframe:config.TimeFrame) -> tuple | None:
    """Returns a single target instance or an entire year of instances."""
    query = f"""
    SELECT * 
    FROM {TARGET_INSTANCES}
    WHERE target = {target_id} 
        AND year = {tframe.year} 
        AND month = {tframe.month.value}
    """
    if result := kdb.run_select_query(query):
        return result


def select_target_instances_year(target_id:int, year:int) -> list:
    """Select the target instances for a whole year."""
    query = f"""
    SELECT * 
    FROM {TARGET_INSTANCES}
    WHERE target = {target_id} AND year = {year}
    """

    return kdb.run_select_query(query)


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


kdb.run_query(target_table_query)
kdb.run_query(target_instances_table_query)
kdb.run_query(entries_table_query)

# logging.info(run_select_query("SELECT * FROM target_instances"))
# logging.info(run_select_query("SELECT * FROM targets"))
# logging.info(run_select_query("SELECT * FROM entries"))