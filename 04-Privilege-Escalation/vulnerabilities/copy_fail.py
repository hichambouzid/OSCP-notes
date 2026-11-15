#!/usr/bin/env python3
"""Retrieve the original Theori Copy Fail PoC for offline, authorized lab review.

This helper never executes the downloaded code. The upstream project does not
display a redistribution license, so the original is fetched rather than copied
into this repository. Source and SHA-256: https://copy.fail/
"""

import argparse
import hashlib
import sys
from pathlib import Path
from urllib.request import urlopen

URL = "https://copy.fail/exp"
SHA256 = "a567d09b15f6e4440e70c9f2aa8edec8ed59f53301952df05c719aa3911687f9"
SIZE = 732


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("copy_fail_exp.py"),
                        help="Destination for the original PoC (must not exist)")
    args = parser.parse_args()
    print("Authorized isolated lab only; never run on production.", file=sys.stderr)
    try:
        with urlopen(URL, timeout=20) as response:
            data = response.read(SIZE + 1)
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != SIZE or digest != SHA256:
            raise ValueError("Upstream content differs from the documented original; "
                             "verify the new release manually.")
        with args.output.open("xb") as output:
            output.write(data)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {args.output} ({len(data)} bytes)")
    print(f"SHA-256: {digest}")
    print("Review the source before using it in a disposable, authorized VM.")
    print("No exploit was executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
