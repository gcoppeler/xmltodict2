"""Independent unit tests for xmltodict.parse.

Every expected value below is sourced either from the pinned reference's
README.md ("doc:") or from running the installed reference package
("observed from reference:" — see PROJECT_STATUS.md for how the oracle venv
was set up). None come from this project's own implementation.
"""

import collections

import pytest

import xmltodict


def test_basic_structure_and_attributes():
    # doc: README.md top example
    doc = xmltodict.parse(
        """
         <mydocument has="an attribute">
           <and>
             <many>elements</many>
             <many>more elements</many>
           </and>
           <plus a="complex">
             element as well
           </plus>
         </mydocument>
         """
    )
    assert doc == {
        "mydocument": {
            "@has": "an attribute",
            "and": {"many": ["elements", "more elements"]},
            "plus": {"@a": "complex", "#text": "element as well"},
        }
    }


def test_return_type_default_is_plain_dict():
    # observed from reference: type(xmltodict.parse('<a/>')) is dict
    doc = xmltodict.parse("<a/>")
    assert type(doc["a"]) is not dict or isinstance(doc, dict)
    assert type(doc) is dict


def test_process_namespaces_expands_uris():
    # README.md "Namespace support" shows this example without an `@xmlns`
    # entry, but running it against the pinned reference shows the README
    # doctest is stale: v1.0.0 (see CHANGELOG) started attaching namespace
    # declarations as `@xmlns` on the declaring element, and the README
    # wasn't updated. Per Section 2 of the guidelines, the installed
    # reference wins over the (stale) doc; this is observed-from-reference.
    xml = """
    <root xmlns="http://defaultns.com/"
          xmlns:a="http://a.com/"
          xmlns:b="http://b.com/">
      <x>1</x>
      <a:y>2</a:y>
      <b:z>3</b:z>
    </root>
    """
    assert xmltodict.parse(xml, process_namespaces=True) == {
        "http://defaultns.com/:root": {
            "@xmlns": {
                "": "http://defaultns.com/",
                "a": "http://a.com/",
                "b": "http://b.com/",
            },
            "http://defaultns.com/:x": "1",
            "http://a.com/:y": "2",
            "http://b.com/:z": "3",
        }
    }


def test_process_namespaces_with_collapse_and_skip():
    # observed from reference (see note on test_process_namespaces_expands_uris
    # above: the README's version of this example is stale, missing `@xmlns`)
    xml = """
    <root xmlns="http://defaultns.com/"
          xmlns:a="http://a.com/"
          xmlns:b="http://b.com/">
      <x>1</x>
      <a:y>2</a:y>
      <b:z>3</b:z>
    </root>
    """
    namespaces = {
        "http://defaultns.com/": None,
        "http://a.com/": "ns_a",
    }
    assert xmltodict.parse(xml, process_namespaces=True, namespaces=namespaces) == {
        "root": {
            # the @xmlns value is the raw prefix->URI map, unaffected by the
            # `namespaces` collapse/skip mapping (observed from reference:
            # only element/attribute *names* go through that mapping).
            "@xmlns": {
                "": "http://defaultns.com/",
                "a": "http://a.com/",
                "b": "http://b.com/",
            },
            "x": "1",
            "ns_a:y": "2",
            "http://b.com/:z": "3",
        },
    }


def test_streaming_item_callback_receives_path_and_item():
    # doc: README.md "Streaming mode" / parse() docstring example.
    # Note (observed from reference): `path` is the handler's own live list,
    # mutated in place as parsing continues -- a callback that wants to keep
    # it after returning must copy it (`list(path)`), as this test does;
    # storing the reference itself would show every entry as `[]` once
    # parsing finishes and every element has closed.
    seen = []

    def handle(path, item):
        seen.append((list(path), item))
        return True

    xmltodict.parse(
        """
        <a prop="x">
          <b>1</b>
          <b>2</b>
        </a>""",
        item_depth=2,
        item_callback=handle,
    )
    assert seen == [
        ([("a", {"prop": "x"}), ("b", None)], "1"),
        ([("a", {"prop": "x"}), ("b", None)], "2"),
    ]


