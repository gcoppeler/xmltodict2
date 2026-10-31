"""dict -> XML serialization, built on `xml.sax.saxutils.XMLGenerator`.

Internal design notes: `_emit` walks the input dict recursively, splitting
each node into (text, attributes, child elements) before writing it.
Namespace-prefix substitution, scalar-to-string conversion, and comment
emission are their own small functions so each piece of observable
behavior has exactly one place it's implemented, independent of how the
reference project happens to be organized internally.
"""

import codecs
from io import StringIO
from xml.sax.saxutils import XMLGenerator, escape
from xml.sax.xmlreader import AttributesImpl

from ._validation import validate_comment_text, validate_xml_name

__all__ = ["unparse"]


def _stringify_scalar(value, encoding, bytes_errors):
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode(encoding, errors=bytes_errors)
    return str(value)


def _resolve_namespace_prefix(name, namespaces, namespace_separator, attr_prefix):
    if not isinstance(name, str) or not namespaces:
        return name
    try:
        namespace, local = name.rsplit(namespace_separator, 1)
    except ValueError:
        return name
    mapped = namespaces.get(namespace.strip(attr_prefix))
    if not mapped:
        return name
    prefix = attr_prefix if namespace.startswith(attr_prefix) else ""
    return f"{prefix}{mapped}{namespace_separator}{local}"


def _as_item_sequence(value):
    if not hasattr(value, "__iter__") or isinstance(value, (str, bytes, bytearray, memoryview, dict)):
        return [value]
    return value


def _normalize_item(item, cdata_key, expand_iter, encoding, bytes_errors):
    if item is None:
        item = {}
    elif not isinstance(item, (dict, str)):
        if expand_iter and hasattr(item, "__iter__") and not isinstance(item, (bytes, bytearray, memoryview)):
            item = {expand_iter: item}
        else:
            item = _stringify_scalar(item, encoding, bytes_errors)
    if isinstance(item, str):
        item = {cdata_key: item}
    return item


def _collect_attribute(raw_key, raw_value, attrs, namespaces, namespace_separator, attr_prefix, encoding, bytes_errors):
    resolved_key = _resolve_namespace_prefix(raw_key, namespaces, namespace_separator, attr_prefix)
    if resolved_key == attr_prefix + "xmlns" and isinstance(raw_value, dict):
        for ns_prefix, ns_uri in raw_value.items():
            validate_xml_name(ns_prefix, "attribute")
            attr_name = "xmlns" if not ns_prefix else f"xmlns:{ns_prefix}"
            attrs[attr_name] = "" if ns_uri is None else _stringify_scalar(ns_uri, encoding, bytes_errors)
        return
    if raw_value is None:
        value = ""
    elif isinstance(raw_value, str):
        value = raw_value
    else:
        value = _stringify_scalar(raw_value, encoding, bytes_errors)
    attr_name = resolved_key[len(attr_prefix):]
    validate_xml_name(attr_name, "attribute")
    attrs[attr_name] = value


def _write_comments(value, writer, depth, pretty, indent, newl, encoding, bytes_errors):
    values = value if isinstance(value, list) else [value]
    for raw in values:
        if raw is None:
            continue
        text = _stringify_scalar(raw, encoding, bytes_errors)
        if not text:
            continue
        if pretty:
            writer.ignorableWhitespace(depth * indent)
        writer.comment(text)
        if pretty:
            writer.ignorableWhitespace(newl)


