"""Independent unit tests for xmltodict.unparse.

Expected values sourced from README.md ("doc:") or from running the
installed reference package ("observed from reference:").
"""

import pytest

import xmltodict


def test_basic_roundtrip_shape():
    # doc: README.md "Roundtripping"
    mydict = {
        "response": {
            "status": "good",
            "last_updated": "2014-02-16T23:10:12Z",
        }
    }
    assert xmltodict.unparse(mydict, pretty=True) == (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<response>\n"
        "\t<status>good</status>\n"
        "\t<last_updated>2014-02-16T23:10:12Z</last_updated>\n"
        "</response>"
    )


def test_attr_prefix_and_cdata_key_defaults():
    # doc: README.md "Roundtripping"
    mydict = {"text": {"@color": "red", "@stroke": "2", "#text": "This is a test"}}
    result = xmltodict.unparse(mydict, pretty=True)
    assert result.startswith('<?xml version="1.0" encoding="utf-8"?>\n<text')
    assert 'stroke="2"' in result and 'color="red"' in result
    assert result.endswith("This is a test</text>")


def test_list_without_parent_key_becomes_string():
    # doc: README.md "Roundtripping" (nested list, no expand_iter)
    mydict = {"line": {"points": [[1, 5], [2, 6]]}}
    result = xmltodict.unparse(mydict, pretty=True)
    assert "<points>[1, 5]</points>" in result
    assert "<points>[2, 6]</points>" in result


def test_expand_iter_gives_tags_to_nested_list_items():
    # doc: README.md "Roundtripping"
    mydict = {"line": {"points": [[1, 5], [2, 6]]}}
    result = xmltodict.unparse(mydict, pretty=True, expand_iter="coord")
    assert "<coord>1</coord>" in result
    assert "<coord>5</coord>" in result


def test_empty_list_value_is_skipped_entirely():
    # doc: README.md API reference note: "{'a': []} produces no <a>
    # element" -- confirmed against the reference, this really does mean no
    # element at all (not even a self-closing one), leaving just the
    # declaration, even though 'a' still counts as the one root key.
    assert xmltodict.unparse({"a": []}) == '<?xml version="1.0" encoding="utf-8"?>\n'


def test_empty_list_placeholder_produces_element():
    # doc: README.md API reference note on unparse()
    assert xmltodict.unparse({"a": [""]}) == '<?xml version="1.0" encoding="utf-8"?>\n<a></a>'


def test_cdata_key_none_value_emits_no_text_node():
    # observed from reference: distinct from an empty string, which would emit text
    assert xmltodict.unparse({"a": {"#text": None, "@x": "1"}}) == (
        '<?xml version="1.0" encoding="utf-8"?>\n<a x="1"></a>'
    )


def test_attribute_none_value_emits_empty_string():
    # observed from reference
    assert xmltodict.unparse({"a": {"@x": None}}) == '<?xml version="1.0" encoding="utf-8"?>\n<a x=""></a>'


def test_short_empty_elements():
    # doc: README.md API reference `short_empty_elements=False`
    assert xmltodict.unparse({"a": {"b": None}}, short_empty_elements=True) == (
        '<?xml version="1.0" encoding="utf-8"?>\n<a><b/></a>'
    )


def test_full_document_false_omits_declaration_and_allows_fragments():
    # observed from reference
    assert xmltodict.unparse({"a": 1, "b": 2}, full_document=False) == "<a>1</a><b>2</b>"


def test_full_document_true_requires_exactly_one_root():
    # observed from reference
    with pytest.raises(ValueError, match="Document must have exactly one root."):
        xmltodict.unparse({"a": 1, "b": 2})
    with pytest.raises(ValueError, match="Document must have exactly one root."):
        xmltodict.unparse({})


def test_multiple_items_at_root_raises_multiple_roots():
    # observed from reference
    with pytest.raises(ValueError, match="document with multiple roots"):
        xmltodict.unparse({"a": [1, 2]})


