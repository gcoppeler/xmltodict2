"""Independent tests for `python -m xmltodict <item_depth>`.

Expected values observed from running the installed reference package's
CLI the same way (see PROJECT_STATUS.md).
"""

import marshal
import subprocess
import sys


def run_cli(args, stdin_bytes):
    return subprocess.run(
        [sys.executable, "-m", "xmltodict", *args],
        input=stdin_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )


def test_depth_zero_emits_whole_document_once():
    proc = run_cli(["0"], b"<a><b>1</b><b>2</b></a>")
    assert proc.returncode == 0
    path, item = marshal.loads(proc.stdout)
    assert path == []
    assert item == {"a": {"b": ["1", "2"]}}


def test_depth_two_streams_each_matching_item():
    proc = run_cli(["2"], b'<a prop="x"><b>1</b><b>2</b></a>')
    assert proc.returncode == 0
    records = []
    stream = proc.stdout
    offset = 0
    while offset < len(stream):
        obj = marshal.loads(stream[offset:])
        records.append(obj)
        offset += len(marshal.dumps(obj))
    assert records == [
        ([("a", {"prop": "x"}), ("b", None)], "1"),
        ([("a", {"prop": "x"}), ("b", None)], "2"),
    ]


def test_missing_argument_exits_nonzero():
    proc = run_cli([], b"<a>1</a>")
    assert proc.returncode != 0


def test_non_integer_argument_exits_nonzero():
    proc = run_cli(["x"], b"<a>1</a>")
    assert proc.returncode != 0


def test_malformed_xml_exits_nonzero():
    proc = run_cli(["0"], b"<a><b>1</a>")
    assert proc.returncode != 0
