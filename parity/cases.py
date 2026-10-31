"""The case matrix fed to both oracle_worker.py processes by run_harness.py.

Each case is a plain dict; `ref(name)` marks a value that oracle_worker.py
must resolve from its REGISTRY (a real function, module, or dict subclass)
rather than send over the wire as-is.
"""

import random

BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<lolz>&lol2;</lolz>
"""


def ref(name):
    return {"__ref__": name}


def parse_case(case_id, xml_input, **kwargs):
    return {"id": case_id, "op": "parse", "xml_input": xml_input, "kwargs": kwargs}


def parse_stream_case(case_id, xml_input, item_depth, stop_after=None, **kwargs):
    return {
        "id": case_id,
        "op": "parse",
        "xml_input": xml_input,
        "kwargs": {"item_depth": item_depth, **kwargs},
        "record_callback": True,
        "stop_after": stop_after,
    }


def unparse_case(case_id, input_dict, **kwargs):
    return {"id": case_id, "op": "unparse", "input_dict": input_dict, "kwargs": kwargs}


def iter_keyword_matrix_cases():
    # --- parse: each keyword at default and at representative non-default values ---
    yield parse_case("parse/defaults/simple", '<a prop="x"><b>1</b><b>2</b></a>')
    yield parse_case("parse/encoding/explicit-utf8", '<a>café</a>'.encode("utf-8"), encoding="utf-8")
    yield parse_case("parse/encoding/latin-1-bytes", '<a>café</a>'.encode("latin-1"), encoding="iso-8859-1")
    yield parse_case("parse/expat/stdlib-explicit", "<a>1</a>", expat=ref("stdlib_expat"))
    yield parse_case(
        "parse/namespaces/process_namespaces-true",
        '<root xmlns="http://defaultns.com/" xmlns:a="http://a.com/">'
        "<x>1</x><a:y>2</a:y></root>",
        process_namespaces=True,
    )
    yield parse_case(
        "parse/namespaces/collapse-and-skip",
        '<root xmlns="http://defaultns.com/" xmlns:a="http://a.com/" xmlns:b="http://b.com/">'
        "<x>1</x><a:y>2</a:y><b:z>3</b:z></root>",
        process_namespaces=True,
        namespaces={"http://defaultns.com/": None, "http://a.com/": "ns_a"},
    )
    yield parse_case(
        "parse/namespaces/custom-separator",
        '<root xmlns:a="http://a.com/"><a:y>2</a:y></root>',
        process_namespaces=True,
        namespace_separator="|",
    )
    yield parse_case("parse/disable_entities/default-doctype-ok", "<!DOCTYPE root><root>hi</root>")
    yield parse_case("parse/disable_entities/false-allows-entity", "<!DOCTYPE a [<!ENTITY x \"hi\">]><a>&x;</a>", disable_entities=False)
    yield parse_case(
        "parse/comments/process_comments-true",
        "<a><!-- c1 --><b><!-- c2 -->1</b></a>",
        process_comments=True,
    )
    yield parse_case(
        "parse/comments/custom-key-no-strip",
        "<a><!--  padded  --><b>1</b></a>",
        process_comments=True,
        comment_key="#remark",
        strip_whitespace=False,
    )
    for depth, stop in [(1, None), (2, None), (2, 1)]:
        yield parse_stream_case(
            f"parse/streaming/item_depth={depth}/stop_after={stop}",
            '<a prop="x"><b>1</b><b>2</b><b>3</b></a>',
            item_depth=depth,
            stop_after=stop,
        )
    yield parse_case("parse/xml_attribs/false", '<a prop="x"><b>1</b></a>', xml_attribs=False)
    yield parse_case("parse/attr_prefix/custom", '<a prop="x">1</a>', attr_prefix="attr_")
    yield parse_case("parse/cdata_key/custom", "<a>hi</a>", cdata_key="#value")
    yield parse_case("parse/force_cdata/true", "<a><b>1</b><c>2</c></a>", force_cdata=True)
    yield parse_case("parse/force_cdata/tuple", "<a><b>1</b><c>2</c></a>", force_cdata=("b",))
    yield parse_case("parse/force_cdata/callable", "<a><b>short</b><c>longertext</c></a>", force_cdata=ref("force_cdata_long_text"))
    yield parse_case("parse/cdata_separator/space", "<a>one<b/>two</a>", cdata_separator=" ")
    yield parse_case("parse/postprocessor/int_cast", "<a><b>1</b><b>2</b><b>x</b></a>", postprocessor=ref("postprocessor_int_cast"))
    yield parse_case("parse/dict_constructor/OrderedDict", '<a z="1" y="2"><b>1</b></a>', dict_constructor=ref("OrderedDict"))
    yield parse_case("parse/strip_whitespace/false", "<a>  padded  </a>", strip_whitespace=False)
    yield parse_case("parse/strip_whitespace/all-whitespace", "<a>   </a>")
    yield parse_case("parse/strip_whitespace/all-whitespace-false", "<a>   </a>", strip_whitespace=False)
    yield parse_case(
        "parse/force_list/tuple",
        "<a><server><name>h1</name></server></a>",
        force_list=("server",),
    )
    yield parse_case("parse/force_list/true", "<a><b>1</b></a>", force_list=True)
    yield parse_case(
        "parse/force_list/callable",
        "<a><b>1</b><c>2</c></a>",
        force_list=ref("force_list_is_b"),
    )

    # --- unparse: each keyword at default and non-default ---
    yield unparse_case("unparse/defaults/simple", {"a": {"@prop": "x", "b": ["1", "2"]}})
    yield unparse_case("unparse/pretty/default-indent", {"a": {"b": "1", "c": "2"}}, pretty=True)
    yield unparse_case("unparse/pretty/int-indent", {"a": {"b": "1"}}, pretty=True, indent=2)
    yield unparse_case("unparse/pretty/custom-newl", {"a": {"b": "1"}}, pretty=True, newl="\r\n")
    yield unparse_case("unparse/short_empty_elements/true", {"a": {"b": None}}, short_empty_elements=True)
    yield unparse_case("unparse/short_empty_elements/false", {"a": {"b": None}}, short_empty_elements=False)
    case = unparse_case("unparse/full_document/false", {"a": 1, "b": 2}, full_document=False)
    case["expect_well_formed"] = False  # a document fragment by design, not a standalone document
    yield case
    yield unparse_case("unparse/attr_prefix/custom", {"a": {"attr_prop": "x", "#text": "hi"}}, attr_prefix="attr_")
    yield unparse_case("unparse/cdata_key/custom", {"a": {"#value": "hi"}}, cdata_key="#value")
    yield unparse_case("unparse/encoding/latin-1", {"a": "café"}, encoding="iso-8859-1")
    yield unparse_case("unparse/bytes_errors/replace-default", {"a": {"#text": b"\xff\xfe"}})
    yield unparse_case("unparse/bytes_errors/ignore", {"a": {"#text": b"\xff\xfe"}}, bytes_errors="ignore")
    yield unparse_case("unparse/expand_iter/set", {"a": {"points": [[1, 5], [2, 6]]}}, expand_iter="coord")
    yield unparse_case("unparse/expand_iter/unset", {"a": {"points": [[1, 5], [2, 6]]}})
    yield unparse_case(
        "unparse/namespaces/short-prefix-key",
        {"a:root": {"#text": "x"}},
        namespaces={"a": "short"},
    )
    yield unparse_case(
        "unparse/namespaces/attribute-key",
        {"root": {"@a:y": "1"}},
        namespaces={"a": "short"},
    )
    case = unparse_case(
        "unparse/namespace_separator/custom", {"a|root": {"#text": "x"}}, namespaces={"a": "short"}, namespace_separator="|"
    )
    # '|' is not a legal XML name character and name validation doesn't block
    # it (see SECURITY.md's CVE-2025-9375 discussion) -- the reference has the
    # same gap, confirmed by probing it directly; this case exists to pin that
    # shared behavior, not to assert well-formed output.
    case["expect_well_formed"] = False
    yield case
    yield unparse_case(
        "unparse/comments/basic",
        {"a": {"#comment": "hi", "#text": "x"}},
    )
    yield unparse_case(
        "unparse/comments/list-and-pretty",
        {"a": {"#comment": ["c1", "c2"], "b": "1"}},
        pretty=True,
    )
    yield unparse_case("unparse/comments/non-str-values", {"a": {"#comment": [123, True, b"\xff\xfe"], "b": "1"}})
    yield unparse_case(
        "unparse/preprocessor/upper-keys",
        {"root": {"keep": "1"}},
        preprocessor=ref("preprocessor_upper_keys"),
    )
    yield unparse_case(
        "unparse/preprocessor/drop-node",
        {"root": {"keep": "1", "skip": "2"}},
        preprocessor=ref("preprocessor_drop_skip"),
    )
    yield unparse_case("unparse/xmlns-dict-child/default-and-prefixed", {"root": {"@xmlns": {"": "http://d/", "a": "http://a/"}}})
    yield unparse_case("unparse/value-types/bool", {"a": {"b": True, "c": False}})
    yield unparse_case("unparse/value-types/none-scalar", {"a": {"b": None}})
    yield unparse_case("unparse/value-types/int-float", {"a": {"b": 1, "c": 1.5}})
    yield unparse_case("unparse/value-types/nested-list-no-expand", {"a": {"points": [[1, 5], [2, 6]]}})
    yield unparse_case("unparse/empty-list-child-skipped", {"a": {"b": [], "c": "1"}})


def iter_edge_input_cases():
    yield parse_case("edge/empty-text", "<a></a>")
    yield parse_case("edge/whitespace-only-text", "<a> \n\t </a>")
    yield parse_case("edge/mixed-content", "<a>before<b>1</b>after</a>")
    yield parse_case("edge/cdata-section", "<a><![CDATA[<raw> & stuff]]></a>")
    yield parse_case("edge/character-references", "<a>&#65;&#x42;&amp;&lt;&gt;</a>")
    yield parse_case("edge/deep-nesting", "<a>" * 200 + "x" + "</a>" * 200)
    yield parse_case("edge/many-siblings", "<a>" + "".join(f"<b>{i}</b>" for i in range(500)) + "</a>")
    yield parse_case("edge/unicode-text", "<a>héllo wörld 日本語 🎉</a>".encode("utf-8"))
    yield parse_case("edge/utf8-bom", b"\xef\xbb\xbf<a>1</a>")
    yield parse_case("edge/utf16-encoded", '<?xml version="1.0" encoding="UTF-16"?><a>hi</a>'.encode("utf-16"))
    yield {
        "id": "edge/generator-input",
        "op": "parse",
        "xml_input": [b"<a>", b"1", b"</a>"],
        "xml_input_is_generator": True,
        "kwargs": {},
    }
    yield {
        "id": "edge/file-input",
        "op": "parse",
        "xml_input": b"<a>from a file</a>",
        "xml_input_is_file": True,
        "kwargs": {},
    }
    yield unparse_case("edge/unparse-empty-element-value-none", {"a": None})
    yield unparse_case("edge/unparse-empty-dict-value", {"a": {}})
    yield unparse_case("edge/unparse-numeric-like-text", {"a": "007"})


def iter_malformed_input_cases():
    yield parse_case("malformed/unclosed-tag", "<a><b>1</a>")
    yield parse_case("malformed/mismatched-tag", "<a><b>1</c></a>")
    yield parse_case("malformed/multiple-roots-in-xml", "<a>1</a><b>2</b>")
    yield parse_case("malformed/invalid-characters", "<a>\x00</a>")
    yield parse_case("malformed/invalid-bytes-for-encoding", b"<a>\xff\xfe</a>", encoding="utf-8")
    yield parse_case("malformed/none-input", None)
    yield parse_case("malformed/empty-input", "")
    yield parse_case("malformed/not-xml-at-all", "just plain text, no tags")
    yield unparse_case("malformed/unparse-two-roots", {"a": 1, "b": 2})
    yield unparse_case("malformed/unparse-zero-roots", {})
    yield unparse_case("malformed/unparse-only-comment-root", {"#comment": "hi"})
    yield unparse_case("malformed/unparse-list-multiple-roots", {"a": [1, 2]})
    yield unparse_case("malformed/unparse-invalid-bytes-errors", {"a": 1}, bytes_errors="bogus-handler")
    for bad_name in ["a b", "a<b", "a>b", "a/b", 'a"b', "a'b", "a=b", "?a", "!a", 123, None]:
        yield unparse_case(f"malformed/unparse-invalid-element-name/{bad_name!r}", {bad_name: "1"})
    for bad_attr in ["a b", "a<b", "a/b", "a=b", "?a"]:
        yield unparse_case(f"malformed/unparse-invalid-attr-name/{bad_attr!r}", {"root": {"@" + bad_attr: "1"}})
    for bad_comment in ["ok--bad", "trailing-"]:
        yield unparse_case(f"malformed/unparse-invalid-comment/{bad_comment!r}", {"a": {"#comment": bad_comment, "#text": "x"}})


def iter_hostile_input_cases():
    yield parse_case("hostile/internal-entity-declaration", '<!DOCTYPE a [<!ENTITY x "hi">]><a>&x;</a>')
    yield parse_case(
        "hostile/external-system-entity",
        '<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>',
    )
    yield parse_case(
        "hostile/external-public-entity",
        '<!DOCTYPE a [<!ENTITY x PUBLIC "-//X//Y" "http://example.com/x.dtd">]><a>&x;</a>',
    )
    yield parse_case(
        "hostile/parameter-entity",
        '<!DOCTYPE a [<!ENTITY % p SYSTEM "http://example.com/p.dtd">%p;]><a>1</a>',
    )
    yield parse_case("hostile/billion-laughs", BILLION_LAUGHS)
    yield parse_case("hostile/billion-laughs/entities-enabled-still-no-fetch", BILLION_LAUGHS, disable_entities=False)
    yield unparse_case(
        "hostile/attribute-injection-attempt",
        {"a": {"@x": '"><script>alert(1)</script>'}},
    )
    yield unparse_case(
        "hostile/element-injection-attempt-via-text",
        {"a": {"#text": "</a><evil>injected</evil><a>"}},
    )
    yield unparse_case(
        "hostile/element-name-injection-attempt",
        {"a><evil>b</evil><c a": "1"},
    )
    yield unparse_case("hostile/ampersand-in-text", {"a": {"#text": "A & B < C > D"}})


# --- seeded random corpus -------------------------------------------------

RANDOM_SEED = 20261031

_TAGS = ["a", "b", "c", "item", "node", "x_y", "n9"]
_ATTR_NAMES = ["id", "class", "data-x", "val"]
_TEXTS = ["hello", "  padded  ", "", "line1\nline2", "<not a tag>", "A&B", "日本語", "007", "3.14", "true"]


def _random_xml_element(rng, depth, max_depth):
    tag = rng.choice(_TAGS)
    attrs = ""
    if rng.random() < 0.5:
        for _ in range(rng.randint(1, 2)):
            attrs += f' {rng.choice(_ATTR_NAMES)}="{rng.choice(_TEXTS)}"'
    if depth >= max_depth or rng.random() < 0.3:
        text = rng.choice(_TEXTS)
        from xml.sax.saxutils import escape as _esc

        return f"<{tag}{attrs}>{_esc(text)}</{tag}>"
    n_children = rng.randint(1, 4)
    children = "".join(_random_xml_element(rng, depth + 1, max_depth) for _ in range(n_children))
    return f"<{tag}{attrs}>{children}</{tag}>"


def _random_dict_value(rng, depth, max_depth):
    choice = rng.random()
    if depth >= max_depth or choice < 0.4:
        return rng.choice([*_TEXTS, 1, 1.5, True, False, None])
    n_children = rng.randint(1, 3)
    node = {}
    if rng.random() < 0.4:
        node["@" + rng.choice(_ATTR_NAMES)] = rng.choice(_TEXTS)
    for _ in range(n_children):
        key = rng.choice(_TAGS)
        if rng.random() < 0.3:
            node[key] = [_random_dict_value(rng, depth + 1, max_depth) for _ in range(rng.randint(1, 3))]
        else:
            node[key] = _random_dict_value(rng, depth + 1, max_depth)
    return node


def iter_random_corpus_cases(n=1000, seed=RANDOM_SEED):
    rng = random.Random(seed)
    for i in range(n):
        if i % 2 == 0:
            xml = _random_xml_element(rng, 0, rng.randint(1, 5))
            yield parse_case(f"random/{seed}/{i}/parse", xml)
        else:
            root_tag = rng.choice(_TAGS)
            value = _random_dict_value(rng, 0, rng.randint(1, 4))
            if not isinstance(value, dict):
                value = {"#text": value}
            yield unparse_case(f"random/{seed}/{i}/unparse", {root_tag: value}, pretty=rng.random() < 0.3)


def iter_all_cases(random_n=1000, random_seed=RANDOM_SEED):
    yield from iter_keyword_matrix_cases()
    yield from iter_edge_input_cases()
    yield from iter_malformed_input_cases()
    yield from iter_hostile_input_cases()
    yield from iter_random_corpus_cases(random_n, random_seed)