def test_streaming_returns_none():
    # observed from reference: parse(..., item_depth=1, item_callback=lambda *a: True) is None
    result = xmltodict.parse("<a><b>1</b></a>", item_depth=1, item_callback=lambda *a: True)
    assert result is None


def test_item_callback_false_raises_parsing_interrupted():
    # doc: parse() docstring: "If the callback's return value is false-ish,
    # parsing will be stopped with the ParsingInterrupted exception."
    with pytest.raises(xmltodict.ParsingInterrupted):
        xmltodict.parse("<a><b>1</b><b>2</b></a>", item_depth=1, item_callback=lambda *a: False)


def test_postprocessor_can_rename_key_and_change_value():
    # doc: parse() docstring postprocessor example
    def postprocessor(path, key, value):
        try:
            return key + ":int", int(value)
        except (ValueError, TypeError):
            return key, value

    result = xmltodict.parse("<a><b>1</b><b>2</b><b>x</b></a>", postprocessor=postprocessor)
    assert result == {"a": {"b:int": [1, 2], "b": "x"}}


def test_force_list_with_tuple():
    # doc: parse() docstring force_list example
    xml = """
    <servers>
      <server>
        <name>host1</name>
        <os>Linux</os>
        <interfaces>
          <interface>
            <name>em0</name>
            <ip_address>10.0.0.1</ip_address>
          </interface>
        </interfaces>
      </server>
    </servers>
    """
    result = xmltodict.parse(xml, force_list=("interface",))
    assert result == {
        "servers": {
            "server": {
                "name": "host1",
                "os": "Linux",
                "interfaces": {"interface": [{"name": "em0", "ip_address": "10.0.0.1"}]},
            }
        }
    }


def test_force_cdata_selective_tuple():
    # doc: README.md "Selective force_cdata"
    xml = "<a><b>data1</b><c>data2</c><d>data3</d></a>"
    assert xmltodict.parse(xml, force_cdata=("b", "d")) == {
        "a": {"b": {"#text": "data1"}, "c": "data2", "d": {"#text": "data3"}}
    }


def test_force_cdata_true_wraps_everything():
    # doc: README.md "Selective force_cdata"
    xml = "<a><b>data1</b><c>data2</c><d>data3</d></a>"
    assert xmltodict.parse(xml, force_cdata=True) == {
        "a": {"b": {"#text": "data1"}, "c": {"#text": "data2"}, "d": {"#text": "data3"}}
    }


def test_force_cdata_callable():
    # doc: README.md "Selective force_cdata"
    xml = "<a><b>data1</b><c>data2</c><d>data3</d></a>"

    def should_force_cdata(path, key, value):
        return key in ["b", "d"] and len(value) > 4

    assert xmltodict.parse(xml, force_cdata=should_force_cdata) == {
        "a": {"b": {"#text": "data1"}, "c": "data2", "d": {"#text": "data3"}}
    }


def test_force_list_selective_tuple_and_callable():
    # doc: README.md "Selective force_list"
    xml = "<a><b>data1</b><b>data2</b><c>data3</c></a>"
    assert xmltodict.parse(xml, force_list=("b",)) == {"a": {"b": ["data1", "data2"], "c": "data3"}}

    def should_force_list(path, key, value):
        return key in ["b"] and isinstance(value, str)

    assert xmltodict.parse(xml, force_list=should_force_list) == {"a": {"b": ["data1", "data2"], "c": "data3"}}


def test_force_list_true_forces_every_level():
    # doc: README.md "Selective force_list"
    xml = "<a><b>data1</b><b>data2</b><c>data3</c></a>"
    assert xmltodict.parse(xml, force_list=True) == {"a": [{"b": ["data1", "data2"], "c": ["data3"]}]}


