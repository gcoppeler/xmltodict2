# Project: Independent Reimplementation of an Existing Open-Source Application

## Objective

Create a new, independently written implementation of the following open-source project:

**Reference repository:** https://github.com/martinblech/xmltodict
**Pinned reference commit:** `6e29fba282e68631034dd2722a413b4e35276584` (version string 1.0.4, six commits after the v1.0.4 tag)

The purpose is to build a functionally equivalent application for my personal use.

"Functionally equivalent" has a precise meaning in this project. It is defined in Section 10 (Definition of Done) and the work is not complete until every condition there is met.

The new application must reproduce the externally observable behavior of the reference at the pinned commit, while being implemented independently, with original source code and an independently designed architecture.

This is NOT a request to fork, clone-and-modify, port, translate, or refactor the existing application.

The reference project is a behavioral specification and a test oracle, not a source-code foundation.

## 1. Implementation Independence

The new application must be written from scratch.

Do not:
- Copy source code from the reference repository.
- Translate existing source code into another programming language.
- Rename variables, classes, functions, or modules to disguise copied code.
- Reproduce existing functions or modules through superficial modifications.
- Use the original repository as a code-generation template.
- Copy its build scripts or implementation artifacts.

Public interface names (function names, keyword-argument names, exception class names, import name) must match the reference exactly. Matching them is required for compatibility and is not copying.

### Reserved evaluation material

The reference's `tests/` directory is reserved for independent evaluation after delivery.

- Do not read, run, copy, paraphrase, or derive test cases from anything in the reference's `tests/` directory.
- Do not search for, open, or summarize those test files by any route (web, GitHub UI, package source).

Use the reference's documentation and the installed reference package (black-box) instead. See Section 6.

## 2. Requirements Discovery

### Sources of truth

Requirements come only from the reference repository at the pinned commit. Clone it and read these files there:

- `README.md` (including "API Reference", "Namespace support", "Streaming mode", "Roundtripping", "Examples", "Security Notes")
- Docstrings of every public function in the source (`parse`, `unparse`), and the module's `__main__` block
- `AGENTS.md`
- `SECURITY.md`
- `CHANGELOG.md` (to understand when and why behaviors were added or changed)

You may read the reference source code to understand behavior, subject to Section 1.

Do not rely on prior knowledge of this project. Your training data may describe an older version with different defaults and fewer features. If your memory and the pinned docs disagree, the pinned docs and the installed reference win. If they are ambiguous, run the reference and observe.

### Feature inventory

Before any design work, produce `FEATURE_INVENTORY.md` with one row per user-facing behavior:

| ID | Behavior | Source (file:line at pinned commit) | Default value | Status |

The inventory must include:

- Every public function, class, and exception exported by the reference module.
- Every keyword argument of every public function, with its exact default value.
- Every accepted form of each argument (for example a boolean, a tuple, or a callable).
- Every documented error condition and the exception class raised.
- Every security behavior (Section 7).
- The command-line interface (Section 8).

Every documented feature is required. There is no "optional" tier. You may choose the order in which features are built, but not whether they are built.

Before implementation, check the inventory line by line against the sources above and confirm in `PROJECT_STATUS.md` that this review was done.

## 3. Independent Architecture

Design the implementation independently.

You are free to:
- Use a different internal architecture.
- Use different internal data structures and algorithms.
- Simplify internal components.
- Improve performance and maintainability.

You are not free to change the public interface or observable behavior (Section 5).

Do not unnecessarily replicate the original application's internal architecture.

Explain major architectural decisions before implementation.

## 4. Technology and Dependencies

- Same language as the reference (Python), same supported Python versions as declared in its `pyproject.toml`.
- Standard library only at runtime, unless a dependency is required to match reference behavior. Justify any dependency.
- Do not incorporate code from the reference implementation.
- Document dependency licenses.
- Include a `LICENSE` file with a copyright notice for the new code.
- Do not commit build artifacts (`build/`, `__pycache__/`, `*.egg-info`).

## 5. Interface Compatibility

The new package must be a drop-in replacement for the reference.

- Same import name (`import xmltodict`) and same public names, including exception classes.
- Every keyword argument accepted by the reference is accepted, with the same name, the same default, and the same accepted forms.
- Same return types, including the container type returned by default.
- Same exception classes for the same error conditions.
- Same output text from `unparse` for the same input and options, byte for byte.
- Same command-line interface (Section 8).

Simplicity applies to the implementation, never to the public interface.

If you believe any documented behavior should deliberately differ (for example because it appears to be a bug), do not change it on your own. Record it in `PROJECT_STATUS.md` under "Proposed deviations" and ask me before implementing the difference.

## 6. Testing

Testing has two parts. Both are required.

### 6a. Independent test suite

Write your own unit and integration tests covering every row of the feature inventory.

Every expected value in a test must come from the reference: from its documentation, or from running the installed reference package on that input. Never take an expected value from your own implementation's output. Note the source of each expected value in the test (doc reference or "observed from reference").

### 6b. Differential test harness (the oracle)

Install the reference at the pinned commit into a separate virtual environment:

```
python -m venv .venv-reference
.venv-reference/bin/pip install "git+https://github.com/martinblech/xmltodict@6e29fba282e68631034dd2722a413b4e35276584"
```

Do not use `pip install xmltodict==1.0.4`; the published 1.0.4 release differs from the pinned commit.

Build a harness in `parity/` that:

