# Feature Inventory — xmltodict reimplementation

Reference: https://github.com/martinblech/xmltodict @ `6e29fba282e68631034dd2722a413b4e35276584` (post-1.0.4)
Source files referenced below are paths inside `reference/xmltodict-ref/` (the pinned clone), used only for citation — no code from them is copied into the new implementation.

Status values: `Not started`, `In progress`, `Pass`, `Fail`.

## A. Public names (module surface)

| ID | Behavior | Source | Default | Status |
|----|----------|--------|---------|--------|
| A1 | `xmltodict.parse` function exported | xmltodict.py:208 | — | Pass |
| A2 | `xmltodict.unparse` function exported | xmltodict.py:567 | — | Pass |
| A3 | `xmltodict.ParsingInterrupted` exception class exported | xmltodict.py:11 | — | Pass |
| A4 | Package importable as `import xmltodict` | pyproject.toml:39 | — | Pass |
| A5 | CLI invocable as `python -m xmltodict <item_depth>` | xmltodict.py:635 (`__main__`) | — | Pass |

## B. `parse()` keyword arguments

| ID | Behavior | Source | Default | Status |
|----|----------|--------|---------|--------|
| B1 | `xml_input` — str, file-like (duck-typed via `read` attr), or generator of chunks | xmltodict.py:208, 348-377 | required | Pass |
| B2 | `encoding=None` — character encoding; when `xml_input` is `str`, encode to bytes with `encoding or 'utf-8'` before feeding expat | xmltodict.py:208, 348-350 | `None` | Pass |
| B3 | `expat=expat` — alternate parser module (e.g. `defusedexpat.pyexpat`), must expose `ParserCreate` | xmltodict.py:208, 353 | `xml.parsers.expat` | Pass |
| B4 | `process_namespaces=False` — expand namespace URIs into names | xmltodict.py:208, 351-356 | `False` | Pass |
| B5 | `namespace_separator=':'` — separator between namespace URI and local name (only active when `process_namespaces=True`) | xmltodict.py:208, 346, 351-356 | `':'` | Pass |
| B6 | `disable_entities=True` — any entity declaration (internal, external SYSTEM/PUBLIC, parameter) raises `ValueError("entities are disabled")`; DOCTYPE itself is still allowed | xmltodict.py:365-369 | `True` | Pass |
| B7 | `process_comments=False` — when `True`, registers a comment handler and comments are added to the output under `comment_key` | xmltodict.py:208, 362-363, 161-164 | `False` | Pass |
| B8 | `item_depth=0` — depth at which `item_callback` fires (streaming mode when > 0) | xmltodict.py:18, 37, 86, 109 | `0` | Pass |
| B9 | `item_callback=lambda *args: True` — called with `(path, item)`; falsy return raises `ParsingInterrupted` | xmltodict.py:19, 123-125 | `lambda *args: True` | Pass |
| B10 | `xml_attribs=True` — include attributes in output dict under `attr_prefix`; `False` ignores them | xmltodict.py:20, 88-101 | `True` | Pass |
| B11 | `attr_prefix='@'` — prefix for attribute keys (also used to build `@xmlns` entries) | xmltodict.py:21, 83, 91 | `'@'` | Pass |
| B12 | `cdata_key='#text'` — dict key for element text content | xmltodict.py:22, 119, 146 | `'#text'` | Pass |
| B13 | `force_cdata=False` — bool / tuple-of-names / callable `(path, key, value) -> bool`; forces an empty dict wrapper so text is stored under `cdata_key` instead of as a bare string | xmltodict.py:23, 187-205 | `False` | Pass |
| B14 | `cdata_separator=''` — string used to join adjacent text (character data) chunks | xmltodict.py:24, 110-111, 136-137 | `''` | Pass |
| B15 | `postprocessor=None` — `(path, key, value) -> (key, value)` or `None`; `None` return drops the entry; applied to attribute entries and to `push_data` calls (child elements, text, comments) | xmltodict.py:25, 92-97, 166-171 | `None` | Pass |
| B16 | `dict_constructor=dict` — constructor used for every dict built during parsing | xmltodict.py:26, 49, 72, 82, 98, 116, 173 | `dict` | Pass |
| B17 | `strip_whitespace=True` — strip leading/trailing whitespace from text nodes (and, per B19, from comment text); `False` preserves text exactly, and an all-whitespace node becomes `None` only when stripped to empty | xmltodict.py:27, 113-114, 140-141 | `True` | Pass |
| B18 | `namespaces=None` — mapping (or `None`) from namespace URI to short prefix or `None`-to-skip; applied to element and attribute names when `process_namespaces=True` | xmltodict.py:28, 48, 53-67 | `None` | Pass |
| B19 | `force_list=None` — bool / tuple-of-keys / callable `(path[:-1], key, value) -> bool`; forces a list even for a single occurrence, applied in `push_data` before any existing-key branch | xmltodict.py:30, 181-195 | `None` | Pass |
| B20 | `comment_key='#comment'` — dict key used for comment text when `process_comments=True` | xmltodict.py:31, 161-164 | `'#comment'` | Pass |
| B21 | Return value: `item_depth == 0` → the parsed document (type from `dict_constructor`); `item_depth > 0` → `None` (streaming items only reach `item_callback`, never accumulated into a parent) | xmltodict.py:378, 104-134 | — | Pass |
| B22 | Namespace declarations on an element are collected and attached as `attrs['xmlns']` (a dict of prefix→URI, `''` key for default namespace) on that element, consumed once per element | xmltodict.py:74-76, 80-84 | — | Pass |
| B23 | `force_cdata` for an element with *no* text still only wraps when text is present (`data and self._should_force_cdata(...)`) — an empty/all-whitespace element is not force-wrapped | xmltodict.py:113-116 | — | Pass |

