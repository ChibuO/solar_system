from __future__ import annotations
from typing import Optional
from datetime import datetime
import json

from cantools.database.can.database import Database
import can.message

class CanValue:
    """
    CAN value object, which manages the common occurence of getting multiple
    values for a specific CAN tag before wanting to send it, through simple averaging.
    """
    def __init__(self: CanValue, value: Optional[float] = None, is_averaged = True) -> None:
        self.value: Optional[int | float] = value
        self.is_averaged = is_averaged
        if value is None:
            self.n = 0
        else:
            self.n = 1

    def fetch(self: CanValue) -> Optional[int | float]:
        if not self.is_averaged:
            return self.value
        else:
            self.n = 0
            save = self.value
            self.value = None
            return save

    def update(self: CanValue, value):
        if not self.is_averaged:
            self.value = value
        else:
            if self.value is None:
                self.value = 0
            self.value = (self.n * self.value + value) / (self.n + 1)
            self.n += 1


class Row:
    def __init__(self, sigdef: Database | dict[str, CanValue], name: str, timestamp: Optional[float] = None) -> None:
        self.timestamp: Optional[float] = timestamp
        self.name = name
        self.signals: dict[str, CanValue] = {}

        if isinstance(sigdef, Database):
            for msg in [msg for msg in sigdef.messages if name in msg.senders]:
                for signal in msg.signals:
                    self.signals[signal.name] = CanValue(is_averaged=signal.is_float)
        elif isinstance(sigdef, dict):
            self.signals = sigdef
        else:
            raise Exception("Unknown type of sigdef: {type(sigdef)}")

    def owns(self, msg: can.message.Message, db: Database) -> bool:
        senders = next(m for m in db.messages if m.frame_id == msg.arbitration_id).senders
        return self.name in senders

    def stamp(self):
        self.timestamp = datetime.now().timestamp()

    def serialize(self, indent=None) -> str:
        if self.timestamp is None:
            raise Exception("Attempt to serialize unstamped row")
        return json.dumps({
            "timestamp": self.timestamp,
            "name"     : self.name,
            "signals"  : {k: v.fetch() for k, v in self.signals.items()}
        }, indent=indent)

    @classmethod
    def deserialize(cls, s: str) -> Row:
        d = json.loads(s)
        signals = {k: CanValue(v) for k, v in d["signals"].items()}
        return Row(signals, d["name"], timestamp=d["timestamp"])