def test_force_cdata_does_not_wrap_an_empty_element():
    # observed from reference: force_cdata only wraps when text is actually present
    assert xmltodict.parse("<a><b></b></a>", force_cdata=True) == {"a": {"b": None}}


def test_xml_attribs_false_ignores_attributes():
    # observed from reference: parse('<a p="1"><b>1</b></a>', xml_attribs=False)
    assert xmltodict.parse('<a p="1"><b>1</b></a>', xml_attribs=False) == {"a": {"b": "1"}}


def test_custom_attr_prefix_and_cdata_key():
    # observed from reference
    assert xmltodict.parse('<a p="1">hi</a>', attr_prefix="attr_", cdata_key="#value") == {
        "a": {"attr_p": "1", "#value": "hi"}
    }


def test_cdata_separator_joins_adjacent_text():
    # observed from reference: text split by a child element is joined with cdata_separator
    assert xmltodict.parse("<a>one<b/>two</a>", cdata_separator=" ") == {"a": {"#text": "one two", "b": None}}


def test_dict_constructor_ordereddict():
    # doc: README.md API reference `dict_constructor=dict`
    result = xmltodict.parse('<a z="1" y="2"/>', dict_constructor=collections.OrderedDict)
    assert isinstance(result, collections.OrderedDict)
    assert isinstance(result["a"], collections.OrderedDict)
    assert list(result["a"].items()) == [("@z", "1"), ("@y", "2")]


def test_strip_whitespace_true_collapses_to_none():
    # observed from reference: parse('<a>   </a>') == {'a': None}
    assert xmltodict.parse("<a>   </a>") == {"a": None}


def test_strip_whitespace_false_preserves_text():
    # observed from reference: parse('<a>   </a>', strip_whitespace=False) == {'a': '   '}
    assert xmltodict.parse("<a>   </a>", strip_whitespace=False) == {"a": "   "}


def test_process_comments_adds_comment_key():
    # doc: parse() docstring process_comments example
    xml = """<a>
      <b>
        <!-- b comment -->
        <c>
            <!-- c comment -->
            1
        </c>
        <d>2</d>
      </b>
    </a>"""
    result = xmltodict.parse(xml, process_comments=True)
    assert result == {
        "a": {
            "b": {
                "#comment": "b comment",
                "c": {"#comment": "c comment", "#text": "1"},
                "d": "2",
            },
        },
    }


def test_disable_entities_default_blocks_entity_declarations():
    # observed from reference: any entity declaration raises ValueError("entities are disabled")
    with pytest.raises(ValueError, match="entities are disabled"):
        xmltodict.parse('<!DOCTYPE a [<!ENTITY x "hi">]><a>&x;</a>')


def test_disable_entities_default_allows_bare_doctype():
    # observed from reference (CHANGELOG v1.0.2: "allow DOCTYPE with disable_entities=True")
    assert xmltodict.parse("<!DOCTYPE root><root>hi</root>") == {"root": "hi"}


def test_disable_entities_false_allows_internal_entity_expansion():
    # observed from reference
    result = xmltodict.parse('<!DOCTYPE a [<!ENTITY x "hi">]><a>&x;</a>', disable_entities=False)
    assert result == {"a": "hi"}


def test_malformed_xml_raises_expat_error():
    import xml.parsers.expat

    with pytest.raises(xml.parsers.expat.ExpatError):
        xmltodict.parse("<a><b>1</a>")


def test_generator_input():
    # doc: parse() docstring: "xml_input can ... be ... a generator of strings"
    def chunks():
        yield b"<a>"
        yield b"1"
        yield b"</a>"

    assert xmltodict.parse(chunks()) == {"a": "1"}


def test_file_like_input():
    import io

    assert xmltodict.parse(io.BytesIO(b"<a>from a file</a>")) == {"a": "from a file"}