def test_bool_values_render_lowercase():
    # observed from reference
    assert xmltodict.unparse({"a": {"b": True, "c": False}}) == (
        '<?xml version="1.0" encoding="utf-8"?>\n<a><b>true</b><c>false</c></a>'
    )


def test_bytes_value_decoded_with_bytes_errors_policy():
    # observed from reference: default bytes_errors='replace'
    result = xmltodict.unparse({"a": {"#text": b"\xff\xfe"}})
    assert result == '<?xml version="1.0" encoding="utf-8"?>\n<a>��</a>'


def test_invalid_bytes_errors_handler_raises():
    # observed from reference
    with pytest.raises(ValueError, match="Invalid bytes_errors handler: bogus"):
        xmltodict.unparse({"a": 1}, bytes_errors="bogus")


@pytest.mark.parametrize(
    "bad_name,message",
    [
        ("a b", 'Invalid element name: whitespace not allowed'),
        ("a<b", 'Invalid element name: "<" or ">" not allowed'),
        ("a/b", 'Invalid element name: "/" not allowed'),
        ("a=b", 'Invalid element name: "=" not allowed'),
        ("?a", r'Invalid element name: cannot start with "\?" or "!"'),
        ("!a", r'Invalid element name: cannot start with "\?" or "!"'),
        (123, "element name must be a string"),
    ],
)
def test_invalid_element_names_rejected(bad_name, message):
    # observed from reference
    with pytest.raises(ValueError, match=message):
        xmltodict.unparse({bad_name: "1"})


@pytest.mark.parametrize("bad_comment", ["ok--bad", "trailing-"])
def test_invalid_comment_text_rejected(bad_comment):
    # observed from reference
    with pytest.raises(ValueError):
        xmltodict.unparse({"a": {"#comment": bad_comment, "#text": "x"}})


def test_comment_values_are_stringified_not_type_checked():
    # observed from reference: int/bool/bytes comment values are converted,
    # not rejected (see PROJECT_STATUS.md architectural notes)
    result = xmltodict.unparse({"a": {"#comment": 123, "#text": "x"}})
    assert result == '<?xml version="1.0" encoding="utf-8"?>\n<a><!--123-->x</a>'


def test_multiple_comments_render_in_order():
    # observed from reference
    result = xmltodict.unparse({"a": {"#comment": ["c1", "c2"], "#text": "x"}})
    assert result == '<?xml version="1.0" encoding="utf-8"?>\n<a><!--c1--><!--c2-->x</a>'


def test_xmlns_dict_child_emits_namespace_attributes():
    # observed from reference
    result = xmltodict.unparse({"root": {"@xmlns": {"": "http://d/", "a": "http://a/"}}})
    assert 'xmlns="http://d/"' in result
    assert 'xmlns:a="http://a/"' in result


def test_preprocessor_can_rename_and_drop_nodes():
    # observed from reference (undocumented but accepted kwarg)
    def preprocessor(key, value):
        if key == "skip":
            return None
        return key.upper(), value

    result = xmltodict.unparse({"root": {"keep": "1", "skip": "2"}}, preprocessor=preprocessor)
    assert result == '<?xml version="1.0" encoding="utf-8"?>\n<ROOT><KEEP>1</KEEP></ROOT>'


def test_namespaces_mapping_substitutes_short_prefix_in_element_key():
    # observed from reference
    result = xmltodict.unparse({"a:root": {"#text": "x"}}, namespaces={"a": "short"})
    assert result == '<?xml version="1.0" encoding="utf-8"?>\n<short:root>x</short:root>'


def test_output_param_writes_to_file_like_and_returns_none():
    import io

    buf = io.StringIO()
    result = xmltodict.unparse({"a": 1}, output=buf)
    assert result is None
    assert buf.getvalue() == '<?xml version="1.0" encoding="utf-8"?>\n<a>1</a>'