## C. `unparse()` keyword arguments

| ID | Behavior | Source | Default | Status |
|----|----------|--------|---------|--------|
| C1 | `input_dict` — dict to serialize; must have exactly one non-comment top-level key when `full_document=True` | xmltodict.py:567, 606-623 | required | Pass |
| C2 | `output=None` — file-like object to write to; `None` returns a `str` | xmltodict.py:567, 596-599, 626-632 | `None` | Pass |
| C3 | `encoding='utf-8'` — output document encoding | xmltodict.py:567, 601-603 | `'utf-8'` | Pass |
| C4 | `bytes_errors='replace'` — error handler passed to `.decode()` when converting `bytes`/`bytearray`/`memoryview` scalar values to text; invalid handler name raises `ValueError(f"Invalid bytes_errors handler: {bytes_errors}")` | xmltodict.py:590-594, 381-392 | `'replace'` | Pass |
| C5 | `full_document=True` — emit XML declaration (`startDocument`/`endDocument`); also enables the single-root and multiple-roots checks | xmltodict.py:567, 604, 608-624, 495-496 | `True` | Pass |
| C6 | `short_empty_elements=False` — use `<tag/>` for empty elements | xmltodict.py:567, 600-603 | `False` | Pass |
| C7 | `attr_prefix='@'` — prefix identifying a dict key as an attribute | xmltodict.py:450, 516 | `'@'` | Pass |
| C8 | `cdata_key='#text'` — dict key identifying text content | xmltodict.py:450, 465, 510 | `'#text'` | Pass |
| C9 | `pretty=False` — pretty-print with indentation/newlines | xmltodict.py:450, 477-481, 540-544, 554-558 | `False` | Pass |
| C10 | `indent='\t'` — indentation unit; `str` used literally, `int` means that many spaces | xmltodict.py:450, 467, 538 | `'\t'` | Pass |
| C11 | `newl='\n'` — newline string used in pretty mode | xmltodict.py:450 | `'\n'` | Pass |
| C12 | `namespace_separator=':'` — separator used when collapsing namespaced keys via `namespaces` | xmltodict.py:450, 433-447 | `':'` | Pass |
| C13 | `namespaces=None` — mapping URI→short prefix (or `None` to skip) for keys of the form `ns<sep>name`, including `@xmlns` children | xmltodict.py:450, 433-447, 484 | `None` | Pass |
| C14 | `expand_iter=None` — tag name used to wrap each item of a nested non-str/dict iterable; breaks roundtripping when set | xmltodict.py:450, 499-501 | `None` | Pass |
| C15 | `comment_key='#comment'` — dict key whose value(s) are emitted as XML comments instead of child elements | xmltodict.py:567, 465-482 | `'#comment'` | Pass |
| C16 | Scalar-to-string conversion: `str` unchanged; `bool` → `"true"`/`"false"`; `bytes`/`bytearray`/`memoryview` decoded with `encoding`/`bytes_errors`; anything else via `str()` | xmltodict.py:381-392 | — | Pass |
| C17 | A value that is `None` renders as an empty element (`{}`) | xmltodict.py:497-498 | — | Pass |
| C18 | A non-dict, non-str value that is iterable (and not bytes-like) with no `expand_iter` is converted to its `str()` directly (no per-item child tags) | xmltodict.py:499-503 | — | Pass |
| C19 | A list value at a given key produces one sibling element per item; `full_document=True` and `depth==0` with more than one item raises `ValueError('document with multiple roots')` | xmltodict.py:494-496 | — | Pass |
| C20 | Empty list value for a child key is skipped entirely — no element emitted (`{"a": []}` → no `<a>`) | xmltodict.py:535-536 | — | Pass |
| C21 | `cdata_key` entry with value `None` emits no text node at all (distinct from `''`) | xmltodict.py:511-512 | — | Pass |
| C22 | Attribute entry (`attr_prefix`-prefixed key) with value `None` is emitted as `''` | xmltodict.py:527-528 | — | Pass |
| C23 | `@xmlns` dict child is special-cased: each `k: v` becomes an `xmlns` or `xmlns:k` attribute; keys validated as attribute names; `v is None` → `''` | xmltodict.py:519-526 | — | Pass |
| C24 | `unparse` must have exactly one root key when `full_document=True`; zero roots (empty dict, or only a `comment_key` entry) or more than one non-comment key raises `ValueError("Document must have exactly one root.")` | xmltodict.py:606-623 | — | Pass |
| C25 | Return type: `str` when `output=None`; otherwise writes to `output` and returns `None` | xmltodict.py:596-599, 626-632 | — | Pass |
| C26 | `preprocessor=None` — undocumented in README but real: `(key, value) -> (key, value)` or `None`; called on every element's own `(key, value)` (not on attributes, and not on `comment_key` entries), before name validation; `None` return drops that node and its subtree entirely. Discovered and confirmed by running the reference, not from docs. | xmltodict.py:450, 465, 484-489 | `None` | Pass |

