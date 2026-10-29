from pathlib import Path
import sqlite3
import time

COLUMNS = {"event_id", "channel", "converted"}

def readonly_connection(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("Database does not exist. Run src/bootstrap_db.py first.")
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only = ON")
    con.enable_load_extension(False)
    return con

def execute_query(path, sql, max_rows=10000, timeout=2.0):
    con = readonly_connection(path)
    deadline = time.monotonic() + timeout
    def authorize(action, arg1, arg2, _db, _source):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and arg1 == "marketing_events" and arg2 in COLUMNS:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    con.set_authorizer(authorize)
    con.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    try:
        cursor = con.execute(sql)
        if [d[0] for d in cursor.description] != ["event_id", "channel", "converted"]:
            raise ValueError("Query must return event_id, channel, converted in that order.")
        rows = cursor.fetchmany(max_rows + 1)
        if len(rows) > max_rows:
            raise ValueError("Result exceeds the row limit; no truncated analysis was produced.")
        return [dict(zip(("event_id", "channel", "converted"), row)) for row in rows]
    except sqlite3.Error as exc:
        raise ValueError("Database rejected the query or exceeded its execution budget.") from exc
    finally:
        con.close()
