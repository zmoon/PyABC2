"""
Python ABC notation tools
"""

__version__ = "0.1.0-dev"

from .note import Key, Note
from .parse import Tune, _load_abcjs_if_in_jupyter
from .pitch import Pitch, PitchClass

__all__ = (
    "Key",
    "Note",
    "Pitch",
    "PitchClass",
    "Tune",
)

_load_abcjs_if_in_jupyter()
