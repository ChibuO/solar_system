# database stuff for contacts list
# this is the code that only interacts with the user

import time
import can_db
from digi.xbee.devices import XBeeDevice
import json

import sqlite3
from pathlib import Path

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from typing import cast

from definitions import PROJECT_ROOT
from can.row import Row
from can.stats import mock_value
from can.util import add_dbc_file

PORT = "COM9"
BAUD_RATE = 9600

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("src", "resources", "mppt.dbc")))
add_dbc_file(db, Path(PROJECT_ROOT).joinpath("src", "resources", "motor_controller.dbc"))


# open database connection
connection = can_db.connect('cantest_data.db')
can_db.create_tables(connection)

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

for row in rows:
    can_db.create_table(row, cursor)

def main():

    device = XBeeDevice(PORT, BAUD_RATE)


    try:
        device.open()

        def data_receive_callback(xbee_message):
            # xbee_message.remote_device.get_64bit_addr()
            print(xbee_message.data.decode())
            r = Row.deserialize(xbee_message.data.decode())
            can_db.insert_row(r, cursor)
            #json_row = json.loads(xbee_message.data)
            #print("\n", json_row, "\n" )
            #can_db.add_row(connection, json_row)

        device.add_data_received_callback(data_receive_callback)

        print("Waiting for data...\n")
        input()
        time.sleep(1000)

    finally:
        if device is not None and device.is_open():
            device.close()


if __name__ == '__main__':
    main()
