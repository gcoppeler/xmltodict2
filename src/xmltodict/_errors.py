"""Exception types raised by this package's public API."""


class ParsingInterrupted(Exception):
    """Raised by :func:`xmltodict.parse` when a callback asks to stop early."""


# Reported as `xmltodict.ParsingInterrupted` (not `xmltodict._errors.Parsing...`)
# by introspection (`type(exc).__module__`), matching the reference's single-file
# layout where the class has no private submodule to live in.
ParsingInterrupted.__module__ = "xmltodict"
