from cantools.database.can.database import Database
from cantools.typechecking import StringPathLike
from cantools.database.can.formats import dbc

def add_dbc_file(self: Database, filename: StringPathLike, encoding: str = 'cp1252') -> None:
    """
    The `add_dbc_file` method of a cantools `Database` for some reason overwrites the
    db nodes with the nodes of the added database instead of adding them to the previous
    nodes. So we patch this here
    (i.e. `self._nodes = database.nodes` -> `self._nodes += database.nodes`).
    """
    with open(filename, 'r', encoding=encoding) as fp:
        string = fp.read()
        database = dbc.load_string(string, self._strict, sort_signals=self._sort_signals) # type: ignore

        self._messages += database.messages
        self._nodes += database.nodes
        self._buses = database.buses
        self._version = database.version
        self._dbc = database.dbc
        self.refresh()
