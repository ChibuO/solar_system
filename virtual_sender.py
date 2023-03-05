from typing import cast
from time import sleep
from threading import Thread, Lock
from pathlib import Path
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from digi.xbee.devices import XBeeDevice

from definitions import PROJECT_ROOT
from src.can.row import Row
from src.can.stats import mock_value
from src.can.util import add_dbc_file

VIRTUAL_BUS_NAME = "virtbus"

PORT = "COM9"
BAUD_RATE = 9600
REMOTE_NODE_ID = "Node"

xbee = XBeeDevice(PORT, BAUD_RATE)
xbee.open()

remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
assert remote is not None

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("src", "resources", "mppt.dbc")))
add_dbc_file(db, Path(PROJECT_ROOT).joinpath("src", "resources", "motor_controller.dbc"))

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

def device_worker(bus: can.ThreadSafeBus, my_messages:  list[cantools.database.Message]) -> None:
    """
    Constantly sends messages on the `bus`.
    """
    while True:
        for msg in my_messages:
            d = {}
            for sig in msg.signals:
                d[sig.name] = mock_value(msg.senders[0], sig.name)
            data = msg.encode(d)
            bus.send(can.Message(arbitration_id=msg.frame_id, data=data))
            sleep(0.1)
        sleep(1)

def row_accumulator_worker(bus: can.ThreadSafeBus):
    """
    Observes messages sent on the `bus` and accumulates them in a global row.
    """
    while True:
        msg = bus.recv()
        assert msg is not None
        
        i = next(i for i, r in enumerate(rows) if r.owns(msg, db))
        decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
        with row_lock:
            for k, v in decoded.items():
                rows[i].signals[k].update(v)

def sender_worker():
    """
    Serializes rows into the queue.
    """
    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
            xbee.send_data(remote, row.serialize())

if __name__ == "__main__":
    dev_threads: list[Thread] = []
    for i, node in enumerate(db.nodes):
        dev_threads.append(Thread(target=device_worker,
                                  args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"),
                                        [msg for msg in db.messages if msg.senders[0] == db.nodes[i].name]),
                                  daemon=True))

    # Create a thread to read of the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype='virtual'),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    # Start all the threads.
    for thread in dev_threads:
        thread.start()

    accumulator.start()
    sender.start()

    sender.join()
