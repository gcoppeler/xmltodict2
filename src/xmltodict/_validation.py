"""Name and comment-text validation shared by the unparse path.

These checks exist purely to keep attacker-controlled dict keys/values from
escaping their XML tag or attribute context (see SECURITY notes in
PROJECT_STATUS.md). The accepted/rejected character sets and the exact
`ValueError` text below are part of this project's observable contract and
were derived by running the pinned reference's `unparse()` on each case, not
by reading its validation source.
"""

_ILLEGAL_NAME_SUBSTRINGS = ("<", ">", "/", '"', "'", "=")


def validate_xml_name(name, kind):
    """Raise ValueError if `name` cannot be used as an element/attribute name."""
    if not isinstance(name, str):
        raise ValueError(f"{kind} name must be a string")
    if name.startswith("?") or name.startswith("!"):
        raise ValueError(f'Invalid {kind} name: cannot start with "?" or "!"')
    if "<" in name or ">" in name:
        raise ValueError(f'Invalid {kind} name: "<" or ">" not allowed')
    if "/" in name:
        raise ValueError(f'Invalid {kind} name: "/" not allowed')
    if '"' in name or "'" in name:
        raise ValueError(f"Invalid {kind} name: quotes not allowed")
    if "=" in name:
        raise ValueError(f'Invalid {kind} name: "=" not allowed')
    if any(ch.isspace() for ch in name):
        raise ValueError(f"Invalid {kind} name: whitespace not allowed")


def validate_comment_text(text):
    """Check a comment's already-stringified text before emitting `<!--text-->`.

    Every comment value reaches this point only after going through the same
    scalar-to-string conversion used for text/attribute values (observed from
    the reference: `unparse(..., comment_key=...)` happily accepts ints,
    bools, and non-UTF-8 bytes, converting them instead of rejecting them).
    So only the two checks below are ever observably reachable; raise on
    either.
    """
    if "--" in text:
        raise ValueError("Comment text cannot contain '--'")
    if text.endswith("-"):
        raise ValueError("Comment text cannot end with '-'")
    return text
