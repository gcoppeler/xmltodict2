# Claude Code Project Instructions

## Primary Development Guidelines

Before performing any development work, read and follow the requirements in:

`REIMPLEMENTATION_GUIDELINES.md`

This document defines the mandatory methodology, implementation requirements, definition of done, and quality expectations for this project.

Treat it as a persistent set of project requirements throughout the entire development lifecycle. Where this file and the guidelines differ, the guidelines win.

## Core Development Principles

1. **Independent implementation:** Write original source code. Do not copy, translate, port, or adapt implementation code from the reference repository.

2. **Exact functional equivalence:** Reproduce the reference's externally observable behavior at the pinned commit exactly: public names, keyword arguments, default values, return types, exception classes, output text, security behavior, and CLI. "Equivalent" is defined in Section 10 of the guidelines, not by judgment.

3. **The reference is the oracle:** Requirements come from the reference's documentation at the pinned commit and from running the installed reference package. Never from memory of this project, and never from your own implementation's output.

4. **Reserved tests:** Do not read, run, copy, or derive cases from the reference's `tests/` directory. It is reserved for independent evaluation.

5. **Independent architecture:** Make your own internal design decisions. Do not reproduce the reference's internal design.

6. **Simplicity of implementation, not of interface:** Prefer the simplest maintainable implementation. Never drop a feature, change a default, change an error type, or change the CLI to simplify.

7. **Incremental development:** Implement and test in increments. Run the differential harness after each significant change.

8. **Quality and security:** Write maintainable, secure, well-documented code. Meet every security requirement in Section 7 of the guidelines.

9. **Transparency:** Do not claim functionality is implemented, tested, or complete unless it is, and the harness shows it.

## Persistent Project Awareness

At the beginning of each new session:

- Review the current project structure.
- Review `PROJECT_STATUS.md` and `FEATURE_INVENTORY.md`.
- Run the differential harness and the test suite, and record the results.
- Identify where previous development work stopped.
- Consult `REIMPLEMENTATION_GUIDELINES.md` whenever making development decisions.

Maintain `PROJECT_STATUS.md` in the repository root.

Update it as development progresses, including:

- Current development phase.
- Completed functionality, with harness status.
- Outstanding functionality.
- Proposed deviations awaiting the user's decision.
- Architectural decisions.
- Known issues and limitations.
- Test and harness results, with dates.
- Next recommended development steps.

Keep the counts and statuses in `PROJECT_STATUS.md` consistent with the actual repository. Re-count tests rather than carrying numbers forward.

Do not unnecessarily repeat completed work or overwrite existing functionality without understanding its purpose.

## Execution Expectations

Act as an autonomous development engineer.

Do not stop at planning, recommendations, or code examples when actual implementation is expected.

Make reasonable engineering decisions about the implementation independently.

Ask before:
- Any change to the public interface or observable behavior relative to the reference.
- Declaring any documented feature out of scope.
- Stopping while any Definition of Done condition is unmet.

When encountering a problem, investigate and attempt to resolve it rather than simply reporting the problem.

If work is split across subagents or roles, verify the shared interface contract against `FEATURE_INVENTORY.md` before implementation starts, and make sure test authors take expected values from the reference, not from the contract.

The work is finished only when every condition in Section 10 of `REIMPLEMENTATION_GUIDELINES.md` is met.
