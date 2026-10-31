"""XML -> dict parsing, built on top of `xml.parsers.expat`.

Internal design notes (see PROJECT_STATUS.md "Architectural decisions" for
the full writeup): parsing state lives in `_TreeBuilder`, one `_Scope` per
XML element currently "in progress". A scope is pushed once parsing reaches
`item_depth` and popped when that element closes; an element that closes
exactly at `item_depth` is handed to `item_callback` and then discarded
rather than attached to its parent, which is what keeps streaming mode's
memory use flat.
"""

from inspect import isgenerator
from xml.parsers import expat as _default_expat

from ._errors import ParsingInterrupted

__all__ = ["parse", "ParsingInterrupted"]


def _default_item_callback(*_args):
    return True


class _Scope:
    """One element's in-progress result: its node (dict or None) and text."""

    __slots__ = ("node", "text")

    def __init__(self, node=None):
        self.node = node
        self.text = []


class _TreeBuilder:
    def __init__(
        self,
        item_depth,
        item_callback,
        xml_attribs,
        attr_prefix,
        cdata_key,
        force_cdata,
        cdata_separator,
        postprocessor,
        dict_constructor,
        strip_whitespace,
        namespace_separator,
        namespaces,
        force_list,
        comment_key,
    ):
        self._path = []
        self._scope_stack = []
        self._current = _Scope()
        self._pending_namespaces = {}

        self._item_depth = item_depth
        self._item_callback = item_callback
        self._xml_attribs = xml_attribs
        self._attr_prefix = attr_prefix
        self._cdata_key = cdata_key
        self._force_cdata = force_cdata
        self._cdata_separator = cdata_separator
        self._postprocessor = postprocessor
        self._dict_constructor = dict_constructor
        self._strip_whitespace = strip_whitespace
        self._namespace_separator = namespace_separator
        self._namespaces = namespaces
        self._force_list = force_list
        self._comment_key = comment_key

    @property
    def result(self):
        return self._current.node

    # -- expat callbacks ---------------------------------------------------

    def start_namespace_decl(self, prefix, uri):
        self._pending_namespaces[prefix or ""] = uri

    def start_element(self, raw_name, raw_attrs):
        name = self._resolve_name(raw_name)
        attrs = self._attrs_to_dict(raw_attrs)
        if self._pending_namespaces:
            if not attrs:
                attrs = self._dict_constructor()
            attrs["xmlns"] = self._pending_namespaces
            self._pending_namespaces = {}
        self._path.append((name, attrs or None))

        if len(self._path) < self._item_depth:
            return

        self._scope_stack.append(self._current)
        if self._xml_attribs:
            entries = []
            for key, value in attrs.items():
                attr_key = self._attr_prefix + self._resolve_name(key)
                if self._postprocessor is not None:
                    entry = self._postprocessor(self._path, attr_key, value)
                else:
                    entry = (attr_key, value)
                if entry:
                    entries.append(entry)
            own_attrs = self._dict_constructor(entries)
        else:
            own_attrs = None
        self._current = _Scope(own_attrs or None)

    def end_element(self, raw_name):
        name = self._resolve_name(raw_name)

        if len(self._path) == self._item_depth:
            text = self._collected_text()
            own_node = self._current.node
            if self._strip_whitespace and text:
                text = text.strip() or None
            if text and own_node is None and self._wants_force_cdata(name, text):
                own_node = self._dict_constructor()
            if own_node is not None:
                emitted = self._attach(own_node, self._cdata_key, text) if text else own_node
            else:
                emitted = text

            if not self._item_callback(self._path, emitted):
                raise ParsingInterrupted

            self._current = self._scope_stack.pop() if self._scope_stack else _Scope()
            self._path.pop()
            return

        if self._scope_stack:
            text = self._collected_text()
            own_node = self._current.node
            self._current = self._scope_stack.pop()
            if self._strip_whitespace and text:
                text = text.strip() or None
            if text and own_node is None and self._wants_force_cdata(name, text):
                own_node = self._dict_constructor()
            if own_node is not None:
                if text:
                    own_node = self._attach(own_node, self._cdata_key, text)
                self._current.node = self._attach(self._current.node, name, own_node)
            else:
                self._current.node = self._attach(self._current.node, name, text)
        else:
            self._current = _Scope()
        self._path.pop()

    def characters(self, data):
        self._current.text.append(data)

    def add_comment(self, data):
        if self._strip_whitespace:
            data = data.strip()
        self._current.node = self._attach(self._current.node, self._comment_key, data)

    # -- helpers -------------------------------------------------------------

    def _collected_text(self):
        if not self._current.text:
            return None
        return self._cdata_separator.join(self._current.text)

    def _attach(self, node, key, value):
        if self._postprocessor is not None:
            result = self._postprocessor(self._path, key, value)
            if result is None:
                return node
            key, value = result
        if node is None:
            node = self._dict_constructor()
        if key in node:
            existing = node[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                node[key] = [existing, value]
        else:
            node[key] = [value] if self._wants_force_list(key, value) else value
        return node

    def _wants_force_list(self, key, value):
        return self._wants(self._force_list, key, value)

    def _wants_force_cdata(self, key, value):
        return self._wants(self._force_cdata, key, value)

    def _wants(self, selector, key, value):
        if not selector:
            return False
        if isinstance(selector, bool):
            return selector
        try:
            return key in selector
        except TypeError:
            return selector(self._path[:-1], key, value)

    def _resolve_name(self, full_name):
        if self._namespaces is None:
            return full_name
        split_at = full_name.rfind(self._namespace_separator)
        if split_at == -1:
            return full_name
        namespace, local = full_name[:split_at], full_name[split_at + 1 :]
        try:
            # Indexing (not `.get`) is deliberate: a `defaultdict` namespace
            # mapping is documented to supply a fallback via its factory,
            # which only `__getitem__` triggers (observed from the reference).
            short = self._namespaces[namespace]
        except KeyError:
            short = namespace
        if not short:
            return local
        return self._namespace_separator.join((short, local))

    def _attrs_to_dict(self, raw_attrs):
        if isinstance(raw_attrs, dict):
            return raw_attrs
        pairs = {}
        values = iter(raw_attrs)
        for attr_name in values:
            pairs[attr_name] = next(values)
        return self._dict_constructor(pairs)


def parse(
    xml_input,
    encoding=None,
    expat=_default_expat,
    process_namespaces=False,
    namespace_separator=":",
    disable_entities=True,
    process_comments=False,
    *,
    item_depth=0,
    item_callback=_default_item_callback,
    xml_attribs=True,
    attr_prefix="@",
    cdata_key="#text",
    force_cdata=False,
    cdata_separator="",
    postprocessor=None,
    dict_constructor=dict,
    strip_whitespace=True,
    namespaces=None,
    force_list=None,
    comment_key="#comment",
):
    """Parse `xml_input` (str, file-like, or generator of chunks) into a dict.

    See README.md for the full parameter reference; defaults and accepted
    forms mirror the pinned xmltodict release this package replaces.
    """
    builder = _TreeBuilder(
        item_depth=item_depth,
        item_callback=item_callback,
        xml_attribs=xml_attribs,
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        force_cdata=force_cdata,
        cdata_separator=cdata_separator,
        postprocessor=postprocessor,
        dict_constructor=dict_constructor,
        strip_whitespace=strip_whitespace,
        namespace_separator=namespace_separator,
        namespaces=namespaces,
        force_list=force_list,
        comment_key=comment_key,
    )

    if isinstance(xml_input, str):
        encoding = encoding or "utf-8"
        xml_input = xml_input.encode(encoding)

    parser_namespace_sep = namespace_separator if process_namespaces else None
    parser = expat.ParserCreate(encoding, parser_namespace_sep)
    parser.ordered_attributes = True
    parser.buffer_text = True
    parser.StartNamespaceDeclHandler = builder.start_namespace_decl
    parser.StartElementHandler = builder.start_element
    parser.EndElementHandler = builder.end_element
    parser.CharacterDataHandler = builder.characters
    if process_comments:
        parser.CommentHandler = builder.add_comment
    if disable_entities:

        def _reject_entity_declaration(*_args, **_kwargs):
            raise ValueError("entities are disabled")

        parser.EntityDeclHandler = _reject_entity_declaration

    if hasattr(xml_input, "read"):
        parser.ParseFile(xml_input)
    elif isgenerator(xml_input):
        for chunk in xml_input:
            parser.Parse(chunk, False)
        parser.Parse(b"", True)
    else:
        parser.Parse(xml_input, True)

    return builder.result
