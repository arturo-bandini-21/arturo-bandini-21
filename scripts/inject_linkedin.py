#!/usr/bin/env python3
"""Re-add the LinkedIn entry to the Contact block of the ASCII profile cards.

gh.crafter.run renders the Contact block from the GitHub profile's website and
handle only — it ignores the account's social links. This script re-inserts the
LinkedIn line after every refresh so it survives the daily regeneration.

Idempotent: does nothing if the card already contains a LinkedIn entry.
"""

import re
import sys

LABEL = ". LinkedIn: "
VALUE = " linkedin.com/in/alonso-diego-lamilla-meza"
VALUE_COLUMN = 30  # chars of "label + dot leader" so the value lines up with the others
LINE_HEIGHT = 20

# Matches the existing GitHub contact line and captures its colors so the injected
# LinkedIn line inherits them — works for both the dark and light themed cards.
GITHUB_LINE = re.compile(
    r'<text x="(?P<x>\d+)" y="(?P<y>\d+)"(?P<attrs>[^>]*)>'
    r'<tspan fill="(?P<c_label>#[0-9a-fA-F]{6})">\. GitHub: </tspan>'
    r'<tspan fill="(?P<c_leader>#[0-9a-fA-F]{6})">\.+</tspan>'
    r'<tspan fill="(?P<c_value>#[0-9a-fA-F]{6})"> github\.com/[^<]*</tspan></text>'
)


def inject(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        svg = f.read()

    if "LinkedIn" in svg:
        return False

    match = GITHUB_LINE.search(svg)
    if not match:
        print(f"WARN: GitHub contact line not found in {path}; skipping", file=sys.stderr)
        return False

    leader = "." * max(1, VALUE_COLUMN - len(LABEL))
    new_line = (
        f'\n  <text x="{match.group("x")}" y="{int(match.group("y")) + LINE_HEIGHT}"'
        f'{match.group("attrs")}>'
        f'<tspan fill="{match.group("c_label")}">{LABEL}</tspan>'
        f'<tspan fill="{match.group("c_leader")}">{leader}</tspan>'
        f'<tspan fill="{match.group("c_value")}">{VALUE}</tspan></text>'
    )
    svg = svg[: match.end()] + new_line + svg[match.end() :]

    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return True


if __name__ == "__main__":
    for target in sys.argv[1:]:
        print(f"injected LinkedIn into {target}" if inject(target) else f"no change for {target}")
