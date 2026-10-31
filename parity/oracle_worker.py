"""Long-lived worker process for the differential harness.

Started once per package-under-test (the reference venv, then this
project's venv) by run_harness.py. Reads one pickled request at a time from
stdin, calls into whichever `xmltodict` package this interpreter resolves
(`import xmltodict` behaves differently per venv — that's the whole point),
and writes one pickled response to stdout. Both subprocesses run this exact
same file, so there is never any reference-specific or new-package-specific
logic here — only the import target differs.

Not a test file; it is deliberately outside `tests/` and `src/` so it is
shared infrastructure, not part of either implementation under comparison.
"""

import collections
import io
import pickle
import sys
from xml.parsers import expat as _stdlib_expat


def _postprocessor_int_cast(path, key, value):
    try:
        return key + ":int", int(value)
    except (ValueError, TypeError):
        return key, value


def _postprocessor_drop_skip(path, key, value):
    if key == "@drop":
        return None
    return key, value


def _preprocessor_upper_keys(key, value):
    if isinstance(key, str):
        return key.upper(), value
    return key, value


def _preprocessor_drop_skip(key, value):
    if key == "skip":
        return None
    return key, value


def _force_list_is_b(path, key, value):
    return key == "b"


def _force_cdata_long_text(path, key, value):
    return isinstance(value, str) and len(value) > 4


REGISTRY = {
    "dict": dict,
    "OrderedDict": collections.OrderedDict,
    "stdlib_expat": _stdlib_expat,
    "postprocessor_int_cast": _postprocessor_int_cast,
    "postprocessor_drop_skip": _postprocessor_drop_skip,
    "preprocessor_upper_keys": _preprocessor_upper_keys,
    "preprocessor_drop_skip": _preprocessor_drop_skip,
    "force_list_is_b": _force_list_is_b,
    "force_cdata_long_text": _force_cdata_long_text,
}


def _resolve(value):
    """Recursively replace {"__ref__": name} markers with REGISTRY[name]."""
    if isinstance(value, dict):
        if set(value) == {"__ref__"}:
            return REGISTRY[value["__ref__"]]
        return {k: _resolve(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_resolve(v) for v in value)
    return value


def _describe_type(value):
    """A short, nested type signature used to catch dict/OrderedDict and
    list/tuple differences that plain `==` would miss."""
    if isinstance(value, dict):
        return ("dict", type(value).__name__, [(k, _describe_type(v)) for k, v in value.items()])
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, [_describe_type(v) for v in value])
    return (type(value).__name__, value)


def _handle_parse(request):
    import xmltodict

    kwargs = _resolve(request["kwargs"])
    collected = []
    if request.get("record_callback"):
        stop_after = request.get("stop_after")

        def _record(path, item):
            collected.append((path, item))
            if stop_after is not None and len(collected) >= stop_after:
                return False
            return True

        kwargs["item_callback"] = _record

    xml_input = request["xml_input"]
    if request.get("xml_input_is_generator"):
        chunks = xml_input

        def _gen():
            for chunk in chunks:
                yield chunk

        xml_input = _gen()
    elif request.get("xml_input_is_file"):
        xml_input = io.BytesIO(xml_input)

    result = xmltodict.parse(xml_input, **kwargs)
    return {
        "result_repr": _describe_type(result),
        "result_value": result,
        "collected": collected,
    }


def _handle_unparse(request):
    import xmltodict

    kwargs = _resolve(request["kwargs"])
    input_dict = _resolve(request["input_dict"])
    result = xmltodict.unparse(input_dict, **kwargs)
    return {"result_repr": _describe_type(result), "result_value": result}


def _handle_exception_class_name(request):
    """Report the exception class's fully-qualified name for a prior failure,
    resolved inside this venv (so `xmltodict.ParsingInterrupted` compares the
    *reference's* class object against the reference's own name, etc.)."""
    import xmltodict

    name = request["name"]
    if name == "ParsingInterrupted":
        exc_type = xmltodict.ParsingInterrupted
    else:
        import builtins

        exc_type = getattr(builtins, name)
    return {"qualname": f"{exc_type.__module__}.{exc_type.__qualname__}"}


OPS = {
    "parse": _handle_parse,
    "unparse": _handle_unparse,
    "exc_qualname": _handle_exception_class_name,
}


def main():
    while True:
        try:
            request = pickle.load(sys.stdin.buffer)
        except EOFError:
            break

        try:
            payload = OPS[request["op"]](request)
            response = {"ok": True, "payload": payload}
        except Exception as exc:  # noqa: BLE001 - reporting, not handling
            response = {
                "ok": False,
                "exc_qualname": f"{type(exc).__module__}.{type(exc).__qualname__}",
                "exc_args": _safe_args(exc.args),
                "exc_str": str(exc),
            }

        pickle.dump(response, sys.stdout.buffer)
        sys.stdout.buffer.flush()


def _safe_args(args):
    safe = []
    for a in args:
        try:
            pickle.dumps(a)
            safe.append(a)
        except Exception:  # noqa: BLE001
            safe.append(repr(a))
    return tuple(safe)


if __name__ == "__main__":
    main()
