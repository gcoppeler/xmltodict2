"""Independent hostile-input tests for Section 7 security requirements.

Expected values observed from the installed reference package.
"""

import pytest

import xmltodict

BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<lolz>&lol2;</lolz>
"""


def test_internal_entity_declaration_blocked_by_default():
    with pytest.raises(ValueError, match="entities are disabled"):
        xmltodict.parse('<!DOCTYPE a [<!ENTITY x "hi">]><a>&x;</a>')


def test_external_system_entity_blocked_by_default():
    with pytest.raises(ValueError, match="entities are disabled"):
        xmltodict.parse('<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>')


def test_external_public_entity_blocked_by_default():
    with pytest.raises(ValueError, match="entities are disabled"):
        xmltodict.parse(
            '<!DOCTYPE a [<!ENTITY x PUBLIC "-//X//Y" "http://example.com/x.dtd">]><a>&x;</a>'
        )


def test_parameter_entity_blocked_by_default():
    with pytest.raises(ValueError, match="entities are disabled"):
        xmltodict.parse('<!DOCTYPE a [<!ENTITY % p SYSTEM "http://example.com/p.dtd">%p;]><a>1</a>')


def test_billion_laughs_blocked_by_default():
    with pytest.raises(ValueError, match="entities are disabled"):
        xmltodict.parse(BILLION_LAUGHS)


def test_bare_doctype_without_entities_is_allowed():
    assert xmltodict.parse("<!DOCTYPE root><root>hi</root>") == {"root": "hi"}


def test_unparse_escapes_special_characters_in_text():
    result = xmltodict.unparse({"a": {"#text": "A & B < C > D"}})
    assert "A &amp; B &lt; C &gt; D" in result
    assert "<C>" not in result and "A & B" not in result


def test_unparse_escapes_special_characters_in_attribute_values():
    result = xmltodict.unparse({"a": {"@x": '"><script>alert(1)</script>'}})
    # the attribute value must not be able to close the attribute or tag
    assert "<script>" not in result
    assert "&quot;" in result or "&gt;" in result


def test_unparse_rejects_element_name_with_angle_brackets():
    with pytest.raises(ValueError):
        xmltodict.unparse({"a><evil>b</evil><c a": "1"})


@pytest.mark.parametrize(
    "bad_name",
    ["a b", "a<b", "a>b", "a/b", 'a"b', "a'b", "a=b", "?a", "!a"],
)
def test_unparse_rejects_illegal_element_names(bad_name):
    with pytest.raises(ValueError):
        xmltodict.unparse({bad_name: "1"})


@pytest.mark.parametrize(
    "bad_name",
    ["a b", "a<b", "a/b", "a=b", "?a"],
)
def test_unparse_rejects_illegal_attribute_names(bad_name):
    with pytest.raises(ValueError):
        xmltodict.unparse({"root": {"@" + bad_name: "1"}})


def test_unparse_rejects_non_string_names():
    with pytest.raises(ValueError, match="element name must be a string"):
        xmltodict.unparse({123: "1"})
    # a non-string dict key that isn't recognized as an attribute (it can't
    # start with attr_prefix) is treated as a child element key instead, so
    # this also fails the *element* name check, not an attribute one.
    with pytest.raises(ValueError, match="element name must be a string"):
        xmltodict.unparse({"root": {123: "1"}})