- Runs identical inputs through the reference and the new implementation in separate processes (both packages are named `xmltodict`, so they must never share an interpreter).
- Compares, for every input: return value, container types (`dict` vs `OrderedDict`, `list` vs `tuple`), exception class, exception message, callback arguments (including streaming `path` values), CLI stdout, stderr, and exit code.
- Checks that every `unparse` output is well-formed XML.
- Covers, at minimum:
  - every keyword argument, in every accepted form, at its default and at non-default values;
  - normal inputs (the README examples);
  - edge inputs (empty and whitespace-only text, mixed content, CDATA, character references, deep nesting, many siblings, Unicode, byte-order marks, non-UTF-8 encodings, generator input, file input);
  - malformed inputs (unclosed and mismatched tags, multiple roots, invalid characters, invalid bytes, `None`);
  - hostile inputs (Section 7);
  - at least 1,000 seeded random documents and dicts, with the seed recorded.
- Prints a summary and exits non-zero on any unexplained mismatch.
- Runs with one command, documented in `README.md`.

The harness must be run after every significant change. A green independent test suite with a red harness means the work is not done.

## 7. Security Requirements

Match the reference's security behavior exactly. At minimum:

- `parse` with `disable_entities=True` (the default): any entity declaration (internal, external `SYSTEM`/`PUBLIC`, or parameter entity) raises the same exception class as the reference.
- `parse` never fetches external resources.
- `unparse` escapes `&`, `<`, `>`, and quotes in text and attribute values, so attacker-controlled values cannot inject elements or attributes.
- `unparse` rejects invalid element and attribute names (containing `<`, `>`, `/`, quotes, `=`, or whitespace, or starting with `?` or `!`, or not strings) with the same exception class as the reference.
- `unparse` validates comment text as the reference does.

Include hostile inputs for each of these in both test parts (Section 6), including attribute-injection and element-injection attempts and an entity-expansion ("billion laughs") document.

## 8. Command-Line Interface

Reproduce the reference CLI: `python -m xmltodict <item_depth>` reads XML from stdin and writes `marshal`-encoded `(path, item)` records to stdout, as described in the reference README "Streaming mode" and implemented in its `__main__` block. Match its exit codes and error behavior for invalid and missing arguments.

Do not add, rename, or replace CLI options. A different CLI is a failed requirement, not an improvement.

## 9. Development Approach

Work incrementally.

**Phase 1: Discovery**
- Clone the reference at the pinned commit.
- Produce `FEATURE_INVENTORY.md` (Section 2) and review it against the sources.

**Phase 2: Design**
- Develop an independent architecture.
- Write the interface contract from the inventory. Every default and accepted form must match the inventory.
- Produce an implementation plan.

**Phase 3: Foundation**
- Establish the project structure, packaging, `LICENSE`, and `.gitignore`.
- Install the reference oracle (Section 6b) and build the differential harness before writing feature code.

**Phase 4: Implementation**
- Implement features in any order; all are required.
- After each feature: run the independent tests and the harness, and update the inventory status.

**Phase 5: Validation**
- Run the full harness, including the random corpus.
- Fix every mismatch, or record it as a proposed deviation and ask me.
- Verify every security requirement (Section 7) with hostile inputs.

**Phase 6: Delivery**
- Provide source, tests, harness, documentation, and installation instructions.
- Provide the final parity report (Section 10).

If work is divided among multiple agents or roles, the interface contract must be verified against `FEATURE_INVENTORY.md` before any implementation starts, and test authors must take expected values from the reference (Section 6a), not from the contract.

## 10. Definition of Done

The work is complete only when all of the following are true:

1. Every row of `FEATURE_INVENTORY.md` is implemented and marked Pass.
2. API parity: every public name, keyword argument, default value, accepted form, return type, and exception class matches the reference.
3. The differential harness reports zero unexplained mismatches across all categories in Section 6b, including the random corpus.
4. Every security requirement in Section 7 is met and demonstrated by hostile-input tests.
5. The CLI matches the reference (Section 8).
6. The independent test suite passes, and its expected values are sourced from the reference.
7. Any remaining deviation was approved by me and is listed in `PROJECT_STATUS.md`.
8. `PROJECT_STATUS.md` contains a final parity report: one row per inventory item with Pass/Fail and the harness evidence (case IDs or command output).

Do not report the project as complete, or stop work, while any condition above is unmet. If you cannot meet a condition, stop and explain which condition, why, and what you need from me.

## 11. Operating Instructions

Act as a senior software architect and hands-on development engineer.

Build the application. Do not stop at a plan, recommendations, or examples.

Make reasonable engineering decisions about the implementation without asking for approval. Ask before any change to the public interface or observable behavior.

Do not claim functionality is complete until it has been implemented, tested against the reference, and marked Pass in the inventory.

Maintain a running list of:
- Completed features (with harness status).
- Outstanding features.
- Proposed deviations awaiting my decision.
- Known limitations.
- Technical debt.
- Test and harness results, with dates.

## Guiding Principle

The reference at the pinned commit establishes the functional requirements, including its interface, defaults, error behavior, and security behavior.

The new application establishes its own implementation.

**Build an independent equivalent, not a derivative codebase. Match what the reference does exactly; choose freely how to do it.**

## 12. Simplicity and Avoiding Overengineering

The objective is functional equivalence, not implementation equivalence.

- Prefer simple internal designs over complex ones.
- Do not reproduce internal architectural complexity simply because it exists in the reference.
- Avoid unnecessary abstractions, layers, dependencies, and infrastructure.
- Minimize code duplication while avoiding premature abstraction.
- Optimize for readability, maintainability, reliability, and ease of future modification.

Simplicity never justifies omitting a feature, changing a default, changing an error type, or changing the CLI. A smaller implementation is preferable only when it meets every condition in Section 10.