def _emit(
    key,
    value,
    writer,
    *,
    depth,
    attr_prefix,
    cdata_key,
    preprocessor,
    pretty,
    newl,
    indent,
    namespace_separator,
    namespaces,
    full_document,
    expand_iter,
    encoding,
    bytes_errors,
    comment_key,
):
    if isinstance(key, str) and key == comment_key:
        _write_comments(value, writer, depth, pretty, indent, newl, encoding, bytes_errors)
        return

    key = _resolve_namespace_prefix(key, namespaces, namespace_separator, attr_prefix)
    if preprocessor is not None:
        result = preprocessor(key, value)
        if result is None:
            return
        key, value = result

    validate_xml_name(key, "element")

    if isinstance(indent, int):
        indent = " " * indent

    for index, raw_item in enumerate(_as_item_sequence(value)):
        if full_document and depth == 0 and index > 0:
            raise ValueError("document with multiple roots")

        node = _normalize_item(raw_item, cdata_key, expand_iter, encoding, bytes_errors)

        text_value = None
        attrs = {}
        children = []
        for child_key, child_value in node.items():
            if child_key == cdata_key:
                text_value = None if child_value is None else _stringify_scalar(child_value, encoding, bytes_errors)
                continue
            if isinstance(child_key, str) and child_key.startswith(attr_prefix):
                _collect_attribute(
                    child_key, child_value, attrs, namespaces, namespace_separator, attr_prefix, encoding, bytes_errors
                )
                continue
            if isinstance(child_value, list) and not child_value:
                continue
            children.append((child_key, child_value))

        if pretty:
            writer.ignorableWhitespace(depth * indent)
        writer.startElement(key, AttributesImpl(attrs))
        if pretty and children:
            writer.ignorableWhitespace(newl)
        for child_key, child_value in children:
            _emit(
                child_key,
                child_value,
                writer,
                depth=depth + 1,
                attr_prefix=attr_prefix,
                cdata_key=cdata_key,
                preprocessor=preprocessor,
                pretty=pretty,
                newl=newl,
                indent=indent,
                namespace_separator=namespace_separator,
                namespaces=namespaces,
                full_document=full_document,
                expand_iter=expand_iter,
                encoding=encoding,
                bytes_errors=bytes_errors,
                comment_key=comment_key,
            )
        if text_value is not None:
            writer.characters(text_value)
        if pretty and children:
            writer.ignorableWhitespace(depth * indent)
        writer.endElement(key)
        if pretty and depth:
            writer.ignorableWhitespace(newl)


class _CommentCapableGenerator(XMLGenerator):
    def comment(self, text):
        text = validate_comment_text(text)
        self._write(f"<!--{escape(text)}-->")


def unparse(
    input_dict,
    output=None,
    encoding="utf-8",
    full_document=True,
    short_empty_elements=False,
    comment_key="#comment",
    *,
    bytes_errors="replace",
    attr_prefix="@",
    cdata_key="#text",
    pretty=False,
    newl="\n",
    indent="\t",
    namespace_separator=":",
    namespaces=None,
    expand_iter=None,
    preprocessor=None,
):
    """Serialize `input_dict` to XML (reverse of `parse`).

    Returns a `str` when `output` is None, otherwise writes to `output` and
    returns None. See README.md for the full parameter reference.
    """
    try:
        codecs.lookup_error(bytes_errors)
    except LookupError as exc:
        raise ValueError(f"Invalid bytes_errors handler: {bytes_errors}") from exc

    returning_string = output is None
    sink = StringIO() if returning_string else output
    writer = _CommentCapableGenerator(sink, encoding, short_empty_elements)

    if full_document:
        writer.startDocument()

    root_seen = False
    for key, value in input_dict.items():
        if full_document and key != comment_key:
            if root_seen:
                raise ValueError("Document must have exactly one root.")
            root_seen = True
        _emit(
            key,
            value,
            writer,
            depth=0,
            attr_prefix=attr_prefix,
            cdata_key=cdata_key,
            preprocessor=preprocessor,
            pretty=pretty,
            newl=newl,
            indent=indent,
            namespace_separator=namespace_separator,
            namespaces=namespaces,
            full_document=full_document,
            expand_iter=expand_iter,
            encoding=encoding,
            bytes_errors=bytes_errors,
            comment_key=comment_key,
        )

    if full_document and not root_seen:
        raise ValueError("Document must have exactly one root.")
    if full_document:
        writer.endDocument()

    if returning_string:
        return sink.getvalue()
    return None
