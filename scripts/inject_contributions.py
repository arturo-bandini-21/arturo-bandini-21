#!/usr/bin/env python3
"""Keep the upstream contribution-calendar metrics intact.

gh.crafter.run now renders a dedicated "Last 12 Months / Contributions" metric,
including the account's published private contributions. The older implementation
rewrote its legacy ``Commits`` field and, after the upstream layout changed,
either crashed the refresh or mislabeled the public commit metric as a
contribution total.

The workflow retains this guard so an upstream response without the calendar
metric cannot be committed as a successful refresh.
"""

import sys


def validate(path: str) -> None:
    with open(path, encoding="utf-8") as file:
        svg = file.read()

    if ". Contributions: " not in svg:
        raise RuntimeError(f"contribution-calendar metric not found in {path}")


if __name__ == "__main__":
    for target in sys.argv[1:]:
        validate(target)
        print(f"kept upstream contribution metric in {target}")
