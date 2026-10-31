# xmldictify2

An independently written, from-scratch Python package that reproduces the
public interface and observable behavior of
[`xmltodict`](https://github.com/martinblech/xmltodict) at commit
`6e29fba282e68631034dd2722a413b4e35276584` (just after the `v1.0.4` release).

This is a clean-room reimplementation for personal use: the reference project
is treated as a behavioral specification (its docs and its installed
package), not as a source-code foundation. See `REIMPLEMENTATION_GUIDELINES.md`
for the full methodology, `FEATURE_INVENTORY.md` for the line-by-line
requirements list, and `PROJECT_STATUS.md` for current progress.

## Install (development)

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"
```

## Run the independent test suite

```bash
.venv/bin/pytest tests/
```

## Run the differential harness (the oracle)

The harness runs identical inputs through the reference package and this
package in separate processes (both are importable as `xmltodict`, so they
must never share an interpreter) and reports any mismatch.

```bash
python -m venv .venv-reference
.venv-reference/bin/pip install "git+https://github.com/martinblech/xmltodict@6e29fba282e68631034dd2722a413b4e35276584"
.venv/bin/python parity/run_harness.py
```

The harness exits non-zero on any unexplained mismatch and prints a summary.
