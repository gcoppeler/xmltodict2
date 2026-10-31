"""`python -m xmltodict <item_depth>`: stream parsed items to stdout.

Reads XML from stdin and writes `marshal`-encoded `(path, item)` records to
stdout for every item reached at `item_depth`, matching the reference
project's command-line interface.
"""

import marshal
import sys

from ._parsing import parse


def _emit_to_stdout(path, item):
    marshal.dump((path, item), sys.stdout.buffer)
    return True


def main():
    (item_depth,) = sys.argv[1:]
    item_depth = int(item_depth)

    try:
        root = parse(
            sys.stdin.buffer,
            item_depth=item_depth,
            item_callback=_emit_to_stdout,
            dict_constructor=dict,
        )
        if item_depth == 0:
            _emit_to_stdout([], root)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
