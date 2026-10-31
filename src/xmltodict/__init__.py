"""Convert between XML and Python dicts.

Independent reimplementation of the public interface of `xmltodict`
(https://github.com/martinblech/xmltodict), pinned at commit
6e29fba282e68631034dd2722a413b4e35276584. See PROJECT_STATUS.md for scope
and parity status.
"""

from ._errors import ParsingInterrupted
from ._parsing import parse
from ._unparsing import unparse

__all__ = ["parse", "unparse", "ParsingInterrupted"]
