# --- Imports --- #

from collections import namedtuple


# --- SymbolTableEntry --- #

SymbolTableEntry = namedtuple("SymbolTableEntry", ["internalName", "type", "mode", "value", "alloc", "units"])