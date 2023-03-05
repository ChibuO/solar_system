from src.can.row import Row
from sqlite3.dbapi2 import Cursor

def create_table(row: Row, cursor: Cursor) -> None:
    columns = "(timestamp REAL,\n" \
              + ",\n".join(f"{k} {'REAL' if v.is_averaged else 'INT'}" for k, v in row.signals.items()) \
              + ")"
    print(columns);
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {row.name}\n" + columns
    )


def insert_row(row: Row, cursor: Cursor) -> None:
    qmarks = f"(?, " + ", ".join("?" for _ in row.signals.values()) + ")"
    vals = [row.timestamp] + [v.value for v in row.signals.values()]
    cursor.execute(f"INSERT INTO {row.name} VALUES\n" + qmarks, vals)
