# Project Status

**Reference:** https://github.com/martinblech/xmltodict @ `6e29fba282e68631034dd2722a413b4e35276584`
**Last updated:** 2026-10-31

## Current phase

Phase 5 (Validation) substantially complete; effectively through Phase 6 (Delivery) for the scope implemented so far. See "Next recommended development steps" for what's left before this can be called fully done per Section 10.

## Feature inventory review

`FEATURE_INVENTORY.md` was built from the pinned commit's `README.md`, `AGENTS.md`, `SECURITY.md`, `CHANGELOG.md`, and `xmltodict.py`'s docstrings/source (read for understanding only, never copied; `tests/` was never opened). It was then checked line-by-line against the running reference package (`.venv-reference`) rather than trusted as written — this caught several things source-reading alone would have missed or gotten wrong:

- `unparse` accepts an **undocumented** `preprocessor` kwarg (not in README's API reference) — confirmed by calling it against the reference, now implemented and covered (inventory row C26).
- `unparse` also accepts **undocumented** `namespaces`/`namespace_separator` kwargs, and their key-matching direction (match against the literal string before the last separator, not necessarily a real namespace URI) was reverse-engineered by probing the oracle, not guessed from source.
- The README's two "Namespace support" doctest examples are **stale**: the pinned commit's actual parse output includes an `@xmlns` attribute (added for v1.0.0 per CHANGELOG) that those examples don't show. Implemented to match the running reference, not the stale doc text (Section 2: installed reference wins over docs when they disagree).
- `parse`'s namespace-URI lookup uses direct dict indexing (`namespaces[uri]`, catching `KeyError`) so a `collections.defaultdict` namespace mapping's factory fires — `unparse`'s equivalent lookup uses `.get()` instead, which does *not* trigger a defaultdict factory. This asymmetry is real (confirmed against the oracle) and is implemented faithfully in both directions.
- `item_callback`'s `path` argument is the parser's own live list, mutated in place as parsing continues — not a per-call snapshot. A callback that stores it for later use (rather than using it synchronously, as the README's doctest does) must copy it. Documented in `tests/test_parse.py` and worth calling out to anyone using this package's streaming mode.

## Architectural decisions

- **Package, not single file.** The reference is one `xmltodict.py`; this project is a package (`src/xmltodict/`) with `_parsing.py`, `_unparsing.py`, `_validation.py`, `_errors.py`, `__main__.py`. `python -m xmltodict` is served by `__main__.py` rather than an `if __name__ == '__main__':` block in the main module — same CLI behavior, independent internal layout (Section 3 permits this).
- **Parsing state**: a `_TreeBuilder` class drives `xml.parsers.expat` callbacks, tracking a `_Scope` (node + accumulated text) per in-progress element and a stack of saved parent scopes, pushed once parsing depth reaches `item_depth` and popped when that element closes. An element that closes exactly at `item_depth` is handed to `item_callback` and dropped rather than attached to its parent — this is what keeps streaming mode's memory flat, and had to be traced carefully from the reference's source (not copied) to get the exact stack-save/restore semantics right, especially for `item_depth > 0`.
- **Unparsing**: a recursive `_emit` function walks the input dict, splitting each node into (text, attributes, children) before writing through a thin `_CommentCapableGenerator` subclass of `xml.sax.saxutils.XMLGenerator` (reused rather than reimplemented, since it's exactly where the reference also gets its escaping behavior from — Section 4's "standard library only" plus Section 5's "same output text... byte for byte" effectively require using it).
- **Exact-text requirements**: every `ValueError` message raised by this project (name validation, comment validation, root-count checks, `bytes_errors` validation, "entities are disabled") is a literal match of the reference's, because Section 6b requires exception *messages* to match, not just classes. These are being matched as observable output text, like `unparse`'s XML output — not as copied implementation.
- **`ParsingInterrupted.__module__` is reassigned to `"xmltodict"`** in `_errors.py` so that introspection (`type(exc).__module__`) matches the reference's single-file layout, where the class has no private submodule to actually live in.

## Completed functionality (harness status)

All rows of `FEATURE_INVENTORY.md` (sections A–F, including the undocumented C26 `preprocessor`) are implemented and marked `Pass`. Evidence:

- **Differential harness** (`parity/run_harness.py`, run 2026-10-31): 1,113 differential cases (keyword matrix at default/non-default values for every `parse`/`unparse` kwarg; edge inputs; malformed inputs; hostile/security inputs; a 1,000-document/dict seeded random corpus, seed `20261031`) plus 7 CLI cases. **Zero unexplained mismatches.**
- **Independent test suite** (`tests/`, run 2026-10-31): 87 tests, all passing, expected values sourced from README.md or from running the installed reference (each test says which).

```
$ .venv/bin/python parity/run_harness.py
Ran 1113 differential cases.
All differential cases matched.
Ran 7 CLI cases.
All CLI cases matched.

HARNESS PASSED: zero unexplained mismatches.

$ .venv/bin/pytest tests/ -q
87 passed in 0.34s
```

### Final parity report (Definition of Done item 8)

| Inventory section | Rows | Status | Evidence |
|---|---|---|---|
| A — public names | A1–A5 | Pass | imports used throughout `tests/`; CLI cases in harness + `tests/test_cli.py` |
| B — `parse()` kwargs | B1–B23 | Pass | harness `parse/*` cases, `edge/*` cases, random corpus; `tests/test_parse.py` |
| C — `unparse()` kwargs | C1–C26 | Pass | harness `unparse/*` cases, `edge/*`, `malformed/*`, random corpus; `tests/test_unparse.py` |
| D — security | D1–D8 | Pass | harness `hostile/*` cases; `tests/test_security.py` |
| E — CLI | E1–E7 | Pass | harness CLI cases; `tests/test_cli.py` |
| F — exceptions | F1–F4 | Pass | harness exception-class/message comparison on every raising case above; `tests/test_security.py`, `tests/test_parse.py`, `tests/test_unparse.py` |

## Outstanding functionality

None known against the pinned commit's documented and oracle-observed behavior. Two areas got comparatively thin dedicated coverage and would benefit from more cases if this continues:

- `expat=` with a genuinely different parser module (only tested with the stdlib module passed explicitly, since no alternate like `defusedexpat` is installed/available here).
- Non-ASCII, non-UTF-8 output encodings for `unparse` (only `utf-8` and `iso-8859-1` exercised).

## Proposed deviations awaiting the user's decision

None. Everything implemented matches observed reference behavior, including two things that look like reference quirks but are documented or load-bearing enough not to unilaterally "fix": the README's two stale namespace doctest examples (implemented to match actual behavior, not the stale text — see above, not a deviation from the reference itself) and the fact that `attr_prefix`/namespace `.strip()` lets a non-default `namespace_separator` like `"|"` produce element names containing characters not valid in XML (reference has the identical gap; see `SECURITY.md`'s CVE-2025-9375 discussion and `parity/cases.py`'s `unparse/namespace_separator/custom` case).

## Known issues and limitations

- Mirrors the reference's own documented limitations (README "Note: xmltodict aims to cover the common 90% of cases..."): mixed-content ordering and attribute order aren't guaranteed preserved beyond insertion order, and multiple top-level comments aren't guaranteed to round-trip in exact order.
- Element/attribute name validation only blocks the specific characters listed in Section 7 (`<`, `>`, `/`, quotes, `=`, whitespace, leading `?`/`!`), not the full XML `Name` grammar — same as the reference (see SECURITY.md).

## Test and harness results (dated)

- 2026-10-31: differential harness, 1,113 + 7 CLI cases, 0 mismatches.
- 2026-10-31: independent test suite, 87/87 passing.

## Next recommended development steps

1. If more confidence is wanted before calling this "done": add `expat=` coverage with an actual alternate parser module, and more `unparse(..., encoding=...)` variety (UTF-16, ASCII-with-errors).
2. Grow the random corpus size/shape (e.g. deliberately bias it toward attribute-heavy or deeply-nested documents) if any future change touches the parsing/unparsing core.
3. Nothing is blocking; re-run `parity/run_harness.py` and `pytest tests/` after any future change, per Section 9's incremental-development requirement.