## D. Security requirements (Section 7)

| ID | Behavior | Source | Default | Status |
|----|----------|--------|---------|--------|
| D1 | `disable_entities=True` (default): internal entity declarations raise | xmltodict.py:365-369 | — | Pass |
| D2 | `disable_entities=True`: external `SYSTEM`/`PUBLIC` entity declarations raise the same way (same handler covers all `EntityDeclHandler` calls) | xmltodict.py:365-369 | — | Pass |
| D3 | `disable_entities=True`: parameter entity declarations raise the same way | xmltodict.py:365-369 | — | Pass |
| D4 | `disable_entities=True`: DOCTYPE declaration alone (no entity decl) is allowed, does not raise | xmltodict.py:365-369 (absence of a `StartDoctypeDeclHandler` override); CHANGELOG v1.0.2 | — | Pass |
| D5 | `parse` never fetches external resources (no `ExternalEntityRefHandler` is registered, and entity declarations are forbidden before any reference could resolve) | xmltodict.py:353-369 | — | Pass |
| D6 | `unparse` escapes `&`, `<`, `>`, and quotes in text and attribute values (delegated to `xml.sax.saxutils.XMLGenerator`) | xmltodict.py:5, 561-564 | — | Pass |
| D7 | `unparse` rejects element/attribute names containing `<`, `>`, `/`, `"`, `'`, `=`, or whitespace, or starting with `?`/`!`, or non-`str`, with `ValueError` | xmltodict.py:395-415 | — | Pass |
| D8 | `unparse` validates comment text: non-`str`/non-UTF8-`bytes` input, `--` substring, or a trailing `-` all raise `ValueError` | xmltodict.py:418-430 | — | Pass |

