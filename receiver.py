from typing import cast
import sqlite3
from pathlib import Path

import cantools.database
from cantools.database.can.database import Database
from digi.xbee.devices import XBeeDevice

from definitions import PROJECT_ROOT
from src.can.row import Row
from src.can.util import add_dbc_file
import src.sql

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("src", "resources", "mppt.dbc")))
add_dbc_file(db, Path(PROJECT_ROOT).joinpath("src", "resources", "motor_controller.dbc"))

PORT = "/dev/tty.usbserial-A21SPPJ6"
BAUD_RATE = 9600

xbee = XBeeDevice(PORT, BAUD_RATE)
xbee.open()

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

def callback(s: str) -> None:
    r = Row.deserialize(s)
    src.sql.insert_row(r, cursor)
    conn.commit()


if __name__ == "__main__":
    # Use the main thread to deserialize rows and update the databse
    # as if it were running on the base station
    conn   = sqlite3.connect(Path(PROJECT_ROOT).joinpath("src", "resources", "virt4.db"))
    cursor = conn.cursor()

    for row in rows:
        src.sql.create_table(row, cursor)
    conn.commit()

    xbee.add_data_received_callback(callback)

    while True:
        pass
