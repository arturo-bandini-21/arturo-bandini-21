#!/usr/bin/env python3
"""Swap the public-repo commit count on the ASCII cards for real contributions.

gh.crafter.run derives "Commits" by summing the commits authored across the
account's *public* repos — it never reads the contribution calendar. With most of
the work living in private repos that number is frozen and understates reality
(98 public commits vs ~174 actual contributions). This script replaces that
column with the calendar total, which does include private contributions because
the account opts into publishing them.

Rewrites in place, preserving the card's fixed-width columns and theme colors.
Idempotent: re-running only refreshes the number.
"""

import json
import os
import re
import sys
import urllib.request

API = "https://api.github.com/graphql"
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions }
    }
  }
}
"""

LABEL = ". Contributions: "

# Left column of the GitHub Stats row: label + dot leader + value. Both columns are
# padded to a fixed width, so the leader has to absorb whatever the new label and
# number cost — otherwise the ` | ` separator drifts out of alignment.
STATS_LEFT = re.compile(
    r'(?P<head><text x="\d+" y="\d+"[^>]*>)'
    r'<tspan fill="(?P<c_label>#[0-9a-fA-F]{6})">(?P<label>\. (?:Commits|Contributions): )</tspan>'
    r'<tspan fill="(?P<c_leader>#[0-9a-fA-F]{6})">(?P<leader>\.+)</tspan>'
    r'<tspan fill="(?P<c_value>#[0-9a-fA-F]{6})">(?P<value> \d+)</tspan>'
)


def fetch_contributions(login: str, token: str) -> int:
    request = urllib.request.Request(
        API,
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-card",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")

    total = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"][
        "totalContributions"
    ]
    # A zero here means the token could not see the calendar. Committing that would
    # silently replace a real number with a lie, so refuse instead.
    if not isinstance(total, int) or total <= 0:
        raise RuntimeError(f"implausible contribution total: {total!r}")
    return total


def patch(path: str, total: int) -> None:
    with open(path, encoding="utf-8") as f:
        svg = f.read()

    match = STATS_LEFT.search(svg)
    if not match:
        raise RuntimeError(f"GitHub Stats row not found in {path}")

    value = f" {total}"
    width = len(match.group("label")) + len(match.group("leader")) + len(match.group("value"))
    leader = "." * max(1, width - len(LABEL) - len(value))

    replacement = (
        f'{match.group("head")}'
        f'<tspan fill="{match.group("c_label")}">{LABEL}</tspan>'
        f'<tspan fill="{match.group("c_leader")}">{leader}</tspan>'
        f'<tspan fill="{match.group("c_value")}">{value}</tspan>'
    )
    svg = svg[: match.start()] + replacement + svg[match.end() :]

    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"ERROR: {name} is not set")
    return value


if __name__ == "__main__":
    contributions = fetch_contributions(require_env("GH_USER"), require_env("GITHUB_TOKEN"))
    print(f"contributions in the last year: {contributions}")
    for target in sys.argv[1:]:
        patch(target, contributions)
        print(f"patched contributions into {target}")