## E. Command-line interface (Section 8)

| ID | Behavior | Source | Default | Status |
|----|----------|--------|---------|--------|
| E1 | `python -m xmltodict <item_depth>` reads XML from `stdin` (binary) | xmltodict.py:635-658 | — | Pass |
| E2 | Writes `marshal`-encoded `(path, item)` tuples to `stdout` (binary) for every item reaching `item_depth` | xmltodict.py:645-647 | — | Pass |
| E3 | When `item_depth == 0`, after parsing, manually emits one `([], root)` record (the whole document), since the streaming callback never fires during a depth-0 parse | xmltodict.py:649-655 | — | Pass |
| E4 | `dict_constructor=dict` is forced for the CLI regardless of any other default | xmltodict.py:653 | — | Pass |
| E5 | Missing or extra CLI argument: `(item_depth,) = sys.argv[1:]` raises uncaught `ValueError` → Python's default traceback + exit code 1 | xmltodict.py:642 | — | Pass |
| E6 | Non-integer CLI argument: `int(item_depth)` raises uncaught `ValueError` → traceback + exit code 1 | xmltodict.py:643 | — | Pass |
| E7 | `KeyboardInterrupt` during parsing is swallowed (clean exit, no traceback) | xmltodict.py:656-657 | — | Pass |

## F. Exceptions

| ID | Behavior | Source | Status |
|----|----------|--------|--------|
| F1 | `xmltodict.ParsingInterrupted` — raised by `parse` when `item_callback` returns a falsy value | xmltodict.py:11-12, 123-125 | Pass |
| F2 | `expat.ExpatError` (from the `expat` module passed in, default `xml.parsers.expat`) on malformed XML (unclosed/mismatched tags, multiple roots in input XML, invalid bytes/characters) — propagated, not wrapped | xmltodict.py:353-377 | Pass |
| F3 | `ValueError("entities are disabled")` — any entity declaration when `disable_entities=True` | xmltodict.py:365-369 | Pass |
| F4 | `ValueError` from `unparse` name/comment/bytes_errors/root-count validation (see C4, C24, D7, D8 for exact messages) | xmltodict.py:395-430, 590-594, 606-623 | Pass |

## G. Out of scope / explicitly not reproduced

None yet identified. Anything found during implementation that looks like a reference bug must be recorded as a **proposed deviation** in `PROJECT_STATUS.md` and the pinned behavior implemented as-is until a decision is made (Section 5 of the guidelines).

## Review note

This inventory was built from the pinned commit's `README.md`, `AGENTS.md`, `SECURITY.md`, `CHANGELOG.md`, and the module docstrings/source of `xmltodict.py` (read for behavioral understanding only, per Section 1). The reference's `tests/` directory was not opened, read, or searched. Ambiguous points (exact return value in streaming mode, exact force_list/force_cdata callable argument shapes, CLI exit behavior, the `preprocessor` kwarg, the `namespaces`/`namespace_separator` kwargs of `unparse`) were resolved or discovered by running the installed reference package directly (Section 6b), not assumed from source reading or memory.

Every row above is `Pass`: implemented independently in `src/xmltodict/`, exercised by the independent test suite (`tests/`, values sourced from docs or the running reference — see each test's comment) and by the differential harness (`parity/`), which as of the date in `PROJECT_STATUS.md` ran 1,113 differential cases (including a 1,000-document/dict seeded random corpus) plus 7 CLI cases against the installed reference with zero unexplained mismatches. See `PROJECT_STATUS.md` for the full parity report and harness command output.

Two README doctests were found to be **stale relative to the pinned commit** while writing the independent tests (confirmed by running the reference, not assumed): the "Namespace support" examples don't show the `@xmlns` attribute that namespace declarations actually produce (added for v1.0.0 per CHANGELOG, after that README text was last written). This project follows the pinned commit's actual installed behavior (per Section 2: the installed reference wins over stale docs), not the outdated doctest text. This is a reference documentation bug, not a deviation by this project.
