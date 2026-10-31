"""Structural comparison between two oracle_worker.py responses."""


class Mismatch(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def compare_responses(expected, actual):
    """Compare two oracle_worker.py top-level responses.

    Raises Mismatch with a human-readable reason on the first difference
    found. `expected` is always the reference's response.
    """
    if expected["ok"] != actual["ok"]:
        if expected["ok"]:
            raise Mismatch(
                f"reference succeeded but new implementation raised "
                f"{actual.get('exc_qualname')}: {actual.get('exc_str')!r}"
            )
        raise Mismatch(
            f"reference raised {expected.get('exc_qualname')}: {expected.get('exc_str')!r} "
            f"but new implementation succeeded with {actual.get('payload')!r}"
        )

    if not expected["ok"]:
        if expected["exc_qualname"] != actual["exc_qualname"]:
            raise Mismatch(
                f"exception class differs: reference={expected['exc_qualname']} "
                f"new={actual['exc_qualname']}"
            )
        if expected["exc_str"] != actual["exc_str"]:
            raise Mismatch(
                f"exception message differs: reference={expected['exc_str']!r} "
                f"new={actual['exc_str']!r}"
            )
        return

    exp_payload, act_payload = expected["payload"], actual["payload"]
    if exp_payload.get("result_repr") != act_payload.get("result_repr"):
        raise Mismatch(
            f"result value/type differs:\n  reference={exp_payload['result_repr']!r}\n"
            f"  new=      {act_payload['result_repr']!r}"
        )
    if "collected" in exp_payload or "collected" in act_payload:
        exp_collected = exp_payload.get("collected", [])
        act_collected = act_payload.get("collected", [])
        if len(exp_collected) != len(act_collected):
            raise Mismatch(
                f"streaming callback fired {len(exp_collected)} times for the reference "
                f"but {len(act_collected)} times for the new implementation"
            )
        for i, (exp_item, act_item) in enumerate(zip(exp_collected, act_collected)):
            if exp_item != act_item:
                raise Mismatch(
                    f"streaming item #{i} differs:\n  reference={exp_item!r}\n  new=      {act_item!r}"
                )
