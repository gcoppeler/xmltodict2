#!/usr/bin/env python3
"""The differential harness (Section 6b of REIMPLEMENTATION_GUIDELINES.md).

Runs every case in cases.py through the reference package and this
project's package, each in its own long-lived subprocess (they're both
importable as `xmltodict`, so they must never share an interpreter), and
reports any unexplained mismatch. Also runs the CLI entry point of both
packages against the same stdin and compares stdout/stderr/exit code, and
checks that every successful `unparse` result is well-formed XML.

Usage (see README.md):
    .venv/bin/python parity/run_harness.py
"""

import pickle
import subprocess
import sys
import xml.parsers.expat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_PYTHON = ROOT / ".venv-reference" / "bin" / "python"
NEW_PYTHON = ROOT / ".venv" / "bin" / "python"
WORKER_SCRIPT = ROOT / "parity" / "oracle_worker.py"

sys.path.insert(0, str(ROOT / "parity"))
from cases import iter_all_cases  # noqa: E402
from compare import Mismatch, compare_responses  # noqa: E402


class Worker:
    def __init__(self, python_exe, label):
        self.label = label
        self.proc = subprocess.Popen(
            [str(python_exe), str(WORKER_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def send(self, request):
        pickle.dump(request, self.proc.stdin)
        self.proc.stdin.flush()
        try:
            return pickle.load(self.proc.stdout)
        except EOFError:
            stderr = self.proc.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(f"{self.label} worker died. stderr:\n{stderr}")

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


def check_well_formed(xml_text, case_id, failures):
    if not isinstance(xml_text, str):
        return
    try:
        xml.parsers.expat.ParserCreate().Parse(xml_text.encode("utf-8"), True)
    except xml.parsers.expat.ExpatError as exc:
        failures.append((case_id, f"unparse produced non-well-formed XML: {exc}\n--- output ---\n{xml_text}"))


def run_case_matrix(reference, new, limit_printed=40):
    failures = []
    total = 0
    for request in iter_all_cases():
        total += 1
        case_id = request["id"]
        to_send = {k: v for k, v in request.items() if k != "id"}
        try:
            ref_response = reference.send(to_send)
            new_response = new.send(to_send)
        except RuntimeError as exc:
            failures.append((case_id, str(exc)))
            continue

        try:
            compare_responses(ref_response, new_response)
        except Mismatch as exc:
            failures.append((case_id, exc.reason))
            continue

        if request["op"] == "unparse" and ref_response["ok"] and request.get("expect_well_formed", True):
            check_well_formed(ref_response["payload"]["result_value"], case_id, failures)

    print(f"Ran {total} differential cases.")
    if failures:
        print(f"{len(failures)} MISMATCH(ES):")
        for case_id, reason in failures[:limit_printed]:
            print(f"  [{case_id}] {reason}")
        if len(failures) > limit_printed:
            print(f"  ... and {len(failures) - limit_printed} more")
    else:
        print("All differential cases matched.")
    return failures


def run_cli_case(label_exe, pythonpath_extra, stdin_bytes, argv):
    env = {"PYTHONPATH": str(pythonpath_extra)} if pythonpath_extra else {}
    import os

    full_env = dict(os.environ)
    if pythonpath_extra:
        full_env["PYTHONPATH"] = str(pythonpath_extra)
    proc = subprocess.run(
        [str(label_exe), "-m", "xmltodict", *argv],
        input=stdin_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=full_env,
        timeout=30,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_cli_cases():
    failures = []
    cases = [
        ("cli/depth0", b"<a><b>1</b><b>2</b></a>", ["0"]),
        ("cli/depth1", b"<a><b>1</b><b>2</b></a>", ["1"]),
        ("cli/depth2", b"<a><b>1</b><b>2</b></a>", ["2"]),
        ("cli/missing-arg", b"<a>1</a>", []),
        ("cli/too-many-args", b"<a>1</a>", ["1", "2"]),
        ("cli/non-integer-arg", b"<a>1</a>", ["x"]),
        ("cli/malformed-xml", b"<a><b>1</a>", ["0"]),
    ]
    new_src = ROOT / "src"
    for case_id, stdin_bytes, argv in cases:
        ref_rc, ref_out, ref_err = run_cli_case(REFERENCE_PYTHON, None, stdin_bytes, argv)
        new_rc, new_out, new_err = run_cli_case(NEW_PYTHON, new_src, stdin_bytes, argv)
        if ref_rc != new_rc:
            failures.append((case_id, f"exit code differs: reference={ref_rc} new={new_rc}"))
            continue
        if ref_out != new_out:
            failures.append((case_id, f"stdout differs: reference={ref_out!r} new={new_out!r}"))
            continue
        # stderr text (tracebacks) is not required to match verbatim, but
        # "has a traceback" vs "doesn't" must agree.
        if bool(ref_err.strip()) != bool(new_err.strip()):
            failures.append((case_id, f"stderr presence differs: reference={ref_err!r} new={new_err!r}"))

    print(f"Ran {len(cases)} CLI cases.")
    if failures:
        print(f"{len(failures)} CLI MISMATCH(ES):")
        for case_id, reason in failures:
            print(f"  [{case_id}] {reason}")
    else:
        print("All CLI cases matched.")
    return failures


def main():
    if not REFERENCE_PYTHON.exists():
        print(f"Missing reference venv at {REFERENCE_PYTHON}. See README.md Section 6b setup.", file=sys.stderr)
        return 2
    if not NEW_PYTHON.exists():
        print(f"Missing dev venv at {NEW_PYTHON}. Run: python -m venv .venv && .venv/bin/pip install -e .", file=sys.stderr)
        return 2

    reference = Worker(REFERENCE_PYTHON, "reference")
    new = Worker(NEW_PYTHON, "new")
    try:
        matrix_failures = run_case_matrix(reference, new)
    finally:
        reference.close()
        new.close()

    cli_failures = run_cli_cases()

    total_failures = len(matrix_failures) + len(cli_failures)
    if total_failures:
        print(f"\nHARNESS FAILED: {total_failures} unexplained mismatch(es).")
        return 1
    print("\nHARNESS PASSED: zero unexplained mismatches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
